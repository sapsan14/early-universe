import { createLogger, defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/**
 * When the Python API isn't running, every fetch to /api/* hits Vite's proxy
 * and triggers an ECONNREFUSED. The frontend already degrades gracefully
 * (each lab falls back to its local approximation) — but Vite's proxy plugin
 * logs its own error line *before* any user-supplied error handler gets a
 * say, so `server.proxy.*.configure` can't suppress the noise on its own.
 *
 * We wrap `createLogger().error` and drop any "http proxy error" messages
 * that are simply ECONNREFUSED/ENOTFOUND — real bugs still surface.
 */
const logger = createLogger();
const origError = logger.error.bind(logger);
logger.error = (msg, opts) => {
  if (typeof msg === "string" && msg.includes("http proxy error")) {
    if (msg.includes("ECONNREFUSED") || msg.includes("ENOTFOUND") || msg.includes("ETIMEDOUT")) {
      return;
    }
  }
  origError(msg, opts);
};

export default defineConfig({
  customLogger: logger,
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
