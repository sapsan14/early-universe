import React from "react";
import { theme } from "../../theme";
import { useT, p } from "../../i18n";

export function Footer() {
  const { t } = useT();
  return (
    <footer style={{
      marginTop: 80,
      padding: "32px 24px 48px",
      borderTop: `1px solid ${theme.color.line}`,
      background: "linear-gradient(180deg, transparent, rgba(5, 6, 15, 0.6))",
      position: "relative",
      zIndex: theme.zIndex.base,
    }}>
      <div style={{
        maxWidth: 1280, margin: "0 auto",
        display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: 32, color: theme.color.inkSoft, fontSize: 14, lineHeight: 1.7,
      }}>
        <div>
          <div style={{ fontFamily: theme.font.serif, fontSize: 20, color: theme.color.starlight, marginBottom: 8 }}>
            Cosmic Academy
          </div>
          <p style={{ color: theme.color.inkDim, fontSize: 13 }}>
            {t(p(
              "Открытый учебник космологии для школьников и любопытных. Двигай слайдеры, читай главы, задавай вопросы Вселенной.",
              "An open cosmology textbook for high-schoolers and the curious. Slide the sliders, read the chapters, ask the Universe questions.",
            ))}
          </p>
        </div>
        <div>
          <div style={{ color: theme.color.ink, marginBottom: 6, fontWeight: 600 }}>
            {t(p("Откуда числа?", "Where do the numbers come from?"))}
          </div>
          <p style={{ fontSize: 12.5, color: theme.color.inkDim }}>
            {t(p(
              "Эталонные параметры берутся из миссии Planck (ESA, 2018). Когда Python-API подключён, расчёты идут на полных уравнениях; в офлайн-режиме мы используем точные приближения.",
              "Reference parameters come from the Planck mission (ESA, 2018). When the Python API is connected, full equations are solved; offline we fall back to accurate approximations.",
            ))}
          </p>
        </div>
        <div>
          <div style={{ color: theme.color.ink, marginBottom: 6, fontWeight: 600 }}>
            {t(p("Как читать", "How to read"))}
          </div>
          <ul style={{ listStyle: "none", padding: 0, fontSize: 13 }}>
            <li>{t(p("Подчёркнутые слова", "Dotted-underlined words"))} → {t(p("определение в словаре", "open a glossary card"))}</li>
            <li>{t(p("Жёлтые формулы", "Gold formulas"))} → {t(p("подробный разбор символов", "step-by-step legend"))}</li>
            <li>{t(p("«Wow!» блоки", "'Wow!' boxes"))} → {t(p("самое удивительное в главе", "the chapter's mind-blowers"))}</li>
          </ul>
        </div>
        <div>
          <div style={{ color: theme.color.ink, marginBottom: 6, fontWeight: 600 }}>
            {t(p("Безопасное любопытство", "Safe curiosity"))}
          </div>
          <p style={{ fontSize: 12.5, color: theme.color.inkDim }}>
            {t(p(
              "Здесь нельзя ничего сломать. Двигай ползунки смело — кнопкой «Сброс» всегда можно вернуться к Planck 2018.",
              "Nothing here can break. Slide freely — 'Reset to Planck 2018' is always one click away.",
            ))}
          </p>
        </div>
      </div>
      <div style={{
        maxWidth: 1280, margin: "32px auto 0",
        textAlign: "center", color: theme.color.inkDim, fontSize: 12,
      }}>
        ✦ {t(p("Сделано с любовью к Вселенной", "Made with love for the Universe"))} ✦
      </div>
    </footer>
  );
}
