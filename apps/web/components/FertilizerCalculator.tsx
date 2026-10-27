"use client";

import { useMemo, useState } from "react";
import { BAG_PRICES, CROP_DOSES, GUNTHA_PER_ACRE, PRICES_AS_OF, computeForArea, type BagPrice } from "@/lib/agronomy";
import { KISAN_CALL_CENTRE } from "@/lib/helplines";
import { speak } from "@/lib/speak";
import { pick, useLang, type Lang } from "@/lib/lang";
import Icon from "@/components/ui/Icon";

// Fertilizer calculator: pick crop + area → exact Urea/DAP/MOP bags, from cited
// PJTSAU/ICAR norms (never company formulas). Deterministic + offline. Honest:
// always shows the soil-test/AEO fallback, prominently for unverified crops. Below the doses: what a
// bag should cost — a number only where the government fixes it — and where to complain when a
// dealer asks for more (2026: over-MRP urea and DAP sales were reported across Telangana).

type Unit = "acre" | "guntha";

export default function FertilizerCalculator() {
  const { lang } = useLang();
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
        ? `${dose.name_te} కోసం, ${r.ureaBags} బస్తాల యూరియా, ${r.dapBags} బస్తాల డీఏపీ, ${r.mopBags} బస్తాల పొటాష్ వేయండి. మీ నేల పరీక్ష ప్రకారం నిర్ధారించుకోండి. బస్తాపై ఉన్న ధర కంటే ఎక్కువ ఇవ్వకండి.`
        : "దయచేసి విస్తీర్ణం నమోదు చేయండి.";
    speak(line, "te");
  }

  return (
    <div className="card p-4">
      <div className="flex items-center gap-2">
        <span className="text-2xl" aria-hidden>🧮</span>
        <div>
          <h2 className="text-lg font-bold leading-snug">{pick(lang, "ఎరువుల లెక్క", "Fertilizer calculator")}</h2>
          <p className="text-caption text-ink-secondary">{pick(lang, "ఎంత వేయాలి?", "How much to apply?")}</p>
        </div>
      </div>

      {/* crop */}
      <div className="mt-4 flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {CROP_DOSES.map((c) => (
          <button
            key={c.key}
            onClick={() => setCropKey(c.key)}
            className={`tap flex shrink-0 items-center gap-1.5 rounded-full px-3.5 py-2 text-sm font-medium ${
              c.key === cropKey ? "bg-brand text-white" : "bg-surface-sunken text-ink"
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
          className="tap w-24 rounded-xl border border-line-strong px-3 py-2.5 text-lg font-semibold outline-none focus:border-brand"
          aria-label="విస్తీర్ణం"
        />
        <div className="flex rounded-xl bg-surface-sunken p-1">
          {(["acre", "guntha"] as Unit[]).map((u) => (
            <button
              key={u}
              onClick={() => setUnit(u)}
              className={`tap rounded-lg px-3 py-1.5 text-sm font-medium ${
                unit === u ? "bg-surface-raised text-brand-ink shadow-1" : "text-ink-secondary"
              }`}
            >
              {u === "acre" ? "ఎకరం" : "గుంట"}
            </button>
          ))}
        </div>
      </div>

      {/* result */}
      {acres > 0 ? (
        <div className="mt-4 rounded-2xl bg-brand-soft p-4">
          <div className="grid grid-cols-3 gap-2 text-center">
            <Bag label="యూరియా" en="Urea" bags={r.ureaBags} kg={r.ureaKg} />
            <Bag label="డీఏపీ" en="DAP" bags={r.dapBags} kg={r.dapKg} />
            <Bag label="పొటాష్" en="MOP" bags={r.mopBags} kg={r.mopKg} />
          </div>
          <p className="mt-3 text-caption leading-relaxed text-ink-secondary">
            <span className="font-semibold text-ink">వేయు విధానం: </span>
            {dose.splits_te}
          </p>
          <button
            onClick={listen}
            className="tap mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-brand py-2.5 text-sm font-semibold text-white"
          >
            <Icon name="volume-2" size={20} /> వినండి
          </button>
        </div>
      ) : (
        <p className="mt-4 rounded-2xl bg-surface-sunken p-4 text-center text-sm text-ink-secondary">
          విస్తీర్ణం నమోదు చేయండి · Enter your area
        </p>
      )}

      <BagPrices lang={lang} />

      {/* honesty */}
      <p
        className={`mt-3 rounded-xl px-3 py-2 text-caption leading-relaxed ${
          dose.needsVerification ? "bg-caution-bg text-caution-fg" : "bg-surface-sunken text-ink-secondary"
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
    <div className="rounded-xl bg-surface-raised p-2.5 shadow-1">
      <p className="text-2xl font-bold tabular-nums text-brand-ink">{bags}</p>
      <p className="text-caption font-medium text-ink-secondary">బస్తాలు</p>
      <p className="mt-0.5 text-sm font-semibold">{label}</p>
      <p className="text-caption text-ink-secondary">{en} · <span className="whitespace-nowrap">{kg} kg</span></p>
    </div>
  );
}

function rupees(n: number): string {
  return `₹${n.toLocaleString("en-IN", { minimumFractionDigits: Number.isInteger(n) ? 0 : 2 })}`;
}

function PriceText({ p, lang }: { p: BagPrice; lang: Lang }) {
  if (p.rupees === null) return <>{pick(lang, "బస్తాపై ముద్రించిన ధర", "Printed on the bag")}</>;
  return (
    <>
      {p.fixed ? rupees(p.rupees) : `~${rupees(p.rupees)}`}
      <span className="block text-caption font-normal text-ink-secondary">
        {p.fixed ? pick(lang, "ప్రభుత్వ ధర", "Fixed by govt") : pick(lang, "బస్తాపై ధర చూడండి", "Check the bag")}
      </span>
    </>
  );
}

function BagPrices({ lang }: { lang: Lang }) {
  const [year, month] = PRICES_AS_OF.split("-").map(Number);
  const asOf = new Date(year!, month! - 1).toLocaleDateString(lang === "te" ? "te-IN" : "en-IN", {
    month: "long",
    year: "numeric",
  });
  return (
    <section aria-labelledby="bag-prices" className="mt-3 rounded-2xl border border-line p-3">
      <h3 id="bag-prices" className="text-base font-semibold">
        {pick(lang, "బస్తా ధర (MRP)", "Price per bag (MRP)")}
      </h3>
      <dl className="mt-2 space-y-2 text-sm">
        {BAG_PRICES.map((p) => (
          <div key={p.key} className="flex items-baseline justify-between gap-3">
            <dt>
              {pick(lang, p.name_te, p.name_en)} <span className="text-caption text-ink-secondary">{p.bagKg} kg</span>
            </dt>
            <dd className="text-right font-semibold tabular-nums">
              <PriceText p={p} lang={lang} />
            </dd>
          </div>
        ))}
      </dl>
      <p className="mt-3 rounded-xl bg-act-bg px-3 py-2 text-sm font-semibold text-act-fg">
        {pick(
          lang,
          "బస్తాపై ముద్రించిన ధర (MRP) కంటే ఒక్క రూపాయి కూడా ఎక్కువ ఇవ్వకండి. బిల్లు తప్పక తీసుకోండి.",
          "Never pay more than the MRP printed on the bag. Always take the bill.",
        )}
      </p>
      <p className="mt-2 text-caption leading-relaxed text-ink-secondary">
        {pick(
          lang,
          "ఎక్కువ అడిగితే: బిల్లుతో మీ మండల వ్యవసాయ అధికారి (MAO) / AEOకి ఫిర్యాదు చేయండి — MRP కంటే ఎక్కువకు అమ్మడం నేరం. ఎవరిని అడగాలో తెలియకపోతే ఉచిత కిసాన్ కాల్ సెంటర్‌కు ఫోన్ చేయండి.",
          "Asked for more? Complain to your Mandal Agriculture Officer (MAO) / AEO with the bill — selling above MRP is an offence. Not sure whom to ask? Call the free Kisan Call Centre.",
        )}
      </p>
      <a
        href={KISAN_CALL_CENTRE.tel}
        className="tap mt-2 flex w-full items-center justify-center gap-2 rounded-xl border border-brand py-2.5 text-sm font-semibold text-brand-ink"
      >
        📞 {KISAN_CALL_CENTRE.display}
      </a>
      <p className="mt-2 text-caption text-ink-secondary">{pick(lang, `ధరలు: ${asOf}`, `Prices as of ${asOf}`)}</p>
    </section>
  );
}
