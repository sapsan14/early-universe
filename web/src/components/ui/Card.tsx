import React from "react";
import { theme } from "../../theme";

/**
 * Glassy "starlit" card. The optional `tone` colors the gradient border;
 * `glow` adds a soft halo. Used as the building block of every panel.
 */
export function Card({
  tone = "default",
  glow = false,
  padding = 24,
  style,
  children,
  onClick,
  as = "div",
}: {
  tone?: "default" | "starlight" | "plasma" | "aurora" | "nova" | "ember";
  glow?: boolean;
  padding?: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
  onClick?: () => void;
  as?: "div" | "button" | "a";
}) {
  const Tag = as as any;
  const accent =
    tone === "starlight" ? theme.color.starlight :
      tone === "plasma" ? theme.color.plasma :
        tone === "aurora" ? theme.color.aurora :
          tone === "nova" ? theme.color.nova :
            tone === "ember" ? theme.color.ember :
              theme.color.quantum;
  return (
    <Tag
      onClick={onClick}
      style={{
        position: "relative",
        padding,
        borderRadius: theme.radius.lg,
        background:
          "linear-gradient(180deg, rgba(20,26,58,0.85), rgba(10,14,34,0.85))",
        border: `1px solid ${theme.color.line}`,
        backdropFilter: "blur(8px)",
        WebkitBackdropFilter: "blur(8px)",
        color: theme.color.ink,
        textAlign: "left",
        cursor: onClick ? "pointer" : undefined,
        boxShadow: glow
          ? `0 0 0 1px ${accent}33, 0 18px 60px ${accent}1a`
          : theme.shadow.soft,
        transition: theme.motion.base,
        ...style,
      }}
    >
      <div aria-hidden style={{
        position: "absolute",
        inset: 0,
        borderRadius: "inherit",
        padding: 1,
        background: `linear-gradient(135deg, ${accent}66, transparent 60%)`,
        WebkitMask:
          "linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0)",
        WebkitMaskComposite: "xor",
        maskComposite: "exclude",
        pointerEvents: "none",
      }} />
      <div style={{ position: "relative" }}>{children}</div>
    </Tag>
  );
}
