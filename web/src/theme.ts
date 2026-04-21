/**
 * Cosmic Academy design tokens.
 *
 * Color palette evokes deep space (indigo/violet base) with warm accents
 * (amber/gold) reminiscent of starlight and ancient maps. Typography pairs
 * a serif "schoolbook" face for narrative reading with a clean sans for UI
 * and a monospace for measured numbers — matching the way physics textbooks
 * differentiate prose, controls, and equations.
 */

export const theme = {
  color: {
    // Background layers
    voidDeep: "#05060f",
    voidMid: "#0a0e22",
    voidSoft: "#111634",
    nebula: "#1a1147",

    // Surfaces
    parchment: "#fdf6e3",
    parchmentDim: "#f5edd6",
    surface: "#141a3a",
    surfaceRaised: "#1d2554",
    surfaceGlow: "rgba(120, 90, 240, 0.10)",

    // Text
    ink: "#e8ecff",
    inkSoft: "#a9b1d6",
    inkDim: "#6f7aa8",
    inkOnLight: "#1c1530",
    inkOnLightSoft: "#5a4f7a",

    // Accents
    starlight: "#ffd56b",
    starlightSoft: "#ffe9a8",
    nova: "#ff7ac6",
    plasma: "#5ee2ff",
    quantum: "#9b8cff",
    aurora: "#7afcb1",
    ember: "#ff8b5e",

    // Semantics
    info: "#5ee2ff",
    success: "#7afcb1",
    warning: "#ffd56b",
    danger: "#ff7a8a",

    // Borders
    line: "rgba(159, 144, 240, 0.18)",
    lineStrong: "rgba(159, 144, 240, 0.35)",
  },
  font: {
    serif: "'Iowan Old Style', 'Palatino Linotype', 'Cambria', 'Georgia', serif",
    sans: "'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif",
    mono: "'JetBrains Mono', 'Fira Code', ui-monospace, monospace",
    math: "'Cambria Math', 'STIX Two Math', 'Latin Modern Math', 'Times New Roman', serif",
  },
  radius: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 18,
    xl: 28,
    pill: 999,
  },
  shadow: {
    soft: "0 6px 24px rgba(8, 4, 36, 0.45)",
    hard: "0 18px 48px rgba(8, 4, 36, 0.6)",
    starlit:
      "0 0 0 1px rgba(159, 144, 240, 0.25), 0 12px 36px rgba(78, 52, 200, 0.35)",
    aurora:
      "0 0 0 1px rgba(122, 252, 177, 0.35), 0 0 24px rgba(122, 252, 177, 0.25)",
  },
  gradient: {
    cosmos:
      "radial-gradient(1200px 800px at 20% -10%, #2a1b6c 0%, transparent 60%)," +
      "radial-gradient(1000px 700px at 90% 10%, #4a1d6c 0%, transparent 55%)," +
      "radial-gradient(900px 700px at 50% 110%, #1a3a8c 0%, transparent 55%)," +
      "linear-gradient(180deg, #05060f 0%, #0a0e22 100%)",
    chapter:
      "linear-gradient(135deg, rgba(155, 140, 255, 0.18), rgba(94, 226, 255, 0.10))",
    starlight:
      "linear-gradient(135deg, #ffd56b 0%, #ff8b5e 60%, #ff7ac6 100%)",
    plasma:
      "linear-gradient(135deg, #5ee2ff 0%, #9b8cff 60%, #ff7ac6 100%)",
    aurora:
      "linear-gradient(135deg, #7afcb1 0%, #5ee2ff 60%, #9b8cff 100%)",
    parchment:
      "linear-gradient(180deg, #fdf6e3 0%, #f0e7c8 100%)",
  },
  spacing: (n: number) => n * 4,
  motion: {
    snap: "120ms cubic-bezier(.2,.8,.2,1)",
    base: "220ms cubic-bezier(.2,.8,.2,1)",
    slow: "480ms cubic-bezier(.2,.8,.2,1)",
  },
  zIndex: {
    background: 0,
    base: 10,
    raised: 100,
    overlay: 1000,
    tooltip: 2000,
    modal: 3000,
  },
} as const;

export type Theme = typeof theme;
