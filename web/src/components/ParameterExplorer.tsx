import React, { useState, useEffect, useCallback, useRef } from "react";
import { post, DEFAULT_PARAMS, type CosmoParams, type SpectrumResponse } from "../api/client.ts";

interface SliderDef {
  key: keyof CosmoParams;
  label: string;
  min: number;
  max: number;
  step: number;
}

const SLIDERS: SliderDef[] = [
  { key: "H0", label: "H₀ (km/s/Mpc)", min: 50, max: 100, step: 0.5 },
  { key: "Omega_b_h2", label: "Ω_b h²", min: 0.015, max: 0.030, step: 0.001 },
  { key: "Omega_cdm_h2", label: "Ω_cdm h²", min: 0.08, max: 0.20, step: 0.005 },
  { key: "n_s", label: "n_s", min: 0.85, max: 1.10, step: 0.005 },
  { key: "ln10As", label: "ln(10¹⁰ A_s)", min: 2.0, max: 4.0, step: 0.05 },
  { key: "tau_reio", label: "τ_reio", min: 0.01, max: 0.15, step: 0.005 },
];

export function ParameterExplorer() {
  const [params, setParams] = useState<CosmoParams>({ ...DEFAULT_PARAMS });
  const [spectrum, setSpectrum] = useState<SpectrumResponse | null>(null);
  const [inferMs, setInferMs] = useState<number>(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const fetchSpectrum = useCallback(async (p: CosmoParams) => {
    try {
      const resp = await post<SpectrumResponse>("/api/v1/spectrum", {
        params: p, l_max: 2500,
      });
      setSpectrum(resp);
      setInferMs(resp.inference_time_ms);
    } catch { /* API offline */ }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => fetchSpectrum(params), 150);
    return () => clearTimeout(timer);
  }, [params, fetchSpectrum]);

  // Draw spectrum on canvas
  useEffect(() => {
    if (!spectrum || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const { ell, cl } = spectrum;
    if (ell.length === 0) return;

    // D_l = l(l+1)C_l / (2π)
    const dl = ell.map((l, i) => l * (l + 1) * cl[i] / (2 * Math.PI));
    const logDl = dl.map(d => Math.log10(Math.max(d, 1e-30)));

    const xMin = Math.log10(ell[0]);
    const xMax = Math.log10(ell[ell.length - 1]);
    const yMin = Math.min(...logDl) - 0.5;
    const yMax = Math.max(...logDl) + 0.5;

    const pad = { l: 60, r: 20, t: 30, b: 40 };
    const pw = w - pad.l - pad.r;
    const ph = h - pad.t - pad.b;

    const toX = (logL: number) => pad.l + ((logL - xMin) / (xMax - xMin)) * pw;
    const toY = (logD: number) => pad.t + ((yMax - logD) / (yMax - yMin)) * ph;

    // Grid
    ctx.strokeStyle = "#21262d";
    ctx.lineWidth = 1;
    for (let lx = Math.ceil(xMin); lx <= xMax; lx++) {
      const x = toX(lx);
      ctx.beginPath(); ctx.moveTo(x, pad.t); ctx.lineTo(x, h - pad.b); ctx.stroke();
    }

    // Spectrum line
    ctx.strokeStyle = "#58a6ff";
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < ell.length; i++) {
      const x = toX(Math.log10(ell[i]));
      const y = toY(logDl[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Labels
    ctx.fillStyle = "#8b949e";
    ctx.font = "12px monospace";
    ctx.textAlign = "center";
    ctx.fillText("Multipole ℓ", w / 2, h - 5);
    ctx.save();
    ctx.translate(14, h / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText("ℓ(ℓ+1)Cₗ/2π", 0, 0);
    ctx.restore();
  }, [spectrum]);

  return (
    <div style={{ maxWidth: 1000 }}>
      <h2 style={{ fontSize: 28, marginBottom: 8 }}>Parameter Explorer</h2>
      <p style={{ color: "#8b949e", marginBottom: 24 }}>
        Двигайте слайдеры — спектр мощности CMB пересчитывается мгновенно
        {inferMs > 0 && <span> ({inferMs.toFixed(1)} мс)</span>}
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 32 }}>
        {/* Sliders */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {SLIDERS.map(s => (
            <div key={s.key}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
                <span style={{ color: "#c9d1d9" }}>{s.label}</span>
                <span style={{ color: "#58a6ff", fontFamily: "monospace" }}>
                  {params[s.key].toFixed(s.step < 0.01 ? 4 : s.step < 0.1 ? 3 : 1)}
                </span>
              </div>
              <input
                type="range"
                min={s.min} max={s.max} step={s.step}
                value={params[s.key]}
                onChange={e => setParams(p => ({ ...p, [s.key]: parseFloat(e.target.value) }))}
                style={{ width: "100%", accentColor: "#1f6feb" }}
              />
            </div>
          ))}
          <button
            onClick={() => setParams({ ...DEFAULT_PARAMS })}
            style={{
              marginTop: 8, padding: "8px 16px", borderRadius: 6,
              border: "1px solid #30363d", background: "transparent",
              color: "#8b949e", cursor: "pointer", fontSize: 13,
            }}
          >
            Reset to Planck 2018
          </button>
        </div>

        {/* Canvas */}
        <div style={{
          background: "#0d1117", borderRadius: 12, border: "1px solid #30363d",
          padding: 16, display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <canvas ref={canvasRef} width={600} height={400} style={{ width: "100%", height: "auto" }} />
        </div>
      </div>
    </div>
  );
}
