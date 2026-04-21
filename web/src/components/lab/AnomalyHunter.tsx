import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { theme } from "../../theme";
import { useT, p } from "../../i18n";
import { post, type AnomalyResponse } from "../../api/client";
import { localAnomaly } from "../../physics";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Callout } from "../ui/Callout";
import { Button } from "../ui/Button";
import { Term } from "../ui/Term";
import { ParamSlider } from "../ui/Slider";
import { Tex } from "../ui/Math";

/** Correlated CMB-like sky with optional injected anomalies. */
function generateMap(size: number, seed: number, contamination: number): number[][] {
  let s = seed >>> 0;
  const rand = () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 0xffffffff;
  };
  const gauss = () => {
    const u1 = Math.max(rand(), 1e-9);
    const u2 = rand();
    return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  };
  const m: number[][] = [];
  for (let y = 0; y < size; y++) {
    const row: number[] = [];
    for (let x = 0; x < size; x++) row.push(gauss() * 80);
    m.push(row);
  }
  // Two passes of box-blur give CMB-like correlated patches
  let smoothed = m.map((r) => r.slice());
  for (let pass = 0; pass < 3; pass++) {
    const next = smoothed.map((r) => r.slice());
    for (let y = 1; y < size - 1; y++) {
      for (let x = 1; x < size - 1; x++) {
        let sum = 0;
        for (let dy = -1; dy <= 1; dy++)
          for (let dx = -1; dx <= 1; dx++)
            sum += smoothed[y + dy][x + dx];
        next[y][x] = sum / 9;
      }
    }
    smoothed = next;
  }
  // Inject anomalies (positive and negative Gaussian bumps)
  const nAnom = Math.round(contamination * 4);
  for (let i = 0; i < nAnom; i++) {
    const cx = Math.floor(rand() * size);
    const cy = Math.floor(rand() * size);
    const radius = 3 + Math.floor(rand() * 4);
    const sign = rand() > 0.5 ? 1 : -1;
    const amp = sign * (80 + rand() * 120);
    for (let dy = -radius * 2; dy <= radius * 2; dy++) {
      for (let dx = -radius * 2; dx <= radius * 2; dx++) {
        const x = cx + dx, y = cy + dy;
        if (x < 0 || x >= size || y < 0 || y >= size) continue;
        const r2 = dx * dx + dy * dy;
        smoothed[y][x] += amp * Math.exp(-r2 / (2 * radius * radius));
      }
    }
  }
  return smoothed;
}

interface Preset {
  id: string;
  label: { ru: string; en: string };
  contamination: number;
  seed: number;
  emoji: string;
}
const PRESETS: Preset[] = [
  { id: "clean", label: { ru: "Чистое небо", en: "Clean sky" }, contamination: 0, seed: 42, emoji: "✨" },
  { id: "one", label: { ru: "Одно пятно", en: "One spot" }, contamination: 1, seed: 2024, emoji: "🎯" },
  { id: "cold-spot", label: { ru: "Холодное пятно WMAP", en: "WMAP cold spot" }, contamination: 2, seed: 196812, emoji: "🥶" },
  { id: "crowded", label: { ru: "Небо в пятнах", en: "Crowded sky" }, contamination: 5, seed: 314159, emoji: "🧨" },
];

export function AnomalyHunter() {
  const { pick, t } = useT();
  const [size] = useState(96);
  const [contamination, setContamination] = useState(1);
  const [seed, setSeed] = useState(() => Math.floor(Math.random() * 1e6));
  const [map, setMap] = useState<number[][] | null>(null);
  const [result, setResult] = useState<AnomalyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [usingApi, setUsingApi] = useState(false);
  const [threshold, setThreshold] = useState(3.0);
  const [probe, setProbe] = useState<{ x: number; y: number; sigma: number; value: number } | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMap(generateMap(size, seed, contamination));
    setProbe(null);
  }, [size, seed, contamination]);

  // Auto-run the detector whenever map or threshold changes.
  useEffect(() => {
    if (!map) return;
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const r = await post<AnomalyResponse>("/api/v1/anomalies", { map_data: map, threshold });
        setResult(r); setUsingApi(true);
      } catch {
        setResult(localAnomaly(map, threshold)); setUsingApi(false);
      }
      setLoading(false);
    }, 160);
    return () => clearTimeout(timer);
  }, [map, threshold]);

  // Map statistics used by the renderer, the histogram and the probe.
  const stats = useMemo(() => {
    if (!map) return null;
    const flat = map.flat();
    let sum = 0; for (const v of flat) sum += v;
    const mean = sum / flat.length;
    let sqSum = 0; for (const v of flat) sqSum += (v - mean) ** 2;
    const std = Math.sqrt(sqSum / flat.length) || 1;
    // 1st / 99th percentiles for colour-map robustness
    const sorted = flat.slice().sort((a, b) => a - b);
    const lo = sorted[Math.floor(sorted.length * 0.01)];
    const hi = sorted[Math.floor(sorted.length * 0.99)];
    return { mean, std, lo, hi };
  }, [map]);

  // Draw pixel map with a rich CMB-palette (blue → cyan → white → yellow → red)
  useEffect(() => {
    if (!map || !stats || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const N = map.length;
    canvas.width = N; canvas.height = N;
    const range = Math.max(stats.hi - stats.lo, 1e-6);
    const img = ctx.createImageData(N, N);
    for (let y = 0; y < N; y++) {
      for (let x = 0; x < N; x++) {
        let v = (map[y][x] - stats.lo) / range;
        v = Math.max(0, Math.min(1, v));
        const i = (y * N + x) * 4;
        let r, g, b;
        // 5-stop Planck-like ramp
        if (v < 0.25) {
          const u = v / 0.25;
          r = 10 + 30 * u; g = 20 + 120 * u; b = 140 + 100 * u;
        } else if (v < 0.50) {
          const u = (v - 0.25) / 0.25;
          r = 40 + 190 * u; g = 140 + 110 * u; b = 240 + 15 * u;
        } else if (v < 0.75) {
          const u = (v - 0.50) / 0.25;
          r = 230 + 25 * u; g = 250 - 70 * u; b = 255 - 200 * u;
        } else {
          const u = (v - 0.75) / 0.25;
          r = 255; g = 180 - 150 * u; b = 55 - 55 * u;
        }
        img.data[i] = r;
        img.data[i + 1] = g;
        img.data[i + 2] = b;
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }, [map, stats]);

  // Build histogram of pixel σ-values for the side panel
  const histogram = useMemo(() => {
    if (!map || !stats) return null;
    const bins = 32;
    const range = 8; // ±4σ
    const counts = new Array(bins).fill(0);
    const flat = map.flat();
    let maxCount = 0;
    for (const v of flat) {
      const s = (v - stats.mean) / stats.std;
      const idx = Math.max(0, Math.min(bins - 1, Math.floor(((s + range / 2) / range) * bins)));
      counts[idx]++;
      if (counts[idx] > maxCount) maxCount = counts[idx];
    }
    return { counts, maxCount, range, bins };
  }, [map, stats]);

  const handleCanvasClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!map || !stats || !wrapRef.current) return;
    const rect = wrapRef.current.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width;
    const py = (e.clientY - rect.top) / rect.height;
    const N = map.length;
    const x = Math.max(0, Math.min(N - 1, Math.floor(px * N)));
    const y = Math.max(0, Math.min(N - 1, Math.floor(py * N)));
    const value = map[y][x];
    const sigma = (value - stats.mean) / stats.std;
    setProbe({ x, y, sigma, value });
  }, [map, stats]);

  return (
    <div style={{ display: "grid", gap: 20, gridTemplateColumns: "minmax(0, 1fr) 340px" }} className="lab-grid">
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <Card padding={18} tone="aurora" glow>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10, flexWrap: "wrap", gap: 8 }}>
            <h3 style={{ fontFamily: theme.font.serif, color: theme.color.ink, fontSize: 22 }}>
              {pick({ ru: "Карта неба (имитация CMB)", en: "Sky map (CMB-like)" })}
            </h3>
            <div style={{ display: "flex", gap: 8 }}>
              <Badge tone={usingApi ? "aurora" : "muted"}>
                {usingApi ? pick({ ru: "API", en: "API" }) : pick({ ru: "офлайн", en: "offline" })}
              </Badge>
              {loading && <Badge tone="ember">{pick({ ru: "сканирую…", en: "scanning…" })}</Badge>}
            </div>
          </div>

          {/* Map + SVG overlay */}
          <div
            ref={wrapRef}
            onClick={handleCanvasClick}
            style={{
              position: "relative",
              background: "#05060f",
              borderRadius: theme.radius.md,
              border: `1px solid ${theme.color.line}`,
              padding: 12,
              display: "flex", justifyContent: "center", alignItems: "center",
              cursor: "crosshair",
            }}
          >
            <canvas
              ref={canvasRef}
              style={{
                width: "100%", maxWidth: 560, aspectRatio: "1/1",
                imageRendering: "auto",
                borderRadius: 10,
                boxShadow: "0 0 60px rgba(122, 252, 177, 0.22), inset 0 0 40px rgba(0,0,0,0.35)",
                display: "block",
              }}
            />
            {/* SVG overlay for pulsing halos — sized to canvas, uses map-coords via viewBox */}
            {result && map && (
              <svg
                viewBox={`0 0 ${map.length} ${map.length}`}
                style={{
                  position: "absolute", inset: 12,
                  width: "calc(100% - 24px)", maxWidth: 560,
                  height: "auto", aspectRatio: "1/1",
                  pointerEvents: "none",
                }}
              >
                {result.candidates.map((c, i) => (
                  <g key={i}>
                    <circle
                      cx={c.x + 0.5} cy={c.y + 0.5}
                      r={(c.radius ?? 3) + 2}
                      fill="none"
                      stroke="#ffd56b"
                      strokeWidth="0.8"
                      opacity="0.9"
                    />
                    <circle
                      cx={c.x + 0.5} cy={c.y + 0.5}
                      r={(c.radius ?? 3) + 5}
                      fill="none"
                      stroke="#ffd56b"
                      strokeWidth="0.5"
                      opacity="0.45"
                      style={{
                        transformOrigin: `${c.x + 0.5}px ${c.y + 0.5}px`,
                        animation: `anom-pulse 1.6s ${i * 0.07}s ease-out infinite`,
                      }}
                    />
                  </g>
                ))}
                {probe && (
                  <g>
                    <line
                      x1={probe.x + 0.5} y1={0} x2={probe.x + 0.5} y2={map.length}
                      stroke="rgba(255, 255, 255, 0.35)" strokeWidth="0.3" strokeDasharray="1,1"
                    />
                    <line
                      x1={0} y1={probe.y + 0.5} x2={map.length} y2={probe.y + 0.5}
                      stroke="rgba(255, 255, 255, 0.35)" strokeWidth="0.3" strokeDasharray="1,1"
                    />
                    <circle
                      cx={probe.x + 0.5} cy={probe.y + 0.5} r="3"
                      fill="none" stroke="#fff" strokeWidth="0.6"
                    />
                  </g>
                )}
              </svg>
            )}
            {/* Click read-out */}
            {probe && (
              <div style={{
                position: "absolute", left: 18, bottom: 18,
                padding: "8px 12px", borderRadius: 10,
                background: "rgba(5, 6, 15, 0.88)",
                border: `1px solid ${theme.color.lineStrong}`,
                color: theme.color.ink,
                fontFamily: theme.font.mono, fontSize: 12.5,
                pointerEvents: "none",
              }}>
                <div style={{ color: theme.color.inkSoft, fontSize: 11 }}>
                  {pick({ ru: "Клик:", en: "Click:" })} ({probe.x}, {probe.y})
                </div>
                <div style={{ color: Math.abs(probe.sigma) >= threshold ? theme.color.starlight : theme.color.ink }}>
                  {probe.sigma >= 0 ? "+" : ""}{probe.sigma.toFixed(2)}σ
                </div>
              </div>
            )}
          </div>

          {/* Presets — click to shift the picture dramatically */}
          <div style={{ display: "flex", gap: 6, marginTop: 14, flexWrap: "wrap" }}>
            {PRESETS.map((pr) => (
              <button
                key={pr.id}
                onClick={() => { setSeed(pr.seed); setContamination(pr.contamination); }}
                style={{
                  padding: "6px 12px", borderRadius: 999,
                  border: `1px solid ${theme.color.line}`,
                  background: "rgba(122, 252, 177, 0.06)",
                  color: theme.color.aurora,
                  cursor: "pointer", fontSize: 13,
                  display: "inline-flex", alignItems: "center", gap: 6,
                }}
              >{pr.emoji} {t(pr.label)}</button>
            ))}
            <button
              onClick={() => setSeed(Math.floor(Math.random() * 1e6))}
              style={{
                padding: "6px 12px", borderRadius: 999,
                border: `1px solid ${theme.color.starlight}`,
                background: "rgba(255, 213, 107, 0.08)",
                color: theme.color.starlight,
                cursor: "pointer", fontSize: 13,
                display: "inline-flex", alignItems: "center", gap: 6,
              }}
            >🎲 {pick({ ru: "Случайная", en: "Random" })}</button>
          </div>

          <div style={{ marginTop: 12, color: theme.color.inkSoft, fontSize: 13, fontStyle: "italic" }}>
            {pick({
              ru: "Наведи мышкой и кликни — покажем температуру этой точки в σ.",
              en: "Hover and click any pixel — we'll show its temperature in σ units.",
            })}
          </div>
        </Card>

        <Card padding={20} tone="plasma">
          <Badge tone="plasma" glyph="✦">{pick({ ru: "Как работает охотник", en: "How the hunter works" })}</Badge>
          <p style={{ color: theme.color.ink, fontFamily: theme.font.serif, fontSize: 17, lineHeight: 1.65, marginTop: 8 }}>
            {pick({
              ru: <>Алгоритм считает среднюю температуру и стандартное отклонение карты, переводит каждый пиксель в «сколько σ», затем подсвечивает места, выходящие за порог. Параллельно меряет <Term id="skewness">асимметрию</Term> и <Term id="kurtosis">эксцесс</Term> — отклонение от <Term id="gaussian">гауссова</Term> поведения.</>,
              en: <>The algorithm computes the map's mean and standard deviation, converts each pixel to "how many σ", and highlights spots beyond the threshold. It also measures <Term id="skewness">skewness</Term> and <Term id="kurtosis">kurtosis</Term> — deviations from <Term id="gaussian">Gaussian</Term> behaviour.</>,
            })}
          </p>
        </Card>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <Card padding={18} tone="aurora">
          <Badge tone="aurora" glyph="🔭">{pick({ ru: "Управление", en: "Controls" })}</Badge>
          <ParamSlider
            label={p("Порог обнаружения", "Detection threshold")}
            symbol="\\sigma"
            value={threshold} min={1} max={5} step={0.25}
            onChange={setThreshold}
            accent="ember"
            caption={p("Сколько стандартных отклонений нужно, чтобы пиксель попал в подозреваемые.", "How many standard deviations a pixel needs to qualify as a suspect.")}
          />
          <ParamSlider
            label={p("Уровень загрязнения", "Contamination level")}
            symbol="N_{\\text{anom}}"
            value={contamination} min={0} max={5} step={1}
            onChange={(v) => setContamination(v)}
            accent="nova"
            caption={p("Сколько искусственных аномалий впрыснуть в карту перед сканом.", "How many fake anomalies to inject before scanning.")}
            precision={0}
          />
        </Card>

        {/* Live histogram of σ values */}
        {histogram && stats && (
          <Card padding={16} tone="plasma">
            <div style={{ fontSize: 13, color: theme.color.ink, fontWeight: 600, marginBottom: 8 }}>
              {pick({ ru: "Гистограмма σ", en: "σ histogram" })}
            </div>
            <div style={{ position: "relative", height: 90, display: "flex", alignItems: "flex-end", gap: 1 }}>
              {histogram.counts.map((c, i) => {
                const binSigma = -histogram.range / 2 + (i / histogram.bins) * histogram.range;
                const outlier = Math.abs(binSigma) >= threshold;
                return (
                  <div key={i} style={{
                    flex: 1,
                    height: `${(c / histogram.maxCount) * 100}%`,
                    background: outlier ? theme.color.starlight : theme.color.plasma,
                    opacity: outlier ? 1 : 0.75,
                    borderRadius: "2px 2px 0 0",
                  }} />
                );
              })}
              {/* Threshold markers */}
              {[-threshold, threshold].map((st, i) => {
                const pos = ((st + histogram.range / 2) / histogram.range) * 100;
                if (pos < 0 || pos > 100) return null;
                return (
                  <div key={i} style={{
                    position: "absolute", top: 0, bottom: 0,
                    left: `${pos}%`,
                    width: 2,
                    background: theme.color.ember,
                    boxShadow: `0 0 6px ${theme.color.ember}`,
                  }} />
                );
              })}
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: theme.color.inkDim, marginTop: 4, fontFamily: theme.font.mono }}>
              <span>−4σ</span><span>0</span><span>+4σ</span>
            </div>
            <div style={{ fontSize: 11, color: theme.color.ember, marginTop: 4, textAlign: "center" }}>
              {pick({ ru: "оранжевые линии — текущий порог", en: "orange lines = current threshold" })}
            </div>
          </Card>
        )}

        {result && (
          <Card padding={16} tone="ember">
            <Badge tone="ember" glyph="✺">{pick({ ru: "Результат", en: "Result" })}</Badge>
            <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
              <Stat label={pick({ ru: "Найдено кандидатов", en: "Candidates found" })}
                value={result.n_anomalies}
                color={result.n_anomalies > 0 ? theme.color.starlight : theme.color.aurora} />
              <Stat label={pick({ ru: "Глобальный счёт", en: "Global score" })}
                value={result.global_score.toFixed(3)} color={theme.color.plasma} />
              <Stat label={pick({ ru: "Время инференса", en: "Inference time" })}
                value={`${result.inference_time_ms.toFixed(1)} ms`} color={theme.color.inkSoft} />
            </div>
            <div style={{ marginTop: 12, padding: 12, borderRadius: 8, background: "rgba(155,140,255,0.05)", border: `1px solid ${theme.color.line}`, fontSize: 13 }}>
              <div style={{ color: theme.color.inkSoft, marginBottom: 6, fontWeight: 600 }}>{pick({ ru: "Негауссовость", en: "Non-Gaussianity" })}</div>
              <Mini label={pick({ ru: "Асимметрия", en: "Skewness" })} val={result.non_gaussianity.skewness.toFixed(3)} pval={result.non_gaussianity.skew_pvalue.toFixed(3)} />
              <Mini label={pick({ ru: "Эксцесс", en: "Kurtosis" })} val={result.non_gaussianity.kurtosis.toFixed(3)} pval={result.non_gaussianity.kurt_pvalue.toFixed(3)} />
              <div style={{
                marginTop: 8, padding: "6px 10px", borderRadius: 6, textAlign: "center", fontSize: 12,
                background: result.non_gaussianity.is_gaussian ? "rgba(122,252,177,0.18)" : "rgba(255,138,94,0.18)",
                color: result.non_gaussianity.is_gaussian ? theme.color.aurora : theme.color.ember,
              }}>
                {result.non_gaussianity.is_gaussian
                  ? pick({ ru: "✓ Согласовано с гауссовым шумом", en: "✓ Consistent with Gaussian noise" })
                  : pick({ ru: "⚠ Похоже, есть отклонение!", en: "⚠ Looks non-Gaussian!" })}
              </div>
            </div>
          </Card>
        )}

        <Callout variant="challenge">
          {pick({
            ru: <>Попробуй пресет «Чистое небо» и порог 2σ — сколько «ложных» кандидатов? Теперь «Холодное пятно» — найдёт ли детектор самое жуткое место во Вселенной?</>,
            en: <>Try the "Clean sky" preset with a 2σ threshold — how many false candidates show up? Now "WMAP cold spot" — does the detector find the scariest spot in the Universe?</>,
          })}
        </Callout>
      </div>

      <style>{`
        @keyframes anom-pulse {
          0%   { transform: scale(1);   opacity: 0.6; }
          70%  { transform: scale(2.5); opacity: 0; }
          100% { transform: scale(2.5); opacity: 0; }
        }
      `}</style>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: React.ReactNode; color: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", padding: "10px 12px", borderRadius: 8, background: "rgba(155,140,255,0.05)" }}>
      <span style={{ color: theme.color.inkSoft, fontSize: 13 }}>{label}</span>
      <span style={{ color, fontFamily: theme.font.mono, fontWeight: 700 }}>{value}</span>
    </div>
  );
}

function Mini({ label, val, pval }: { label: string; val: string; pval: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 3 }}>
      <span style={{ color: theme.color.inkSoft }}>{label}</span>
      <span style={{ fontFamily: theme.font.mono, color: theme.color.ink }}>{val} <span style={{ color: theme.color.inkDim }}>(p={pval})</span></span>
    </div>
  );
}
