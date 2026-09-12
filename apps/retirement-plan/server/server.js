/**
 * server.js
 * Express backend for the Retirement Plan Tracker (P7-PLAN).
 * Serves the Vite-built React frontend + mock API endpoints
 * for plan edits (Lakebase write-back pending P5-SCHEMA).
 */
import express from 'express';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
app.use(express.json());

// Serve built React frontend from dist/
app.use(express.static(path.join(__dirname, '..', 'dist')));

// --- PUT /api/plan/wave-assignment ---
// Update wire-center wave assignment (drag-to-reschedule on Gantt).
app.put('/api/plan/wave-assignment', (req, res) => {
  const { wireCenterId, wave, scheduledStart, scheduledEnd } = req.body;
  console.log(
    `[retirement-plan] Wave assignment update: WC ${wireCenterId} -> Wave ${wave} (${scheduledStart} to ${scheduledEnd})`
  );
  res.json({
    success: true,
    wireCenterId,
    wave,
    scheduledStart,
    scheduledEnd,
    message: 'Plan updated (mock — Lakebase write-back pending P5-SCHEMA)',
  });
});

// --- PUT /api/plan/status ---
// Update wire-center migration status.
app.put('/api/plan/status', (req, res) => {
  const { wireCenterId, status, notes } = req.body;
  console.log(
    `[retirement-plan] Status update: WC ${wireCenterId} -> ${status}`
  );
  res.json({
    success: true,
    wireCenterId,
    status,
    updatedAt: new Date().toISOString(),
    message: 'Status updated (mock — Lakebase write-back pending P5-SCHEMA)',
  });
});

// --- POST /api/plan/scenario ---
// Request new optimizer scenario run.
app.post('/api/plan/scenario', (req, res) => {
  const { constraints, objectiveWeights } = req.body;
  console.log(
    '[retirement-plan] Scenario request:',
    JSON.stringify({ constraints, objectiveWeights })
  );
  res.json({
    success: true,
    scenarioId: `SCN-${Date.now()}`,
    status: 'queued',
    message: 'Scenario queued (mock — P4-SEQ optimizer not yet deployed)',
  });
});

// SPA fallback
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'dist', 'index.html'));
});

const port = parseInt(process.env.DATABRICKS_APP_PORT || '8000', 10);
app.listen(port, '0.0.0.0', () => {
  console.log(`[retirement-plan] Server listening on 0.0.0.0:${port}`);
});