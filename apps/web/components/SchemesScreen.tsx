"use client";

import { useId, useState } from "react";
import { SCHEMES, type Scheme, type SchemeStatus } from "@/lib/schemes";
import { pick, useLang, type Lang } from "@/lib/lang";
import LangToggle from "@/components/LangToggle";
import Icon from "@/components/ui/Icon";

type Filter = "all" | "state" | "central";

const FILTERS: { key: Filter; te: string; en: string }[] = [
  { key: "all", te: "అన్నీ", en: "All" },
  { key: "state", te: "తెలంగాణ", en: "State" },
  { key: "central", te: "కేంద్రం", en: "Central" },
];

// Honest status badges — never silently omit a scheme a farmer knows by name.
const STATUS: Record<SchemeStatus, { te: string; en: string; cls: string }> = {
  active: { te: "అందుబాటులో", en: "Active", cls: "bg-success-bg text-success-fg" },
  verify: { te: "నిర్ధారించుకోండి", en: "Verify", cls: "bg-caution-bg text-caution-fg" },
  at_risk: { te: "ఈ సీజన్ చూడండి", en: "At risk", cls: "bg-warn-bg text-warn-fg" },
  closed: { te: "ముగిసింది", en: "Closed", cls: "bg-neutral-bg text-neutral-fg" },
  suspended: { te: "నిలిపివేయబడింది", en: "Suspended", cls: "bg-act-bg text-act-fg" },
};

function SchemeCard({ s, lang }: { s: Scheme; lang: Lang }) {
  const [open, setOpen] = useState(false);
  const detailsId = useId();
  const badge = STATUS[s.status];
  const dimmed = s.status === "closed" || s.status === "suspended";
  return (
    <div className={`card p-4 ${dimmed ? "bg-surface-sunken! shadow-none!" : ""}`}>
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={detailsId}
        className="flex w-full items-start justify-between gap-3 text-left"
      >
        <div>
          <h2 className="text-lg font-semibold leading-snug">{pick(lang, s.name_te, s.name_en)}</h2>
          <p className="text-caption text-ink-secondary">{pick(lang, s.name_en, s.name_te)}</p>
        </div>
        <span className={`shrink-0 rounded-full px-2.5 py-1 text-caption font-medium ${badge.cls}`}>
          {pick(lang, badge.te, badge.en)}
        </span>
      </button>

      <p className="mt-2 text-sm">
        {pick(lang, s.what_te, s.what_en)}
        <span className="mt-0.5 block text-caption text-ink-secondary">{pick(lang, s.what_en, s.what_te)}</span>
      </p>

      {open && (
        <div id={detailsId} className="mt-3 space-y-3 border-t border-line pt-3 text-sm">
          <p>
            <span className="font-medium text-brand-ink">{pick(lang, "ఎవరికి", "Who")}: </span>
            {pick(lang, s.who_te, s.who_en)}
          </p>
          <p>
            <span className="font-medium text-brand-ink">{pick(lang, "ఎలా", "How")}: </span>
            {pick(lang, s.how_te, s.how_en)}
          </p>
          {s.honesty_te && (
            <p className="rounded-xl bg-caution-bg px-3 py-2 text-caution-fg">
              ⚠️ {pick(lang, s.honesty_te, s.honesty_en ?? s.honesty_te)}
            </p>
          )}
        </div>
      )}

      <div className="mt-3 flex items-center justify-between">
        <button
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls={detailsId}
          className="tap -ml-2 flex items-center gap-1 px-2 text-sm font-semibold text-brand-ink"
        >
          {open ? pick(lang, "మూసివేయి", "Close") : pick(lang, "వివరాలు", "Details")}
          <Icon name="chevron-down" size={18} className={open ? "rotate-180" : ""} />
        </button>
        <a
          href={s.url}
          target="_blank"
          rel="noopener noreferrer"
          className="tap flex items-center rounded-xl bg-brand px-4 py-1.5 text-sm font-semibold text-white"
        >
          {pick(lang, "అధికారిక సైట్ →", "Official site →")}
        </a>
      </div>
    </div>
  );
}

export default function SchemesScreen() {
  const { lang } = useLang();
  const [filter, setFilter] = useState<Filter>("all");
  const shown = [...SCHEMES]
    .filter((s) => filter === "all" || s.level === filter)
    .sort((a, b) => b.priority - a.priority);

  return (
    <main className="mx-auto min-h-dvh w-full max-w-md pb-28 text-ink">
      <header className="safe-top rounded-b-[2.25rem] bg-gradient-to-b from-hero-brand-from to-hero-brand-to px-5 pb-6 pt-4 text-white shadow-hero">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">🏛️ {pick(lang, "ప్రభుత్వ పథకాలు", "Govt schemes")}</h1>
            <p className="mt-0.5 text-sm text-white/90">
              {pick(lang, "రైతులకు ఉపయోగపడే పథకాలు", "Benefits for farmers")}
            </p>
          </div>
          <LangToggle light />
        </div>
      </header>

      {/* filter tabs */}
      <div className="flex gap-2 px-4 pt-5 pb-2">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            aria-pressed={filter === f.key}
            className={`tap rounded-full border px-4 py-1.5 text-sm font-medium transition-colors ${
              filter === f.key
                ? "border-brand bg-brand text-white"
                : "border-line-strong bg-surface-raised text-ink"
            }`}
          >
            {pick(lang, f.te, f.en)}
          </button>
        ))}
      </div>

      <div className="space-y-3 p-4 pt-1">
        {shown.map((s) => (
          <SchemeCard key={s.key} s={s} lang={lang} />
        ))}
        <p className="px-1 pt-1 text-caption text-ink-secondary">
          {pick(
            lang,
            "మొత్తాలు, అర్హతలు ఏటా మారవచ్చు — అధికారిక వెబ్‌సైట్ లేదా మీ AEOని సంప్రదించండి. Rythu ఏమీ అమ్మదు.",
            "Amounts & eligibility change yearly — confirm on the official site or with your AEO. Rythu sells nothing.",
          )}
        </p>
      </div>
    </main>
  );
}
