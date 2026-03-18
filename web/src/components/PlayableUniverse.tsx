import React, { useState, useCallback, useRef, useEffect } from "react";
import { post, DEFAULT_PARAMS, type CosmoParams, type PlayableResponse } from "../api/client.ts";

export function PlayableUniverse() {
  const [params, setParams] = useState<CosmoParams>({ ...DEFAULT_PARAMS });
  const [gridSize] = useState(64);
  const [nSteps] = useState(10);
  const [data, setData] = useState<PlayableResponse | null>(null);
  const [frame, setFrame] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const simulate = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await post<PlayableResponse>("/api/v1/simulations/playable", {
        params, grid_size: gridSize, n_steps: nSteps, seed: 42,
      });
      setData(resp);
      setFrame(0);
    } catch { /* API offline */ }
    setLoading(false);
  }, [params, gridSize, nSteps]);

  // Animation loop
  useEffect(() => {
    if (!playing || !data) return;
    const interval = setInterval(() => {
      setFrame(f => {
        const next = f + 1;
        if (next >= data.snapshots.length) { setPlaying(false); return f; }
        return next;
      });
    }, 300);
    return () => clearInterval(interval);
  }, [playing, data]);

  // Render density field on canvas
  useEffect(() => {
    if (!data || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const snapshot = data.snapshots[frame];
    const size = snapshot.length;
    canvas.width = size;
    canvas.height = size;

    const flat = snapshot.flat();
    const vmin = Math.min(...flat);
    const vmax = Math.max(...flat);
    const range = vmax - vmin || 1;

    const imgData = ctx.createImageData(size, size);
    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const v = (snapshot[y][x] - vmin) / range;
        const idx = (y * size + x) * 4;
        // Dark blue → white → red colormap
        if (v < 0.5) {
          const t = v * 2;
          imgData.data[idx] = Math.floor(10 + 80 * t);
          imgData.data[idx + 1] = Math.floor(10 + 100 * t);
          imgData.data[idx + 2] = Math.floor(60 + 195 * t);
        } else {
          const t = (v - 0.5) * 2;
          imgData.data[idx] = Math.floor(90 + 165 * t);
          imgData.data[idx + 1] = Math.floor(110 - 60 * t);
          imgData.data[idx + 2] = Math.floor(255 - 220 * t);
        }
        imgData.data[idx + 3] = 255;
      }
    }
    ctx.putImageData(imgData, 0, 0);
  }, [data, frame]);

  return (
    <div style={{ maxWidth: 900 }}>
      <h2 style={{ fontSize: 28, marginBottom: 8 }}>Playable Universe</h2>
      <p style={{ color: "#8b949e", marginBottom: 24 }}>
        Измените фундаментальные константы и наблюдайте формирование (или разрушение) космической структуры
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 32 }}>
        {/* Controls */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {([
            ["H0", "H₀", 50, 100, 1],
            ["n_s", "n_s", 0.5, 1.5, 0.01],
            ["ln10As", "ln(10¹⁰ A_s)", 1.0, 5.0, 0.1],
            ["Omega_cdm_h2", "Ω_cdm h²", 0.01, 0.50, 0.01],
          ] as const).map(([key, label, min, max, step]) => (
            <div key={key}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                <span>{label}</span>
                <span style={{ color: "#58a6ff", fontFamily: "monospace" }}>
                  {params[key].toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min={min} max={max} step={step}
                value={params[key]}
                onChange={e => setParams(p => ({ ...p, [key]: parseFloat(e.target.value) }))}
                style={{ width: "100%", accentColor: "#da3633" }}
              />
            </div>
          ))}

          <button
            onClick={simulate}
            disabled={loading}
            style={{
              marginTop: 12, padding: "10px 20px", borderRadius: 8,
              border: "none", background: "#238636", color: "#fff",
              cursor: loading ? "wait" : "pointer", fontSize: 14, fontWeight: 600,
            }}
          >
            {loading ? "Simulating..." : "Create Universe"}
          </button>

          {data && (
            <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
              <button
                onClick={() => { setFrame(0); setPlaying(true); }}
                style={{
                  flex: 1, padding: "8px", borderRadius: 6,
                  border: "1px solid #30363d", background: "#161b22",
                  color: "#c9d1d9", cursor: "pointer", fontSize: 13,
                }}
              >
                Play
              </button>
              <button
                onClick={() => setPlaying(false)}
                style={{
                  flex: 1, padding: "8px", borderRadius: 6,
                  border: "1px solid #30363d", background: "#161b22",
                  color: "#c9d1d9", cursor: "pointer", fontSize: 13,
                }}
              >
                Pause
              </button>
            </div>
          )}

          {data && (
            <div style={{ marginTop: 8 }}>
              <input
                type="range"
                min={0} max={data.snapshots.length - 1} value={frame}
                onChange={e => { setPlaying(false); setFrame(parseInt(e.target.value)); }}
                style={{ width: "100%", accentColor: "#da3633" }}
              />
              <div style={{ fontSize: 12, color: "#8b949e", textAlign: "center" }}>
                z = {data.redshifts[frame]?.toFixed(1)} | a = {data.scale_factors[frame]?.toFixed(4)}
              </div>
            </div>
          )}

          {data && (
            <div style={{
              marginTop: 8, padding: 12, borderRadius: 8,
              background: data.structure_formed ? "#238636" + "22" : "#da3633" + "22",
              border: `1px solid ${data.structure_formed ? "#238636" : "#da3633"}`,
              textAlign: "center", fontSize: 14,
            }}>
              {data.structure_formed
                ? "Structure formed successfully"
                : "No significant structure formed"}
            </div>
          )}
        </div>

        {/* Density field canvas */}
        <div style={{
          background: "#0d1117", borderRadius: 12, border: "1px solid #30363d",
          display: "flex", alignItems: "center", justifyContent: "center",
          minHeight: 400, padding: 16,
        }}>
          {data ? (
            <canvas
              ref={canvasRef}
              style={{ width: "100%", maxWidth: 500, imageRendering: "pixelated", borderRadius: 4 }}
            />
          ) : (
            <div style={{ color: "#484f58", textAlign: "center" }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>&#x1F30C;</div>
              <div>Нажмите "Create Universe" для запуска симуляции</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
