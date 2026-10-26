"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLang } from "@/lib/lang";

// Bottom tab bar. Big tap targets + icons for low-literacy users, safe-area padding
// so it clears the phone's home indicator when installed. Labels follow the app language.
const TABS = [
  { href: "/", icon: "🌦️", te: "వాతావరణం", en: "Weather" },
  { href: "/crops", icon: "🌱", te: "పంటలు", en: "Crops" },
  { href: "/schemes", icon: "🏛️", te: "పథకాలు", en: "Schemes" },
  { href: "/account", icon: "👤", te: "ఖాతా", en: "Account" },
] as const;

export default function BottomNav() {
  const pathname = usePathname();
  const { lang } = useLang();
  return (
    <nav className="safe-bottom fixed inset-x-0 bottom-0 z-30 mx-auto flex max-w-md justify-around border-t border-line/80 bg-surface-raised/85 backdrop-blur-xl">
      {TABS.map((t) => {
        const active = pathname === t.href;
        return (
          <Link
            key={t.href}
            href={t.href}
            aria-current={active ? "page" : undefined}
            className="flex flex-1 flex-col items-center gap-1 pt-2.5 pb-2"
          >
            <span
              className={`flex h-9 w-16 items-center justify-center rounded-2xl text-2xl transition-all ${
                active ? "scale-105 bg-brand-soft" : "opacity-60"
              }`}
              aria-hidden
            >
              {t.icon}
            </span>
            <span className={`text-caption ${active ? "font-bold text-brand-ink" : "text-ink-secondary"}`}>
              {lang === "te" ? t.te : t.en}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
