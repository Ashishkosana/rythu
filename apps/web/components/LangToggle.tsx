"use client";

import { useLang } from "@/lib/lang";

// The app-wide language switch. Placed in every screen header so a farmer can flip
// Telugu ⇄ English from anywhere, and it changes the whole app at once.
// `light` = for use on a colored/green header (white pill).
export default function LangToggle({ light = false }: { light?: boolean }) {
  const { lang, toggle } = useLang();
  return (
    <button
      onClick={toggle}
      aria-label={lang === "te" ? "Switch to English" : "తెలుగులోకి మార్చు"}
      className={
        light
          ? "hit-48 h-8 rounded-full bg-surface-raised px-3 text-sm font-bold text-brand-ink"
          : "hit-48 h-8 rounded-full border border-line-strong bg-surface-raised px-3 text-sm font-bold text-brand-ink"
      }
    >
      {lang === "te" ? "English" : "తెలుగు"}
    </button>
  );
}
