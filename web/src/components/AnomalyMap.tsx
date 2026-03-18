import React, { useState, useRef, useEffect, useCallback } from "react";
import { post, type AnomalyResponse } from "../api/client.ts";

function generateSyntheticMap(size: number, seed: number): number[][] {
  // Simple client-side Gaussian random field for demo
  const map: number[][] = [];
  let s = seed;
  const rand = () => {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    return (s / 0x7fffffff) * 2 - 1;
  };
  for (let y = 0; y < size; y++) {
    const row: number[] = [];
    for (let x = 0; x < size; x++) {
      row.push(rand() * 100);
    }
    map.push(row);
  }
  // Smooth with simple box filter
  const smoothed: number[][] = Array.from({ length: size }, () => Array(size).fill(0));
  for (let y = 1; y < size - 1; y++) {
    for (let x = 1; x < size - 1; x++) {
      let sum = 0;
      for (let dy = -1; dy <= 1; dy++)
        for (let dx = -1; dx <= 1; dx++)
          sum += map[y + dy][x + dx];
      smoothed[y][x] = sum / 9;
    }
  }
  return smoothed;
}

export function AnomalyMap() {
  const [mapSize] = useState(64);
  const [mapData, setMapData] = useState<number[][] | null>(null);
  const [result, setResult] = useState<AnomalyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [threshold, setThreshold] = useState(3.0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const generateMap = useCallback(() => {
    const seed = Math.floor(Math.random() * 100000);
    setMapData(generateSyntheticMap(mapSize, seed));
    setResult(null);
  }, [mapSize]);

  useEffect(() => { generateMap(); }, [generateMap]);

  const analyzeMap = useCallback(async () => {
    if (!mapData) return;
    setLoading(true);
    try {
      const resp = await post<AnomalyResponse>("/api/v1/anomalies", {
        map_data: mapData, threshold,
      });
      setResult(resp);
    } catch { /* API offline */ }
    setLoading(false);
  }, [mapData, threshold]);

  // Draw map
  useEffect(() => {
    if (!mapData || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const size = mapData.length;
    canvas.width = size;
    canvas.height = size;

    const flat = mapData.flat();
    const vmin = Math.min(...flat);
    const vmax = Math.max(...flat);
    const range = vmax - vmin || 1;

    const imgData = ctx.createImageData(size, size);
    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const v = (mapData[y][x] - vmin) / range;
        const idx = (y * size + x) * 4;
        // CMB-style blue-white-red
        if (v < 0.5) {
          const t = v * 2;
          imgData.data[idx] = Math.floor(20 * t);
          imgData.data[idx + 1] = Math.floor(50 + 150 * t);
          imgData.data[idx + 2] = Math.floor(150 + 105 * t);
        } else {
          const t = (v - 0.5) * 2;
          imgData.data[idx] = Math.floor(20 + 235 * t);
          imgData.data[idx + 1] = Math.floor(200 - 150 * t);
          imgData.data[idx + 2] = Math.floor(255 - 225 * t);
        }
        imgData.data[idx + 3] = 255;
      }
    }
    ctx.putImageData(imgData, 0, 0);

    // Overlay anomaly candidates
    if (result) {
      ctx.strokeStyle = "#ff4444";
      ctx.lineWidth = 1.5;
      for (const c of result.candidates) {
        ctx.beginPath();
        ctx.arc(c.x, c.y, c.radius + 2, 0, Math.PI * 2);
        ctx.stroke();
      }
    }
  }, [mapData, result]);

  return (
    <div style={{ maxWidth: 900 }}>
      <h2 style={{ fontSize: 28, marginBottom: 8 }}>CMB Anomaly Map</h2>
      <p style={{ color: "#8b949e", marginBottom: 24 }}>
        Анализ CMB-карт на аномалии: автоэнкодер + статистические тесты
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 32 }}>
        {/* Map */}
        <div style={{
          background: "#0d1117", borderRadius: 12, border: "1px solid #30363d",
          padding: 16, display: "flex", flexDirection: "column", alignItems: "center",
        }}>
          <canvas
            ref={canvasRef}
            style={{ width: "100%", maxWidth: 400, imageRendering: "pixelated", borderRadius: 4 }}
          />
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button
              onClick={generateMap}
              style={{
                padding: "8px 16px", borderRadius: 6,
                border: "1px solid #30363d", background: "#161b22",
                color: "#c9d1d9", cursor: "pointer", fontSize: 13,
              }}
            >
              New Map
            </button>
            <button
              onClick={analyzeMap}
              disabled={loading}
              style={{
                padding: "8px 16px", borderRadius: 6,
                border: "none", background: "#1f6feb",
                color: "#fff", cursor: loading ? "wait" : "pointer", fontSize: 13,
              }}
            >
              {loading ? "Analyzing..." : "Detect Anomalies"}
            </button>
          </div>
        </div>

        {/* Results panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div>
            <div style={{ fontSize: 12, color: "#8b949e", marginBottom: 4 }}>
              Detection threshold (σ)
            </div>
            <input
              type="range"
              min={1} max={5} step={0.5} value={threshold}
              onChange={e => setThreshold(parseFloat(e.target.value))}
              style={{ width: "100%", accentColor: "#f0883e" }}
            />
            <div style={{ fontSize: 12, color: "#f0883e", textAlign: "center" }}>{threshold}σ</div>
          </div>

          {result && (
            <>
              <div style={{ padding: 12, borderRadius: 8, background: "#161b22", border: "1px solid #30363d" }}>
                <div style={{ fontSize: 11, color: "#8b949e" }}>Global anomaly score</div>
                <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "monospace" }}>
                  {result.global_score.toFixed(4)}
                </div>
              </div>

              <div style={{ padding: 12, borderRadius: 8, background: "#161b22", border: "1px solid #30363d" }}>
                <div style={{ fontSize: 11, color: "#8b949e" }}>Detected anomalies</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: result.n_anomalies > 0 ? "#f85149" : "#3fb950" }}>
                  {result.n_anomalies}
                </div>
              </div>

              <div style={{ padding: 12, borderRadius: 8, background: "#161b22", border: "1px solid #30363d" }}>
                <div style={{ fontSize: 11, color: "#8b949e", marginBottom: 6 }}>Non-Gaussianity</div>
                {[
                  ["Skewness", result.non_gaussianity.skewness, result.non_gaussianity.skew_pvalue],
                  ["Kurtosis", result.non_gaussianity.kurtosis, result.non_gaussianity.kurt_pvalue],
                ].map(([name, val, pval]) => (
                  <div key={name as string} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 2 }}>
                    <span>{name as string}</span>
                    <span style={{ fontFamily: "monospace" }}>
                      {(val as number).toFixed(3)} (p={((pval as number)).toFixed(3)})
                    </span>
                  </div>
                ))}
                <div style={{
                  marginTop: 6, padding: "4px 8px", borderRadius: 4, textAlign: "center", fontSize: 12,
                  background: result.non_gaussianity.is_gaussian ? "#238636" + "22" : "#da3633" + "22",
                  color: result.non_gaussianity.is_gaussian ? "#3fb950" : "#f85149",
                }}>
                  {result.non_gaussianity.is_gaussian ? "Consistent with Gaussian" : "Non-Gaussian detected"}
                </div>
              </div>

              <div style={{ fontSize: 11, color: "#484f58", textAlign: "center" }}>
                Inference: {result.inference_time_ms.toFixed(1)} ms
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
