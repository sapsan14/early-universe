import React from "react";
import { theme } from "../../theme";
import { useT } from "../../i18n";
import type { Phrase } from "../../i18n";
import { Term } from "./Term";

/**
 * A schoolbook slider — labelled with name, symbol and unit, current value
 * shown as a chip, plus a small caption explaining what the slider does.
 *
 * `marks` lets you label notable values (e.g. "Planck 2018") which a
 * student can click to snap.
 */
export function ParamSlider({
  label,
  symbol,
  unit,
  value,
  min,
  max,
  step,
  onChange,
  termId,
  caption,
  marks,
  accent = "starlight",
  precision,
  format,
}: {
  label: Phrase;
  symbol?: string;
  unit?: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
  termId?: string;
  caption?: Phrase;
  marks?: { value: number; label: Phrase }[];
  accent?: "starlight" | "plasma" | "aurora" | "nova" | "ember";
  precision?: number;
  format?: (v: number) => string;
}) {
  const { t } = useT();
  const accentColor =
    accent === "plasma" ? theme.color.plasma :
      accent === "aurora" ? theme.color.aurora :
        accent === "nova" ? theme.color.nova :
          accent === "ember" ? theme.color.ember : theme.color.starlight;
  const display = format
    ? format(value)
    : value.toFixed(precision ?? (step < 0.001 ? 4 : step < 0.01 ? 3 : step < 0.1 ? 2 : 1));
  const t01 = (value - min) / (max - min);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, padding: "10px 12px", borderRadius: theme.radius.md, background: "rgba(155, 140, 255, 0.05)", border: `1px solid ${theme.color.line}` }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
          {termId
            ? <Term id={termId}><span style={{ color: theme.color.ink, fontWeight: 600 }}>{t(label)}</span></Term>
            : <span style={{ color: theme.color.ink, fontWeight: 600 }}>{t(label)}</span>}
          {symbol && <span style={{ fontFamily: theme.font.math, color: theme.color.inkSoft }}>{symbol}</span>}
          {unit && <span style={{ color: theme.color.inkDim, fontSize: 11 }}>{unit}</span>}
        </div>
        <span style={{
          fontFamily: theme.font.mono,
          fontSize: 14,
          color: accentColor,
          padding: "3px 10px",
          borderRadius: 999,
          background: accentColor + "22",
          minWidth: 70,
          textAlign: "center",
        }}>{display}</span>
      </div>
      <div style={{ position: "relative", padding: "10px 0 4px" }}>
        <div aria-hidden style={{
          position: "absolute",
          left: 0, right: 0, top: 17,
          height: 6,
          borderRadius: 999,
          background: "rgba(155, 140, 255, 0.18)",
        }} />
        <div aria-hidden style={{
          position: "absolute",
          left: 0,
          top: 17,
          height: 6,
          width: `${t01 * 100}%`,
          borderRadius: 999,
          background: `linear-gradient(90deg, ${accentColor}, #fff8)`,
          boxShadow: `0 0 12px ${accentColor}66`,
        }} />
        <input
          type="range"
          min={min} max={max} step={step}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          style={{
            position: "relative",
            width: "100%",
            accentColor: accentColor,
            background: "transparent",
          }}
        />
      </div>
      {marks && marks.length > 0 && (
        <div style={{ display: "flex", justifyContent: "space-between", gap: 4, fontSize: 11, color: theme.color.inkDim, marginTop: -4 }}>
          {marks.map((m) => (
            <button
              key={m.value}
              onClick={() => onChange(m.value)}
              type="button"
              style={{
                background: "transparent",
                border: "none",
                color: theme.color.inkSoft,
                cursor: "pointer",
                fontSize: 11,
                textDecoration: "underline",
                textDecorationStyle: "dotted",
                padding: 0,
              }}
              title={String(m.value)}
            >
              {t(m.label)}
            </button>
          ))}
        </div>
      )}
      {caption && (
        <div style={{ color: theme.color.inkSoft, fontSize: 12.5, lineHeight: 1.45, fontStyle: "italic" }}>
          {t(caption)}
        </div>
      )}
    </div>
  );
}
