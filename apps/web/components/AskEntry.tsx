"use client";

// The way into Ask Rythu (S17) from the screens where questions come up.

import Link from "next/link";
import Icon from "@/components/ui/Icon";
import { pick, useLang } from "@/lib/lang";

export default function AskEntry() {
  const { lang } = useLang();
  return (
    <Link href="/ask/" className="card tap flex items-center gap-3 p-4">
      <span className="text-2xl" aria-hidden>🙋</span>
      <span className="flex-1">
        <span className="block text-lg font-bold leading-snug">{pick(lang, "రైతు ప్రశ్న", "Ask Rythu")}</span>
        <span className="block text-caption text-ink-secondary">
          {pick(lang, "టైప్ చేయండి లేదా మాట్లాడండి — Rythu సమాచారం నుంచే సమాధానం", "Type or speak — answered only from Rythu's information")}
        </span>
      </span>
      <Icon name="chevron-down" size={20} className="-rotate-90 text-ink-secondary" />
    </Link>
  );
}
