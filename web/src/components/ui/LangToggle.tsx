import React from "react";
import { theme } from "../../theme";
import { useT } from "../../i18n";

export function LangToggle() {
  const { lang, setLang } = useT();
  return (
    <div role="group" aria-label="language" style={{
      display: "inline-flex",
      padding: 3,
      borderRadius: 999,
      background: "rgba(155, 140, 255, 0.12)",
      border: `1px solid ${theme.color.line}`,
      gap: 2,
    }}>
      {(["ru", "en"] as const).map((l) => (
        <button
          key={l}
          onClick={() => setLang(l)}
          style={{
            padding: "4px 12px",
            borderRadius: 999,
            border: "none",
            background: lang === l ? theme.gradient.starlight : "transparent",
            color: lang === l ? "#1c1530" : theme.color.inkSoft,
            fontWeight: 700,
            fontSize: 12,
            cursor: "pointer",
            letterSpacing: 1,
            textTransform: "uppercase",
            transition: theme.motion.snap,
          }}
        >{l}</button>
      ))}
    </div>
  );
}
