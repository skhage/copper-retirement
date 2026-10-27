/**
 * server.js
 * Express backend for the Retirement Plan Tracker (P7-PLAN).
 * Serves the Vite-built React frontend + API endpoints.
 * Demo Beat 2: "Capital-efficient plan to zero copper?"
 *
 * V2 (2026-09-20): Connected to live gold tables:
 *   - gold_wave_schedule  → GET /api/plan/waves, /api/plan/waves/summary, /api/plan/kpis
 *   - gold_contractor_assignment_plan → GET /api/plan/contractors
 */
import express from 'express';
import { fileURLToPath } from 'url';
import path from 'path';
import {
  fetchWaveSchedule,
  fetchWaveSummary,
  fetchContractorAssignments,
  fetchPlanKPIs,
  fetchBudgetByWave,
  fetchRegulatoryChecklist,
  fetchMilestones,
  healthCheck,
} from './databricksSQL.js';
import triageRouter from './routes/triage.js'; // ACC-APP-PORT-TRIAGE (ported from dig-triage)
import regulatoryRouter from './routes/regulatory.js'; // ACC-APP-PORT-REG (ported from regulatory-assistant)
import mapRouter from './routes/map.js'; // ACC-APP-PORT-MAP (ported from copper-map Dash app)
import commodityRouter from './routes/commodity.js'; // ACC-APP-PORT-COMMODITY (ported from commodity-dashboard)

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

// ============================================================
// Live Data Endpoints (V2 — gold_wave_schedule + gold_contractor_assignment_plan)
// ============================================================

// --- GET /api/plan/waves ---
// Full wave schedule data mapped to WireCenterPlan format.
app.get('/api/plan/waves', async (req, res) => {
  try {
    const rows = await fetchWaveSchedule();

    // Map gold_wave_schedule rows to WireCenterPlan format for Gantt/Table
    const wireCenterPlans = rows.map((r, idx) => {
      const waveYear = parseInt(r.wave_year, 10);
      const waveQtr = parseInt(r.wave_quarter, 10);
      const startMonth = (waveQtr - 1) * 3 + 1;
      const endMonth = startMonth + 2;
      const scheduledStart = `${waveYear}-${String(startMonth).padStart(2, '0')}-01`;
      const endDate = new Date(waveYear, endMonth, 0); // last day of end month
      const scheduledEnd = endDate.toISOString().split('T')[0];

      // Derive constraint from puc_filing_required + fiber_ready
      let constraint = 'none';
      let constraintDetail = '';
      if (r.puc_filing_required === 'true' || r.puc_filing_required === true) {
        constraint = 'regulatory_notice_pending';
        constraintDetail = `PUC filing required for ${r.state_code}`;
      } else if (r.fiber_ready === 'false' || r.fiber_ready === false) {
        constraint = 'crew_capacity_constrained';
        constraintDetail = 'Wire center not yet fiber-ready';
      }

      // Assign wave number by sequence (2026-Q3=1, 2026-Q4=2, ...)
      const waveSeq = (waveYear - 2026) * 4 + waveQtr - 2; // 2026-Q3→1

      return {
        wire_center_id: r.wire_center_id,
        wire_center_name: r.wire_center_name,
        state: r.state_code,
        wave: Math.max(1, Math.min(8, waveSeq)),
        assigned_wave: r.assigned_wave,
        scheduled_start: scheduledStart,
        scheduled_end: scheduledEnd,
        status: 'planned', // Live data has no status tracking yet
        customers_affected: parseInt(r.affected_customer_count, 10) || 0,
        copper_devices: parseInt(r.copper_device_count, 10) || 0,
        migration_cost_usd: (parseInt(r.estimated_crew_days, 10) || 0) * 5500,
        revenue_at_risk_mrr: parseFloat(r.annual_revenue_at_risk || 0) / 12,
        scrap_recovery_usd: (parseInt(r.copper_device_count, 10) || 0) * 360,
        net_savings_usd: 0,
        completion_pct: 0,
        constraint,
        constraint_detail: constraintDetail,
        assigned_crew: '', // Filled from contractor overlay
        priority_score: parseFloat(r.retirement_readiness_score || 0),
        // Extra fields from gold_wave_schedule
        fiber_ready: r.fiber_ready,
        puc_filing_required: r.puc_filing_required,
        critical_risk_devices: parseInt(r.critical_risk_devices, 10) || 0,
        high_risk_devices: parseInt(r.high_risk_devices, 10) || 0,
        estimated_crew_days: parseInt(r.estimated_crew_days, 10) || 0,
        retirement_priority_rank: parseInt(r.retirement_priority_rank, 10) || 0,
        risk_urgency_weight: parseFloat(r.risk_urgency_weight || 0),
        earliest_eligible_wave: r.earliest_eligible_wave,
        optimizer_version: r.optimizer_version,
      };
    });

    res.json({ success: true, count: wireCenterPlans.length, data: wireCenterPlans });
  } catch (err) {
    console.error('[retirement-plan] waves error:', err.message);
    planFail(res, 'Failed to fetch wave schedule', err);
  }
});

// COO-Q-20261027-0550-2: UC permission failures (err.status 403, tagged in executeSQL) surface as 403
// 'Data access pending' so the Plan tab shows the pending state, never mock or 'no data'.
function planFail(res, label, err) {
  const status = err.status || 500;
  res.status(status).json({ error: status === 403 ? err.message : label, detail: err.message });
}

// --- GET /api/plan/waves/summary ---
// Regional rollup: aggregated by quarter and state.
app.get('/api/plan/waves/summary', async (req, res) => {
  try {
    const rows = await fetchWaveSummary();
    res.json({ success: true, count: rows.length, data: rows });
  } catch (err) {
    console.error('[retirement-plan] waves/summary error:', err.message);
    planFail(res, 'Failed to fetch wave summary', err);
  }
});

// --- GET /api/plan/contractors ---
// Contractor assignment plan overlay.
app.get('/api/plan/contractors', async (req, res) => {
  try {
    const rows = await fetchContractorAssignments();
    res.json({ success: true, count: rows.length, data: rows });
  } catch (err) {
    console.error('[retirement-plan] contractors error:', err.message);
    planFail(res, 'Failed to fetch contractors', err);
  }
});

// --- GET /api/plan/kpis ---
// Computed KPIs from gold_wave_schedule.
app.get('/api/plan/kpis', async (req, res) => {
  try {
    const kpis = await fetchPlanKPIs();
    if (!kpis) return res.status(500).json({ error: 'No KPI data available' });
    res.json({ success: true, data: kpis });
  } catch (err) {
    console.error('[retirement-plan] kpis error:', err.message);
    planFail(res, 'Failed to compute KPIs', err);
  }
});

// --- GET /api/plan/budget ---
// Budget allocation by wave from retirement_plan.
app.get('/api/plan/budget', async (req, res) => {
  try {
    const rows = await fetchBudgetByWave();
    res.json({ success: true, count: rows.length, data: rows });
  } catch (err) {
    console.error('[retirement-plan] budget error:', err.message);
    planFail(res, 'Failed to fetch budget data', err);
  }
});

// --- GET /api/plan/regulatory ---
// Regulatory checklist items, optionally filtered by ?wire_center_id=...
app.get('/api/plan/regulatory', async (req, res) => {
  try {
    const wireCenterId = req.query.wire_center_id || null;
    const rows = await fetchRegulatoryChecklist(wireCenterId);
    res.json({ success: true, count: rows.length, data: rows });
  } catch (err) {
    console.error('[retirement-plan] regulatory error:', err.message);
    planFail(res, 'Failed to fetch regulatory checklist', err);
  }
});

// --- GET /api/plan/milestones ---
// Retirement milestones, optionally filtered by ?wire_center_id=...
app.get('/api/plan/milestones', async (req, res) => {
  try {
    const wireCenterId = req.query.wire_center_id || null;
    const rows = await fetchMilestones(wireCenterId);
    res.json({ success: true, count: rows.length, data: rows });
  } catch (err) {
    console.error('[retirement-plan] milestones error:', err.message);
    planFail(res, 'Failed to fetch milestones', err);
  }
});

// --- GET /api/plan/health ---
app.get('/api/plan/health', async (req, res) => {
  const sqlOk = await healthCheck();
  res.json({
    status: sqlOk ? 'healthy' : 'degraded',
    sql_connected: sqlOk,
    timestamp: new Date().toISOString(),
    env: {
      host_set: !!process.env.DATABRICKS_HOST,
      warehouse_set: !!process.env.DATABRICKS_WAREHOUSE_ID,
      token_set: !!(process.env.DATABRICKS_TOKEN || process.env.DATABRICKS_CLIENT_ID), // PAT or app SP OAuth
    },
  });
});

// --- Unified accelerator tab routers (DEC-ACCEL-UNIFIED-APP) ---
app.use('/api/triage', triageRouter);
app.use('/api/regulatory', regulatoryRouter);
app.use('/api/map', mapRouter);
app.use('/api/commodity', commodityRouter);

// SPA fallback
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'dist', 'index.html'));
});

const port = parseInt(process.env.DATABRICKS_APP_PORT || '8000', 10);
app.listen(port, '0.0.0.0', () => {
  console.log(`[retirement-plan] Server listening on 0.0.0.0:${port}`);
  console.log(`[retirement-plan] Live data: ${process.env.DATABRICKS_TOKEN || process.env.DATABRICKS_CLIENT_ID ? 'ENABLED' : 'DISABLED'}`);
  console.log(`[retirement-plan] SQL warehouse: ${process.env.DATABRICKS_WAREHOUSE_ID || 'NOT SET'}`);
});