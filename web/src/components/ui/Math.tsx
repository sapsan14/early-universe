import React, { useRef, useState } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";
import { theme } from "../../theme";
import { useT } from "../../i18n";
import type { Phrase } from "../../i18n";
import { historyFor } from "../../math-history";
import { FloatingCard } from "./FloatingCard";

/**
 * Safely render a LaTeX source string to HTML.
 *
 * If KaTeX can't parse the string (unknown command, typo), we fall back to
 * raw text so the page never crashes.
 */
function renderTex(tex: string, displayMode = true): string {
  try {
    return katex.renderToString(tex, {
      displayMode,
      throwOnError: false,
      output: "html",
      strict: false,
      trust: false,
    });
  } catch {
    return `<span style="font-family: monospace">${tex}</span>`;
  }
}

export function Tex({ children, display = false }: { children: string; display?: boolean }) {
  const html = renderTex(children, display);
  return <span dangerouslySetInnerHTML={{ __html: html }} />;
}

/**
 * Schoolbook-style math display with KaTeX rendering, a bilingual symbol
 * legend, optional derivation steps, and (if a `historyId` is supplied) a
 * round "ⓘ" button that opens a popover with the formula's author, year
 * and backstory.
 */
export function MathBlock({
  formula,
  title,
  caption,
  legend,
  steps,
  highlight,
  historyId,
}: {
  /** Pure LaTeX source, e.g. "a(t) = a_0 \\, e^{H_{\\rm inf} t}" */
  formula: string;
  title?: Phrase;
  caption?: Phrase;
  legend?: { sym: string; meaning: Phrase }[];
  steps?: { eq: string; note: Phrase }[];
  highlight?: "plasma" | "starlight" | "aurora";
  historyId?: string;
}) {
  const { t, pick } = useT();
  const accent = highlight === "starlight"
    ? theme.color.starlight
    : highlight === "aurora"
      ? theme.color.aurora
      : theme.color.plasma;
  const history = historyId ? historyFor(historyId) : undefined;

  const infoRef = useRef<HTMLButtonElement>(null);
  const [infoOpen, setInfoOpen] = useState(false);

  return (
    <figure style={{
      margin: "20px 0",
      padding: 22,
      borderRadius: theme.radius.md,
      border: `1px solid ${theme.color.lineStrong}`,
      background:
        "linear-gradient(180deg, rgba(94, 226, 255, 0.06), rgba(155, 140, 255, 0.04))",
      position: "relative",
      overflow: "visible",
    }}>
      <div aria-hidden style={{
        position: "absolute",
        inset: 0,
        borderRadius: "inherit",
        background:
          `radial-gradient(260px 140px at 12% 0%, ${accent}26, transparent 60%)`,
        pointerEvents: "none",
      }} />
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        position: "relative", gap: 10, marginBottom: title ? 8 : 0,
      }}>
        {title && (
          <figcaption style={{
            fontFamily: theme.font.serif,
            color: accent,
            fontSize: 14, fontWeight: 600,
            letterSpacing: 0.5,
            textTransform: "uppercase",
          }}>
            {t(title)}
          </figcaption>
        )}
        {history && (
          <button
            ref={infoRef}
            onClick={(e) => { e.stopPropagation(); setInfoOpen((x) => !x); }}
            aria-label={pick({ ru: "История формулы", en: "Formula history" })}
            title={pick({ ru: "История формулы", en: "Formula history" })}
            style={{
              width: 28, height: 28, borderRadius: "50%",
              border: `1px solid ${accent}66`,
              background: `${accent}18`,
              color: accent, cursor: "pointer",
              fontFamily: theme.font.serif,
              fontSize: 15, fontWeight: 700,
              display: "grid", placeItems: "center",
              transition: theme.motion.snap,
            }}
          >ⓘ</button>
        )}
      </div>

      <div style={{
        fontSize: 22,
        color: theme.color.ink,
        textAlign: "center",
        padding: "10px 0 6px",
        position: "relative",
        overflowX: "auto",
        overflowY: "hidden",
      }}>
        <Tex display>{formula}</Tex>
      </div>

      {caption && (
        <div style={{
          textAlign: "center",
          fontFamily: theme.font.serif,
          fontStyle: "italic",
          color: theme.color.inkSoft,
          fontSize: 14,
          marginTop: 4,
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
          gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
          gap: 10,
          position: "relative",
        }}>
          {legend.map((row) => (
            <div key={row.sym} style={{ display: "flex", gap: 10, alignItems: "baseline" }}>
              <span style={{
                minWidth: 36,
                textAlign: "right",
                color: accent,
              }}>
                <Tex>{row.sym}</Tex>
              </span>
              <span style={{ color: theme.color.inkSoft, fontSize: 13, lineHeight: 1.5 }}>
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
              gap: 12,
              alignItems: "center",
              padding: "10px 0",
              borderTop: i ? `1px dashed ${theme.color.line}` : undefined,
            }}>
              <span style={{
                width: 26, height: 26, borderRadius: 999,
                background: accent + "33", color: accent,
                display: "grid", placeItems: "center",
                fontWeight: 700, fontSize: 13,
              }}>{i + 1}</span>
              <div>
                <div style={{ fontSize: 16, color: theme.color.ink }}>
                  <Tex>{s.eq}</Tex>
                </div>
                <div style={{ color: theme.color.inkSoft, fontSize: 12.5, marginTop: 3 }}>{t(s.note)}</div>
              </div>
            </li>
          ))}
        </ol>
      )}

      {history && (
        <FloatingCard
          anchor={infoRef.current}
          open={infoOpen}
          onRequestClose={() => setInfoOpen(false)}
          width={380}
        >
          <div style={{
            display: "flex", justifyContent: "space-between",
            alignItems: "baseline", gap: 8, marginBottom: 6,
          }}>
            <strong style={{
              fontFamily: theme.font.serif, fontSize: 16,
              color: theme.color.starlight,
            }}>
              {t(history.title)}
            </strong>
            <span style={{ fontFamily: theme.font.mono, color: theme.color.plasma, fontSize: 12 }}>
              {history.year}
            </span>
          </div>
          <div style={{ color: theme.color.ink, marginBottom: 10 }}>
            {t(history.author)}
            {history.origin && (
              <div style={{ color: theme.color.inkSoft, fontSize: 12, marginTop: 2 }}>
                {t(history.origin)}
              </div>
            )}
          </div>
          <div style={{ color: theme.color.inkSoft, fontFamily: theme.font.serif, fontSize: 14, lineHeight: 1.55 }}>
            {t(history.story)}
          </div>
          {history.fun && (
            <div style={{
              marginTop: 10, padding: "8px 10px",
              borderRadius: 8,
              background: "rgba(255, 213, 107, 0.10)",
              border: "1px solid rgba(255, 213, 107, 0.30)",
              color: theme.color.starlight, fontSize: 13, lineHeight: 1.5,
              fontStyle: "italic",
            }}>
              ✦ {t(history.fun)}
            </div>
          )}
        </FloatingCard>
      )}
    </figure>
  );
}

export function MathInline({ children }: { children: string }) {
  return (
    <span style={{ padding: "0 2px", color: theme.color.plasma }}>
      <Tex>{children}</Tex>
    </span>
  );
}
