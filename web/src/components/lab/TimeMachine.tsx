import React, { useState, useEffect, useRef, useMemo } from "react";
import { theme } from "../../theme";
import { useT, p } from "../../i18n";
import { post, DEFAULT_PARAMS, type TimelineResponse } from "../../api/client";
import { EPOCH_DEFS, buildLocalEpoch, findEpoch } from "../../physics";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Callout } from "../ui/Callout";
import { Term } from "../ui/Term";
import { MathBlock } from "../ui/Math";

const MIN_LT = -43;
const MAX_LT = 17.64;

function fmt(n: number): string {
  if (!Number.isFinite(n)) return "—";
  if (n === 0) return "0";
  if (Math.abs(n) < 0.01 || Math.abs(n) > 1e6) {
    const e = n.toExponential(2);
    return e.replace(/e([+-]?\d+)/, "·10^{$1}");
  }
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function formatTimeAgo(t_seconds: number, lang: "ru" | "en"): string {
  const yr = 3.156e7;
  if (t_seconds < 1) {
    const e = Math.log10(t_seconds);
    return lang === "ru" ? `≈ 10^${e.toFixed(0)} с после Большого Взрыва` : `≈ 10^${e.toFixed(0)} s after the Big Bang`;
  }
  if (t_seconds < 60) return lang === "ru" ? `${t_seconds.toFixed(1)} сек после Большого Взрыва` : `${t_seconds.toFixed(1)} sec after the Big Bang`;
  if (t_seconds < 3600) return lang === "ru" ? `${(t_seconds / 60).toFixed(1)} минут после ББ` : `${(t_seconds / 60).toFixed(1)} min after the BB`;
  if (t_seconds < yr) return lang === "ru" ? `${(t_seconds / 86400).toFixed(0)} дней после ББ` : `${(t_seconds / 86400).toFixed(0)} days after the BB`;
  const years = t_seconds / yr;
  if (years < 1e6) return lang === "ru" ? `${(years / 1e3).toFixed(1)} тыс. лет после ББ` : `${(years / 1e3).toFixed(1)} kyr after the BB`;
  if (years < 1e9) return lang === "ru" ? `${(years / 1e6).toFixed(1)} млн лет после ББ` : `${(years / 1e6).toFixed(1)} Myr after the BB`;
  return lang === "ru" ? `${(years / 1e9).toFixed(2)} млрд лет после ББ` : `${(years / 1e9).toFixed(2)} Gyr after the BB`;
}

export function TimeMachine() {
  const { t, lang, pick } = useT();
  const [logT, setLogT] = useState(17.14);
  const [data, setData] = useState<TimelineResponse | null>(null);
  const [usingApi, setUsingApi] = useState(false);
  const [playing, setPlaying] = useState(false);
  const rafRef = useRef<number | null>(null);

  const localEpochDef = useMemo(() => findEpoch(logT), [logT]);
  const epoch = data?.epoch ?? buildLocalEpoch(logT, DEFAULT_PARAMS, lang);

  // Fetch from API with debounce, fall back to local on error
  useEffect(() => {
    const timer = setTimeout(() => {
      post<TimelineResponse>("/api/v1/simulations/timeline", {
        log_time_seconds: logT,
        params: DEFAULT_PARAMS,
      })
        .then((r) => { setData(r); setUsingApi(true); })
        .catch(() => { setData(null); setUsingApi(false); });
    }, 120);
    return () => clearTimeout(timer);
  }, [logT]);

  // Auto-play sweep
  useEffect(() => {
    if (!playing) return;
    let last = performance.now();
    const tick = (now: number) => {
      const dt = (now - last) / 1000;
      last = now;
      setLogT((lt) => {
        const next = lt + dt * 4;
        if (next >= MAX_LT) { setPlaying(false); return MAX_LT; }
        return next;
      });
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [playing]);

  const t01 = (logT - MIN_LT) / (MAX_LT - MIN_LT);

  return (
    <div style={{ display: "grid", gap: 24, gridTemplateColumns: "minmax(0, 1fr) 360px" }} className="lab-grid">
      <div>
        <Card padding={28} tone="starlight" glow>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 12 }}>
            <Badge tone="starlight" glyph="⏳">{pick({ ru: "Машина времени", en: "Time Machine" })}</Badge>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                onClick={() => setPlaying((x) => !x)}
                style={{
                  padding: "6px 14px",
                  borderRadius: 999,
                  border: `1px solid ${theme.color.starlight}`,
                  background: playing ? theme.color.starlight : "transparent",
                  color: playing ? "#1c1530" : theme.color.starlight,
                  cursor: "pointer", fontWeight: 600, fontSize: 13,
                }}
              >{playing ? pick({ ru: "⏸ Пауза", en: "⏸ Pause" }) : pick({ ru: "▶ Авто-показ", en: "▶ Auto-tour" })}</button>
              <button
                onClick={() => setLogT(17.14)}
                style={{
                  padding: "6px 14px",
                  borderRadius: 999,
                  border: `1px solid ${theme.color.line}`,
                  background: "transparent",
                  color: theme.color.inkSoft,
                  cursor: "pointer", fontSize: 13,
                }}
              >{pick({ ru: "К сегодня", en: "Now" })}</button>
            </div>
          </div>

          {/* Time labels */}
          <div style={{ display: "flex", justifyContent: "space-between", color: theme.color.inkDim, fontSize: 12, fontFamily: theme.font.mono }}>
            <span>10⁻⁴³ с</span>
            <span>10⁰ с</span>
            <span>10⁹ с</span>
            <span>13.8 Gyr</span>
          </div>

          {/* Custom timeline visualization */}
          <div style={{ position: "relative", padding: "20px 0 60px" }}>
            <div aria-hidden style={{
              position: "absolute", left: 0, right: 0, top: 26,
              height: 12, borderRadius: 999,
              background:
                "linear-gradient(90deg, #9b8cff 0%, #ff7ac6 8%, #ff8b5e 18%, #ffd56b 35%, #7afcb1 60%, #5ee2ff 75%, #ff7ac6 100%)",
              opacity: 0.85,
              boxShadow: "0 0 20px rgba(255,138,94,0.45)",
            }} />
            <input
              type="range"
              min={MIN_LT} max={MAX_LT} step={0.05}
              value={logT}
              onChange={(e) => setLogT(parseFloat(e.target.value))}
              style={{
                position: "relative", width: "100%",
                accentColor: theme.color.starlight,
                marginTop: 14,
              }}
            />
            <div aria-hidden style={{
              position: "absolute",
              left: `calc(${t01 * 100}% - 24px)`,
              top: -6,
              width: 48, height: 48, borderRadius: "50%",
              background: `radial-gradient(circle, ${localEpochDef.color}, ${localEpochDef.color}33 70%, transparent)`,
              filter: "blur(2px)",
              pointerEvents: "none",
            }} />
            <div aria-hidden style={{
              position: "absolute",
              left: `calc(${t01 * 100}% - 14px)`,
              top: 12,
              fontSize: 28,
              color: localEpochDef.color,
              textShadow: `0 0 12px ${localEpochDef.color}`,
              pointerEvents: "none",
            }}>{localEpochDef.glyph}</div>

            {/* Epoch markers */}
            <div style={{
              position: "absolute", left: 0, right: 0, top: 50,
              display: "flex", justifyContent: "space-between",
              fontSize: 11,
            }}>
              {EPOCH_DEFS.map((e) => {
                const center = (e.log_t_min + e.log_t_max) / 2;
                const pos = (center - MIN_LT) / (MAX_LT - MIN_LT);
                return (
                  <button
                    key={e.id}
                    onClick={() => setLogT(center)}
                    style={{
                      position: "absolute",
                      left: `${pos * 100}%`,
                      transform: "translateX(-50%)",
                      background: "transparent",
                      border: "none",
                      color: e.id === localEpochDef.id ? e.color : theme.color.inkSoft,
                      cursor: "pointer",
                      whiteSpace: "nowrap",
                      fontSize: 10.5,
                      fontWeight: e.id === localEpochDef.id ? 700 : 400,
                      padding: 0,
                    }}
                  >
                    {t(e.name).split(" ").slice(0, 2).join(" ")}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Numbers */}
          <div style={{
            display: "grid", gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
            marginTop: 28,
          }}>
            {[
              { label: pick({ ru: "Время после ББ", en: "Time after BB" }), value: formatTimeAgo(epoch.time_seconds, lang), term: "big-bang" },
              { label: pick({ ru: "Красное смещение z", en: "Redshift z" }), value: fmt(epoch.redshift), term: "redshift" },
              { label: pick({ ru: "Температура T", en: "Temperature T" }), value: `${fmt(epoch.temperature_K)} K`, term: undefined },
              { label: pick({ ru: "Масштабный фактор a", en: "Scale factor a" }), value: fmt(epoch.scale_factor), term: "scale-factor" },
              { label: pick({ ru: "H — Хаббл", en: "H — Hubble" }), value: `${fmt(epoch.hubble_parameter)} km/s/Mpc`, term: "hubble" },
              { label: pick({ ru: "Доминирует", en: "Dominant" }), value: epoch.dominant_component, term: undefined },
            ].map((row, i) => (
              <div key={i} style={{
                padding: 14, borderRadius: theme.radius.md,
                background: "rgba(155, 140, 255, 0.05)",
                border: `1px solid ${theme.color.line}`,
              }}>
                <div style={{ color: theme.color.inkSoft, fontSize: 12, marginBottom: 6 }}>
                  {row.term ? <Term id={row.term}>{row.label}</Term> : row.label}
                </div>
                <div style={{ fontFamily: theme.font.mono, color: theme.color.starlight, fontSize: 17, fontWeight: 600 }}>
                  {row.value}
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Big epoch description */}
        <Card padding={28} tone="aurora" style={{ marginTop: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 12 }}>
            <div style={{
              width: 48, height: 48, borderRadius: 14,
              background: `linear-gradient(135deg, ${localEpochDef.color}, ${localEpochDef.color}66)`,
              display: "grid", placeItems: "center", fontSize: 24,
              boxShadow: `0 6px 18px ${localEpochDef.color}55`,
            }}>{localEpochDef.glyph}</div>
            <div>
              <Badge tone="muted">{pick({ ru: "Эпоха", en: "Epoch" })}</Badge>
              <h3 style={{ fontFamily: theme.font.serif, fontSize: 26, color: theme.color.ink, marginTop: 4 }}>
                {t(localEpochDef.name)}
              </h3>
            </div>
          </div>
          <p style={{ fontFamily: theme.font.serif, fontSize: 17, color: theme.color.ink, lineHeight: 1.65 }}>
            {t(localEpochDef.description)}
          </p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 14 }}>
            {localEpochDef.key_processes.map((kp, i) => (
              <Badge key={i} tone="plasma">{t(kp)}</Badge>
            ))}
          </div>
        </Card>
      </div>

      {/* Side panel: math + tip */}
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <Card padding={20} tone="plasma">
          <Badge tone="plasma" glyph="∑">{pick({ ru: "За кадром", en: "Behind the scenes" })}</Badge>
          <h4 style={{ fontFamily: theme.font.serif, marginTop: 8, color: theme.color.ink }}>
            {pick({ ru: "Откуда числа?", en: "Where do the numbers come from?" })}
          </h4>
          <p style={{ color: theme.color.inkSoft, fontSize: 13.5, lineHeight: 1.55, marginTop: 6 }}>
            {pick({
              ru: <>Сначала по log(t) находим эпоху. Затем считаем масштабный фактор: a ∝ t^{1/2} в эпоху излучения, a ∝ t^{2/3} в эпоху материи. Из a получаем z = 1/a − 1 и T = T_0/a.</>,
              en: <>From log(t) we first locate the epoch. Then the scale factor: a ∝ t^{1/2} in the radiation era, a ∝ t^{2/3} in the matter era. From a we get z = 1/a − 1 and T = T_0/a.</>,
            })}
          </p>
          <MathBlock
            formula="a ∝ t^{1/2} (рад.)  /  a ∝ t^{2/3} (матер.)"
            caption={p("Решение уравнения Фридмана для двух режимов.", "Friedmann equation solved in two regimes.")}
          />
        </Card>
        <Callout variant="tip">
          {pick({
            ru: <>Включи «Авто-показ» — слайдер сам прогуляется по 13.8 миллиардам лет за несколько секунд. Каждый цвет на полосе — отдельная эпоха.</>,
            en: <>Hit "Auto-tour" — the slider strolls through 13.8 Gyr in a few seconds. Each colour band is a different epoch.</>,
          })}
        </Callout>
        <Callout variant={usingApi ? "tip" : "warning"} title={usingApi ? p("API подключён", "API connected") : p("Офлайн-режим", "Offline mode")}>
          {usingApi
            ? pick({ ru: "Числа считает Python-API.", en: "Numbers come straight from the Python API." })
            : pick({ ru: "Расчёты идут на встроенных приближениях. Это нормально — числа реалистичны.", en: "Numbers are computed locally with accurate approximations. Perfectly fine to learn." })
          }
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
