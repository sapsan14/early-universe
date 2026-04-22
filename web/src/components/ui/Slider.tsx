import React, { useCallback, useRef, useState } from "react";
import { theme } from "../../theme";
import { useT } from "../../i18n";
import type { Phrase } from "../../i18n";
import { Term } from "./Term";
import { Tex } from "./Math";

/**
 * A schoolbook slider with a hand-drawn fill bar, a big accent-coloured glowing
 * thumb, and an active-drag scale-up so the control feels precise and lively.
 * Pointer events drive the value directly — the native `<input type="range">`
 * was lazy on fast drags, this version is snappy.
 *
 * `marks` lets you label notable values (e.g. "Planck 2018") which a student
 * can click to snap.
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
  const t01 = Math.max(0, Math.min(1, (value - min) / (max - min)));

  const trackRef = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState(false);
  const [hover, setHover] = useState(false);

  const quantize = useCallback((v: number) => {
    const clamped = Math.max(min, Math.min(max, v));
    const n = Math.round((clamped - min) / step);
    return Math.max(min, Math.min(max, min + n * step));
  }, [min, max, step]);

  const valueFromEvent = useCallback((clientX: number) => {
    const rect = trackRef.current?.getBoundingClientRect();
    if (!rect) return value;
    const u = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    return quantize(min + u * (max - min));
  }, [min, max, quantize, value]);

  const onPointerDown = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    setDragging(true);
    onChange(valueFromEvent(e.clientX));
  }, [onChange, valueFromEvent]);

  const onPointerMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragging) return;
    onChange(valueFromEvent(e.clientX));
  }, [dragging, onChange, valueFromEvent]);

  const onPointerUp = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    setDragging(false);
    try { (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId); } catch { /* ignore */ }
  }, []);

  const onKeyDown = useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
    let delta = 0;
    if (e.key === "ArrowLeft" || e.key === "ArrowDown") delta = -step;
    else if (e.key === "ArrowRight" || e.key === "ArrowUp") delta = step;
    else if (e.key === "PageDown") delta = -step * 10;
    else if (e.key === "PageUp") delta = step * 10;
    else if (e.key === "Home") { e.preventDefault(); onChange(min); return; }
    else if (e.key === "End") { e.preventDefault(); onChange(max); return; }
    if (delta !== 0) {
      e.preventDefault();
      onChange(quantize(value + delta));
    }
  }, [step, onChange, quantize, value, min, max]);

  const active = dragging || hover;

  return (
    <div style={{
      display: "flex", flexDirection: "column", gap: 8,
      padding: "12px 14px",
      borderRadius: theme.radius.md,
      background: dragging
        ? `linear-gradient(180deg, ${accentColor}14, ${accentColor}08)`
        : "rgba(155, 140, 255, 0.05)",
      border: `1px solid ${dragging ? accentColor + "66" : theme.color.line}`,
      transition: "background 180ms, border-color 180ms",
    }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
          {termId
            ? <Term id={termId}><span style={{ color: theme.color.ink, fontWeight: 600, fontSize: 14 }}>{t(label)}</span></Term>
            : <span style={{ color: theme.color.ink, fontWeight: 600, fontSize: 14 }}>{t(label)}</span>}
          {symbol && (
            <span style={{ color: theme.color.inkSoft, fontSize: 15 }}>
              <Tex>{symbol}</Tex>
            </span>
          )}
          {unit && <span style={{ color: theme.color.inkDim, fontSize: 12 }}>{unit}</span>}
        </div>
        <span style={{
          fontFamily: theme.font.mono,
          fontSize: 15,
          fontWeight: 700,
          color: accentColor,
          padding: "5px 14px",
          borderRadius: 999,
          background: dragging ? accentColor + "33" : accentColor + "1f",
          minWidth: 84,
          textAlign: "center",
          transition: "background 160ms",
          boxShadow: dragging ? `0 0 0 2px ${accentColor}55, 0 6px 16px ${accentColor}33` : "none",
        }}>{display}</span>
      </div>

      {/* Custom pointer-driven track. */}
      <div
        ref={trackRef}
        role="slider"
        tabIndex={0}
        aria-valuemin={min}
        aria-valuemax={max}
        aria-valuenow={value}
        aria-label={t(label)}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onPointerEnter={() => setHover(true)}
        onPointerLeave={() => setHover(false)}
        onKeyDown={onKeyDown}
        style={{
          position: "relative",
          height: 26,
          cursor: dragging ? "grabbing" : "grab",
          touchAction: "none",
          outline: "none",
        }}
      >
        {/* Track */}
        <div style={{
          position: "absolute", left: 0, right: 0, top: "50%",
          transform: "translateY(-50%)",
          height: active ? 8 : 6,
          borderRadius: 999,
          background: "rgba(155, 140, 255, 0.16)",
          transition: "height 140ms",
        }} />
        {/* Fill */}
        <div style={{
          position: "absolute", left: 0, top: "50%",
          transform: "translateY(-50%)",
          height: active ? 8 : 6,
          width: `${t01 * 100}%`,
          borderRadius: 999,
          background: `linear-gradient(90deg, ${accentColor}, #ffffffcc)`,
          boxShadow: `0 0 16px ${accentColor}88`,
          transition: "height 140ms",
        }} />
        {/* Mark ticks on track */}
        {marks?.map((m) => {
          const mx = ((m.value - min) / (max - min)) * 100;
          return (
            <div
              key={`m-${m.value}`}
              aria-hidden
              style={{
                position: "absolute", left: `${mx}%`, top: "50%",
                transform: "translate(-50%, -50%)",
                width: 3, height: 10, borderRadius: 2,
                background: "rgba(255, 255, 255, 0.55)",
                boxShadow: "0 0 4px rgba(255, 255, 255, 0.45)",
                pointerEvents: "none",
              }}
            />
          );
        })}
        {/* Thumb */}
        <div style={{
          position: "absolute",
          left: `${t01 * 100}%`,
          top: "50%",
          transform: `translate(-50%, -50%) scale(${dragging ? 1.25 : (hover ? 1.1 : 1)})`,
          width: 22, height: 22, borderRadius: "50%",
          background: `radial-gradient(circle at 35% 30%, #ffffff 0%, #ffffff 45%, ${accentColor} 100%)`,
          border: `2px solid ${accentColor}`,
          boxShadow: `0 0 0 4px ${accentColor}2b, 0 8px 22px ${accentColor}55`,
          transition: "transform 140ms cubic-bezier(.2,.8,.2,1)",
          pointerEvents: "none",
        }} />
      </div>

      {marks && marks.length > 0 && (
        <div style={{ position: "relative", height: 18, marginTop: -4 }}>
          {marks.map((m) => {
            const mx = ((m.value - min) / (max - min)) * 100;
            return (
              <button
                key={`ml-${m.value}`}
                onClick={() => onChange(m.value)}
                type="button"
                style={{
                  position: "absolute",
                  left: `${mx}%`,
                  transform: "translateX(-50%)",
                  background: "transparent",
                  border: "none",
                  color: theme.color.inkSoft,
                  cursor: "pointer",
                  fontSize: 11,
                  textDecoration: "underline",
                  textDecorationStyle: "dotted",
                  padding: 0,
                  whiteSpace: "nowrap",
                }}
                title={String(m.value)}
              >
                {t(m.label)}
              </button>
            );
          })}
        </div>
      )}
      {caption && (
        <div style={{ color: theme.color.inkSoft, fontSize: 13.5, lineHeight: 1.5, fontStyle: "italic" }}>
          {t(caption)}
        </div>
      )}
    </div>
  );
}
