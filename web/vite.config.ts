import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/**
 * Silenced proxy errors: when the Python API isn't running, fetch calls to
 * /api/* will fail with ECONNREFUSED. The frontend already degrades
 * gracefully (each lab falls back to its local approximation), but Vite's
 * default proxy error handler logs every single failure to the dev server
 * console. We swallow those events and reply with a 503 so the frontend's
 * catch() branch is the single source of truth for "is the API up?".
 */
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on("error", (_err, _req, res) => {
            if (res && !res.headersSent && "writeHead" in res) {
              try {
                res.writeHead(503, { "content-type": "application/json" });
                res.end(JSON.stringify({ offline: true }));
              } catch { /* socket already closed */ }
            }
          });
        },
      },
      "/health": {
        target: "http://localhost:8000",
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on("error", (_err, _req, res) => {
            if (res && !res.headersSent && "writeHead" in res) {
              try {
                res.writeHead(503, { "content-type": "application/json" });
                res.end(JSON.stringify({ offline: true }));
              } catch { /* socket already closed */ }
            }
          });
        },
      },
    },
  },
});

