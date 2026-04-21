import React, { useState, useRef, useEffect } from "react";
import { theme } from "../../theme";
import { useT } from "../../i18n";
import { GLOSSARY, term as lookupTerm } from "../../glossary";

/**
 * <Term id="cmb">CMB</Term> — renders a clickable underlined word.
 *
 * Hovering or focusing pops a small definition card. Click pins the card.
 * If no `children` are passed, the glossary's short label is used.
 */
export function Term({
  id,
  children,
}: {
  id: string;
  children?: React.ReactNode;
}) {
  const { t, pick } = useT();
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);

  const entry = lookupTerm(id);
  if (!entry) return <span style={{ color: theme.color.danger }}>?{id}?</span>;

  useEffect(() => {
    if (!pinned) return;
    const onDoc = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) {
        setPinned(false);
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [pinned]);

  const showCard = open || pinned;

  return (
    <span
      ref={ref}
      style={{ position: "relative", display: "inline-block" }}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => !pinned && setOpen(false)}
    >
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setPinned((p) => !p);
          setOpen(true);
        }}
        style={{
          font: "inherit",
          color: theme.color.starlight,
          background: "transparent",
          border: "none",
          padding: 0,
          margin: 0,
          cursor: "help",
          textDecoration: "underline",
          textDecorationStyle: "dotted",
          textUnderlineOffset: 3,
          textDecorationColor: "rgba(255, 213, 107, 0.55)",
        }}
        aria-describedby={`term-${id}`}
      >
        {children ?? t(entry.short)}
      </button>
      {showCard && (
        <span
          id={`term-${id}`}
          role="tooltip"
          style={{
            position: "absolute",
            top: "calc(100% + 8px)",
            left: 0,
            zIndex: theme.zIndex.tooltip,
            width: 320,
            background: "linear-gradient(180deg, #1a1147 0%, #0f0a2e 100%)",
            border: `1px solid ${theme.color.lineStrong}`,
            borderRadius: theme.radius.md,
            padding: 14,
            boxShadow: theme.shadow.starlit,
            fontFamily: theme.font.sans,
            fontSize: 13,
            lineHeight: 1.5,
            color: theme.color.ink,
            textAlign: "left",
            cursor: "default",
          }}
        >
          <div style={{
            display: "flex",
            alignItems: "baseline",
            justifyContent: "space-between",
            gap: 8,
            marginBottom: 6,
          }}>
            <strong style={{ fontFamily: theme.font.serif, fontSize: 15, color: theme.color.starlight }}>
              {t(entry.short)}
            </strong>
            {entry.symbol && (
              <span style={{
                fontFamily: theme.font.math,
                color: theme.color.plasma,
                fontSize: 14,
              }}>{entry.symbol}{entry.unit ? ` (${entry.unit})` : ""}</span>
            )}
          </div>
          <div style={{ marginBottom: entry.analogy || entry.formula ? 8 : 0 }}>
            {t(entry.definition)}
          </div>
          {entry.formula && (
            <div style={{
              fontFamily: theme.font.math,
              fontSize: 14,
              padding: "6px 10px",
              borderRadius: 6,
              background: "rgba(94, 226, 255, 0.08)",
              border: "1px solid rgba(94, 226, 255, 0.25)",
              color: theme.color.plasma,
              marginBottom: entry.analogy ? 8 : 0,
            }}>{entry.formula}</div>
          )}
          {entry.analogy && (
            <div style={{
              fontStyle: "italic",
              color: theme.color.inkSoft,
              fontSize: 12,
              borderLeft: `2px solid ${theme.color.starlight}`,
              paddingLeft: 8,
            }}>
              {pick({
                ru: "Аналогия: ",
                en: "Analogy: ",
              })}{t(entry.analogy)}
            </div>
          )}
          <div style={{
            marginTop: 8,
            fontSize: 11,
            color: theme.color.inkDim,
            textTransform: "uppercase",
            letterSpacing: 1,
          }}>
            {entry.category}{pinned ? pick({ ru: " · закреплено", en: " · pinned" }) : ""}
          </div>
        </span>
      )}
    </span>
  );
}

/** Shortcut: an inline glossary term that uses the glossary short label. */
export function T({ id }: { id: string }) {
  return <Term id={id} />;
}

/** Mini-table that lists every term in a category. */
export function TermsByCategory({ category }: { category: string }) {
  const { t } = useT();
  const list = Object.values(GLOSSARY).filter((e) => e.category === category);
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 8 }}>
      {list.map((e) => (
        <div key={e.id} style={{
          padding: 10,
          borderRadius: 8,
          background: "rgba(155, 140, 255, 0.06)",
          border: "1px solid " + theme.color.line,
          fontSize: 13,
        }}>
          <div style={{ fontWeight: 600, color: theme.color.starlight, marginBottom: 4 }}>
            <Term id={e.id} />
          </div>
          <div style={{ color: theme.color.inkSoft, lineHeight: 1.4 }}>
            {t(e.definition)}
          </div>
        </div>
      ))}
    </div>
  );
}
