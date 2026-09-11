/**
 * server.ts
 * AppKit backend entry point for the Regulatory Assistant (P7-REG).
 * Analytics-only app — SQL queries in config/queries/ are served automatically.
 *
 * Future: Add a /api/agent proxy endpoint when P6-REG Model Serving
 * endpoint is deployed, to forward chat messages and stream responses.
 */
import { createApp } from '@databricks/appkit/server';

const app = createApp({
  plugins: ['analytics'],
  onPluginsReady: async (server) => {
    // Analytics plugin handles SQL queries automatically.
    //
    // TODO (P6-REG): Add agent proxy endpoint:
    // server.extend((expressApp) => {
    //   expressApp.post('/api/agent/chat', async (req, res) => {
    //     const { message, jurisdiction } = req.body;
    //     // Forward to P6-REG Model Serving endpoint via SSE
    //     // const endpoint = process.env.REG_AGENT_ENDPOINT;
    //     // Stream response back to client
    //   });
    // });
    console.log('[regulatory-assistant] Server ready. Analytics plugin active.');
  },
});

export default app;
