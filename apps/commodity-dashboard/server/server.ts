/**
 * server.ts
 * AppKit backend entry point for the Commodity & Workforce Dashboard.
 * Analytics plugin serves SQL queries from config/queries/.
 * Custom endpoints for forecast requests and contractor assignment.
 */
import { createApp } from '@databricks/appkit/server';

const app = createApp({
  plugins: ['analytics'],
  onPluginsReady: async (server) => {
    console.log('[commodity-dashboard] Server ready. Analytics plugin active.');

    server.extend((expressApp) => {
      // --- POST /api/commodity/forecast ---
      // Proxy to P4-COMMODITY model serving endpoint.
      // TODO: Implement once P4-COMMODITY is deployed.
      // For now returns mock forecast data.
      expressApp.post('/api/commodity/forecast', async (req, res) => {
        const { horizon_months = 12 } = req.body;
        // Mock forecast response
        const basePrice = 4.25; // $/lb
        const forecasts = Array.from({ length: horizon_months }, (_, i) => {
          const month = i + 1;
          const trend = 0.02 * month;
          const noise = (Math.random() - 0.5) * 0.3;
          const price = basePrice + trend + noise;
          return {
            month_offset: month,
            forecast_price_usd_lb: Math.round(price * 100) / 100,
            lower_bound: Math.round((price - 0.35) * 100) / 100,
            upper_bound: Math.round((price + 0.35) * 100) / 100,
            confidence: 0.95 - 0.02 * month,
          };
        });
        res.json({
          model_version: 'mock-v1',
          generated_at: new Date().toISOString(),
          recommendation: basePrice > 4.0 ? 'SELL' : 'HOLD',
          recommendation_confidence: 0.78,
          forecasts,
        });
      });

      // --- POST /api/commodity/assign-contractor ---
      // Assign contractor to decommission project.
      // TODO: Write to Lakebase once P5-SCHEMA lands.
      expressApp.post('/api/commodity/assign-contractor', async (req, res) => {
        const { contractor_id, project_id, wire_center_id } = req.body;
        console.log(
          `[commodity-dashboard] Assign contractor ${contractor_id} to project ${project_id} (WC: ${wire_center_id})`
        );
        res.json({
          success: true,
          assignment_id: `ASSIGN-${Date.now()}`,
          message: 'Contractor assigned (mock — Lakebase write-back pending P5-SCHEMA)',
        });
      });
    });
  },
});

export default app;
