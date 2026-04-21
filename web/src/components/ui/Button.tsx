import React from "react";
import { theme } from "../../theme";

type Variant = "primary" | "ghost" | "soft" | "outline";
type Size = "sm" | "md" | "lg";

export function Button({
  variant = "primary",
  size = "md",
  iconLeft,
  iconRight,
  full,
  children,
  ...rest
}: {
  variant?: Variant;
  size?: Size;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
  full?: boolean;
  children: React.ReactNode;
} & Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "size">) {
  const padding =
    size === "lg" ? "14px 24px" :
      size === "sm" ? "6px 12px" : "10px 18px";
  const fontSize = size === "lg" ? 16 : size === "sm" ? 13 : 14;
  let bg = "";
  let color = "#fff";
  let border = "1px solid transparent";
  switch (variant) {
    case "primary":
      bg = theme.gradient.starlight;
      color = "#1c1530";
      break;
    case "ghost":
      bg = "transparent";
      color = theme.color.ink;
      break;
    case "soft":
      bg = "rgba(155, 140, 255, 0.14)";
      color = theme.color.ink;
      border = `1px solid ${theme.color.line}`;
      break;
    case "outline":
      bg = "transparent";
      color = theme.color.starlight;
      border = `1px solid ${theme.color.starlight}`;
      break;
  }
  return (
    <button
      {...rest}
      style={{
        padding,
        fontSize,
        fontFamily: theme.font.sans,
        fontWeight: variant === "primary" ? 700 : 600,
        background: bg,
        color,
        border,
        borderRadius: theme.radius.pill,
        cursor: "pointer",
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        width: full ? "100%" : undefined,
        justifyContent: full ? "center" : undefined,
        boxShadow:
          variant === "primary"
            ? "0 8px 24px rgba(255, 138, 94, 0.35)"
            : undefined,
        transition: theme.motion.snap,
        ...(rest.style ?? {}),
      }}
    >
      {iconLeft}
      {children}
      {iconRight}
    </button>
  );
}
