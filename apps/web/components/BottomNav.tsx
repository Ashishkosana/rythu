"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// Telugu-first bottom tab bar. Big tap targets + icons for low-literacy users.
const TABS = [
  { href: "/", icon: "🌦️", te: "వాతావరణం", en: "Weather" },
  { href: "/crops", icon: "🌱", te: "పంటలు", en: "Crops" },
  { href: "/schemes", icon: "🏛️", te: "పథకాలు", en: "Schemes" },
] as const;

export default function BottomNav() {
  const pathname = usePathname();
  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 mx-auto flex max-w-md justify-around border-t border-slate-200 bg-white/95 backdrop-blur">
      {TABS.map((t) => {
        const active = pathname === t.href;
        return (
          <Link
            key={t.href}
            href={t.href}
            aria-current={active ? "page" : undefined}
            className={`flex flex-1 flex-col items-center gap-0.5 py-2 text-xs ${
              active ? "text-green-700" : "text-slate-500"
            }`}
          >
            <span className="text-xl" aria-hidden>
              {t.icon}
            </span>
            <span className={active ? "font-bold" : ""}>{t.te}</span>
          </Link>
        );
      })}
    </nav>
  );
}
