/**
 * @file Vite build configuration for KubeNova frontend.
 *
 * Proxies /api and /ws paths to the backend uvicorn server so that the
 * Vite dev server and the backend can coexist on different ports during
 * development without CORS issues.
 *
 * Path alias `@/` maps to `src/` for clean imports throughout the codebase.
 */

import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
        secure: false,
        ws: true,
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    css: true,
  },
});
