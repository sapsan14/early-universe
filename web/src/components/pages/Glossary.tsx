import React, { useState, useMemo } from "react";
import { theme } from "../../theme";
import { useT, p } from "../../i18n";
import { GLOSSARY } from "../../glossary";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";

const CATEGORIES: { id: string; label: { ru: string; en: string }; tone: any }[] = [
  { id: "all", label: { ru: "Всё", en: "All" }, tone: "starlight" },
  { id: "epoch", label: { ru: "Эпохи", en: "Epochs" }, tone: "nova" },
  { id: "physics", label: { ru: "Физика", en: "Physics" }, tone: "plasma" },
  { id: "math", label: { ru: "Математика", en: "Math" }, tone: "aurora" },
  { id: "parameter", label: { ru: "Параметры", en: "Parameters" }, tone: "ember" },
  { id: "observable", label: { ru: "Наблюдения", en: "Observables" }, tone: "starlight" },
  { id: "ml", label: { ru: "Машинное обучение", en: "Machine learning" }, tone: "aurora" },
];

export function Glossary() {
  const { t, pick } = useT();
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("all");

  const items = useMemo(() => {
    const raw = Object.values(GLOSSARY);
    const filtered = raw.filter((e) => {
      if (cat !== "all" && e.category !== cat) return false;
      if (!q) return true;
      const lower = q.toLowerCase();
      return (
        t(e.short).toLowerCase().includes(lower) ||
        t(e.definition).toLowerCase().includes(lower) ||
        (e.symbol ?? "").toLowerCase().includes(lower) ||
        e.id.includes(lower)
      );
    });
    return filtered.sort((a, b) => t(a.short).localeCompare(t(b.short)));
  }, [q, cat, t]);

  return (
    <div style={{ maxWidth: 1280, margin: "0 auto", padding: "32px 24px 0" }}>
      <Badge tone="starlight" glyph="✦">{pick({ ru: "Словарь", en: "Glossary" })}</Badge>
      <h1 style={{ fontFamily: theme.font.serif, fontSize: 46, marginTop: 12, color: theme.color.ink, lineHeight: 1.05 }}>
        {pick({ ru: "Космологический карманный словарь", en: "Pocket cosmology dictionary" })}
      </h1>
      <p style={{ color: theme.color.inkSoft, fontSize: 17, fontFamily: theme.font.serif, maxWidth: 720, marginTop: 12 }}>
        {pick({
          ru: "Каждый термин снабжён определением, аналогией и формулой (если уместно). Кликни — получишь полную карточку.",
          en: "Every term has a definition, analogy and formula where it makes sense. Click for the full card.",
        })}
      </p>

      <div style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 28, flexWrap: "wrap" }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={pick({ ru: "Поиск (например «реликтовое»)", en: "Search (e.g. 'redshift')" })}
          style={{
            flex: "1 1 280px",
            background: "rgba(155,140,255,0.06)",
            border: `1px solid ${theme.color.line}`,
            borderRadius: 999,
            padding: "10px 18px",
            color: theme.color.ink,
            fontSize: 14,
            fontFamily: theme.font.sans,
            outline: "none",
          }}
        />
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {CATEGORIES.map((c) => (
            <button
              key={c.id}
              onClick={() => setCat(c.id)}
              style={{
                padding: "6px 14px",
                borderRadius: 999,
                border: `1px solid ${cat === c.id ? theme.color.starlight : theme.color.line}`,
                background: cat === c.id ? "rgba(255,213,107,0.16)" : "transparent",
                color: cat === c.id ? theme.color.starlight : theme.color.inkSoft,
                cursor: "pointer", fontSize: 12.5, fontWeight: cat === c.id ? 700 : 500,
              }}
            >{t(c.label)}</button>
          ))}
        </div>
      </div>

      <div style={{
        display: "grid", gap: 16,
        gridTemplateColumns: "repeat(auto-fill, minmax(290px, 1fr))",
        marginTop: 28,
      }}>
        {items.map((e) => (
          <Card key={e.id} padding={18} tone={e.category === "epoch" ? "nova" : e.category === "math" ? "aurora" : "plasma"}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8 }}>
              <strong style={{ fontFamily: theme.font.serif, fontSize: 18, color: theme.color.starlight }}>
                {t(e.short)}
              </strong>
              {e.symbol && (
                <span style={{ fontFamily: theme.font.math, color: theme.color.plasma, fontSize: 15 }}>
                  {e.symbol}{e.unit ? ` (${e.unit})` : ""}
                </span>
              )}
            </div>
            <div style={{ color: theme.color.ink, marginTop: 8, fontSize: 14, lineHeight: 1.55 }}>
              {t(e.definition)}
            </div>
            {e.formula && (
              <div style={{
                marginTop: 10,
                padding: "6px 10px",
                borderRadius: 6,
                background: "rgba(94,226,255,0.06)",
                border: "1px solid rgba(94,226,255,0.2)",
                color: theme.color.plasma,
                fontFamily: theme.font.math,
                fontSize: 14,
              }}>{e.formula}</div>
            )}
            {e.analogy && (
              <div style={{
                marginTop: 10, paddingLeft: 10,
                borderLeft: `2px solid ${theme.color.starlight}`,
                color: theme.color.inkSoft, fontStyle: "italic", fontSize: 13,
              }}>
                {pick({ ru: "Аналогия: ", en: "Analogy: " })}{t(e.analogy)}
              </div>
            )}
            <div style={{ marginTop: 10, fontSize: 11, color: theme.color.inkDim, textTransform: "uppercase", letterSpacing: 1 }}>
              {e.category}
            </div>
          </Card>
        ))}
      </div>
      {items.length === 0 && (
        <div style={{ textAlign: "center", color: theme.color.inkSoft, marginTop: 60, fontSize: 16 }}>
          {pick({ ru: "Ничего не нашлось. Попробуй другое слово.", en: "Nothing found. Try a different word." })}
        </div>
      )}
    </div>
  );
}
