import React from "react";
import { theme } from "../../theme";
import { useT } from "../../i18n";
import type { Phrase } from "../../i18n";

export function SectionTitle({
  eyebrow,
  title,
  subtitle,
  align = "left",
}: {
  eyebrow?: Phrase;
  title: Phrase;
  subtitle?: Phrase;
  align?: "left" | "center";
}) {
  const { t } = useT();
  return (
    <div style={{ textAlign: align, margin: "32px 0 24px" }}>
      {eyebrow && (
        <div style={{
          display: "inline-block",
          fontFamily: theme.font.sans,
          fontSize: 12,
          letterSpacing: 3,
          textTransform: "uppercase",
          color: theme.color.starlight,
          padding: "4px 14px",
          borderRadius: 999,
          background: "rgba(255, 213, 107, 0.12)",
          border: "1px solid rgba(255, 213, 107, 0.35)",
          marginBottom: 12,
        }}>
          {t(eyebrow)}
        </div>
      )}
      <h2 style={{
        fontFamily: theme.font.serif,
        fontSize: "clamp(28px, 4vw, 44px)",
        lineHeight: 1.15,
        margin: 0,
        color: theme.color.ink,
        fontWeight: 700,
      }}>
        {t(title)}
      </h2>
      {subtitle && (
        <p style={{
          fontFamily: theme.font.serif,
          fontSize: 18,
          color: theme.color.inkSoft,
          marginTop: 10,
          maxWidth: 720,
          marginLeft: align === "center" ? "auto" : 0,
          marginRight: align === "center" ? "auto" : 0,
          lineHeight: 1.6,
        }}>
          {t(subtitle)}
        </p>
      )}
    </div>
  );
}
