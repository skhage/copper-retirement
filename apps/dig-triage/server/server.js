/**
 * server.js
 * Express backend for the Dig-Safe Triage Console (P7-TRIAGE).
 * Serves the Vite-built React frontend + mock API endpoints.
 * Demo Beat 3: "Dig crew hit something — triage/reroute fast?"
 */
import express from 'express';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
app.use(express.json());

// Serve built React frontend from dist/
app.use(express.static(path.join(__dirname, '..', 'dist')));

// --- POST /api/triage/chat ---
// Proxy to P6-TRIAGE agent Model Serving endpoint.
// Returns mock agent responses until P6-TRIAGE is deployed.
app.post('/api/triage/chat', (req, res) => {
  const { incidentId, message } = req.body;
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
    sources: ['network_route topology', 'device_service_allocation', 'alarm history'],
  });
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
});