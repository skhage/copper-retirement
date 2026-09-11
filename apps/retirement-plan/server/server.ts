/**
 * server.ts
 * AppKit backend entry point for the Retirement Plan Tracker.
 * Analytics plugin serves SQL queries from config/queries/.
 * Custom endpoints for plan edits (Lakebase write-back when P5-SCHEMA lands).
 */
import { createApp } from '@databricks/appkit/server';

const app = createApp({
  plugins: ['analytics'],
  onPluginsReady: async (server) => {
    console.log('[retirement-plan] Server ready. Analytics plugin active.');

    server.extend((expressApp) => {
      // --- PUT /api/plan/wave-assignment ---
      // Update wire-center wave assignment (drag-to-reschedule on Gantt).
      // TODO: Write to Lakebase `retirement_plan` table once P5-SCHEMA lands.
      // For now logs to console and returns success.
      expressApp.put('/api/plan/wave-assignment', async (req, res) => {
        const { wireCenterId, wave, scheduledStart, scheduledEnd } = req.body;
        console.log(
          `[retirement-plan] Wave assignment update: WC ${wireCenterId} → Wave ${wave} (${scheduledStart} to ${scheduledEnd})`
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
      // TODO: Write to Lakebase once P5-SCHEMA lands.
      expressApp.put('/api/plan/status', async (req, res) => {
        const { wireCenterId, status, notes } = req.body;
        console.log(
          `[retirement-plan] Status update: WC ${wireCenterId} → ${status}`
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
      // TODO: Trigger P4-SEQ optimizer job via Databricks Jobs API.
      expressApp.post('/api/plan/scenario', async (req, res) => {
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
    });
  },
});

export default app;
