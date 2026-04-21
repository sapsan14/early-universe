import React, { useState, useRef } from "react";
import { theme } from "../../theme";
import { useT } from "../../i18n";
import { GLOSSARY, term as lookupTerm } from "../../glossary";
import { FloatingCard } from "./FloatingCard";
import { Tex } from "./Math";

/**
 * <Term id="cmb">CMB</Term> — dotted-underlined word. Hovering or clicking
 * opens a portalled popover with the glossary definition, an analogy, and
 * (if present) the formula. Because the card is portalled it is never cut
 * off by a scrolling card above it.
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
  const triggerRef = useRef<HTMLButtonElement>(null);

  const entry = lookupTerm(id);
  if (!entry) return <span style={{ color: theme.color.danger }}>?{id}?</span>;

  const shouldShow = open || pinned;

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => !pinned && setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => !pinned && setOpen(false)}
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
          display: "inline",
        }}
        aria-describedby={`term-${id}`}
      >
        {children ?? t(entry.short)}
      </button>
      <FloatingCard
        anchor={triggerRef.current}
        open={shouldShow}
        width={340}
        onRequestClose={pinned ? () => { setPinned(false); setOpen(false); } : undefined}
      >
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 8, marginBottom: 6 }}>
          <strong style={{ fontFamily: theme.font.serif, fontSize: 15, color: theme.color.starlight }}>
            {t(entry.short)}
          </strong>
          {entry.symbol && (
            <span style={{ color: theme.color.plasma, fontSize: 14, display: "inline-flex", alignItems: "baseline", gap: 4 }}>
              <Tex>{entry.symbol}</Tex>
              {entry.unit ? <span style={{ color: theme.color.inkDim, fontSize: 12 }}>({entry.unit})</span> : null}
            </span>
          )}
        </div>
        <div style={{ marginBottom: entry.analogy || entry.formula ? 8 : 0 }}>
          {t(entry.definition)}
        </div>
        {entry.formula && (
          <div style={{
            padding: "6px 10px",
            borderRadius: 6,
            background: "rgba(94, 226, 255, 0.08)",
            border: "1px solid rgba(94, 226, 255, 0.25)",
            color: theme.color.plasma,
            marginBottom: entry.analogy ? 8 : 0,
            fontSize: 15,
            textAlign: "center",
          }}>
            <Tex>{entry.formula}</Tex>
          </div>
        )}
        {entry.analogy && (
          <div style={{
            fontStyle: "italic",
            color: theme.color.inkSoft,
            fontSize: 12,
            borderLeft: `2px solid ${theme.color.starlight}`,
            paddingLeft: 8,
          }}>
            {pick({ ru: "Аналогия: ", en: "Analogy: " })}{t(entry.analogy)}
          </div>
        )}
        <div style={{ marginTop: 8, fontSize: 11, color: theme.color.inkDim, textTransform: "uppercase", letterSpacing: 1 }}>
          {entry.category}{pinned ? pick({ ru: " · закреплено", en: " · pinned" }) : ""}
        </div>
      </FloatingCard>
    </>
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
