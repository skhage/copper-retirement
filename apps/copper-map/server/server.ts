/**
 * server.ts
 * AppKit backend entry point for the Copper Prioritization Map.
 * Analytics-only app — no custom endpoints needed.
 * SQL queries in config/queries/ are served automatically by AppKit.
 */
import { createApp } from '@databricks/appkit/server';

const app = createApp({
  plugins: ['analytics'],
  onPluginsReady: async (server) => {
    // Analytics plugin handles SQL queries automatically.
    // Custom endpoints can be added here if needed in the future.
    // Example: server.extend((expressApp) => { ... });
    console.log('[copper-map] Server ready. Analytics plugin active.');
  },
});

export default app;
