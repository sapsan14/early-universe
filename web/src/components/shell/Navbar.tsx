import React from "react";
import { theme } from "../../theme";
import { useT, p } from "../../i18n";
import { LangToggle } from "../ui/LangToggle";
import { useRouter, type Route } from "../../router";

const NAV: { id: Route["name"]; label: { ru: string; en: string }; glyph: string }[] = [
  { id: "home", label: p("Главная", "Home"), glyph: "✺" },
  { id: "lessons", label: p("Уроки", "Lessons"), glyph: "📖" },
  { id: "lab", label: p("Лаборатория", "Lab"), glyph: "✸" },
  { id: "glossary", label: p("Словарь", "Glossary"), glyph: "✦" },
  { id: "about", label: p("О проекте", "About"), glyph: "❂" },
];

export function Navbar() {
  const { t } = useT();
  const { route, go } = useRouter();
  return (
    <header style={{
      position: "sticky",
      top: 0,
      zIndex: theme.zIndex.raised,
      backdropFilter: "blur(14px) saturate(140%)",
      WebkitBackdropFilter: "blur(14px) saturate(140%)",
      background: "linear-gradient(180deg, rgba(5, 6, 15, 0.85), rgba(5, 6, 15, 0.55))",
      borderBottom: `1px solid ${theme.color.line}`,
    }}>
      <div style={{
        maxWidth: 1280, margin: "0 auto", padding: "12px 24px",
        display: "flex", alignItems: "center", gap: 18,
      }}>
        <button
          onClick={() => go({ name: "home" })}
          style={{
            background: "transparent", border: "none", cursor: "pointer",
            display: "flex", alignItems: "center", gap: 12, color: theme.color.ink,
          }}
        >
          <span style={{
            width: 36, height: 36, borderRadius: 10,
            background: theme.gradient.starlight,
            display: "grid", placeItems: "center",
            fontWeight: 800, color: "#1c1530", fontSize: 18,
            boxShadow: theme.shadow.starlit,
          }}>✺</span>
          <span style={{ fontFamily: theme.font.serif, fontSize: 20, lineHeight: 1, letterSpacing: 0.5 }}>
            <span style={{ fontWeight: 700 }}>Cosmic</span>
            <span style={{ color: theme.color.starlight, fontWeight: 700 }}> Academy</span>
          </span>
        </button>

        <nav style={{ display: "flex", gap: 4, marginLeft: 24, flexWrap: "wrap" }}>
          {NAV.map((n) => {
            const active = route.name === n.id;
            return (
              <button
                key={n.id}
                onClick={() => go({ name: n.id } as Route)}
                style={{
                  padding: "8px 16px",
                  borderRadius: 999,
                  border: "none",
                  background: active ? "rgba(255, 213, 107, 0.18)" : "transparent",
                  color: active ? theme.color.starlight : theme.color.inkSoft,
                  cursor: "pointer",
                  fontWeight: active ? 700 : 500,
                  fontSize: 14,
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 8,
                  transition: theme.motion.snap,
                }}
              >
                <span aria-hidden style={{ opacity: 0.85 }}>{n.glyph}</span>
                {t(n.label)}
              </button>
            );
          })}
        </nav>

        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12 }}>
          <a
            href="https://github.com/sapsan14/early-universe"
            target="_blank"
            rel="noreferrer"
            style={{
              fontSize: 12,
              color: theme.color.inkSoft,
              padding: "4px 10px",
              borderRadius: 999,
              border: `1px solid ${theme.color.line}`,
            }}
          >GitHub</a>
          <LangToggle />
        </div>
      </div>
    </header>
  );
}
