import React, { useState, useCallback, useEffect } from "react";
import { post, DEFAULT_PARAMS, type TimelineResponse } from "../api/client.ts";

const EPOCH_MARKERS = [
  { log_t: -43, label: "Planck" },
  { log_t: -36, label: "Inflation" },
  { log_t: -10, label: "QCD" },
  { log_t: 2, label: "BBN" },
  { log_t: 12, label: "CMB" },
  { log_t: 15.5, label: "Dawn" },
  { log_t: 17.14, label: "Now" },
];

function formatNumber(n: number): string {
  if (n === 0) return "0";
  if (Math.abs(n) < 0.01 || Math.abs(n) > 1e6) return n.toExponential(2);
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export function TimeTraveler() {
  const [logTime, setLogTime] = useState(17.14);
  const [data, setData] = useState<TimelineResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchTimeline = useCallback(async (lt: number) => {
    setLoading(true);
    try {
      const resp = await post<TimelineResponse>("/api/v1/simulations/timeline", {
        log_time_seconds: lt,
        params: DEFAULT_PARAMS,
      });
      setData(resp);
    } catch {
      /* offline / API not running */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => fetchTimeline(logTime), 200);
    return () => clearTimeout(timer);
  }, [logTime, fetchTimeline]);

  const ep = data?.epoch;

  return (
    <div style={{ maxWidth: 900 }}>
      <h2 style={{ fontSize: 28, marginBottom: 8 }}>Cosmic Time Machine</h2>
      <p style={{ color: "#8b949e", marginBottom: 24 }}>
        Двигайте слайдер, чтобы путешествовать по истории Вселенной
      </p>

      {/* Slider */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#8b949e", marginBottom: 4 }}>
          <span>10⁻⁴³ s</span>
          <span>13.8 Gyr</span>
        </div>
        <input
          type="range"
          min={-43}
          max={17.64}
          step={0.1}
          value={logTime}
          onChange={e => setLogTime(parseFloat(e.target.value))}
          style={{ width: "100%", accentColor: "#1f6feb" }}
        />
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#484f58", marginTop: 4 }}>
          {EPOCH_MARKERS.map(m => (
            <span
              key={m.label}
              onClick={() => setLogTime(m.log_t)}
              style={{ cursor: "pointer", textDecoration: "underline", textDecorationStyle: "dotted" }}
            >
              {m.label}
            </span>
          ))}
        </div>
      </div>

      {/* Current time */}
      <div style={{
        padding: 20,
        borderRadius: 12,
        background: "linear-gradient(135deg, #161b22, #0d1117)",
        border: "1px solid #30363d",
        marginBottom: 16,
      }}>
        <div style={{ fontSize: 13, color: "#8b949e" }}>Время после Большого Взрыва</div>
        <div style={{ fontSize: 32, fontWeight: 700, fontFamily: "monospace" }}>
          10<sup>{logTime.toFixed(1)}</sup> секунд
        </div>
      </div>

      {/* Epoch info */}
      {ep && (
        <div style={{
          padding: 24,
          borderRadius: 12,
          background: "#161b22",
          border: "1px solid #30363d",
        }}>
          <h3 style={{ fontSize: 22, color: "#58a6ff", marginBottom: 12 }}>{ep.name}</h3>
          <p style={{ lineHeight: 1.6, marginBottom: 16 }}>{ep.description}</p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12, marginBottom: 16 }}>
            {[
              ["Красное смещение z", formatNumber(ep.redshift)],
              ["Температура", `${formatNumber(ep.temperature_K)} K`],
              ["Масштабный фактор a", formatNumber(ep.scale_factor)],
              ["Параметр Хаббла H", `${formatNumber(ep.hubble_parameter)} km/s/Mpc`],
              ["Доминирующая компонента", ep.dominant_component],
            ].map(([label, val]) => (
              <div key={label} style={{ padding: 12, borderRadius: 8, background: "#0d1117" }}>
                <div style={{ fontSize: 11, color: "#8b949e" }}>{label}</div>
                <div style={{ fontSize: 16, fontWeight: 600, fontFamily: "monospace" }}>{val}</div>
              </div>
            ))}
          </div>

          <div>
            <div style={{ fontSize: 13, color: "#8b949e", marginBottom: 6 }}>Ключевые процессы</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {ep.key_processes.map(p => (
                <span key={p} style={{
                  padding: "4px 10px", borderRadius: 12, background: "#1f6feb22",
                  color: "#58a6ff", fontSize: 13,
                }}>
                  {p}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {loading && <div style={{ marginTop: 12, color: "#8b949e" }}>Loading...</div>}
    </div>
  );
}
