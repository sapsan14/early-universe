import React, { useMemo } from "react";
import { theme } from "../../theme";

/**
 * Tiny SVG line-plot with a moving cursor. Built for the Time Machine —
 * each physical quantity (T, H, a, z, etc.) gets one of these strips.
 * Input `xs` is the common x-axis (e.g. log₁₀(t/s)), `ys` the series.
 *
 * `cursor` (in xs-space) draws a vertical line at the currently-selected
 * time so that several stacked strips stay visually synchronised.
 *
 * If `logY` is true, the y-axis is log10-compressed (and negative / zero
 * values are clamped). We also show the current value on the right.
 */
export function MiniChart({
  xs,
  ys,
  cursor,
  title,
  value,
  unit,
  color,
  logY = false,
  height = 56,
}: {
  xs: number[];
  ys: number[];
  cursor: number;
  title: string;
  value: string;
  unit?: string;
  color: string;
  logY?: boolean;
  height?: number;
}) {
  const { path, yMin, yMax } = useMemo(() => {
    if (!xs.length) return { path: "", yMin: 0, yMax: 1 };
    const transform = (v: number) => logY ? Math.log10(Math.max(v, 1e-30)) : v;
    const tys = ys.map(transform);
    const yMin = Math.min(...tys);
    const yMax = Math.max(...tys);
    const xMin = xs[0];
    const xMax = xs[xs.length - 1];
    const W = 100, H = 100;
    const yRange = Math.max(yMax - yMin, 1e-6);
    const xRange = Math.max(xMax - xMin, 1e-6);
    const pathParts: string[] = [];
    for (let i = 0; i < xs.length; i++) {
      const x = ((xs[i] - xMin) / xRange) * W;
      const y = H - ((tys[i] - yMin) / yRange) * H;
      pathParts.push(`${i === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`);
    }
    return { path: pathParts.join(" "), yMin, yMax };
  }, [xs, ys, logY]);

  const xMin = xs[0];
  const xMax = xs[xs.length - 1];
  const cursorPct = ((cursor - xMin) / Math.max(xMax - xMin, 1e-6)) * 100;

  return (
    <div style={{
      padding: "8px 12px",
      borderRadius: theme.radius.sm,
      background: "rgba(155, 140, 255, 0.05)",
      border: `1px solid ${theme.color.line}`,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 4 }}>
        <span style={{ fontSize: 12, color: theme.color.inkSoft, fontWeight: 600 }}>{title}</span>
        <span style={{ fontFamily: theme.font.mono, fontSize: 13, color, fontWeight: 700 }}>
          {value}{unit ? <span style={{ color: theme.color.inkDim, fontWeight: 400, marginLeft: 4 }}>{unit}</span> : null}
        </span>
      </div>
      <div style={{ position: "relative", height }}>
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          style={{ width: "100%", height: "100%", display: "block" }}
        >
          {/* axes guideline */}
          <line x1="0" y1="50" x2="100" y2="50"
            stroke="rgba(159,144,240,0.10)" strokeWidth="0.4" strokeDasharray="1,1" />
          {/* curve */}
          <path d={path}
            fill="none"
            stroke={color}
            strokeWidth="1.2"
            strokeLinecap="round"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
            style={{ filter: `drop-shadow(0 0 4px ${color}aa)` }}
          />
          {/* cursor vertical line */}
          <line
            x1={cursorPct} y1="0" x2={cursorPct} y2="100"
            stroke={color} strokeWidth="0.8" strokeDasharray="1.5,1.5"
            opacity="0.85"
          />
        </svg>
        {/* min / max hints */}
        <div style={{
          position: "absolute", top: 2, left: 4,
          fontSize: 9, color: theme.color.inkDim, fontFamily: theme.font.mono,
          pointerEvents: "none",
        }}>{logY ? `10^${yMax.toFixed(1)}` : yMax.toFixed(2)}</div>
        <div style={{
          position: "absolute", bottom: 2, left: 4,
          fontSize: 9, color: theme.color.inkDim, fontFamily: theme.font.mono,
          pointerEvents: "none",
        }}>{logY ? `10^${yMin.toFixed(1)}` : yMin.toFixed(2)}</div>
      </div>
    </div>
  );
}
