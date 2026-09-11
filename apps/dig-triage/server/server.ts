/**
 * server.ts
 * AppKit backend entry point for the Dig-Safe Triage Console.
 * Analytics plugin serves SQL queries from config/queries/.
 * Custom endpoints for agent chat proxy and incident submission.
 */
import { createApp } from '@databricks/appkit/server';

const app = createApp({
  plugins: ['analytics'],
  onPluginsReady: async (server) => {
    console.log('[dig-triage] Server ready. Analytics plugin active.');

    server.extend((expressApp) => {
      // --- POST /api/triage/chat ---
      // Proxy to P6-TRIAGE agent Model Serving endpoint.
      // TODO: Implement SSE streaming once P6-TRIAGE is deployed.
      // For now returns mock agent responses.
      expressApp.post('/api/triage/chat', async (req, res) => {
        const { incidentId, message } = req.body;
        // Mock agent response
        res.json({
          response: `[Mock Agent] Analyzing incident ${incidentId}: ${message}. ` +
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
      // For now logs to console.
      expressApp.post('/api/triage/incident', async (req, res) => {
        const incident = req.body;
        console.log('[dig-triage] New incident submitted:', JSON.stringify(incident));
        res.json({
          success: true,
          incident_id: `INC-${Date.now()}`,
          message: 'Incident logged (mock — Lakebase write-back pending P5-SCHEMA)',
        });
      });

      // --- POST /api/triage/action ---
      // Human-in-loop approve/reject agent action.
      // TODO: Write to Lakebase audit table once P5-SCHEMA lands.
      expressApp.post('/api/triage/action', async (req, res) => {
        const { action_id, decision, reviewer } = req.body;
        console.log(`[dig-triage] Action ${action_id}: ${decision} by ${reviewer}`);
        res.json({
          success: true,
          action_id,
          decision,
          timestamp: new Date().toISOString(),
        });
      });
    });
  },
});

export default app;
