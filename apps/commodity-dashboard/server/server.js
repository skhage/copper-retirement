/**
 * server.js
 * Express backend for the Commodity & Workforce Dashboard.
 * Serves the Vite-built React frontend + mock API endpoints.
 */
import express from 'express';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
app.use(express.json());

// Serve built React frontend from dist/
app.use(express.static(path.join(__dirname, '..', 'dist')));

// --- POST /api/commodity/forecast ---
// Mock copper price forecast (replaces P4-COMMODITY model endpoint)
app.post('/api/commodity/forecast', (req, res) => {
  const { horizon_months = 12 } = req.body;
  const basePrice = 4.25;
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
// Mock contractor assignment
app.post('/api/commodity/assign-contractor', (req, res) => {
  const { contractor_id, project_id, wire_center_id } = req.body;
  console.log(
    `[commodity-dashboard] Assign contractor ${contractor_id} to project ${project_id} (WC: ${wire_center_id})`
  );
  res.json({
    success: true,
    assignment_id: `ASSIGN-${Date.now()}`,
    message: 'Contractor assigned (mock)',
  });
});

// SPA fallback — serve index.html for client-side routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'dist', 'index.html'));
});

const port = parseInt(process.env.DATABRICKS_APP_PORT || '8000', 10);
app.listen(port, '0.0.0.0', () => {
  console.log(`[commodity-dashboard] Server listening on 0.0.0.0:${port}`);
});