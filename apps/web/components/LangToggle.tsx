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
          ? "h-8 rounded-full bg-white px-3 text-sm font-bold text-green-800"
          : "h-8 rounded-full border border-stone-300 bg-white px-3 text-sm font-bold text-green-800"
      }
    >
      {lang === "te" ? "English" : "తెలుగు"}
    </button>
  );
}
