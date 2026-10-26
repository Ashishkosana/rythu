"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLang } from "@/lib/lang";
import Icon from "@/components/ui/Icon";
import type { IconName } from "@/components/ui/icon-nodes";

// Bottom tab bar. Big tap targets + icons for low-literacy users, safe-area padding
// so it clears the phone's home indicator when installed. Labels follow the app language.
// Icons are SVG (same shape on every phone); trailing slashes match the static export's URLs.
const TABS: readonly { href: string; icon: IconName; te: string; en: string }[] = [
  { href: "/", icon: "cloud-sun", te: "వాతావరణం", en: "Weather" },
  { href: "/crops/", icon: "sprout", te: "పంటలు", en: "Crops" },
  { href: "/schemes/", icon: "landmark", te: "పథకాలు", en: "Schemes" },
  { href: "/account/", icon: "user", te: "ఖాతా", en: "Account" },
];

export default function BottomNav() {
  const pathname = usePathname();
  const { lang } = useLang();
  return (
    <nav className="safe-bottom fixed inset-x-0 bottom-0 z-30 mx-auto flex max-w-md justify-around border-t border-line/80 bg-surface-raised/85 backdrop-blur-xl">
      {TABS.map((t) => {
        const active = pathname === t.href || pathname === t.href.replace(/\/$/, "");
        return (
          <Link
            key={t.href}
            href={t.href}
            aria-current={active ? "page" : undefined}
            className="flex flex-1 flex-col items-center gap-1 pt-2.5 pb-2"
          >
            <span
              className={`flex h-9 w-16 items-center justify-center rounded-2xl transition-colors ${
                active ? "bg-brand-soft text-brand-ink" : "text-ink-secondary"
              }`}
            >
              <Icon name={t.icon} size={24} />
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
