import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/v2/",
  server: {
    proxy: {
      "/auth": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/chats": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/stats": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/bots": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/health": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
});
