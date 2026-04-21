import React from "react";
import { theme } from "../../theme";
import { useT, p } from "../../i18n";
import { useRouter } from "../../router";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { TimeMachine } from "../lab/TimeMachine";
import { ParameterStudio } from "../lab/ParameterStudio";
import { UniverseGarden } from "../lab/UniverseGarden";
import { AnomalyHunter } from "../lab/AnomalyHunter";

const TOOLS = [
  { id: "time", glyph: "⏳", color: "#ffd56b", title: { ru: "Машина времени", en: "Time Machine" }, sub: { ru: "Прыгай по эпохам — от Планка до сегодня", en: "Jump across epochs — from Planck to now" } },
  { id: "params", glyph: "⚛", color: "#5ee2ff", title: { ru: "Шесть параметров", en: "Six Parameters" }, sub: { ru: "Подвинь рычаги — спектр CMB перерисуется", en: "Slide the levers — the CMB spectrum redraws" } },
  { id: "playable", glyph: "🌀", color: "#ff7ac6", title: { ru: "Играбельная Вселенная", en: "Playable Universe" }, sub: { ru: "Вырасти космическую паутину", en: "Grow a cosmic web" } },
  { id: "anomaly", glyph: "🔭", color: "#7afcb1", title: { ru: "Охота за аномалиями", en: "Anomaly Hunter" }, sub: { ru: "Найди подозрительные пятна на небе", en: "Find suspicious patches in the sky" } },
] as const;

export function Lab({ tool }: { tool?: "time" | "params" | "playable" | "anomaly" }) {
  const { t } = useT();
  const { go, route } = useRouter();
  const active = tool ?? "time";

  return (
    <div style={{ maxWidth: 1280, margin: "0 auto", padding: "32px 24px 0" }}>
      <Badge tone="aurora" glyph="✸">{t(p("Лаборатория", "Laboratory"))}</Badge>
      <h1 style={{ fontFamily: theme.font.serif, fontSize: 46, marginTop: 12, color: theme.color.ink, lineHeight: 1.05 }}>
        {t(p("Четыре окна во Вселенную", "Four windows into the Universe"))}
      </h1>
      <p style={{ color: theme.color.inkSoft, fontSize: 17, fontFamily: theme.font.serif, maxWidth: 720, marginTop: 12 }}>
        {t(p(
          "Здесь живут все интерактивные инструменты. Можно крутить параметры как угодно — никаких поломок, всегда есть кнопка Сброс.",
          "All interactive tools live here. Spin the parameters any way you like — nothing breaks, the Reset button is always there.",
        ))}
      </p>

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 28, marginBottom: 24 }}>
        {TOOLS.map((tool) => {
          const isActive = tool.id === active;
          return (
            <Card
              key={tool.id}
              as="button"
              onClick={() => go({ name: "lab", tool: tool.id as any })}
              padding={14}
              tone={isActive ? "aurora" : "plasma"}
              glow={isActive}
              style={{
                flex: "1 1 220px",
                minWidth: 200,
                opacity: isActive ? 1 : 0.85,
                transform: isActive ? "translateY(-2px)" : "none",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 10,
                  background: `linear-gradient(135deg, ${tool.color}, ${tool.color}66)`,
                  display: "grid", placeItems: "center",
                  fontSize: 20, color: "#fff",
                  boxShadow: `0 4px 14px ${tool.color}55`,
                }}>{tool.glyph}</div>
                <div>
                  <div style={{ fontFamily: theme.font.serif, fontSize: 16, color: theme.color.ink }}>{t(tool.title)}</div>
                  <div style={{ color: theme.color.inkSoft, fontSize: 12 }}>{t(tool.sub)}</div>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      <div key={active} className="fade-in">
        {active === "time" && <TimeMachine />}
        {active === "params" && <ParameterStudio />}
        {active === "playable" && <UniverseGarden />}
        {active === "anomaly" && <AnomalyHunter />}
      </div>
    </div>
  );
}
