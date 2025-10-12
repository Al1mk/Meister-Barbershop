import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// اگر خواستی به‌جای CORS، درخواست‌ها رو پروکسی کنی:
// server: { proxy: { "/api": "http://localhost:8000" } }

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: true
  }
});