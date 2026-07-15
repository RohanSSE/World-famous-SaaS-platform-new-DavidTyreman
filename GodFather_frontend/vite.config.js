import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@admin": path.resolve(__dirname, "./src/admin"),
    },
  },
  server: {
    host: "0.0.0.0",
    port: Number(process.env.VITE_PORT) || 4001,
    // Allow the app to be reached through Microsoft dev tunnels (*.devtunnels.ms).
    allowedHosts: [".devtunnels.ms"],
    // Route API calls through the dev server so the whole app is shareable on a
    // single tunnel URL (frontend + backend served from the same origin).
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
      },
    },
  },
  assetsInclude: ["**/*.mov"],
});
