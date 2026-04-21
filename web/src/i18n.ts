/**
 * Tiny bilingual store (RU / EN) for the Cosmic Academy.
 *
 * Every visible string lives here twice. Components consume it via the `useT`
 * hook, which returns a translator function and lets users flip language at
 * runtime — both languages stay shipped in the bundle so the swap is instant.
 */

import React, { createContext, useContext, useMemo, useState, useEffect } from "react";

export type Lang = "ru" | "en";

export type Phrase = { ru: string; en: string };

const STORAGE_KEY = "cosmic-academy:lang";

interface I18nContextValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (p: Phrase) => string;
  /** Pick the language-specific value from any object {ru, en}. */
  pick: <T>(obj: { ru: T; en: T }) => T;
}

const Ctx = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    if (typeof window === "undefined") return "ru";
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "ru" || stored === "en") return stored;
    const navLang = (navigator.language || "ru").toLowerCase();
    return navLang.startsWith("ru") ? "ru" : "en";
  });

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, lang);
      document.documentElement.lang = lang;
    }
  }, [lang]);

  const value = useMemo<I18nContextValue>(() => ({
    lang,
    setLang: setLangState,
    t: (p: Phrase) => p[lang],
    pick: <T,>(obj: { ru: T; en: T }) => obj[lang],
  }), [lang]);

  return React.createElement(Ctx.Provider, { value }, children);
}

export function useT() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useT must be used inside <I18nProvider>");
  return ctx;
}

/** Inline shortcut: build a Phrase. */
export function p(ru: string, en: string): Phrase {
  return { ru, en };
}
