import React, { useEffect, useRef, useState } from "react";
import { theme } from "../../theme";
import { useT, p } from "../../i18n";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { Callout } from "../ui/Callout";
import { useRouter } from "../../router";
import { CHAPTERS } from "../../lessons";
import { Term } from "../ui/Term";

/**
 * Hero with a slow-rotating spiral of glyphs around the title — pure CSS so
 * it animates smoothly even on weaker phones. Below: chapter map, the four
 * lab tools, "What you'll learn" pillars and a tour CTA.
 */
export function Home() {
  const { t, pick } = useT();
  const { go } = useRouter();
  const heroRef = useRef<HTMLDivElement>(null);
  const [parallax, setParallax] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      const rect = heroRef.current?.getBoundingClientRect();
      if (!rect) return;
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      setParallax({
        x: ((e.clientX - cx) / rect.width) * 18,
        y: ((e.clientY - cy) / rect.height) * 18,
      });
    };
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, []);

  return (
    <div style={{ position: "relative" }}>
      {/* Hero ─────────────────────────────────────────────────────── */}
      <section ref={heroRef} style={{
        maxWidth: 1280, margin: "0 auto", padding: "60px 24px 40px",
        display: "grid", gap: 32,
        gridTemplateColumns: "minmax(0, 1fr) 420px",
        alignItems: "center",
      }} className="home-hero">
        <div className="fade-in">
          <Badge tone="starlight" glyph="✺">
            {t(p("Учебник нового поколения · 13.8 миллиардов лет за один вечер", "A new-kind textbook · 13.8 billion years in one evening"))}
          </Badge>
          <h1 style={{
            fontFamily: theme.font.serif,
            fontSize: "clamp(40px, 6vw, 76px)",
            lineHeight: 1.05,
            margin: "20px 0",
            color: theme.color.ink,
          }}>
            {pick({
              ru: <>Открой <span style={{ background: theme.gradient.starlight, WebkitBackgroundClip: "text", color: "transparent" }}>раннюю Вселенную</span> — пальцами и любопытством.</>,
              en: <>Discover the <span style={{ background: theme.gradient.starlight, WebkitBackgroundClip: "text", color: "transparent" }}>early Universe</span> with your own fingertips.</>,
            })}
          </h1>
          <p style={{
            fontFamily: theme.font.serif,
            fontSize: "clamp(17px, 1.5vw, 21px)",
            color: theme.color.inkSoft,
            maxWidth: 620,
            lineHeight: 1.55,
          }}>
            {t(p(
              "Cosmic Academy — это бесплатный интерактивный учебник по космологии для школьников. Восемь иллюстрированных глав, переведённый математический язык, чёткие аналогии и четыре лаборатории, где можно подвинуть параметры и собрать собственную Вселенную.",
              "Cosmic Academy is a free, interactive cosmology textbook for high-schoolers. Eight illustrated chapters, translated math, vivid analogies, and four laboratories where you can slide the parameters and grow a Universe of your own.",
            ))}
          </p>
          <div style={{ display: "flex", gap: 12, marginTop: 28, flexWrap: "wrap" }}>
            <Button variant="primary" size="lg" onClick={() => go({ name: "lessons", chapter: "intro" })} iconRight={<span>→</span>}>
              {t(p("Начать с главы 1", "Start with Chapter 1"))}
            </Button>
            <Button variant="outline" size="lg" onClick={() => go({ name: "lab" })}>
              {t(p("Сразу в лабораторию", "Straight to the Lab"))}
            </Button>
          </div>
          <div style={{
            display: "flex", gap: 18, marginTop: 32,
            color: theme.color.inkDim, fontSize: 13, flexWrap: "wrap",
          }}>
            <span>✶ {t(p("Без регистрации", "No sign-up"))}</span>
            <span>✶ {t(p("Работает офлайн", "Works offline"))}</span>
            <span>✶ {t(p("Русский / English", "Russian / English"))}</span>
            <span>✶ {t(p("Открытый код", "Open source"))}</span>
          </div>
        </div>

        {/* Cosmic mandala: rotating rings + drifting planet */}
        <div style={{ position: "relative", aspectRatio: "1/1", maxWidth: 420, margin: "0 auto", width: "100%" }} className="fade-in">
          <div style={{
            position: "absolute", inset: 0,
            transform: `translate(${parallax.x}px, ${parallax.y}px)`,
            transition: "transform 240ms ease-out",
          }}>
            <div style={{
              position: "absolute", inset: 0, borderRadius: "50%",
              background:
                "radial-gradient(circle at 50% 50%, #ffd56b 0%, #ff7ac6 40%, #5e34c8 70%, transparent 78%)",
              filter: "blur(2px)",
              boxShadow: "0 0 80px 20px rgba(255, 138, 94, 0.25)",
            }} />
            {[0, 1, 2].map((i) => (
              <div key={i} style={{
                position: "absolute", inset: i === 0 ? -20 : i === 1 ? -50 : -90,
                borderRadius: "50%",
                border: `${i === 0 ? 1.5 : 1}px solid ${["#ffd56b", "#5ee2ff", "#9b8cff"][i]}55`,
                animation: `spin-slow ${30 + i * 25}s linear ${i % 2 ? "reverse" : ""} infinite`,
              }}>
                <div style={{
                  position: "absolute",
                  top: "50%", left: i % 2 ? 0 : "100%",
                  transform: "translate(-50%, -50%)",
                  width: i === 0 ? 14 : 10,
                  height: i === 0 ? 14 : 10,
                  borderRadius: "50%",
                  background: ["#ffd56b", "#5ee2ff", "#9b8cff"][i],
                  boxShadow: `0 0 20px ${["#ffd56b", "#5ee2ff", "#9b8cff"][i]}`,
                }} />
              </div>
            ))}
            {/* Glyph constellation */}
            {["✺", "✸", "✦", "✪", "❂", "✶", "☀", "✴"].map((g, i) => {
              const a = (i / 8) * Math.PI * 2;
              const r = 38;
              return (
                <div key={i} style={{
                  position: "absolute",
                  left: `${50 + Math.cos(a) * r}%`,
                  top: `${50 + Math.sin(a) * r}%`,
                  transform: "translate(-50%, -50%)",
                  fontSize: 22,
                  color: i % 2 ? theme.color.starlight : theme.color.plasma,
                  textShadow: `0 0 14px currentColor`,
                  opacity: 0.85,
                  fontFamily: theme.font.serif,
                  pointerEvents: "none",
                }}>{g}</div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Big number band */}
      <section style={{ maxWidth: 1280, margin: "20px auto 60px", padding: "0 24px" }}>
        <div style={{
          display: "grid", gap: 12,
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        }}>
          {[
            { v: "13.8", u: pick({ ru: "млрд лет истории", en: "Gyr of history" }), c: theme.color.starlight },
            { v: "10⁻⁴³", u: pick({ ru: "секунды — старт", en: "seconds — the start" }), c: theme.color.nova },
            { v: "10²⁶×", u: pick({ ru: "за инфляцию", en: "during inflation" }), c: theme.color.ember },
            { v: "2.725 K", u: pick({ ru: "температура CMB", en: "CMB temperature" }), c: theme.color.plasma },
            { v: "6", u: pick({ ru: "ингредиентов Вселенной", en: "ingredients of the Universe" }), c: theme.color.aurora },
            { v: "∞", u: pick({ ru: "вопросов впереди", en: "questions ahead" }), c: theme.color.quantum },
          ].map((n, i) => (
            <Card key={i} padding={18} tone={i % 2 ? "starlight" : "plasma"}>
              <div style={{ fontFamily: theme.font.mono, fontSize: 28, color: n.c, fontWeight: 700 }}>
                {n.v}
              </div>
              <div style={{ color: theme.color.inkSoft, fontSize: 13, marginTop: 4 }}>{n.u}</div>
            </Card>
          ))}
        </div>
      </section>

      {/* Chapter map ─────────────────────────────────────────────────── */}
      <section id="chapters" style={{ maxWidth: 1280, margin: "0 auto", padding: "0 24px" }}>
        <div style={{ marginBottom: 24, display: "flex", alignItems: "baseline", gap: 16, flexWrap: "wrap" }}>
          <h2 style={{ fontFamily: theme.font.serif, fontSize: 36, color: theme.color.ink }}>
            {t(p("Восьмиглавное путешествие", "An eight-chapter journey"))}
          </h2>
          <p style={{ color: theme.color.inkSoft, maxWidth: 520, fontFamily: theme.font.serif, fontSize: 17 }}>
            {t(p(
              "Каждая глава — короткий рассказ + лаборатория + словарь. Читай по порядку или прыгай сразу к интересному.",
              "Each chapter pairs a short story with a hands-on lab and a glossary. Read in order or jump to whatever sparks your curiosity.",
            ))}
          </p>
        </div>
        <div style={{
          display: "grid", gap: 16,
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
        }}>
          {CHAPTERS.map((ch) => (
            <Card key={ch.id} as="button" onClick={() => go({ name: "lessons", chapter: ch.id })} padding={20} tone="aurora" style={{ height: "100%" }}>
              <div style={{
                display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12,
              }}>
                <div style={{
                  width: 42, height: 42, borderRadius: 12,
                  background: `linear-gradient(135deg, ${ch.color}, ${ch.color}77)`,
                  display: "grid", placeItems: "center",
                  fontSize: 22, color: "#fff",
                  boxShadow: `0 8px 24px ${ch.color}55`,
                }}>{ch.glyph}</div>
                <Badge tone="muted">
                  {t(p("Глава", "Chapter"))} {ch.number}
                </Badge>
              </div>
              <div style={{ fontFamily: theme.font.serif, fontSize: 20, fontWeight: 700, color: theme.color.ink, marginBottom: 6, lineHeight: 1.2 }}>
                {t(ch.title)}
              </div>
              <div style={{ color: theme.color.inkSoft, fontSize: 14, lineHeight: 1.5, marginBottom: 12, fontFamily: theme.font.serif }}>
                {t(ch.subtitle)}
              </div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
                {ch.tags.map((tg, i) => (
                  <Badge key={i} tone={i ? "plasma" : "starlight"}>{t(tg)}</Badge>
                ))}
              </div>
              <div style={{
                display: "flex", justifyContent: "space-between",
                color: theme.color.inkDim, fontSize: 12, marginTop: 4,
              }}>
                <span>⏱ {t(ch.duration)}</span>
                <span aria-label="difficulty">
                  {"●".repeat(ch.difficulty)}{<span style={{ color: theme.color.line }}>{"●".repeat(3 - ch.difficulty)}</span>}
                </span>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Lab preview ─────────────────────────────────────────────────── */}
      <section style={{ maxWidth: 1280, margin: "80px auto 0", padding: "0 24px" }}>
        <div style={{ marginBottom: 24, textAlign: "center" }}>
          <Badge tone="plasma" glyph="✸">{t(p("Лаборатория", "The Lab"))}</Badge>
          <h2 style={{ fontFamily: theme.font.serif, fontSize: 40, color: theme.color.ink, marginTop: 14 }}>
            {t(p("Четыре окна во Вселенную", "Four windows into the Universe"))}
          </h2>
          <p style={{ color: theme.color.inkSoft, maxWidth: 720, margin: "12px auto 0", fontFamily: theme.font.serif, fontSize: 17 }}>
            {t(p(
              "Каждый инструмент сопровождается уроком, а каждый урок — кнопкой «Открыть в лаборатории».",
              "Every tool has a lesson, and every lesson has an 'Open in Lab' button.",
            ))}
          </p>
        </div>
        <div style={{
          display: "grid", gap: 16,
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
        }}>
          {([
            { id: "time", glyph: "⏳", color: theme.color.starlight, title: p("Машина времени", "Time Machine"), text: p("Слайдером прошагай 13,8 миллиардов лет. На каждой эпохе — температура, плотность, что происходит.", "Slide through 13.8 Gyr. At every epoch you see temperature, density, and what's actually happening.") },
            { id: "params", glyph: "⚛", color: theme.color.plasma, title: p("Шесть параметров", "Six Parameters"), text: p("Двигай Ω_b, n_s, A_s — и спектр CMB перестраивается в реальном времени.", "Slide Ω_b, n_s, A_s — and the CMB spectrum re-draws in real time.") },
            { id: "playable", glyph: "🌀", color: theme.color.nova, title: p("Играбельная Вселенная", "Playable Universe"), text: p("Запусти симуляцию роста структур. Получишь космическую паутину или серую кашу.", "Run a structure-growth simulation. You'll either grow a cosmic web — or a grey mush.") },
            { id: "anomaly", glyph: "🔭", color: theme.color.aurora, title: p("Охота за аномалиями", "Anomaly Hunter"), text: p("Найди в карте CMB то, что не вписывается в гауссов шум — может быть, это новая физика?", "Spot what doesn't fit Gaussian noise in a CMB map — maybe new physics?") },
          ] as const).map((tool) => (
            <Card key={tool.id} as="button" onClick={() => go({ name: "lab", tool: tool.id as any })} padding={22} tone="nova" style={{ textAlign: "left" }}>
              <div style={{
                width: 56, height: 56, borderRadius: 16,
                background: `linear-gradient(135deg, ${tool.color}cc, ${tool.color}33)`,
                display: "grid", placeItems: "center", fontSize: 28,
                marginBottom: 14, boxShadow: `0 8px 24px ${tool.color}55`,
              }}>{tool.glyph}</div>
              <div style={{ fontFamily: theme.font.serif, fontSize: 22, color: theme.color.ink, marginBottom: 8 }}>
                {t(tool.title)}
              </div>
              <p style={{ color: theme.color.inkSoft, fontSize: 14, lineHeight: 1.55, fontFamily: theme.font.serif }}>
                {t(tool.text)}
              </p>
              <div style={{ marginTop: 14, color: tool.color, fontWeight: 600, fontSize: 13 }}>
                {t(p("Запустить →", "Launch →"))}
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* How to read ─────────────────────────────────────────────────── */}
      <section style={{ maxWidth: 1280, margin: "80px auto 0", padding: "0 24px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(0,1fr)", gap: 24 }} className="home-howto">
          <Card padding={28} tone="starlight">
            <Badge tone="starlight" glyph="✦">{t(p("Как читать", "How to read"))}</Badge>
            <h3 style={{ fontFamily: theme.font.serif, fontSize: 28, color: theme.color.ink, marginTop: 14 }}>
              {t(p("Слова, которые сами объясняют себя", "Words that explain themselves"))}
            </h3>
            <p style={{ marginTop: 10, color: theme.color.inkSoft, fontFamily: theme.font.serif, fontSize: 16, lineHeight: 1.6 }}>
              {pick({
                ru: <>Каждый научный термин в учебнике подчёркнут пунктиром: например, <Term id="cmb" /> или <Term id="redshift" />. Наведи мышкой — появится короткое определение, аналогия и формула.</>,
                en: <>Every scientific term is dotted-underlined: try <Term id="cmb" /> or <Term id="redshift" />. Hover with the mouse and a short definition, analogy and formula pop up.</>,
              })}
            </p>
            <p style={{ marginTop: 8, color: theme.color.inkSoft, fontFamily: theme.font.serif, fontSize: 16, lineHeight: 1.6 }}>
              {t(p(
                "Формулы выводятся вместе с легендой: каждая буква подписана понятным русским (или английским) текстом. Никакой магии — только математика.",
                "Equations come with a legend: each symbol is labelled in plain language. No magic — just math.",
              ))}
            </p>
          </Card>
          <Card padding={28} tone="aurora">
            <Badge tone="aurora" glyph="✸">{t(p("Главное обещание", "The big promise"))}</Badge>
            <h3 style={{ fontFamily: theme.font.serif, fontSize: 28, color: theme.color.ink, marginTop: 14 }}>
              {t(p("Ты ничего не сломаешь", "You can't break anything"))}
            </h3>
            <p style={{ marginTop: 10, color: theme.color.inkSoft, fontFamily: theme.font.serif, fontSize: 16, lineHeight: 1.6 }}>
              {t(p(
                "Все ползунки можно крутить как угодно. Случайно стёрли водород? Получили мёртвую Вселенную? Кнопка «Сброс» возвращает всё к параметрам Planck 2018.",
                "Every slider goes anywhere. Accidentally erased hydrogen? Got a dead Universe? The 'Reset' button restores Planck 2018 in one click.",
              ))}
            </p>
            <Callout variant="wow" title={p("Wow!", "Wow!")}>
              {t(p(
                "Ты можешь поставить параметры так, что во Вселенной не успеют образоваться звёзды. Это правда — учёные обсуждают такие альтернативные миры в серьёзных статьях.",
                "You can set parameters so that no stars ever form. That's a real thing — scientists debate such alternative universes in peer-reviewed papers.",
              ))}
            </Callout>
          </Card>
        </div>
      </section>

      {/* CTA */}
      <section style={{ maxWidth: 1100, margin: "80px auto 40px", padding: "0 24px" }}>
        <Card padding={48} tone="ember" glow style={{ textAlign: "center" }}>
          <Badge tone="ember" glyph="✺">{t(p("Готов(а)?", "Ready?"))}</Badge>
          <h2 style={{ fontFamily: theme.font.serif, fontSize: 40, marginTop: 14, color: theme.color.ink }}>
            {t(p("Чашка чая, наушники и самая большая история на свете.", "Pour a tea, put on headphones, and tell yourself the biggest story there is."))}
          </h2>
          <div style={{ display: "flex", gap: 12, justifyContent: "center", marginTop: 24, flexWrap: "wrap" }}>
            <Button variant="primary" size="lg" onClick={() => go({ name: "lessons", chapter: "intro" })} iconRight={<span>→</span>}>
              {t(p("Открыть главу 1", "Open Chapter 1"))}
            </Button>
            <Button variant="soft" size="lg" onClick={() => go({ name: "glossary" })}>
              {t(p("Сначала словарь", "Glossary first"))}
            </Button>
          </div>
        </Card>
      </section>

      <style>{`
        @media (max-width: 900px) {
          .home-hero { grid-template-columns: 1fr !important; }
          .home-howto { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}
