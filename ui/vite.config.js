import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import eslint from "vite-plugin-eslint2";
import vuetify from 'vite-plugin-vuetify';

export default defineConfig({
  plugins: [
    vue(),
    vuetify({ autoImport: true }),
    eslint({ fix: true }),
  ],
  server: {
    host: '::',
    port: 5173,
    open: false,
    proxy: {
      '/auth': {
        target: 'http://localhost:3390',
      },
      '/api': {
        target: 'http://localhost:3390',
      },
    },
  },
});
