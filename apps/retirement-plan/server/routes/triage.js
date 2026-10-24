/**
 * routes/triage.js — Dig Triage tab API (ACC-APP-PORT-TRIAGE).
 * Ported from the retired standalone dig-triage app (server/server.js + server/databricksSQL.js, 2026-10-24).
 * Mounted at /api/triage by server/server.js. Shares the single SQL-warehouse helper (databricksSQL.executeSQL).
 *
 * Data (reused, nothing new created):
 *   UC functions cdm_tmforum.copper_retirement.incident_lookup / proximity_search / reroute_suggest
 *   cdm_tmforum.copper_retirement.silver_dig_incident_enriched  (5,000 rows, SYNTHETIC)
 *   cdm_tmforum.provable_resilience_intelligence.stg_811_dig_ticket (3,000 rows, origin=INGESTED; directive 13)
 */
import express from 'express';
import { executeSQL } from '../databricksSQL.js';

const CATALOG = process.env.CATALOG || 'cdm_tmforum';
const SCHEMA = process.env.SCHEMA || 'copper_retirement';
const FQ = `${CATALOG}.${SCHEMA}`;
const T811 = process.env.DIG_811_TABLE || 'cdm_tmforum.provable_resilience_intelligence.stg_811_dig_ticket';

const bool = (v) => v === true || v === 'true';
const toId = (v) => {
  const id = parseInt(String(v).replace(/^INC-/i, ''), 10);
  if (isNaN(id)) throw Object.assign(new Error(`Invalid incident ID: ${v}`), { status: 400 });
  return id;
};

// ---------- data functions (inline SQL; all inputs coerced to numbers / whitelisted) ----------
async function incidentLookup(id) {
  const rows = await executeSQL(`SELECT * FROM ${FQ}.incident_lookup(${toId(id)})`);
  return rows[0] || null;
}

async function proximitySearch(lat, lon, radiusKm = 25) {
  const la = parseFloat(lat), lo = parseFloat(lon), r = parseFloat(radiusKm);
  if ([la, lo, r].some(isNaN)) throw Object.assign(new Error('Invalid lat/lon/radius'), { status: 400 });
  return executeSQL(`SELECT * FROM ${FQ}.proximity_search(${la}, ${lo}, ${r})`);
}

async function rerouteSuggest(id) {
  const rows = await executeSQL(`SELECT * FROM ${FQ}.reroute_suggest(${toId(id)})`);
  return rows[0] || null;
}

async function fetchIncidentList(limit = 100) {
  const rows = await executeSQL(`
    SELECT CONCAT('INC-', CAST(incident_id AS STRING)) AS incident_id,
      CAST(incident_date AS STRING) AS incident_date, CAST(incident_timestamp AS STRING) AS incident_timestamp,
      severity, cable_type, cable_damage_type, root_cause, state,
      CAST(incident_latitude AS DOUBLE) AS latitude, CAST(incident_longitude AS DOUBLE) AS longitude,
      CAST(resolution_time_hours AS DOUBLE) AS resolution_time_hours, reroute_required, service_interruption,
      affected_pair_count, CAST(repair_cost_amount AS DOUBLE) AS repair_cost, contractor_at_fault, one_call_ticket_submitted,
      CASE WHEN resolution_time_hours IS NOT NULL AND resolution_time_hours > 0 THEN 'resolved'
           WHEN reroute_required = true AND service_interruption = true THEN 'open'
           WHEN severity = 'critical' THEN 'open' ELSE 'in_progress' END AS status,
      work_id, triage_priority, recommended_action
    FROM ${FQ}.silver_dig_incident_enriched
    ORDER BY incident_date DESC
    LIMIT ${Math.min(parseInt(limit, 10) || 100, 500)}`);
  return rows.map((r) => ({
    ...r,
    latitude: parseFloat(r.latitude) || 0,
    longitude: parseFloat(r.longitude) || 0,
    resolution_time_hours: r.resolution_time_hours ? parseFloat(r.resolution_time_hours) : null,
    repair_cost: parseFloat(r.repair_cost) || 0,
    affected_pair_count: parseInt(r.affected_pair_count, 10) || 0,
    work_id: r.work_id ? parseInt(r.work_id, 10) : null,
    reroute_required: bool(r.reroute_required),
    service_interruption: bool(r.service_interruption),
    contractor_at_fault: bool(r.contractor_at_fault),
    one_call_ticket_submitted: bool(r.one_call_ticket_submitted),
    contractor_name: 'N/A',
  }));
}

async function fetchIncidentKPIs() {
  const [r = {}] = await executeSQL(`
    SELECT COUNT(*) FILTER (WHERE resolution_time_hours IS NULL OR resolution_time_hours = 0) AS open_incidents,
      ROUND(AVG(CASE WHEN resolution_time_hours > 0 THEN resolution_time_hours END), 1) AS avg_resolution_hours,
      COUNT(*) FILTER (WHERE incident_date >= DATE_SUB(CURRENT_DATE(), 7)) AS incidents_this_week,
      COUNT(*) FILTER (WHERE reroute_required = true AND (resolution_time_hours IS NULL OR resolution_time_hours = 0)) AS reroutes_pending,
      COUNT(*) FILTER (WHERE severity = 'critical' AND (resolution_time_hours IS NULL OR resolution_time_hours = 0)) AS critical_incidents
    FROM ${FQ}.silver_dig_incident_enriched`);
  return {
    open_incidents: parseInt(r.open_incidents, 10) || 0,
    avg_resolution_hours: parseFloat(r.avg_resolution_hours) || 0,
    incidents_this_week: parseInt(r.incidents_this_week, 10) || 0,
    reroutes_pending: parseInt(r.reroutes_pending, 10) || 0,
    active_contractors: 1254,
    critical_incidents: parseInt(r.critical_incidents, 10) || 0,
  };
}

/** 811 / one-call tickets (directive 13 reuse). state must be a 2-letter code (whitelisted, no injection). */
async function fetch811Summary(state) {
  const st = state && /^[A-Za-z]{2}$/.test(state) ? state.toUpperCase() : null;
  const where = st ? `WHERE state = '${st}'` : '';
  return executeSQL(`
    SELECT state, ticket_status, COUNT(*) AS tickets,
      SUM(CASE WHEN emergency_flag THEN 1 ELSE 0 END) AS emergency_tickets,
      SUM(CASE WHEN utility_type IN ('copper','telecom','fiber') THEN 1 ELSE 0 END) AS telecom_tickets,
      MAX(origin) AS origin, MAX(source_system) AS source_system
    FROM ${T811} ${where}
    GROUP BY state, ticket_status ORDER BY tickets DESC LIMIT 200`);
}

// ---------- router ----------
const router = express.Router();
const wrap = (fn) => (req, res) => fn(req, res).catch((err) => {
  console.error(`[accelerator:triage] ${req.method} ${req.path}:`, err.message);
  res.status(err.status || 500).json({ error: err.message });
});

router.get('/incident/:id', wrap(async (req, res) => {
  const data = await incidentLookup(req.params.id);
  if (!data) return res.status(404).json({ error: `Incident ${req.params.id} not found` });
  res.json({ success: true, data });
}));

router.post('/nearby', wrap(async (req, res) => {
  const { latitude, longitude, radius_km } = req.body || {};
  if (latitude == null || longitude == null) return res.status(400).json({ error: 'latitude and longitude are required' });
  const data = await proximitySearch(latitude, longitude, radius_km ?? 25);
  res.json({ success: true, count: data.length, data });
}));

router.get('/reroute/:id', wrap(async (req, res) => {
  const data = await rerouteSuggest(req.params.id);
  if (!data) return res.status(404).json({ error: `No reroute suggestion for ${req.params.id}` });
  res.json({ success: true, data });
}));

router.get('/incidents', wrap(async (req, res) => {
  const data = await fetchIncidentList(req.query.limit);
  res.json({ success: true, count: data.length, data });
}));

router.get('/kpis', wrap(async (_req, res) => res.json({ success: true, data: await fetchIncidentKPIs() })));

router.get('/811', wrap(async (req, res) => {
  const data = await fetch811Summary(req.query.state);
  res.json({ success: true, count: data.length, source: T811, data });
}));

router.get('/health', async (_req, res) => {
  let ok = false;
  try { ok = (await executeSQL('SELECT 1 AS ok'))[0]?.ok === '1'; } catch { ok = false; }
  res.json({ status: ok ? 'healthy' : 'degraded', sql_connected: ok, timestamp: new Date().toISOString() });
});

const mockChat = (incidentId, message, tag = 'mock_data') => ({
  response: `[Mock Agent] Analyzing incident ${incidentId}: ${message}. Recommending immediate reroute via alternate conduit path. Affected customers: 47. Priority: HIGH.`,
  actions: [{ action_id: `act_${Date.now()}`, type: 'reroute', description: 'Reroute traffic via alternate conduit path B-7', priority: 'high', affected_customers: 47, estimated_time_hours: 2.5, status: 'pending_approval' }],
  confidence: 0.87,
  sources: [tag],
  live_data: false,
});

// Triage agent chat: live UC function data when SQL is reachable, mock fallback otherwise (labeled live_data=false).
router.post('/chat', async (req, res) => {
  const { incidentId, message } = req.body || {};
  try {
    const [live, reroute] = await Promise.all([
      incidentLookup(incidentId).catch(() => null),
      rerouteSuggest(incidentId).catch(() => null),
    ]);
    if (!live) return res.json(mockChat(incidentId, message));
    const prio = { P1: 'critical', P2: 'high', P3: 'medium' }[live.triage_priority] || 'low';
    const actions = reroute ? [{
      action_id: `act_${Date.now()}`,
      type: reroute.reroute_option?.toLowerCase() || 'reroute',
      description: reroute.reroute_rationale || 'Reroute recommended',
      priority: prio,
      affected_customers: parseInt(live.impacted_customer_count, 10) || 0,
      estimated_time_hours: bool(live.reroute_required) ? 3.0 : 1.0,
      status: 'pending_approval',
    }] : [];
    const svc = live.impacted_service_types ? ` Impacted services: ${live.impacted_service_types}.` : '';
    res.json({
      response:
        `[Triage Agent] Incident ${live.incident_id} in ${live.state}: ${live.severity?.toUpperCase()} ${live.cable_damage_type} (${live.root_cause}). ` +
        `Priority: ${live.triage_priority}. Nearest device: ${live.nearest_device_type} (${parseFloat(live.nearest_device_distance_km || 0).toFixed(1)} km). ` +
        `Affected customers: ${live.impacted_customer_count || 0}.${svc} Recommended action: ${live.recommended_action?.replace(/_/g, ' ')}.` +
        (reroute?.reroute_option ? ` Reroute: ${reroute.reroute_option.replace(/_/g, ' ')} — ${reroute.reroute_rationale}` : ''),
      actions,
      confidence: 0.92,
      sources: [`${FQ}.incident_lookup`, `${FQ}.reroute_suggest`, `${FQ}.silver_dig_incident_enriched`],
      live_data: true,
      wire_center: live.wire_center_name || null,
    });
  } catch (err) {
    console.error('[accelerator:triage] chat error:', err.message);
    res.json(mockChat(incidentId, message, 'mock_data (fallback)'));
  }
});

// Incident submission + human-in-loop action log. Mock until Lakebase copper_app.incident_actions write-back is wired.
router.post('/incident', (req, res) => {
  console.log('[accelerator:triage] new incident:', JSON.stringify(req.body));
  res.json({ success: true, incident_id: `INC-${Date.now()}`, message: 'Incident logged (mock — Lakebase write-back pending)' });
});

router.post('/action', (req, res) => {
  const { action_id, decision, reviewer } = req.body || {};
  console.log(`[accelerator:triage] action ${action_id}: ${decision} by ${reviewer}`);
  res.json({ success: true, action_id, decision, timestamp: new Date().toISOString() });
});

export default router;
