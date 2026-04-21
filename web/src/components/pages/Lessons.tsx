import React from "react";
import { theme } from "../../theme";
import { useT, p } from "../../i18n";
import { useRouter } from "../../router";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { CHAPTERS, chapterById } from "../../lessons";
import { ChapterIntro } from "../lessons/ChapterIntro";
import { ChapterBigBang } from "../lessons/ChapterBigBang";
import { ChapterInflation } from "../lessons/ChapterInflation";
import { ChapterBBN } from "../lessons/ChapterBBN";
import { ChapterCMB } from "../lessons/ChapterCMB";
import { ChapterDawn } from "../lessons/ChapterDawn";
import { ChapterIngredients } from "../lessons/ChapterIngredients";
import { ChapterPlay } from "../lessons/ChapterPlay";

const RENDERERS: Record<string, React.FC> = {
  intro: ChapterIntro,
  "big-bang": ChapterBigBang,
  inflation: ChapterInflation,
  bbn: ChapterBBN,
  cmb: ChapterCMB,
  dawn: ChapterDawn,
  ingredients: ChapterIngredients,
  play: ChapterPlay,
};

export function Lessons({ chapterId }: { chapterId?: string }) {
  const { t, pick } = useT();
  const { go } = useRouter();

  if (!chapterId) {
    return (
      <div style={{ maxWidth: 1280, margin: "0 auto", padding: "40px 24px 0" }}>
        <Badge tone="starlight" glyph="📖">{t(p("Программа", "Curriculum"))}</Badge>
        <h1 style={{ fontFamily: theme.font.serif, fontSize: 48, marginTop: 12, color: theme.color.ink }}>
          {t(p("Восемь глав космологии", "Eight chapters of cosmology"))}
        </h1>
        <p style={{ color: theme.color.inkSoft, fontSize: 18, fontFamily: theme.font.serif, maxWidth: 720, marginTop: 12 }}>
          {t(p(
            "Дорогу осилит идущий. Каждая глава занимает 10–18 минут чтения и заканчивается лабораторией.",
            "A journey of a thousand parsecs starts with one chapter. Each takes 10–18 minutes and ends in a hands-on lab.",
          ))}
        </p>
        <div style={{
          marginTop: 36,
          display: "grid", gap: 16,
          gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
        }}>
          {CHAPTERS.map((ch) => (
            <Card key={ch.id} as="button" onClick={() => go({ name: "lessons", chapter: ch.id })} padding={22} tone="aurora">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 14,
                  background: `linear-gradient(135deg, ${ch.color}, ${ch.color}66)`,
                  display: "grid", placeItems: "center", fontSize: 24,
                  boxShadow: `0 6px 18px ${ch.color}55`,
                }}>{ch.glyph}</div>
                <Badge tone="muted">{t(p("Глава", "Chapter"))} {ch.number}</Badge>
              </div>
              <div style={{ fontFamily: theme.font.serif, fontSize: 22, color: theme.color.ink, marginBottom: 6 }}>
                {t(ch.title)}
              </div>
              <p style={{ color: theme.color.inkSoft, fontSize: 14, fontFamily: theme.font.serif }}>
                {t(ch.subtitle)}
              </p>
              <ul style={{ marginTop: 12, paddingLeft: 0, listStyle: "none", color: theme.color.inkSoft, fontSize: 13 }}>
                {ch.highlights.map((h, i) => (
                  <li key={i} style={{ marginBottom: 4 }}>
                    <span style={{ color: ch.color, marginRight: 6 }}>✦</span>{t(h)}
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const meta = chapterById(chapterId);
  const Renderer = RENDERERS[chapterId];
  if (!meta || !Renderer) {
    return (
      <div style={{ maxWidth: 720, margin: "100px auto", padding: 24, textAlign: "center" }}>
        <h2 style={{ color: theme.color.danger }}>{t(p("Глава не найдена", "Chapter not found"))}</h2>
        <Button variant="soft" onClick={() => go({ name: "lessons" })}>
          {t(p("К списку глав", "Back to chapter list"))}
        </Button>
      </div>
    );
  }

  const idx = CHAPTERS.findIndex((c) => c.id === meta.id);
  const prev = CHAPTERS[idx - 1];
  const next = CHAPTERS[idx + 1];

  return (
    <div style={{ maxWidth: 1280, margin: "0 auto", padding: "20px 24px 0" }}>
      {/* Progress bar */}
      <div style={{
        position: "sticky", top: 60, zIndex: 50,
        background: "linear-gradient(180deg, rgba(5,6,15,0.92), rgba(5,6,15,0.5))",
        backdropFilter: "blur(8px)",
        padding: "10px 0", marginBottom: 12,
      }}>
        <div style={{ display: "flex", gap: 4 }}>
          {CHAPTERS.map((c) => (
            <button
              key={c.id}
              onClick={() => go({ name: "lessons", chapter: c.id })}
              style={{
                flex: 1,
                height: 6, borderRadius: 999, border: "none",
                background: c.id === meta.id ? c.color : (idx >= CHAPTERS.indexOf(c) ? c.color + "55" : "rgba(255,255,255,0.06)"),
                cursor: "pointer", transition: theme.motion.snap,
              }}
              title={pick(c.title)}
            />
          ))}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontSize: 12, color: theme.color.inkDim }}>
          <span>{t(p("Глава", "Chapter"))} {meta.number} / {CHAPTERS.length}</span>
          <span>⏱ {t(meta.duration)}</span>
        </div>
      </div>

      {/* Chapter header */}
      <div style={{ display: "grid", gap: 18, gridTemplateColumns: "auto 1fr", alignItems: "center", marginTop: 12, marginBottom: 32 }}>
        <div style={{
          width: 80, height: 80, borderRadius: 20,
          background: `linear-gradient(135deg, ${meta.color}, ${meta.color}55)`,
          display: "grid", placeItems: "center",
          fontSize: 40, boxShadow: `0 12px 36px ${meta.color}55`,
        }}>{meta.glyph}</div>
        <div>
          <Badge tone="starlight">{t(p("Глава", "Chapter"))} {meta.number}</Badge>
          <h1 style={{ fontFamily: theme.font.serif, fontSize: "clamp(34px, 5vw, 52px)", color: theme.color.ink, lineHeight: 1.1, margin: "8px 0 6px" }}>
            {t(meta.title)}
          </h1>
          <p style={{ fontFamily: theme.font.serif, color: theme.color.inkSoft, fontSize: 19 }}>
            {t(meta.subtitle)}
          </p>
        </div>
      </div>

      {/* Chapter body */}
      <article style={{ maxWidth: 880, margin: "0 auto", fontFamily: theme.font.serif, fontSize: 18, lineHeight: 1.75, color: theme.color.ink }}>
        <Renderer />
      </article>

      {/* Pager */}
      <div style={{ maxWidth: 880, margin: "60px auto 0", display: "flex", gap: 12, justifyContent: "space-between", flexWrap: "wrap" }}>
        {prev ? (
          <Button variant="soft" onClick={() => go({ name: "lessons", chapter: prev.id })} iconLeft={<span>←</span>}>
            {t(prev.title)}
          </Button>
        ) : <span />}
        {next ? (
          <Button variant="primary" onClick={() => go({ name: "lessons", chapter: next.id })} iconRight={<span>→</span>}>
            {t(next.title)}
          </Button>
        ) : (
          <Button variant="primary" onClick={() => go({ name: "lab" })} iconRight={<span>✺</span>}>
            {t(p("В лабораторию", "Off to the Lab"))}
          </Button>
        )}
      </div>
    </div>
  );
}
