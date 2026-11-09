import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  root: 'client',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
  plugins: [react()],
  // ACC-DES-DEF-FOOTER-VERSION-1107: footer release label from build env (APP_RELEASE), default 'dev'.
  define: {
    __APP_RELEASE__: JSON.stringify(process.env.APP_RELEASE || 'dev'),
  },
});