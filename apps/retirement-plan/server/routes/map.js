/**
 * routes/map.js — Map & Risk tab API (ACC-APP-PORT-MAP).
 * Ported 2026-10-25 from the retired standalone copper-map Dash app (app.py + data.py).
 * Mounted at /api/map by server/server.js. Shares the single SQL-warehouse helper (databricksSQL.executeSQL).
 *
 * Data (reused, nothing new created; all SYNTHETIC and labeled in the UI):
 *   ${CATALOG}.${SCHEMA}.gold_retirement_executive_summary  (6 footprint states, DEC-DSI-FOOTPRINT)
 *   ${CATALOG}.${SCHEMA}.gold_wire_center_scorecard         (103 wire centers, readiness + priority rank)
 *   ${CATALOG}.${SCHEMA}.copper_risk_predictions            (2,672 devices scored by champion V5 via the SERVING_ENDPOINT model endpoint)
 *   ${CATALOG}.tmf_enterprise.physical_device + ${CATALOG}.tmf_shared.geographic_address (device location)
 *   ${CATALOG}.${SCHEMA}.copper_retirement_project_status / copper_customers_impacted / copper_ebitda_impact_achieved
 *     (governed UC metric views; headline KPIs, same numbers as copper-map + PARTNER-PLAYBOOK §5; ACC-APP-MAP-TAB-CODE)
 * All user input goes through Statement API named parameters (no string interpolation of input).
 */
import express from 'express';
import { executeSQL } from '../databricksSQL.js';

const CATALOG = process.env.CATALOG || 'cdm_tmforum';
const SCHEMA = process.env.SCHEMA || 'copper_retirement';
const FQ = `${CATALOG}.${SCHEMA}`;
// ACC-APP-SERVING-ENDPOINT-VAR: risk model serving endpoint name is partner-configurable (bundle var serving_endpoint).
const SERVING_ENDPOINT = process.env.SERVING_ENDPOINT || 'copper-retirement-risk';
// Legacy LakeLink footprint (DEC-DSI-FOOTPRINT): only these states have wire centers + the cited jurisdiction matrix.
const FOOTPRINT = (process.env.FOOTPRINT_STATES || 'CO,MN,WA,OR,ID,AZ').split(',').map((s) => s.trim().toUpperCase()).filter((s) => /^[A-Z]{2}$/.test(s));
const FOOT_SQL = `(${FOOTPRINT.map((s) => `'${s}'`).join(',')})`; // whitelisted 2-letter codes only
const TIERS = ['critical', 'high', 'medium', 'low'];

const stateParam = (v) => (v && /^[A-Za-z]{2}$/.test(v) ? v.toUpperCase() : 'ALL');
const tierParam = (v) => (TIERS.includes(String(v || '').toLowerCase()) ? String(v).toLowerCase() : 'ALL');
const num = (v) => (v == null || v === '' ? null : Number(v));
const int = (v) => (v == null || v === '' ? 0 : parseInt(v, 10) || 0);

async function fetchKpis() {
  const [r = {}] = await executeSQL(`
    WITH es AS (SELECT * FROM ${FQ}.gold_retirement_executive_summary WHERE state_code IN ${FOOT_SQL}),
         p  AS (SELECT predicted_risk_tier AS t, model_version FROM ${FQ}.copper_risk_predictions)
    SELECT (SELECT SUM(total_copper_devices) FROM es) AS footprint_devices,
      (SELECT SUM(wire_center_count) FROM es) AS wire_centers,
      (SELECT SUM(total_affected_customers) FROM es) AS customers_affected,
      (SELECT ROUND(SUM(fiber_ready_devices) * 100.0 / NULLIF(SUM(total_copper_devices), 0), 1) FROM es) AS fiber_ready_pct,
      (SELECT SUM(critical_risk_count) FROM es) AS footprint_critical,
      (SELECT SUM(high_risk_count) FROM es) AS footprint_high,
      (SELECT COUNT(*) FROM es) AS footprint_states,
      (SELECT COUNT(*) FROM p) AS scored_devices,
      (SELECT COUNT(*) FROM p WHERE t = 'critical') AS scored_critical,
      (SELECT COUNT(*) FROM p WHERE t = 'high') AS scored_high,
      (SELECT MAX(model_version) FROM p) AS model_version`);
  return {
    footprint_devices: int(r.footprint_devices), wire_centers: int(r.wire_centers), customers_affected: int(r.customers_affected),
    fiber_ready_pct: num(r.fiber_ready_pct) ?? 0, footprint_critical: int(r.footprint_critical), footprint_high: int(r.footprint_high),
    footprint_states: int(r.footprint_states), scored_devices: int(r.scored_devices), scored_critical: int(r.scored_critical),
    scored_high: int(r.scored_high), model_version: r.model_version || null, footprint: FOOTPRINT,
    serving_endpoint: SERVING_ENDPOINT,
  };
}

// ACC-APP-MAP-TAB-CODE: headline KPIs come from the governed metric views (parity with copper-map
// ACC-APP-DEF-PLANB-KPI-MISMATCH). Verified 2026-10-31: 2,672 devices, 103 WCs, 383 (14.3%) critical,
// 122 (4.6%) fiber ready, 288 customers / 304 services, $603.8M annual revenue at risk.
async function fetchGovernedKpis() {
  const ps = `${FQ}.copper_retirement_project_status`;
  const ci = `${FQ}.copper_customers_impacted`;
  const eb = `${FQ}.copper_ebitda_impact_achieved`;
  const [r = {}] = await executeSQL(`
    SELECT
      (SELECT MEASURE(\`Total Copper Devices\`) FROM ${ps}) AS total_devices,
      (SELECT MEASURE(\`Critical Risk Devices\`) FROM ${ps}) AS critical_devices,
      (SELECT CAST(MEASURE(\`Critical Risk Pct\`) AS DOUBLE) FROM ${ps}) AS critical_pct,
      (SELECT MEASURE(\`Fiber Ready Devices\`) FROM ${ps}) AS fiber_ready_devices,
      (SELECT CAST(MEASURE(\`Fiber Ready Pct\`) AS DOUBLE) FROM ${ps}) AS fiber_ready_pct,
      (SELECT MEASURE(\`Unique Wire Centers\`) FROM ${ps}) AS wire_centers,
      (SELECT MEASURE(\`Customers Impacted\`) FROM ${ci}) AS customers,
      (SELECT MEASURE(\`Services at Risk\`) FROM ${ci}) AS services,
      (SELECT CAST(MEASURE(\`Total Annual Revenue at Risk\`) AS DOUBLE) FROM ${eb}) AS annual_revenue_at_risk`);
  const pct = (v) => (num(v) == null ? null : Math.round(num(v) * 10) / 10);
  return {
    total_devices: int(r.total_devices), critical_devices: int(r.critical_devices), critical_pct: pct(r.critical_pct),
    fiber_ready_devices: int(r.fiber_ready_devices), fiber_ready_pct: pct(r.fiber_ready_pct), wire_centers: int(r.wire_centers),
    customers: int(r.customers), services: int(r.services), annual_revenue_at_risk: num(r.annual_revenue_at_risk),
  };
}

// UC objects the app service principal must be able to read for this tab (feeds the H1a grant list).
const UC_OBJECTS = [
  `${FQ}.gold_retirement_executive_summary`, `${FQ}.gold_wire_center_scorecard`, `${FQ}.copper_risk_predictions`,
  `${FQ}.copper_retirement_project_status`, `${FQ}.copper_customers_impacted`, `${FQ}.copper_ebitda_impact_achieved`,
  `${CATALOG}.tmf_enterprise.physical_device`, `${CATALOG}.tmf_shared.geographic_address`,
];

async function fetchStates() {
  const rows = await executeSQL(`
    SELECT state_code, total_copper_devices, critical_risk_count, high_risk_count, wire_center_count,
      CAST(fiber_ready_pct AS DOUBLE) AS fiber_ready_pct, total_affected_customers, total_dig_incidents,
      regulatory_violations, program_health_status
    FROM ${FQ}.gold_retirement_executive_summary WHERE state_code IN ${FOOT_SQL}
    ORDER BY total_copper_devices DESC`);
  return rows.map((r) => ({
    state: r.state_code, devices: int(r.total_copper_devices), critical: int(r.critical_risk_count), high: int(r.high_risk_count),
    wire_centers: int(r.wire_center_count), fiber_ready_pct: num(r.fiber_ready_pct) ?? 0, customers: int(r.total_affected_customers),
    dig_incidents: int(r.total_dig_incidents), regulatory_violations: int(r.regulatory_violations), health: r.program_health_status,
  }));
}

async function fetchWireCenters(state) {
  const rows = await executeSQL(`
    SELECT wire_center_id, wire_center_name, clli_code, state_code,
      CAST(fiber_ready AS STRING) AS fiber_ready, CAST(puc_filing_required AS STRING) AS puc_filing_required, puc_name,
      copper_device_count, critical_risk_devices, high_risk_devices, affected_customer_count,
      CAST(retirement_readiness_score AS DOUBLE) AS readiness, retirement_priority_rank AS priority_rank,
      (CAST(bbox_min_lat AS DOUBLE) + CAST(bbox_max_lat AS DOUBLE)) / 2 AS lat,
      (CAST(bbox_min_lon AS DOUBLE) + CAST(bbox_max_lon AS DOUBLE)) / 2 AS lon
    FROM ${FQ}.gold_wire_center_scorecard
    WHERE (:state = 'ALL' OR state_code = :state)
    ORDER BY retirement_priority_rank ASC LIMIT 500`, [{ name: 'state', value: state }]);
  return rows.map((r) => ({
    id: r.wire_center_id, name: r.wire_center_name, clli: r.clli_code, state: r.state_code,
    fiber_ready: r.fiber_ready === 'true', puc_filing_required: r.puc_filing_required === 'true', puc_name: r.puc_name,
    devices: int(r.copper_device_count), critical: int(r.critical_risk_devices), high: int(r.high_risk_devices),
    customers: int(r.affected_customer_count), readiness: num(r.readiness) ?? 0, priority_rank: int(r.priority_rank),
    lat: num(r.lat), lon: num(r.lon),
  }));
}

async function fetchDevices(state, tier) {
  const rows = await executeSQL(`
    SELECT CAST(p.physical_device_id AS STRING) AS id, p.device_type, p.device_status, p.predicted_risk_tier AS tier,
      ROUND(p.max_confidence, 3) AS confidence, ga.state_or_province AS state,
      ROUND(CAST(ga.latitude AS DOUBLE), 3) AS lat, ROUND(CAST(ga.longitude AS DOUBLE), 3) AS lon
    FROM ${FQ}.copper_risk_predictions p
    JOIN ${CATALOG}.tmf_enterprise.physical_device pd ON pd.physical_device_id = p.physical_device_id
    JOIN ${CATALOG}.tmf_shared.geographic_address ga ON ga.geographic_address_id = pd.geographic_address_id
    WHERE (:state = 'ALL' OR ga.state_or_province = :state) AND (:tier = 'ALL' OR p.predicted_risk_tier = :tier)
    ORDER BY CASE p.predicted_risk_tier WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END,
      p.max_confidence DESC
    LIMIT 3000`, [{ name: 'state', value: state }, { name: 'tier', value: tier }]);
  return rows.map((r) => ({
    id: r.id, type: r.device_type, status: r.device_status, tier: r.tier, confidence: num(r.confidence),
    state: r.state, lat: num(r.lat), lon: num(r.lon),
  }));
}

// ---------- router ----------
const router = express.Router();
const wrap = (fn) => (req, res) => fn(req, res).catch((err) => {
  console.error(`[accelerator:map] ${req.method} ${req.path}:`, err.message);
  res.status(err.status || 500).json({ error: err.message });
});

router.get('/kpis', wrap(async (_req, res) => {
  const [footprint, governed] = await Promise.all([fetchKpis(), fetchGovernedKpis()]);
  res.json({ success: true, synthetic: true, data: { ...footprint, governed } });
}));
router.get('/states', wrap(async (_req, res) => {
  const data = await fetchStates();
  res.json({ success: true, synthetic: true, count: data.length, data });
}));
router.get('/wire-centers', wrap(async (req, res) => {
  const data = await fetchWireCenters(stateParam(req.query.state));
  res.json({ success: true, synthetic: true, count: data.length, data });
}));
router.get('/devices', wrap(async (req, res) => {
  const data = await fetchDevices(stateParam(req.query.state), tierParam(req.query.tier));
  res.json({ success: true, synthetic: true, count: data.length, data });
}));
// No SQL here, so it still answers when the SP lacks grants (the client uses uc_objects in its 'Data access pending' state).
router.get('/filters', (_req, res) => res.json({ success: true, data: { footprint: FOOTPRINT, tiers: TIERS, uc_objects: UC_OBJECTS } }));

export default router;
