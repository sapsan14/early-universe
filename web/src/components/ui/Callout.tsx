import React from "react";
import { theme } from "../../theme";
import { useT } from "../../i18n";
import type { Phrase } from "../../i18n";

type Variant =
  | "note"
  | "tip"
  | "wow"
  | "challenge"
  | "warning"
  | "story"
  | "math"
  | "history";

const STYLE: Record<Variant, { color: string; glyph: string; label: Phrase }> = {
  note: { color: theme.color.plasma, glyph: "✶", label: { ru: "Заметка", en: "Note" } },
  tip: { color: theme.color.aurora, glyph: "✦", label: { ru: "Подсказка", en: "Tip" } },
  wow: { color: theme.color.nova, glyph: "✺", label: { ru: "Wow!", en: "Wow!" } },
  challenge: { color: theme.color.starlight, glyph: "❂", label: { ru: "Задание", en: "Challenge" } },
  warning: { color: theme.color.ember, glyph: "⚠", label: { ru: "Внимание", en: "Heads up" } },
  story: { color: theme.color.quantum, glyph: "✸", label: { ru: "История", en: "Story" } },
  math: { color: theme.color.plasma, glyph: "∑", label: { ru: "Математика", en: "Math" } },
  history: { color: theme.color.starlight, glyph: "✧", label: { ru: "Из истории", en: "From history" } },
};

export function Callout({
  variant = "note",
  title,
  children,
}: {
  variant?: Variant;
  title?: Phrase | string;
  children: React.ReactNode;
}) {
  const { t } = useT();
  const s = STYLE[variant];
  const titleText = typeof title === "string" ? title : title ? t(title) : t(s.label);
  return (
    <aside style={{
      margin: "18px 0",
      padding: "16px 18px 16px 16px",
      borderRadius: theme.radius.md,
      background: `linear-gradient(135deg, ${s.color}1a, transparent 70%)`,
      border: `1px solid ${s.color}55`,
      borderLeft: `4px solid ${s.color}`,
      position: "relative",
      color: theme.color.ink,
      lineHeight: 1.65,
    }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        marginBottom: 8,
        fontFamily: theme.font.serif,
        color: s.color,
        fontWeight: 700,
        letterSpacing: 0.5,
      }}>
        <span aria-hidden style={{ fontSize: 20, lineHeight: 1 }}>{s.glyph}</span>
        <span style={{ textTransform: "uppercase", fontSize: 13 }}>{titleText}</span>
      </div>
      <div style={{ fontFamily: theme.font.serif, fontSize: 17, lineHeight: 1.65 }}>
        {children}
      </div>
    </aside>
  );
}
