import React from "react";
import { theme } from "../../theme";
import { useT, p } from "../../i18n";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Callout } from "../ui/Callout";

export function About() {
  const { t, pick } = useT();
  return (
    <div style={{ maxWidth: 980, margin: "0 auto", padding: "32px 24px 0" }}>
      <Badge tone="starlight" glyph="❂">{pick({ ru: "О проекте", en: "About" })}</Badge>
      <h1 style={{ fontFamily: theme.font.serif, fontSize: 46, marginTop: 12, color: theme.color.ink, lineHeight: 1.1 }}>
        {pick({
          ru: "Cosmic Academy — открытый учебник Вселенной",
          en: "Cosmic Academy — an open textbook of the Universe",
        })}
      </h1>
      <p style={{ color: theme.color.inkSoft, fontSize: 18, fontFamily: theme.font.serif, marginTop: 16, lineHeight: 1.65 }}>
        {pick({
          ru: "Этот проект родился из исследовательской платформы ARCHEON — модели, симулирующей раннюю Вселенную и охотящейся на аномалии в реликтовом излучении. Мы взяли её мощный «движок» и обернули в учебник для школьников. Чтобы каждый, кто хочет, мог за один вечер понять, как устроена самая большая история на свете.",
          en: "This project grew out of the ARCHEON research platform — a model that simulates the early Universe and hunts for anomalies in the cosmic microwave background. We took its powerful engine and wrapped it in a textbook for high-schoolers. So anyone who's curious can understand the biggest story there is in a single evening.",
        })}
      </p>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", marginTop: 28 }}>
        <Card padding={20} tone="plasma">
          <h3 style={{ fontFamily: theme.font.serif, color: theme.color.ink }}>{pick({ ru: "Для кого", en: "Who it's for" })}</h3>
          <p style={{ marginTop: 8, color: theme.color.inkSoft, fontSize: 14, lineHeight: 1.6 }}>
            {pick({
              ru: "Старшеклассники, студенты-первокурсники, любопытные взрослые, учителя физики — словом, для всех, кто хочет понимать космологию руками, а не через формулы из учебника.",
              en: "High-school upperclassmen, first-year undergrads, curious adults, physics teachers — anyone who wants to grasp cosmology hands-on, not through textbook formulas alone.",
            })}
          </p>
        </Card>
        <Card padding={20} tone="aurora">
          <h3 style={{ fontFamily: theme.font.serif, color: theme.color.ink }}>{pick({ ru: "Как это сделано", en: "How it's built" })}</h3>
          <p style={{ marginTop: 8, color: theme.color.inkSoft, fontSize: 14, lineHeight: 1.6 }}>
            {pick({
              ru: "Фронтенд: React + TypeScript + Vite. Бэкенд: FastAPI + PyTorch + numpy для эталонных моделей космологии. Все интерактивы умеют работать офлайн (фолбек-приближения).",
              en: "Frontend: React + TypeScript + Vite. Backend: FastAPI + PyTorch + numpy for reference cosmology models. Every interactive falls back to local approximations when the API is offline.",
            })}
          </p>
        </Card>
        <Card padding={20} tone="nova">
          <h3 style={{ fontFamily: theme.font.serif, color: theme.color.ink }}>{pick({ ru: "Откуда числа", en: "Where the numbers come from" })}</h3>
          <p style={{ marginTop: 8, color: theme.color.inkSoft, fontSize: 14, lineHeight: 1.6 }}>
            {pick({
              ru: "Эталон — параметры миссии Planck 2018 (ESA). Уравнения — ΛCDM с модулями инфляции, рекомбинации и аномалий. Симуляции структур — простой линейный рост со встроенной нелинейной поправкой.",
              en: "Reference — ESA Planck 2018 mission parameters. Equations — ΛCDM with inflation, recombination and anomaly modules. Structure simulations — simple linear growth with a built-in non-linear correction.",
            })}
          </p>
        </Card>
        <Card padding={20} tone="ember">
          <h3 style={{ fontFamily: theme.font.serif, color: theme.color.ink }}>{pick({ ru: "Что дальше", en: "What's next" })}</h3>
          <p style={{ marginTop: 8, color: theme.color.inkSoft, fontSize: 14, lineHeight: 1.6 }}>
            {pick({
              ru: "Рассматриваем добавление режима «класс» (учитель → ученики), мини-квестов (например, «найди WMAP-аномалию холодного пятна») и трёхмерной WebGPU-симуляции N-body.",
              en: "We're exploring a 'classroom' mode (teacher → students), mini-quests ('find the WMAP cold spot anomaly') and a 3D WebGPU N-body simulation.",
            })}
          </p>
        </Card>
      </div>

      <Callout variant="story" title={p("Спасибо", "Thank you")}>
        {pick({
          ru: "Спасибо коллабораций Planck, WMAP, COBE — за полвека терпеливых наблюдений неба. Спасибо разработчикам CAMB, CLASS, HEALPix — за инструменты, которыми космологи говорят о Вселенной. И спасибо тебе — за то, что добрался до этой страницы.",
          en: "Thanks to the Planck, WMAP and COBE collaborations — for half a century of patient sky observation. Thanks to the developers of CAMB, CLASS, HEALPix — for the tools cosmologists use to speak about the Universe. And thanks to you, for making it all the way here.",
        })}
      </Callout>

      <div style={{ marginTop: 32, padding: 20, borderRadius: theme.radius.md, border: `1px dashed ${theme.color.line}`, color: theme.color.inkDim, fontSize: 13, fontFamily: theme.font.mono }}>
        {pick({ ru: "Лицензия: MIT.", en: "License: MIT." })} ✦{" "}
        {pick({ ru: "Сделано для всех, кому когда-то говорили: «не задавай слишком больших вопросов».", en: "Made for everyone who was ever told: 'don't ask such big questions'." })}
      </div>
    </div>
  );
}
