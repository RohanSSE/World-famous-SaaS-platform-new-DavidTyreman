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
  },
  assetsInclude: ["**/*.mov"],
});
