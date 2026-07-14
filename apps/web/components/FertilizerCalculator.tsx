"use client";

import { useMemo, useState } from "react";
import { CROP_DOSES, GUNTHA_PER_ACRE, computeForArea } from "@/lib/agronomy";
import { speak } from "@/lib/speak";

// Fertilizer calculator: pick crop + area → exact Urea/DAP/MOP bags, from cited
// PJTSAU/ICAR norms (never company formulas). Deterministic + offline. Honest:
// always shows the soil-test/AEO fallback, prominently for unverified crops.

type Unit = "acre" | "guntha";

export default function FertilizerCalculator() {
  const [cropKey, setCropKey] = useState(CROP_DOSES[0].key);
  const [amount, setAmount] = useState("1");
  const [unit, setUnit] = useState<Unit>("acre");

  const dose = CROP_DOSES.find((c) => c.key === cropKey)!;
  const acres = useMemo(() => {
    const n = parseFloat(amount);
    if (!Number.isFinite(n) || n <= 0) return 0;
    return unit === "acre" ? n : n / GUNTHA_PER_ACRE;
  }, [amount, unit]);

  const r = useMemo(() => computeForArea(dose, acres), [dose, acres]);

  function listen() {
    const line =
      acres > 0
        ? `${dose.name_te} కోసం, ${r.ureaBags} బస్తాల యూరియా, ${r.dapBags} బస్తాల డీఏపీ, ${r.mopBags} బస్తాల పొటాష్ వేయండి. మీ నేల పరీక్ష ప్రకారం నిర్ధారించుకోండి.`
        : "దయచేసి విస్తీర్ణం నమోదు చేయండి.";
    speak(line, "te");
  }

  return (
    <div className="card p-4">
      <div className="flex items-center gap-2">
        <span className="text-2xl" aria-hidden>🧮</span>
        <div>
          <h2 className="text-lg font-bold leading-tight">ఎరువుల లెక్క</h2>
          <p className="text-xs text-stone-500">Fertilizer calculator · ఎంత వేయాలి?</p>
        </div>
      </div>

      {/* crop */}
      <div className="mt-4 flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {CROP_DOSES.map((c) => (
          <button
            key={c.key}
            onClick={() => setCropKey(c.key)}
            className={`flex shrink-0 items-center gap-1.5 rounded-full px-3.5 py-2 text-sm font-medium ${
              c.key === cropKey ? "bg-green-700 text-white" : "bg-stone-100 text-stone-700"
            }`}
          >
            <span>{c.emoji}</span>
            {c.name_te}
          </button>
        ))}
      </div>

      {/* area */}
      <div className="mt-3 flex items-center gap-2">
        <input
          type="number"
          inputMode="decimal"
          min="0"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="w-24 rounded-xl border border-stone-300 px-3 py-2.5 text-lg font-semibold outline-none focus:border-green-600"
          aria-label="విస్తీర్ణం"
        />
        <div className="flex rounded-xl bg-stone-100 p-1">
          {(["acre", "guntha"] as Unit[]).map((u) => (
            <button
              key={u}
              onClick={() => setUnit(u)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                unit === u ? "bg-white text-green-800 shadow-[var(--shadow-1)]" : "text-stone-500"
              }`}
            >
              {u === "acre" ? "ఎకరం" : "గుంట"}
            </button>
          ))}
        </div>
      </div>

      {/* result */}
      {acres > 0 ? (
        <div className="mt-4 rounded-2xl bg-green-50 p-4">
          <div className="grid grid-cols-3 gap-2 text-center">
            <Bag label="యూరియా" en="Urea" bags={r.ureaBags} kg={r.ureaKg} />
            <Bag label="డీఏపీ" en="DAP" bags={r.dapBags} kg={r.dapKg} />
            <Bag label="పొటాష్" en="MOP" bags={r.mopBags} kg={r.mopKg} />
          </div>
          <p className="mt-3 text-xs leading-relaxed text-stone-500">
            <span className="font-semibold text-stone-700">వేయు విధానం: </span>
            {dose.splits_te}
          </p>
          <button
            onClick={listen}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-green-600 py-2.5 text-sm font-semibold text-white"
          >
            🔊 వినండి
          </button>
        </div>
      ) : (
        <p className="mt-4 rounded-2xl bg-stone-50 p-4 text-center text-sm text-stone-500">
          విస్తీర్ణం నమోదు చేయండి · Enter your area
        </p>
      )}

      {/* honesty */}
      <p
        className={`mt-3 rounded-xl px-3 py-2 text-xs leading-relaxed ${
          dose.needsVerification ? "bg-amber-50 text-amber-900" : "bg-stone-50 text-stone-500"
        }`}
      >
        ⚠️ ఇవి PJTSAU/ICAR సాధారణ సిఫార్సులు. మీ నేల పరీక్ష (Soil Health Card), నేల రకం, నీటి వసతిని బట్టి అసలు
        అవసరం మారుతుంది — మీ వ్యవసాయ అధికారి (AEO)/KVKను సంప్రదించండి. మేము ఏమీ అమ్మము.
      </p>
    </div>
  );
}

function Bag({ label, en, bags, kg }: { label: string; en: string; bags: number; kg: number }) {
  return (
    <div className="rounded-xl bg-white p-2.5 shadow-[var(--shadow-1)]">
      <p className="text-2xl font-bold tabular-nums text-green-800">{bags}</p>
      <p className="text-[11px] font-medium text-stone-600">బస్తాలు</p>
      <p className="mt-0.5 text-sm font-semibold">{label}</p>
      <p className="text-[10px] text-stone-400">{en} · {kg} kg</p>
    </div>
  );
}
