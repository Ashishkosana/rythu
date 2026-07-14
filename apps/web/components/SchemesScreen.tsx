"use client";

import { useState } from "react";
import { SCHEMES, type Scheme, type SchemeStatus } from "@/lib/schemes";

type Filter = "all" | "state" | "central";

const FILTERS: { key: Filter; te: string }[] = [
  { key: "all", te: "అన్నీ" },
  { key: "state", te: "తెలంగాణ" },
  { key: "central", te: "కేంద్రం" },
];

// Honest status badges — the whole point of the research: never silently omit a
// scheme a farmer knows by name; show its real state instead.
const STATUS: Record<SchemeStatus, { te: string; cls: string }> = {
  active: { te: "అందుబాటులో", cls: "bg-green-100 text-green-800" },
  verify: { te: "నిర్ధారించుకోండి", cls: "bg-amber-100 text-amber-800" },
  at_risk: { te: "ఈ సీజన్ చూడండి", cls: "bg-orange-100 text-orange-800" },
  closed: { te: "ముగిసింది", cls: "bg-stone-200 text-stone-600" },
  suspended: { te: "నిలిపివేయబడింది", cls: "bg-red-100 text-red-800" },
};

function SchemeCard({ s }: { s: Scheme }) {
  const [open, setOpen] = useState(false);
  const badge = STATUS[s.status];
  const dimmed = s.status === "closed" || s.status === "suspended";
  return (
    <div className={`card p-4 ${dimmed ? "opacity-70" : ""}`}>
      <button onClick={() => setOpen((v) => !v)} className="flex w-full items-start justify-between gap-3 text-left">
        <div>
          <h2 className="text-lg font-semibold leading-tight">{s.name_te}</h2>
          <p className="text-xs text-stone-500">{s.name_en}</p>
        </div>
        <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${badge.cls}`}>{badge.te}</span>
      </button>

      <p className="mt-2 text-sm">
        {s.what_te}
        <span className="mt-0.5 block text-xs text-stone-400">{s.what_en}</span>
      </p>

      {open && (
        <div className="mt-3 space-y-3 border-t border-stone-100 pt-3 text-sm">
          <p>
            <span className="font-medium text-green-800">ఎవరికి · Who: </span>
            {s.who_te}
            <span className="block text-xs text-stone-400">{s.who_en}</span>
          </p>
          <p>
            <span className="font-medium text-green-800">ఎలా · How: </span>
            {s.how_te}
            <span className="block text-xs text-stone-400">{s.how_en}</span>
          </p>
          {s.honesty_te && (
            <p className="rounded-xl bg-amber-50 px-3 py-2 text-amber-900">
              ⚠️ {s.honesty_te}
              <span className="mt-0.5 block text-xs text-amber-700/80">{s.honesty_en}</span>
            </p>
          )}
        </div>
      )}

      <div className="mt-3 flex items-center justify-between">
        <button onClick={() => setOpen((v) => !v)} className="text-sm font-semibold text-green-700">
          {open ? "మూసివేయి ▲" : "వివరాలు · Details ▼"}
        </button>
        <a
          href={s.url}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-xl bg-green-600 px-3 py-1.5 text-sm font-semibold text-white"
        >
          అధికారిక సైట్ →
        </a>
      </div>
    </div>
  );
}

export default function SchemesScreen() {
  const [filter, setFilter] = useState<Filter>("all");
  const shown = [...SCHEMES]
    .filter((s) => filter === "all" || s.level === filter)
    .sort((a, b) => b.priority - a.priority);

  return (
    <div className="mx-auto min-h-dvh max-w-md pb-28 text-stone-900">
      <header className="safe-top rounded-b-[2.25rem] bg-gradient-to-b from-green-700 to-green-800 px-5 pb-6 pt-4 text-white shadow-[var(--shadow-hero)]">
        <h1 className="text-2xl font-bold tracking-tight">🏛️ ప్రభుత్వ పథకాలు</h1>
        <p className="mt-0.5 text-sm text-green-100">రైతులకు ఉపయోగపడే పథకాలు · Benefits for farmers</p>
      </header>

      {/* filter tabs */}
      <div className="flex gap-2 px-4 pt-5 pb-2">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`rounded-full border px-4 py-1.5 text-sm font-medium transition-colors ${
              filter === f.key
                ? "border-green-700 bg-green-700 text-white"
                : "border-stone-300 bg-white text-stone-700"
            }`}
          >
            {f.te}
          </button>
        ))}
      </div>

      <div className="space-y-3 p-4 pt-1">
        {shown.map((s) => (
          <SchemeCard key={s.key} s={s} />
        ))}
        <p className="px-1 pt-1 text-xs text-stone-400">
          మొత్తాలు, అర్హతలు ఏటా మారవచ్చు — అధికారిక వెబ్‌సైట్ లేదా మీ AEOని సంప్రదించండి. Rythu ఏమీ అమ్మదు.
        </p>
      </div>
    </div>
  );
}
