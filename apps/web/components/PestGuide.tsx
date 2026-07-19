"use client";

import { useState } from "react";
import { PESTS, type Pest } from "@/lib/pests";
import { pick, useLang } from "@/lib/lang";

const CROP_FILTERS = [
  { key: "all", te: "అన్నీ" },
  { key: "paddy", te: "వరి" },
  { key: "cotton", te: "పత్తి" },
  { key: "maize", te: "మొక్కజొన్న" },
  { key: "red_gram", te: "కంది" },
  { key: "chilli", te: "మిర్చి" },
] as const;

function PestCard({ p }: { p: Pest }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-3.5 shadow-[var(--shadow-1)]">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center gap-3 text-left"
      >
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-stone-100 text-xl">
          {p.emoji}
        </span>
        <span className="flex-1">
          <span className="block font-semibold leading-tight">{p.name_te}</span>
          <span className="block text-xs text-stone-400">{p.crop_te} · {p.name_en}</span>
        </span>
        <span className="text-sm text-green-700">{open ? "▲" : "▼"}</span>
      </button>

      <p className="mt-2 text-sm text-stone-600">
        <span className="font-medium text-stone-700">గుర్తులు: </span>
        {p.symptom_te}
      </p>

      {open && (
        <div className="mt-3 space-y-2.5 border-t border-stone-100 pt-3 text-sm">
          <Field label="ఎప్పుడు చర్య (ETL)" body={p.threshold_te} />
          <Field label="ముందుగా (మందు లేకుండా)" body={p.ipmFirst_te} tint="bg-green-50" />
          <Field label="అవసరమైతే మందు" body={p.chemical_te} tint="bg-stone-50" />
          {/* Always shown wherever a chemical is named — label, dose, and the
              pre-harvest interval (కోత ముందు గడువు) must be confirmed with an AEO. */}
          <p className="rounded-xl bg-amber-50 px-3 py-2 text-xs leading-relaxed text-amber-900">
            ⚠️ మందు వాడే ముందు లేబుల్ చదవండి; మోతాదు మరియు కోత ముందు వేచి ఉండాల్సిన గడువు (pre-harvest
            interval)ను మీ AEOతో నిర్ధారించుకోండి.
          </p>
          {p.needsVerification && (
            <p className="rounded-xl bg-amber-100 px-3 py-2 text-xs leading-relaxed text-amber-900">
              ⚠️ ఈ పురుగు పరిమితి/మోతాదు అధికారికంగా నిర్ధారించబడలేదు — AEO/PJTSAUతో సరిచూసుకోండి.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function Field({ label, body, tint }: { label: string; body: string; tint?: string }) {
  return (
    <div className={tint ? `rounded-xl ${tint} px-3 py-2` : ""}>
      <p className="text-xs font-semibold text-green-800">{label}</p>
      <p className="mt-0.5 leading-relaxed text-stone-700">{body}</p>
    </div>
  );
}

export default function PestGuide() {
  const { lang } = useLang();
  const [crop, setCrop] = useState<string>("all");
  const shown = PESTS.filter((p) => crop === "all" || p.cropKey === crop);

  return (
    <div className="card p-4">
      <div className="flex items-center gap-2">
        <span className="text-2xl" aria-hidden>🐛</span>
        <div>
          <h2 className="text-lg font-bold leading-tight">{pick(lang, "పురుగులు & తెగుళ్లు", "Pests & diseases")}</h2>
          <p className="text-xs text-stone-500">{pick(lang, "గుర్తించి, జాగ్రత్తగా చర్య", "Identify, then act carefully")}</p>
        </div>
      </div>

      {/* honest framing up top */}
      <p className="mt-3 rounded-xl bg-green-50 px-3 py-2 text-xs leading-relaxed text-green-900">
        పురుగు కనిపిస్తే మొదట <span className="font-semibold">పరిశీలించండి</span>. మందు కంటే ముందు సహజ పద్ధతులు.
        పంటకు నష్టం స్థాయి (ETL) దాటితేనే మందు. మేము బ్రాండ్ కాదు — <span className="font-semibold">మందు రకం (active ingredient)</span> మాత్రమే చెబుతాం. మేము ఏమీ అమ్మము.
      </p>

      {/* crop filter — wraps so every crop is visible (no hidden horizontal scroll) */}
      <div className="mt-3 flex flex-wrap gap-2">
        {CROP_FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setCrop(f.key)}
            aria-pressed={crop === f.key}
            className={`rounded-full px-4 py-2.5 text-sm font-medium ${
              crop === f.key ? "bg-green-700 text-white" : "bg-stone-100 text-stone-700"
            }`}
          >
            {f.te}
          </button>
        ))}
      </div>

      <div className="mt-3 space-y-2.5">
        {shown.map((p) => (
          <PestCard key={p.key} p={p} />
        ))}
      </div>
    </div>
  );
}
