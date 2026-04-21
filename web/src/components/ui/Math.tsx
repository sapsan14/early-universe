import React from "react";
import { theme } from "../../theme";
import { useT } from "../../i18n";
import type { Phrase } from "../../i18n";

/**
 * Schoolbook-style math display.
 *
 * The `formula` is rendered with the math font; an optional `legend` lists
 * each symbol with a bilingual description so a student can decode every
 * letter without leaving the page. Use `inline` for in-paragraph snippets.
 */
export function MathBlock({
  formula,
  title,
  caption,
  legend,
  steps,
  highlight,
}: {
  formula: string;
  title?: Phrase;
  caption?: Phrase;
  legend?: { sym: string; meaning: Phrase }[];
  steps?: { eq: string; note: Phrase }[];
  highlight?: "plasma" | "starlight" | "aurora";
}) {
  const { t } = useT();
  const accent = highlight === "starlight"
    ? theme.color.starlight
    : highlight === "aurora"
      ? theme.color.aurora
      : theme.color.plasma;

  return (
    <figure style={{
      margin: "20px 0",
      padding: 18,
      borderRadius: theme.radius.md,
      border: `1px solid ${theme.color.lineStrong}`,
      background:
        "linear-gradient(180deg, rgba(94, 226, 255, 0.06), rgba(155, 140, 255, 0.04))",
      position: "relative",
      overflow: "hidden",
    }}>
      <div aria-hidden style={{
        position: "absolute",
        inset: 0,
        background:
          `radial-gradient(220px 120px at 12% 0%, ${accent}22, transparent 60%)`,
        pointerEvents: "none",
      }} />
      {title && (
        <figcaption style={{
          fontFamily: theme.font.serif,
          color: accent,
          fontSize: 14,
          fontWeight: 600,
          letterSpacing: 0.5,
          marginBottom: 10,
          textTransform: "uppercase",
          position: "relative",
        }}>
          {t(title)}
        </figcaption>
      )}
      <div style={{
        fontFamily: theme.font.math,
        fontSize: 26,
        color: theme.color.ink,
        textAlign: "center",
        padding: "10px 0",
        position: "relative",
      }}>
        {formula}
      </div>
      {caption && (
        <div style={{
          textAlign: "center",
          fontFamily: theme.font.serif,
          fontStyle: "italic",
          color: theme.color.inkSoft,
          fontSize: 14,
          marginTop: 6,
          position: "relative",
        }}>
          {t(caption)}
        </div>
      )}
      {legend && legend.length > 0 && (
        <div style={{
          marginTop: 14,
          paddingTop: 12,
          borderTop: `1px dashed ${theme.color.line}`,
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: 8,
          position: "relative",
        }}>
          {legend.map((row) => (
            <div key={row.sym} style={{ display: "flex", gap: 10, alignItems: "baseline" }}>
              <span style={{
                fontFamily: theme.font.math,
                color: accent,
                fontSize: 16,
                minWidth: 28,
                textAlign: "right",
              }}>{row.sym}</span>
              <span style={{ color: theme.color.inkSoft, fontSize: 13, lineHeight: 1.4 }}>
                {t(row.meaning)}
              </span>
            </div>
          ))}
        </div>
      )}
      {steps && steps.length > 0 && (
        <ol style={{
          marginTop: 14,
          paddingLeft: 0,
          listStyle: "none",
          position: "relative",
        }}>
          {steps.map((s, i) => (
            <li key={i} style={{
              display: "grid",
              gridTemplateColumns: "32px 1fr",
              gap: 10,
              alignItems: "center",
              padding: "8px 0",
              borderTop: i ? `1px dashed ${theme.color.line}` : undefined,
            }}>
              <span style={{
                width: 26,
                height: 26,
                borderRadius: 999,
                background: accent + "33",
                color: accent,
                display: "grid",
                placeItems: "center",
                fontWeight: 700,
                fontSize: 13,
              }}>{i + 1}</span>
              <div>
                <div style={{ fontFamily: theme.font.math, fontSize: 16, color: theme.color.ink }}>{s.eq}</div>
                <div style={{ color: theme.color.inkSoft, fontSize: 12, marginTop: 2 }}>{t(s.note)}</div>
              </div>
            </li>
          ))}
        </ol>
      )}
    </figure>
  );
}

export function MathInline({ children }: { children: React.ReactNode }) {
  return (
    <span style={{
      fontFamily: theme.font.math,
      color: theme.color.plasma,
      padding: "0 2px",
    }}>{children}</span>
  );
}
