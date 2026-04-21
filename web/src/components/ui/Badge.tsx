import React from "react";
import { theme } from "../../theme";

export function Badge({
  children,
  tone = "plasma",
  glyph,
  style,
}: {
  children: React.ReactNode;
  tone?: "plasma" | "starlight" | "aurora" | "nova" | "ember" | "muted";
  glyph?: string;
  style?: React.CSSProperties;
}) {
  const c =
    tone === "starlight" ? theme.color.starlight :
      tone === "aurora" ? theme.color.aurora :
        tone === "nova" ? theme.color.nova :
          tone === "ember" ? theme.color.ember :
            tone === "muted" ? theme.color.inkDim :
              theme.color.plasma;
  return (
    <span style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 6,
      padding: "3px 10px",
      borderRadius: 999,
      background: c + "22",
      color: c,
      fontFamily: theme.font.sans,
      fontSize: 12,
      fontWeight: 600,
      letterSpacing: 0.5,
      border: `1px solid ${c}40`,
      ...style,
    }}>
      {glyph && <span aria-hidden>{glyph}</span>}
      {children}
    </span>
  );
}
