"use client";

import { useState } from "react";
import { SCHEMES, type Scheme, type SchemeStatus } from "@/lib/schemes";
import { pick, useLang, type Lang } from "@/lib/lang";
import LangToggle from "@/components/LangToggle";

type Filter = "all" | "state" | "central";

const FILTERS: { key: Filter; te: string; en: string }[] = [
  { key: "all", te: "అన్నీ", en: "All" },
  { key: "state", te: "తెలంగాణ", en: "State" },
  { key: "central", te: "కేంద్రం", en: "Central" },
];

// Honest status badges — never silently omit a scheme a farmer knows by name.
const STATUS: Record<SchemeStatus, { te: string; en: string; cls: string }> = {
  active: { te: "అందుబాటులో", en: "Active", cls: "bg-green-100 text-green-800" },
  verify: { te: "నిర్ధారించుకోండి", en: "Verify", cls: "bg-amber-100 text-amber-800" },
  at_risk: { te: "ఈ సీజన్ చూడండి", en: "At risk", cls: "bg-orange-100 text-orange-800" },
  closed: { te: "ముగిసింది", en: "Closed", cls: "bg-stone-200 text-stone-600" },
  suspended: { te: "నిలిపివేయబడింది", en: "Suspended", cls: "bg-red-100 text-red-800" },
};

function SchemeCard({ s, lang }: { s: Scheme; lang: Lang }) {
  const [open, setOpen] = useState(false);
  const badge = STATUS[s.status];
  const dimmed = s.status === "closed" || s.status === "suspended";
  return (
    <div className={`card p-4 ${dimmed ? "opacity-70" : ""}`}>
      <button onClick={() => setOpen((v) => !v)} className="flex w-full items-start justify-between gap-3 text-left">
        <div>
          <h2 className="text-lg font-semibold leading-tight">{pick(lang, s.name_te, s.name_en)}</h2>
          <p className="text-xs text-stone-500">{pick(lang, s.name_en, s.name_te)}</p>
        </div>
        <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${badge.cls}`}>
          {pick(lang, badge.te, badge.en)}
        </span>
      </button>

      <p className="mt-2 text-sm">
        {pick(lang, s.what_te, s.what_en)}
        <span className="mt-0.5 block text-xs text-stone-400">{pick(lang, s.what_en, s.what_te)}</span>
      </p>

      {open && (
        <div className="mt-3 space-y-3 border-t border-stone-100 pt-3 text-sm">
          <p>
            <span className="font-medium text-green-800">{pick(lang, "ఎవరికి", "Who")}: </span>
            {pick(lang, s.who_te, s.who_en)}
          </p>
          <p>
            <span className="font-medium text-green-800">{pick(lang, "ఎలా", "How")}: </span>
            {pick(lang, s.how_te, s.how_en)}
          </p>
          {s.honesty_te && (
            <p className="rounded-xl bg-amber-50 px-3 py-2 text-amber-900">
              ⚠️ {pick(lang, s.honesty_te, s.honesty_en ?? s.honesty_te)}
            </p>
          )}
        </div>
      )}

      <div className="mt-3 flex items-center justify-between">
        <button onClick={() => setOpen((v) => !v)} className="text-sm font-semibold text-green-700">
          {open ? pick(lang, "మూసివేయి ▲", "Close ▲") : pick(lang, "వివరాలు ▼", "Details ▼")}
        </button>
        <a
          href={s.url}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-xl bg-green-600 px-3 py-1.5 text-sm font-semibold text-white"
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
    <div className="mx-auto min-h-dvh max-w-md pb-28 text-stone-900">
      <header className="safe-top rounded-b-[2.25rem] bg-gradient-to-b from-green-700 to-green-800 px-5 pb-6 pt-4 text-white shadow-[var(--shadow-hero)]">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">🏛️ {pick(lang, "ప్రభుత్వ పథకాలు", "Govt schemes")}</h1>
            <p className="mt-0.5 text-sm text-green-100">
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
            className={`rounded-full border px-4 py-1.5 text-sm font-medium transition-colors ${
              filter === f.key
                ? "border-green-700 bg-green-700 text-white"
                : "border-stone-300 bg-white text-stone-700"
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
        <p className="px-1 pt-1 text-xs text-stone-400">
          {pick(
            lang,
            "మొత్తాలు, అర్హతలు ఏటా మారవచ్చు — అధికారిక వెబ్‌సైట్ లేదా మీ AEOని సంప్రదించండి. Rythu ఏమీ అమ్మదు.",
            "Amounts & eligibility change yearly — confirm on the official site or with your AEO. Rythu sells nothing.",
          )}
        </p>
      </div>
    </div>
  );
}
