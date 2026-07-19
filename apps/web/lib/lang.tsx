"use client";

import { createContext, useContext, useState, useSyncExternalStore, type ReactNode } from "react";
import { loadLang, saveLang } from "./prefs";

export type Lang = "te" | "en";

interface LangCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  toggle: () => void;
}

const Ctx = createContext<LangCtx>({ lang: "te", setLang: () => {}, toggle: () => {} });

// App-wide language. Persists to localStorage (via prefs) and is shared by every
// screen, so the toggle changes the whole app — not just the page you're on.
// Server + first client render are always "te" (Telugu-first) → no hydration mismatch;
// the saved choice is read right after mount.
export function LanguageProvider({ children }: { children: ReactNode }) {
  const saved = useSyncExternalStore(
    () => () => {},
    () => loadLang(),
    () => null,
  );
  const [override, setOverride] = useState<Lang | null>(null);
  const lang: Lang = override ?? saved ?? "te";

  const setLang = (l: Lang) => {
    saveLang(l);
    setOverride(l);
  };

  return (
    <Ctx.Provider value={{ lang, setLang, toggle: () => setLang(lang === "te" ? "en" : "te") }}>
      {children}
    </Ctx.Provider>
  );
}

export function useLang(): LangCtx {
  return useContext(Ctx);
}

/** Pick the string for the current language. */
export function pick(lang: Lang, te: string, en: string): string {
  return lang === "te" ? te : en;
}
