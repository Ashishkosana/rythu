"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// Telugu-first bottom tab bar. Big tap targets + icons for low-literacy users,
// safe-area padding so it clears the phone's home indicator when installed.
const TABS = [
  { href: "/", icon: "🌦️", te: "వాతావరణం" },
  { href: "/crops", icon: "🌱", te: "పంటలు" },
  { href: "/schemes", icon: "🏛️", te: "పథకాలు" },
  { href: "/account", icon: "👤", te: "ఖాతా" },
] as const;

export default function BottomNav() {
  const pathname = usePathname();
  return (
    <nav className="safe-bottom fixed inset-x-0 bottom-0 z-30 mx-auto flex max-w-md justify-around border-t border-stone-200/80 bg-white/85 backdrop-blur-xl">
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
                active ? "scale-105 bg-green-100" : "opacity-60"
              }`}
              aria-hidden
            >
              {t.icon}
            </span>
            <span className={`text-[13px] ${active ? "font-bold text-green-800" : "text-stone-500"}`}>
              {t.te}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
