/**
 * server.js
 * Express backend for the Dig-Safe Triage Console (P7-TRIAGE).
 * Serves the Vite-built React frontend + API endpoints.
 * Demo Beat 3: "Dig crew hit something — triage/reroute fast?"
 *
 * V2 (2026-09-20): Integrated UC triage functions:
 *   - incident_lookup  → GET /api/triage/incident/:id
 *   - proximity_search → POST /api/triage/nearby
 *   - reroute_suggest  → GET /api/triage/reroute/:id
 *   - Enhanced /api/triage/chat with live reroute data
 */
import express from 'express';
import { fileURLToPath } from 'url';
import path from 'path';
import {
  incidentLookup,
  proximitySearch,
  rerouteSuggest,
  healthCheck,
} from './databricksSQL.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
app.use(express.json());

// Serve built React frontend from dist/
app.use(express.static(path.join(__dirname, '..', 'dist')));

// ============================================================
// UC Function Endpoints (V2 — live data from silver_dig_incident_enriched)
// ============================================================

// --- GET /api/triage/incident/:id ---
// Lookup enriched incident details via UC incident_lookup function.
app.get('/api/triage/incident/:id', async (req, res) => {
  try {
    const id = parseInt(req.params.id, 10);
    if (isNaN(id)) return res.status(400).json({ error: 'Invalid incident ID' });

    console.log(`[dig-triage] incident_lookup(${id})`);
    const result = await incidentLookup(id);

    if (!result) return res.status(404).json({ error: `Incident ${id} not found` });
    res.json({ success: true, data: result });
  } catch (err) {
    console.error('[dig-triage] incident_lookup error:', err.message);
    res.status(500).json({ error: 'Failed to lookup incident', detail: err.message });
  }
});

// --- POST /api/triage/nearby ---
// Find nearby incidents via UC proximity_search function.
// Body: { latitude, longitude, radius_km? }
app.post('/api/triage/nearby', async (req, res) => {
  try {
    const { latitude, longitude, radius_km } = req.body;
    if (latitude == null || longitude == null) {
      return res.status(400).json({ error: 'latitude and longitude are required' });
    }

    const radius = radius_km ?? 25;
    console.log(`[dig-triage] proximity_search(${latitude}, ${longitude}, ${radius})`);
    const results = await proximitySearch(latitude, longitude, radius);

    res.json({ success: true, count: results.length, data: results });
  } catch (err) {
    console.error('[dig-triage] proximity_search error:', err.message);
    res.status(500).json({ error: 'Failed to search nearby incidents', detail: err.message });
  }
});

// --- GET /api/triage/reroute/:id ---
// Get reroute suggestions via UC reroute_suggest function.
app.get('/api/triage/reroute/:id', async (req, res) => {
  try {
    const id = parseInt(req.params.id, 10);
    if (isNaN(id)) return res.status(400).json({ error: 'Invalid incident ID' });

    console.log(`[dig-triage] reroute_suggest(${id})`);
    const result = await rerouteSuggest(id);

    if (!result) return res.status(404).json({ error: `No reroute suggestion for ${id}` });
    res.json({ success: true, data: result });
  } catch (err) {
    console.error('[dig-triage] reroute_suggest error:', err.message);
    res.status(500).json({ error: 'Failed to get reroute suggestion', detail: err.message });
  }
});

// --- GET /api/triage/health ---
// Health check for SQL connectivity.
app.get('/api/triage/health', async (req, res) => {
  const sqlOk = await healthCheck();
  res.json({
    status: sqlOk ? 'healthy' : 'degraded',
    sql_connected: sqlOk,
    timestamp: new Date().toISOString(),
    env: {
      host_set: !!process.env.DATABRICKS_HOST,
      warehouse_set: !!process.env.DATABRICKS_WAREHOUSE_ID,
      token_set: !!process.env.DATABRICKS_TOKEN,
    },
  });
});

// ============================================================
// Original Endpoints (mock agent + incident submission)
// ============================================================

// --- POST /api/triage/chat ---
// Triage agent chat. Uses live UC functions when available,
// falls back to mock responses if SQL is not configured.
app.post('/api/triage/chat', async (req, res) => {
  const { incidentId, message } = req.body;

  try {
    // Try to enrich with live UC function data
    const numericId = parseInt(String(incidentId).replace('INC-', ''), 10);
    let liveData = null;
    let rerouteData = null;

    if (!isNaN(numericId) && process.env.DATABRICKS_TOKEN) {
      [liveData, rerouteData] = await Promise.all([
        incidentLookup(numericId).catch(() => null),
        rerouteSuggest(numericId).catch(() => null),
      ]);
    }

    if (liveData) {
      // Build response from live UC function data
      const actions = [];
      if (rerouteData) {
        actions.push({
          action_id: `act_${Date.now()}`,
          type: rerouteData.reroute_option?.toLowerCase() || 'reroute',
          description: rerouteData.reroute_rationale || 'Reroute recommended',
          priority: liveData.triage_priority === 'P1' ? 'critical'
            : liveData.triage_priority === 'P2' ? 'high'
            : liveData.triage_priority === 'P3' ? 'medium' : 'low',
          affected_customers: parseInt(liveData.impacted_customer_count, 10) || 0,
          estimated_time_hours: liveData.reroute_required ? 3.0 : 1.0,
          status: 'pending_approval',
        });
      }

      const serviceSummary = liveData.impacted_service_types
        ? ` Impacted services: ${liveData.impacted_service_types}.`
        : '';

      res.json({
        response:
          `[Triage Agent] Incident ${liveData.incident_id} in ${liveData.state}: ` +
          `${liveData.severity?.toUpperCase()} ${liveData.cable_damage_type} (${liveData.root_cause}). ` +
          `Priority: ${liveData.triage_priority}. ` +
          `Nearest device: ${liveData.nearest_device_type} (${parseFloat(liveData.nearest_device_distance_km || 0).toFixed(1)} km). ` +
          `Affected customers: ${liveData.impacted_customer_count || 0}.${serviceSummary} ` +
          `Recommended action: ${liveData.recommended_action?.replace(/_/g, ' ')}.` +
          (rerouteData?.reroute_option
            ? ` Reroute: ${rerouteData.reroute_option.replace(/_/g, ' ')} — ${rerouteData.reroute_rationale}`
            : ''),
        actions,
        confidence: 0.92,
        sources: [
          'cdm_tmforum.copper_retirement.incident_lookup',
          'cdm_tmforum.copper_retirement.reroute_suggest',
          'silver_dig_incident_enriched',
        ],
        live_data: true,
        wire_center: liveData.wire_center_name || null,
      });
    } else {
      // Fallback to mock response
      res.json({
        response:
          `[Mock Agent] Analyzing incident ${incidentId}: ${message}. ` +
          'Recommending immediate reroute via alternate conduit path. ' +
          'Affected customers: 47. Priority: HIGH.',
        actions: [
          {
            action_id: `act_${Date.now()}`,
            type: 'reroute',
            description: 'Reroute traffic via alternate conduit path B-7',
            priority: 'high',
            affected_customers: 47,
            estimated_time_hours: 2.5,
            status: 'pending_approval',
          },
        ],
        confidence: 0.87,
        sources: ['mock_data'],
        live_data: false,
      });
    }
  } catch (err) {
    console.error('[dig-triage] chat error:', err.message);
    // Graceful fallback to mock on any error
    res.json({
      response:
        `[Mock Agent] Analyzing incident ${incidentId}: ${message}. ` +
        'Recommending immediate reroute via alternate conduit path. ' +
        'Affected customers: 47. Priority: HIGH.',
      actions: [
        {
          action_id: `act_${Date.now()}`,
          type: 'reroute',
          description: 'Reroute traffic via alternate conduit path B-7',
          priority: 'high',
          affected_customers: 47,
          estimated_time_hours: 2.5,
          status: 'pending_approval',
        },
      ],
      confidence: 0.87,
      sources: ['mock_data (fallback)'],
      live_data: false,
    });
  }
});

// --- POST /api/triage/incident ---
// Submit new dig-safe incident.
// TODO: Write to Lakebase `dig_incidents` table once P5-SCHEMA lands.
app.post('/api/triage/incident', (req, res) => {
  const incident = req.body;
  console.log('[dig-triage] New incident submitted:', JSON.stringify(incident));
  res.json({
    success: true,
    incident_id: `INC-${Date.now()}`,
    message: 'Incident logged (mock \u2014 Lakebase write-back pending P5-SCHEMA)',
  });
});

// --- POST /api/triage/action ---
// Human-in-loop approve/reject agent action.
// TODO: Write to Lakebase audit table once P5-SCHEMA lands.
app.post('/api/triage/action', (req, res) => {
  const { action_id, decision, reviewer } = req.body;
  console.log(`[dig-triage] Action ${action_id}: ${decision} by ${reviewer}`);
  res.json({
    success: true,
    action_id,
    decision,
    timestamp: new Date().toISOString(),
  });
});

// SPA fallback \u2014 serve index.html for client-side routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'dist', 'index.html'));
});

const port = parseInt(process.env.DATABRICKS_APP_PORT || '8000', 10);
app.listen(port, '0.0.0.0', () => {
  console.log(`[dig-triage] Server listening on 0.0.0.0:${port}`);
  console.log(`[dig-triage] UC functions: ${process.env.DATABRICKS_TOKEN ? 'ENABLED' : 'DISABLED (no token)'}`);
  console.log(`[dig-triage] SQL warehouse: ${process.env.DATABRICKS_WAREHOUSE_ID || 'NOT SET'}`);
});