import React, { useEffect, useRef, useState, useCallback } from "react";
import { theme } from "../../theme";
import { useT, p } from "../../i18n";
import { post, DEFAULT_PARAMS, type CosmoParams, type PlayableResponse } from "../../api/client";
import { localPlayable } from "../../physics";
import { ParamSlider } from "../ui/Slider";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Callout } from "../ui/Callout";
import { Button } from "../ui/Button";

export function UniverseGarden() {
  const { pick, t } = useT();
  const [params, setParams] = useState<CosmoParams>({ ...DEFAULT_PARAMS });
  const [data, setData] = useState<PlayableResponse | null>(null);
  const [frame, setFrame] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [usingApi, setUsingApi] = useState(false);
  const [seed, setSeed] = useState(42);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const simulate = useCallback(async () => {
    setLoading(true);
    let result: PlayableResponse;
    try {
      result = await post<PlayableResponse>("/api/v1/simulations/playable", {
        params, grid_size: 96, n_steps: 12, seed,
      });
      setUsingApi(true);
    } catch {
      result = localPlayable(params, 96, 12, seed);
      setUsingApi(false);
    }
    setData(result);
    setFrame(result.snapshots.length - 1); // show the final "grown" state
    setPlaying(false);
    setLoading(false);
  }, [params, seed]);

  // Auto-regenerate (debounced) whenever parameters change so sliders feel alive.
  useEffect(() => {
    const timer = setTimeout(() => { simulate(); }, 250);
    return () => clearTimeout(timer);
  }, [simulate]);

  // animation
  useEffect(() => {
    if (!playing || !data) return;
    const id = setInterval(() => {
      setFrame((f) => {
        if (f >= data.snapshots.length - 1) { setPlaying(false); return f; }
        return f + 1;
      });
    }, 280);
    return () => clearInterval(id);
  }, [playing, data]);

  // render snapshot
  const [strength, setStrength] = useState(0);
  useEffect(() => {
    if (!data || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const snap = data.snapshots[frame];
    const N = snap.length;
    canvas.width = N; canvas.height = N;

    const flat = snap.flat();

    // Robust statistics: sort once, use 1st / 99th percentiles as colour-map
    // bounds so a single extreme pixel can't wash the whole frame to one colour.
    const sorted = flat.slice().sort((a, b) => a - b);
    const lo = sorted[Math.floor(sorted.length * 0.01)];
    const hi = sorted[Math.floor(sorted.length * 0.99)];
    const range = Math.max(hi - lo, 1e-6);

    // True std for the "structure strength" meter
    let sum = 0; for (const v of flat) sum += v;
    const mean = sum / flat.length;
    let sumSq = 0; for (const v of flat) sumSq += (v - mean) ** 2;
    setStrength(Math.sqrt(sumSq / flat.length));

    const img = ctx.createImageData(N, N);
    for (let y = 0; y < N; y++) {
      for (let x = 0; x < N; x++) {
        // Normalise, clip into [0, 1]
        let v = (snap[y][x] - lo) / range;
        v = Math.max(0, Math.min(1, v));
        // Aggressive gamma lifts the midtones so a mostly-Gaussian field
        // looks colourful even when it sits around 0.3–0.5 of the range.
        v = Math.pow(v, 0.45);
        const i = (y * N + x) * 4;
        // Inferno-inspired 5-stop ramp: deep violet → magenta → orange →
        // amber → cream. No near-black region so the canvas never looks
        // empty even at low A_s.
        let r, g, b;
        if (v < 0.25) {
          const u = v / 0.25;
          r = 22 + 68 * u; g = 8 + 14 * u; b = 58 + 102 * u;
        } else if (v < 0.50) {
          const u = (v - 0.25) / 0.25;
          r = 90 + 130 * u; g = 22 + 38 * u; b = 160 - 40 * u;
        } else if (v < 0.75) {
          const u = (v - 0.50) / 0.25;
          r = 220 + 35 * u; g = 60 + 105 * u; b = 120 - 95 * u;
        } else {
          const u = (v - 0.75) / 0.25;
          r = 255; g = 165 + 80 * u; b = 25 + 190 * u;
        }
        img.data[i] = r;
        img.data[i + 1] = g;
        img.data[i + 2] = b;
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }, [data, frame]);

  const verdict = data?.structure_formed
    ? { tone: "aurora" as const, label: pick({ ru: "Структура сформировалась! Космическая паутина видна.", en: "Structure formed! Cosmic web visible." }) }
    : { tone: "ember" as const, label: pick({ ru: "Структуры почти нет. Скорее всего, не хватает тёмной материи или мала громкость инфляции.", en: "Almost no structure. Likely too little dark matter or quiet inflation." }) };

  return (
    <div style={{ display: "grid", gap: 24, gridTemplateColumns: "320px minmax(0, 1fr)" }} className="lab-grid">
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <Card padding={18} tone="nova">
          <Badge tone="nova" glyph="🌀">{pick({ ru: "Играбельная Вселенная", en: "Playable Universe" })}</Badge>
          <p style={{ color: theme.color.inkSoft, fontSize: 13, lineHeight: 1.5, marginTop: 8 }}>
            {pick({
              ru: <>Двигай слайдеры — симуляция пересчитывается автоматически. Показываем финальный кадр; ползунок времени внизу прокручивает рост.</>,
              en: <>Move the sliders — the simulation auto-regenerates. The final frame is shown; scrub the time slider below to replay the growth.</>,
            })}
          </p>
        </Card>

        <ParamSlider
          label={p("Хаббл", "Hubble")}
          symbol="H_0" unit="km/s/Mpc"
          value={params.H0} min={50} max={100} step={1}
          onChange={(v) => setParams((p) => ({ ...p, H0: v }))}
          accent="starlight"
          termId="hubble"
        />
        <ParamSlider
          label={p("Тёмная материя", "Dark matter")}
          symbol="\\Omega_{\\rm cdm} h^2"
          value={params.Omega_cdm_h2} min={0.005} max={0.40} step={0.005}
          onChange={(v) => setParams((p) => ({ ...p, Omega_cdm_h2: v }))}
          accent="nova"
          termId="dark-matter"
        />
        <ParamSlider
          label={p("Громкость инфляции", "Inflation loudness")}
          symbol="\\ln(10^{10}\\, A_s)"
          value={params.ln10As} min={1.5} max={4.5} step={0.05}
          onChange={(v) => setParams((p) => ({ ...p, ln10As: v }))}
          accent="ember"
          termId="a-s"
        />
        <ParamSlider
          label={p("Наклон спектра", "Spectral tilt")}
          symbol="n_s"
          value={params.n_s} min={0.7} max={1.3} step={0.01}
          onChange={(v) => setParams((p) => ({ ...p, n_s: v }))}
          accent="plasma"
          termId="n-s"
        />

        <Button variant="primary" full onClick={() => setSeed(Math.floor(Math.random() * 1_000_000))} disabled={loading}>
          {loading ? pick({ ru: "Пересчитываю…", en: "Recomputing…" }) : pick({ ru: "🎲 Бросить новый мир", en: "🎲 Re-roll the world" })}
        </Button>
        <Button variant="soft" full onClick={() => setParams({ ...DEFAULT_PARAMS })}>
          {pick({ ru: "Сброс к Planck 2018", en: "Reset to Planck 2018" })}
        </Button>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <Card padding={18} tone="nova" glow>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10, flexWrap: "wrap", gap: 8 }}>
            <h3 style={{ fontFamily: theme.font.serif, color: theme.color.ink }}>
              {pick({ ru: "Поле плотности материи", en: "Matter density field" })}
            </h3>
            <Badge tone={usingApi ? "aurora" : "muted"}>
              {usingApi ? pick({ ru: "API", en: "API" }) : pick({ ru: "офлайн", en: "offline" })}
            </Badge>
          </div>
          <div style={{
            position: "relative",
            background: "#05060f",
            borderRadius: theme.radius.md,
            border: `1px solid ${theme.color.line}`,
            display: "flex", justifyContent: "center", alignItems: "center",
            padding: 12,
            minHeight: 360,
            overflow: "hidden",
          }}>
            <canvas
              ref={canvasRef}
              style={{
                width: "100%", maxWidth: 560, aspectRatio: "1/1",
                // auto gives us browser-smooth interpolation — the 96×96
                // grid rendered at 560 px looks silky instead of blocky
                imageRendering: "auto",
                borderRadius: 12,
                boxShadow: "0 0 60px rgba(255, 122, 198, 0.35), inset 0 0 60px rgba(0,0,0,0.3)",
                opacity: data ? 1 : 0.15,
                transition: theme.motion.base,
              }}
            />
            {loading && (
              <div style={{
                position: "absolute", inset: 12,
                borderRadius: 8,
                background: "linear-gradient(120deg, rgba(255,122,198,0.0) 30%, rgba(255,255,255,0.12) 50%, rgba(255,122,198,0.0) 70%)",
                backgroundSize: "200% 100%",
                animation: "shimmer 1.1s linear infinite",
                pointerEvents: "none",
              }} />
            )}
            {loading && (
              <div style={{
                position: "absolute",
                top: 18, right: 22,
                padding: "4px 12px",
                borderRadius: 999,
                background: "rgba(5, 6, 15, 0.8)",
                border: `1px solid ${theme.color.nova}`,
                color: theme.color.nova,
                fontSize: 12, fontWeight: 600,
              }}>
                {pick({ ru: "пересчёт…", en: "recomputing…" })}
              </div>
            )}
            {!data && !loading && (
              <div style={{ position: "absolute", color: theme.color.inkDim, textAlign: "center", pointerEvents: "none" }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>🌌</div>
                <div>{pick({ ru: "Готовлю Вселенную…", en: "Preparing the Universe…" })}</div>
              </div>
            )}
          </div>

          {/* Live structure strength meter — makes slider response unmissable */}
          {data && (
            <div style={{ marginTop: 12, padding: "10px 12px", borderRadius: theme.radius.md, background: "rgba(255, 122, 198, 0.06)", border: `1px solid ${theme.color.line}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: theme.color.inkSoft, marginBottom: 6 }}>
                <span>{pick({ ru: "Сила структуры (σ δρ/ρ)", en: "Structure strength (σ δρ/ρ)" })}</span>
                <span style={{ color: theme.color.nova, fontFamily: theme.font.mono, fontWeight: 600 }}>{strength.toFixed(3)}</span>
              </div>
              <div style={{ position: "relative", height: 8, borderRadius: 999, background: "rgba(255, 255, 255, 0.06)", overflow: "hidden" }}>
                <div style={{
                  position: "absolute", left: 0, top: 0, bottom: 0,
                  width: `${Math.min(100, strength * 40)}%`,
                  background: "linear-gradient(90deg, #5ee2ff, #9b8cff, #ff7ac6, #ffd56b)",
                  transition: "width 0.25s cubic-bezier(.2,.8,.2,1)",
                }} />
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: theme.color.inkDim, marginTop: 4 }}>
                <span>{pick({ ru: "серая каша", en: "grey mush" })}</span>
                <span>{pick({ ru: "космическая паутина", en: "cosmic web" })}</span>
              </div>
            </div>
          )}

          {data && (
            <>
              <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
                <Button variant="soft" size="sm" onClick={() => { setFrame(0); setPlaying(true); }}>▶ {pick({ ru: "Воспроизвести", en: "Play" })}</Button>
                <Button variant="soft" size="sm" onClick={() => setPlaying(false)}>⏸ {pick({ ru: "Пауза", en: "Pause" })}</Button>
                <Button variant="ghost" size="sm" onClick={() => setFrame(0)}>↺ {pick({ ru: "В начало", en: "Restart" })}</Button>
              </div>
              <input
                type="range" min={0} max={data.snapshots.length - 1} value={frame}
                onChange={(e) => { setPlaying(false); setFrame(parseInt(e.target.value)); }}
                style={{ width: "100%", marginTop: 10, accentColor: theme.color.nova }}
              />
              <div style={{ display: "flex", justifyContent: "space-between", color: theme.color.inkSoft, fontSize: 12, fontFamily: theme.font.mono }}>
                <span>{pick({ ru: "Кадр", en: "Frame" })} {frame + 1}/{data.snapshots.length}</span>
                <span>z = {data.redshifts[frame]?.toFixed(2)}</span>
                <span>a = {data.scale_factors[frame]?.toFixed(3)}</span>
              </div>
              <Callout variant={verdict.tone === "aurora" ? "tip" : "warning"} title={pick({ ru: "Вердикт", en: "Verdict" })}>
                {verdict.label}
              </Callout>
            </>
          )}
        </Card>

        <Card padding={20} tone="plasma">
          <Badge tone="plasma" glyph="✦">{pick({ ru: "Что происходит", en: "What's happening" })}</Badge>
          <p style={{ color: theme.color.ink, fontFamily: theme.font.serif, fontSize: 16, lineHeight: 1.65, marginTop: 8 }}>
            {pick({
              ru: <>На входе — крошечные первичные флуктуации (≈10⁻⁵), след инфляции. Каждый кадр гравитация чуть-чуть «сгущает» более плотные места. Тёмная материя — главный архитектор: чем её больше, тем выразительнее паутина.</>,
              en: <>The input: tiny primordial fluctuations (≈10⁻⁵), the imprint of inflation. Each frame, gravity slightly amplifies the denser spots. Dark matter is the architect — the more of it, the sharper the web.</>,
            })}
          </p>
        </Card>

        <Callout variant="wow">
          {pick({
            ru: <>Поставь Ω_cdm h² на минимум — увидишь скучную «серую кашу». Поставь на максимум — паутина становится плотной, как мраморный узор. И помни: при слишком плотной тёмной материи звёздам было бы негде сформироваться.</>,
            en: <>Push Ω_cdm h² to the minimum — you get a boring "grey mush". Push it to the maximum — the web becomes dense like marble. Remember: with too much dark matter, stars couldn't form.</>,
          })}
        </Callout>
      </div>
    </div>
  );
}
