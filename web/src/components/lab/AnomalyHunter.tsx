import React, { useCallback, useEffect, useRef, useState } from "react";
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

function generateMap(size: number, seed: number, contamination: number): number[][] {
  let s = seed;
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
  // Smooth (gives correlated CMB-like patches)
  let smoothed = m.map((r) => r.slice());
  for (let p = 0; p < 3; p++) {
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
  // Inject anomalies
  const nAnom = Math.round(contamination * 4);
  for (let i = 0; i < nAnom; i++) {
    const cx = Math.floor(rand() * size);
    const cy = Math.floor(rand() * size);
    const radius = 3 + Math.floor(rand() * 4);
    const sign = rand() > 0.5 ? 1 : -1;
    const amp = sign * (60 + rand() * 80);
    for (let dy = -radius; dy <= radius; dy++) {
      for (let dx = -radius; dx <= radius; dx++) {
        const x = cx + dx, y = cy + dy;
        if (x < 0 || x >= size || y < 0 || y >= size) continue;
        const r2 = dx * dx + dy * dy;
        if (r2 > radius * radius) continue;
        smoothed[y][x] += amp * Math.exp(-r2 / (radius * radius));
      }
    }
  }
  return smoothed;
}

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
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Regenerate map whenever seed or contamination changes.
  useEffect(() => {
    setMap(generateMap(size, seed, contamination));
  }, [size, seed, contamination]);

  const regen = useCallback(() => {
    setSeed(Math.floor(Math.random() * 1e6));
  }, []);

  // Auto-run the detector whenever map or threshold changes (debounced).
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
    }, 180);
    return () => clearTimeout(timer);
  }, [map, threshold]);

  // Render map + overlays
  useEffect(() => {
    if (!map || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const N = map.length;
    canvas.width = N; canvas.height = N;
    const flat = map.flat();
    let mn = Infinity, mx = -Infinity;
    for (const v of flat) { if (v < mn) mn = v; if (v > mx) mx = v; }
    const r = mx - mn || 1;
    const img = ctx.createImageData(N, N);
    for (let y = 0; y < N; y++) {
      for (let x = 0; x < N; x++) {
        const v = (map[y][x] - mn) / r;
        const i = (y * N + x) * 4;
        // Real CMB Planck colormap-ish: deep blue → red
        if (v < 0.5) {
          const u = v * 2;
          img.data[i] = 10 + 50 * u;
          img.data[i + 1] = 40 + 130 * u;
          img.data[i + 2] = 160 + 95 * u;
        } else {
          const u = (v - 0.5) * 2;
          img.data[i] = 60 + 195 * u;
          img.data[i + 1] = 170 - 120 * u;
          img.data[i + 2] = 255 - 220 * u;
        }
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    if (result) {
      ctx.lineWidth = 1.5;
      for (const c of result.candidates) {
        ctx.strokeStyle = "#ffd56b";
        ctx.beginPath();
        ctx.arc(c.x, c.y, c.radius + 2, 0, Math.PI * 2);
        ctx.stroke();
        // halo
        ctx.strokeStyle = "rgba(255,213,107,0.35)";
        ctx.beginPath();
        ctx.arc(c.x, c.y, c.radius + 5, 0, Math.PI * 2);
        ctx.stroke();
      }
    }
  }, [map, result]);

  return (
    <div style={{ display: "grid", gap: 24, gridTemplateColumns: "minmax(0, 1fr) 360px" }} className="lab-grid">
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <Card padding={18} tone="aurora" glow>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10, flexWrap: "wrap", gap: 8 }}>
            <h3 style={{ fontFamily: theme.font.serif, color: theme.color.ink }}>
              {pick({ ru: "Карта неба (имитация CMB)", en: "Sky map (CMB-like)" })}
            </h3>
            <Badge tone={usingApi ? "aurora" : "muted"}>
              {usingApi ? pick({ ru: "API", en: "API" }) : pick({ ru: "офлайн", en: "offline" })}
            </Badge>
          </div>
          <div style={{
            background: "#05060f",
            borderRadius: theme.radius.md,
            border: `1px solid ${theme.color.line}`,
            padding: 12,
            display: "flex", justifyContent: "center",
          }}>
            <canvas
              ref={canvasRef}
              style={{
                width: "100%", maxWidth: 460, aspectRatio: "1/1",
                imageRendering: "pixelated",
                borderRadius: 8,
                boxShadow: "0 0 40px rgba(122, 252, 177, 0.25)",
              }}
            />
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap", alignItems: "center" }}>
            <Button variant="primary" onClick={regen}>🎲 {pick({ ru: "Новая карта", en: "New map" })}</Button>
            <span style={{ fontSize: 12, color: theme.color.inkDim }}>
              {loading
                ? pick({ ru: "Сканирую…", en: "Scanning…" })
                : pick({ ru: "Детектор работает автоматически — двигай порог и уровень загрязнения.", en: "Detector runs automatically — move the threshold and contamination sliders." })}
            </span>
          </div>
        </Card>

        <Card padding={20} tone="plasma">
          <Badge tone="plasma" glyph="✦">{pick({ ru: "Как работает охотник", en: "How the hunter works" })}</Badge>
          <p style={{ color: theme.color.ink, fontFamily: theme.font.serif, fontSize: 16, lineHeight: 1.65, marginTop: 8 }}>
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
            symbol="σ"
            value={threshold} min={1} max={5} step={0.25}
            onChange={setThreshold}
            accent="ember"
            caption={p("Сколько стандартных отклонений нужно, чтобы пиксель попал в подозреваемые.", "How many standard deviations a pixel needs to qualify as a suspect.")}
          />
          <ParamSlider
            label={p("Уровень загрязнения", "Contamination level")}
            symbol="N_anom"
            value={contamination} min={0} max={5} step={1}
            onChange={(v) => setContamination(v)}
            accent="nova"
            caption={p("Сколько искусственных аномалий впрыснуть в карту перед сканом.", "How many fake anomalies to inject before scanning.")}
            precision={0}
          />
        </Card>

        {result && (
          <Card padding={18} tone="ember">
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
            <div style={{ marginTop: 12, padding: 10, borderRadius: 8, background: "rgba(155,140,255,0.05)", border: `1px solid ${theme.color.line}`, fontSize: 12 }}>
              <div style={{ color: theme.color.inkSoft, marginBottom: 6, fontWeight: 600 }}>{pick({ ru: "Негауссовость", en: "Non-Gaussianity" })}</div>
              <Mini label={pick({ ru: "Асимметрия", en: "Skewness" })} val={result.non_gaussianity.skewness.toFixed(3)} pval={result.non_gaussianity.skew_pvalue.toFixed(3)} />
              <Mini label={pick({ ru: "Эксцесс", en: "Kurtosis" })} val={result.non_gaussianity.kurtosis.toFixed(3)} pval={result.non_gaussianity.kurt_pvalue.toFixed(3)} />
              <div style={{
                marginTop: 8, padding: "5px 8px", borderRadius: 6, textAlign: "center", fontSize: 11.5,
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
            ru: <>Нажми «Сгенерировать» с уровнем загрязнения 0 — это «чистое» небо. Запусти детектор. Сколько «ложных» кандидатов он нашёл при пороге 3σ? А при 2σ?</>,
            en: <>Set contamination to 0 (a "clean" sky) and run the detector. How many false candidates pop up at 3σ? And at 2σ?</>,
          })}
        </Callout>
      </div>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: React.ReactNode; color: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", padding: "8px 12px", borderRadius: 8, background: "rgba(155,140,255,0.05)" }}>
      <span style={{ color: theme.color.inkSoft, fontSize: 12 }}>{label}</span>
      <span style={{ color, fontFamily: theme.font.mono, fontWeight: 700 }}>{value}</span>
    </div>
  );
}

function Mini({ label, val, pval }: { label: string; val: string; pval: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 3 }}>
      <span style={{ color: theme.color.inkSoft }}>{label}</span>
      <span style={{ fontFamily: theme.font.mono, color: theme.color.ink }}>{val} <span style={{ color: theme.color.inkDim }}>(p={pval})</span></span>
    </div>
  );
}
