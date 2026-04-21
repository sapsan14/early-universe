import React, { useEffect, useRef, useState } from "react";
import { theme } from "../../theme";
import { useT, p } from "../../i18n";
import { post, DEFAULT_PARAMS, type CosmoParams, type SpectrumResponse } from "../../api/client";
import { localSpectrum } from "../../physics";
import { ParamSlider } from "../ui/Slider";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Callout } from "../ui/Callout";
import { Button } from "../ui/Button";
import { MathBlock } from "../ui/Math";

const PRESETS: { id: string; label: { ru: string; en: string }; params: CosmoParams }[] = [
  { id: "planck", label: { ru: "Planck 2018 (наш мир)", en: "Planck 2018 (our world)" }, params: { ...DEFAULT_PARAMS } },
  { id: "wmap", label: { ru: "WMAP 2013", en: "WMAP 2013" }, params: { H0: 69.32, Omega_b_h2: 0.02223, Omega_cdm_h2: 0.1153, n_s: 0.9608, ln10As: 3.089, tau_reio: 0.081 } },
  { id: "tilted", label: { ru: "Сильный наклон n_s=1.05", en: "Strong tilt n_s=1.05" }, params: { ...DEFAULT_PARAMS, n_s: 1.05 } },
  { id: "no-cdm", label: { ru: "Без тёмной материи", en: "No dark matter" }, params: { ...DEFAULT_PARAMS, Omega_cdm_h2: 0.005 } },
  { id: "noisy", label: { ru: "Громкая инфляция", en: "Loud inflation" }, params: { ...DEFAULT_PARAMS, ln10As: 3.6 } },
];

export function ParameterStudio() {
  const { t, pick, lang } = useT();
  const [params, setParams] = useState<CosmoParams>({ ...DEFAULT_PARAMS });
  const [spectrum, setSpectrum] = useState<SpectrumResponse | null>(null);
  const [reference, setReference] = useState<SpectrumResponse | null>(null);
  const [usingApi, setUsingApi] = useState(false);
  const [showRef, setShowRef] = useState(true);
  const [hover, setHover] = useState<{ x: number; ell: number; dl: number } | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Reference spectrum (Planck 2018) — fetch once
  useEffect(() => {
    post<SpectrumResponse>("/api/v1/spectrum", { params: DEFAULT_PARAMS, l_max: 2500 })
      .then((r) => setReference(r))
      .catch(() => setReference(localSpectrum(DEFAULT_PARAMS, 2500)));
  }, []);

  // Active spectrum on every param change
  useEffect(() => {
    const timer = setTimeout(() => {
      post<SpectrumResponse>("/api/v1/spectrum", { params, l_max: 2500 })
        .then((r) => { setSpectrum(r); setUsingApi(true); })
        .catch(() => { setSpectrum(localSpectrum(params, 2500)); setUsingApi(false); });
    }, 80);
    return () => clearTimeout(timer);
  }, [params]);

  // Render canvas
  useEffect(() => {
    if (!spectrum || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const dpr = window.devicePixelRatio;
    const cssW = canvas.parentElement?.clientWidth ?? 600;
    const cssH = 360;
    canvas.width = cssW * dpr; canvas.height = cssH * dpr;
    canvas.style.width = cssW + "px"; canvas.style.height = cssH + "px";
    ctx.scale(dpr, dpr);
    const w = cssW, h = cssH;
    ctx.clearRect(0, 0, w, h);

    const compute = (s: SpectrumResponse) => {
      const dl = s.ell.map((l, i) => l * (l + 1) * s.cl[i] / (2 * Math.PI));
      const log = dl.map((d) => Math.log10(Math.max(d, 1e-30)));
      return { ell: s.ell, log };
    };
    const a = compute(spectrum);
    const b = reference ? compute(reference) : null;

    const xMin = Math.log10(Math.max(a.ell[0], 2));
    const xMax = Math.log10(a.ell[a.ell.length - 1]);
    const all = b ? [...a.log, ...b.log] : a.log;
    const yMin = Math.min(...all) - 0.4;
    const yMax = Math.max(...all) + 0.4;

    const pad = { l: 56, r: 16, t: 14, b: 36 };
    const pw = w - pad.l - pad.r;
    const ph = h - pad.t - pad.b;
    const toX = (lx: number) => pad.l + ((lx - xMin) / (xMax - xMin)) * pw;
    const toY = (ly: number) => pad.t + ((yMax - ly) / (yMax - yMin)) * ph;

    // Grid
    ctx.strokeStyle = "rgba(159, 144, 240, 0.18)";
    ctx.lineWidth = 1;
    ctx.font = "11px ui-monospace,monospace";
    ctx.fillStyle = "rgba(169,177,214,0.7)";
    for (let lx = Math.ceil(xMin); lx <= xMax; lx++) {
      const x = toX(lx);
      ctx.beginPath(); ctx.moveTo(x, pad.t); ctx.lineTo(x, h - pad.b); ctx.stroke();
      ctx.fillText(`10^${lx}`, x - 14, h - pad.b + 14);
    }
    for (let ly = Math.ceil(yMin); ly <= yMax; ly++) {
      const y = toY(ly);
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
      ctx.fillText(`10^${ly}`, 6, y + 4);
    }

    // Axis labels
    ctx.fillStyle = "rgba(232,236,255,0.85)";
    ctx.font = "12px Inter";
    ctx.fillText(pick({ ru: "Мультиполь ℓ", en: "Multipole ℓ" }), w / 2 - 30, h - 4);
    ctx.save();
    ctx.translate(14, h / 2 + 40); ctx.rotate(-Math.PI / 2);
    ctx.fillText("ℓ(ℓ+1)Cℓ / (2π)  [μK²]", 0, 0);
    ctx.restore();

    // Reference (Planck 2018) line
    if (b && showRef) {
      ctx.strokeStyle = "rgba(255, 213, 107, 0.45)";
      ctx.setLineDash([6, 4]);
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      for (let i = 0; i < b.ell.length; i++) {
        const x = toX(Math.log10(b.ell[i]));
        const y = toY(b.log[i]);
        i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
      }
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Active spectrum
    const grad = ctx.createLinearGradient(0, 0, w, 0);
    grad.addColorStop(0, "#5ee2ff");
    grad.addColorStop(0.5, "#9b8cff");
    grad.addColorStop(1, "#ff7ac6");
    ctx.strokeStyle = grad;
    ctx.lineWidth = 2.5;
    ctx.shadowColor = "rgba(155,140,255,0.6)";
    ctx.shadowBlur = 8;
    ctx.beginPath();
    for (let i = 0; i < a.ell.length; i++) {
      const x = toX(Math.log10(a.ell[i]));
      const y = toY(a.log[i]);
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Hover indicator
    if (hover) {
      ctx.strokeStyle = "rgba(255, 213, 107, 0.7)";
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(hover.x, pad.t);
      ctx.lineTo(hover.x, h - pad.b);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }, [spectrum, reference, showRef, pick, hover]);

  return (
    <div style={{ display: "grid", gap: 24, gridTemplateColumns: "320px minmax(0, 1fr)" }} className="lab-grid">
      {/* Sliders */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <Card padding={18} tone="plasma">
          <Badge tone="plasma" glyph="⚛">{pick({ ru: "Шесть параметров", en: "Six Parameters" })}</Badge>
          <p style={{ color: theme.color.inkSoft, fontSize: 13, lineHeight: 1.5, marginTop: 8 }}>
            {pick({
              ru: <>Подвинь любой ползунок — спектр CMB перерисуется на лету. Желтая пунктирная линия = эталон Planck 2018.</>,
              en: <>Move any slider — the CMB spectrum redraws on the fly. The dashed gold line = Planck 2018 reference.</>,
            })}
          </p>
        </Card>

        <ParamSlider
          label={p("Хаббл H₀", "Hubble H₀")}
          symbol="H₀" unit="km/s/Mpc"
          termId="hubble"
          value={params.H0} min={50} max={100} step={0.1}
          onChange={(v) => setParams((p) => ({ ...p, H0: v }))}
          accent="starlight"
          marks={[{ value: 67.36, label: p("Planck", "Planck") }, { value: 73, label: p("HST", "HST") }]}
          caption={p("Скорость расширения сегодня. Загадка H₀ — Planck и HST спорят на 7%.", "Today's expansion rate. The H₀ tension — Planck and HST disagree by ~7%.")}
        />
        <ParamSlider
          label={p("Барионы Ω_b h²", "Baryons Ω_b h²")}
          symbol="Ω_b h²"
          termId="omega-b-h2"
          value={params.Omega_b_h2} min={0.015} max={0.030} step={0.0005}
          onChange={(v) => setParams((p) => ({ ...p, Omega_b_h2: v }))}
          accent="aurora"
          caption={p("Сколько обычного вещества. Управляет балансом первого/второго пика.", "Amount of ordinary matter. Sets the first/second peak balance.")}
        />
        <ParamSlider
          label={p("Тёмная материя Ω_cdm h²", "Dark matter Ω_cdm h²")}
          symbol="Ω_cdm h²"
          termId="omega-cdm-h2"
          value={params.Omega_cdm_h2} min={0.05} max={0.20} step={0.005}
          onChange={(v) => setParams((p) => ({ ...p, Omega_cdm_h2: v }))}
          accent="nova"
          caption={p("Невидимая «опора» структур. Сдвигает все пики горизонтально.", "Invisible 'scaffolding' for structure. Shifts every peak horizontally.")}
        />
        <ParamSlider
          label={p("Наклон n_s", "Tilt n_s")}
          symbol="n_s"
          termId="n-s"
          value={params.n_s} min={0.85} max={1.10} step={0.005}
          onChange={(v) => setParams((p) => ({ ...p, n_s: v }))}
          accent="plasma"
          marks={[{ value: 1.0, label: p("Хариссон", "Harrison") }, { value: 0.965, label: p("Planck", "Planck") }]}
          caption={p("n_s = 1 — все масштабы равны. n_s < 1 — больше крупных пятен.", "n_s = 1 — all scales equal. n_s < 1 — more big patches.")}
        />
        <ParamSlider
          label={p("Амплитуда A_s", "Amplitude A_s")}
          symbol="ln(10¹⁰ A_s)"
          termId="a-s"
          value={params.ln10As} min={2.4} max={3.8} step={0.02}
          onChange={(v) => setParams((p) => ({ ...p, ln10As: v }))}
          accent="ember"
          caption={p("Громкость инфляционного шёпота. Поднимает спектр выше.", "Loudness of the inflation whisper. Lifts the whole spectrum.")}
        />
        <ParamSlider
          label={p("Реионизация τ", "Reionization τ")}
          symbol="τ_reio"
          termId="tau"
          value={params.tau_reio} min={0.01} max={0.15} step={0.005}
          onChange={(v) => setParams((p) => ({ ...p, tau_reio: v }))}
          accent="aurora"
          caption={p("Какая часть фотонов CMB рассеялась первыми звёздами.", "Fraction of CMB photons re-scattered by the first stars.")}
        />

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Button variant="primary" size="sm" full onClick={() => setParams({ ...DEFAULT_PARAMS })}>
            ✦ {pick({ ru: "Сброс к Planck 2018", en: "Reset to Planck 2018" })}
          </Button>
        </div>

        <Card padding={14} tone="aurora">
          <div style={{ fontSize: 12, color: theme.color.inkSoft, marginBottom: 8, fontWeight: 600 }}>
            {pick({ ru: "Готовые наборы", en: "Ready presets" })}
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {PRESETS.map((pr) => (
              <button
                key={pr.id}
                onClick={() => setParams(pr.params)}
                style={{
                  padding: "5px 10px", borderRadius: 999,
                  border: `1px solid ${theme.color.line}`,
                  background: "rgba(122, 252, 177, 0.08)",
                  color: theme.color.aurora,
                  cursor: "pointer", fontSize: 12,
                }}
              >{t(pr.label)}</button>
            ))}
          </div>
        </Card>
      </div>

      {/* Plot + interpretation */}
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <Card padding={18} tone="plasma" glow>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6, flexWrap: "wrap", gap: 8 }}>
            <h3 style={{ fontFamily: theme.font.serif, color: theme.color.ink }}>
              {pick({ ru: "Спектр мощности CMB", en: "CMB power spectrum" })}
            </h3>
            <div style={{ display: "flex", gap: 10, fontSize: 12, color: theme.color.inkSoft, alignItems: "center" }}>
              <label style={{ display: "inline-flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
                <input type="checkbox" checked={showRef} onChange={(e) => setShowRef(e.target.checked)} />
                {pick({ ru: "Эталон Planck 2018", en: "Planck 2018 reference" })}
              </label>
              <Badge tone={usingApi ? "aurora" : "muted"}>
                {usingApi ? pick({ ru: "API", en: "API" }) : pick({ ru: "офлайн", en: "offline" })}
              </Badge>
            </div>
          </div>
          <div
            style={{ position: "relative" }}
            onMouseMove={(e) => {
              const c = canvasRef.current;
              if (!c || !spectrum) return;
              const rect = c.getBoundingClientRect();
              const x = e.clientX - rect.left;
              const lMin = Math.log10(Math.max(spectrum.ell[0], 2));
              const lMax = Math.log10(spectrum.ell[spectrum.ell.length - 1]);
              const pad = 56, prgt = 16;
              const u = (x - pad) / (rect.width - pad - prgt);
              const lx = lMin + u * (lMax - lMin);
              const ell = Math.round(Math.pow(10, lx));
              const i = spectrum.ell.findIndex((v) => v >= ell);
              if (i < 0) return;
              const dl = spectrum.ell[i] * (spectrum.ell[i] + 1) * spectrum.cl[i] / (2 * Math.PI);
              setHover({ x, ell: spectrum.ell[i], dl });
            }}
            onMouseLeave={() => setHover(null)}
          >
            <canvas ref={canvasRef} style={{ width: "100%", display: "block" }} />
            {hover && (
              <div style={{
                position: "absolute",
                left: hover.x + 12, top: 14,
                background: "rgba(15,10,46,0.95)",
                border: `1px solid ${theme.color.lineStrong}`,
                borderRadius: 8, padding: "6px 10px",
                fontSize: 12, fontFamily: theme.font.mono,
                color: theme.color.starlight,
                pointerEvents: "none",
              }}>
                ℓ = {hover.ell} → D_ℓ = {hover.dl.toExponential(2)}
              </div>
            )}
          </div>
        </Card>

        <Card padding={20} tone="aurora">
          <Badge tone="aurora" glyph="✦">{pick({ ru: "Что я вижу?", en: "What am I looking at?" })}</Badge>
          <p style={{ color: theme.color.ink, fontFamily: theme.font.serif, fontSize: 16, lineHeight: 1.65, marginTop: 8 }}>
            {pick({
              ru: <>Этот график называется «спектром мощности CMB». По горизонтали — мультиполь ℓ (мелкость рисунка на небе). По вертикали — сколько «энергии» в флуктуациях на данном масштабе. Три горба — следы звуковых волн в плазме до рекомбинации.</>,
              en: <>This graph is called the "CMB power spectrum". The horizontal axis is multipole ℓ (the fineness of the sky pattern). The vertical axis is how much "energy" lives in fluctuations at that scale. The three humps are echoes of sound waves in the plasma before recombination.</>,
            })}
          </p>
          <MathBlock
            formula="D_ℓ = ℓ(ℓ + 1) C_ℓ / (2π)"
            caption={p("Так удобно отображать спектр — он становится почти плоским на больших ℓ.", "A convenient form — it makes the spectrum nearly flat at large ℓ.")}
          />
        </Card>

        <Callout variant="challenge">
          {pick({
            ru: <>Попробуй три эксперимента: 1) снизь Ω_b h² до минимума — куда уходит второй пик? 2) подвинь n_s к 1.10 — что происходит со спектром в целом? 3) подними A_s — как меняется высота пиков?</>,
            en: <>Try three experiments: 1) drop Ω_b h² to its minimum — where does the second peak go? 2) slide n_s to 1.10 — what happens to the overall spectrum? 3) raise A_s — how do the peak heights change?</>,
          })}
        </Callout>
      </div>

      <style>{`
        @media (max-width: 980px) {
          .lab-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}
