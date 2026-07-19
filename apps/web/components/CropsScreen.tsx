"use client";

import { CROP_GUIDES } from "@/lib/crops";
import FertilizerCalculator from "@/components/FertilizerCalculator";
import PestGuide from "@/components/PestGuide";
import ExpertBridge from "@/components/ExpertBridge";
import LangToggle from "@/components/LangToggle";
import { pick, useLang, type Lang } from "@/lib/lang";

function Row({ label, te, en, lang }: { label: string; te: string; en: string; lang: Lang }) {
  return (
    <div className="flex gap-2">
      <dt className="w-20 shrink-0 font-medium text-stone-500">{label}</dt>
      <dd>
        {pick(lang, te, en)}
        <span className="block text-xs text-stone-400">{pick(lang, en, te)}</span>
      </dd>
    </div>
  );
}

export default function CropsScreen() {
  const { lang } = useLang();
  return (
    <div className="mx-auto min-h-dvh max-w-md pb-28 text-stone-900">
      <header className="safe-top rounded-b-[2.25rem] bg-gradient-to-b from-green-700 to-green-800 px-5 pb-6 pt-4 text-white shadow-[var(--shadow-hero)]">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">🌱 {pick(lang, "పంటల మార్గదర్శి", "Crop guide")}</h1>
            <p className="mt-0.5 text-sm text-green-100">{pick(lang, "ఖరీఫ్ · భూపాలపల్లి", "Kharif · Bhupalpally")}</p>
          </div>
          <LangToggle light />
        </div>
      </header>

      <div className="space-y-3 p-4 pt-6">
        <FertilizerCalculator />
        <PestGuide />
        <ExpertBridge />
        <h2 className="px-1 pt-2 text-lg font-bold tracking-tight text-stone-800">
          {pick(lang, "పంటల వివరాలు", "Crop details")}
        </h2>
        {CROP_GUIDES.map((c) => (
          <details key={c.key} className="card p-4" open={c.key === "paddy"}>
            <summary className="flex cursor-pointer items-center gap-3 text-lg font-semibold">
              <span className="text-2xl" aria-hidden>
                {c.emoji}
              </span>
              <span>
                {pick(lang, c.name_te, c.name_en)}{" "}
                <span className="text-sm font-normal text-stone-500">· {pick(lang, c.name_en, c.name_te)}</span>
              </span>
            </summary>

            <dl className="mt-3 space-y-2 text-sm">
              <Row label={pick(lang, "కాలం", "Season")} te={c.season_te} en={c.season_en} lang={lang} />
              <Row label={pick(lang, "నీరు", "Water")} te={c.water_te} en={c.water_en} lang={lang} />
              <Row label={pick(lang, "విత్తడం", "Sowing")} te={c.sow_te} en={c.sow_en} lang={lang} />
            </dl>

            <div className="mt-3">
              <p className="text-sm font-medium text-green-800">{pick(lang, "ముఖ్య సూచనలు", "Key tips")}</p>
              <ul className="mt-1 space-y-1">
                {c.tips_te.map((tip, i) => (
                  <li key={i} className="flex gap-2 text-sm">
                    <span className="text-green-600" aria-hidden>
                      ✓
                    </span>
                    <span>{pick(lang, tip, c.tips_en[i])}</span>
                  </li>
                ))}
              </ul>
            </div>

            <p className="mt-3 text-xs text-stone-500">
              {pick(
                lang,
                "సరైన తేదీలు, మోతాదుల కోసం మీ వ్యవసాయ అధికారి (AEO)ని సంప్రదించండి",
                "Confirm exact dates & doses with your Agriculture Officer (AEO)",
              )}{" "}
              ·{" "}
              <a href={c.source} target="_blank" rel="noopener noreferrer" className="text-green-700 underline">
                Source: PJTSAU
              </a>
            </p>
          </details>
        ))}
      </div>
    </div>
  );
}
