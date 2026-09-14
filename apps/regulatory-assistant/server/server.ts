/**
 * server.ts
 * AppKit backend entry point for the Regulatory Assistant (P7-REG).
 * Analytics plugin serves SQL queries from config/queries/.
 * RAG chat endpoint is implemented in server.js (Express) which is the
 * primary server used for deployment (app.yaml runs server.js).
 *
 * This file is preserved for AppKit-native future migration.
 */
import { createApp } from '@databricks/appkit/server';

const app = createApp({
  plugins: ['analytics'],
  onPluginsReady: async (server) => {
    // Analytics plugin handles SQL queries automatically.
    // RAG chat endpoint (/api/agent/chat) is in server.js.
    console.log('[regulatory-assistant] AppKit server ready. Analytics plugin active.');
    console.log('[regulatory-assistant] Note: RAG chat is served by server.js (Express).');
  },
});

export default app;
