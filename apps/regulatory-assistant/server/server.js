/**
 * server.js
 * Express backend for the Regulatory Assistant (P7-REG).
 * Serves the Vite-built React frontend from dist/.
 */
import express from 'express';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
app.use(express.json());

// Serve built React frontend from dist/
app.use(express.static(path.join(__dirname, '..', 'dist')));

// SPA fallback — serve index.html for client-side routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'dist', 'index.html'));
});

const port = parseInt(process.env.DATABRICKS_APP_PORT || '8000', 10);
app.listen(port, '0.0.0.0', () => {
  console.log(`[regulatory-assistant] Server listening on 0.0.0.0:${port}`);
});