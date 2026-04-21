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
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const simulate = useCallback(async () => {
    setLoading(true);
    try {
      const r = await post<PlayableResponse>("/api/v1/simulations/playable", {
        params, grid_size: 96, n_steps: 12, seed: 42,
      });
      setData(r); setUsingApi(true);
    } catch {
      setData(localPlayable(params, 96, 12)); setUsingApi(false);
    }
    setFrame(0);
    setLoading(false);
  }, [params]);

  // initial run
  useEffect(() => {
    if (!data) simulate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
  useEffect(() => {
    if (!data || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const snap = data.snapshots[frame];
    const N = snap.length;
    canvas.width = N; canvas.height = N;
    const flat = snap.flat();
    let min = Infinity, max = -Infinity;
    for (const v of flat) { if (v < min) min = v; if (v > max) max = v; }
    const range = max - min || 1;
    const img = ctx.createImageData(N, N);
    for (let y = 0; y < N; y++) {
      for (let x = 0; x < N; x++) {
        const v = (snap[y][x] - min) / range;
        const i = (y * N + x) * 4;
        // Cosmic ramp: indigo → magenta → gold
        if (v < 0.4) {
          const u = v / 0.4;
          img.data[i] = 10 + 80 * u;
          img.data[i + 1] = 14 + 30 * u;
          img.data[i + 2] = 60 + 130 * u;
        } else if (v < 0.75) {
          const u = (v - 0.4) / 0.35;
          img.data[i] = 90 + 165 * u;
          img.data[i + 1] = 44 + 60 * u;
          img.data[i + 2] = 190 - 100 * u;
        } else {
          const u = (v - 0.75) / 0.25;
          img.data[i] = 255;
          img.data[i + 1] = 104 + 130 * u;
          img.data[i + 2] = 90 + 80 * u;
        }
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
              ru: <>Поставь параметры — нажми «Создать Вселенную». На экране запустится симуляция роста структур. Внизу — слайдер времени.</>,
              en: <>Set parameters and hit "Create Universe". A structure-growth simulation runs in the panel. The slider below scrubs time.</>,
            })}
          </p>
        </Card>

        <ParamSlider
          label={p("Хаббл H₀", "Hubble H₀")}
          symbol="H₀" unit="km/s/Mpc"
          value={params.H0} min={50} max={100} step={1}
          onChange={(v) => setParams((p) => ({ ...p, H0: v }))}
          accent="starlight"
          termId="hubble"
        />
        <ParamSlider
          label={p("Тёмная материя Ω_cdm h²", "Dark matter Ω_cdm h²")}
          symbol="Ω_cdm h²"
          value={params.Omega_cdm_h2} min={0.005} max={0.40} step={0.005}
          onChange={(v) => setParams((p) => ({ ...p, Omega_cdm_h2: v }))}
          accent="nova"
          termId="dark-matter"
        />
        <ParamSlider
          label={p("Громкость A_s", "Loudness A_s")}
          symbol="ln(10¹⁰ A_s)"
          value={params.ln10As} min={1.5} max={4.5} step={0.05}
          onChange={(v) => setParams((p) => ({ ...p, ln10As: v }))}
          accent="ember"
          termId="a-s"
        />
        <ParamSlider
          label={p("Наклон n_s", "Tilt n_s")}
          symbol="n_s"
          value={params.n_s} min={0.7} max={1.3} step={0.01}
          onChange={(v) => setParams((p) => ({ ...p, n_s: v }))}
          accent="plasma"
          termId="n-s"
        />

        <Button variant="primary" full onClick={simulate} disabled={loading}>
          {loading ? pick({ ru: "Создаю Вселенную…", en: "Creating Universe…" }) : pick({ ru: "✺ Создать Вселенную", en: "✺ Create Universe" })}
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
          }}>
            {data ? (
              <canvas
                ref={canvasRef}
                style={{
                  width: "100%", maxWidth: 480, aspectRatio: "1/1",
                  imageRendering: "pixelated",
                  borderRadius: 8,
                  boxShadow: "0 0 40px rgba(255, 122, 198, 0.35)",
                }}
              />
            ) : (
              <div style={{ color: theme.color.inkDim, textAlign: "center" }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>🌌</div>
                <div>{pick({ ru: "Нажми «Создать Вселенную»", en: "Press 'Create Universe'" })}</div>
              </div>
            )}
          </div>

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
