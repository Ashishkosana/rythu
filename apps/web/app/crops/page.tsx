import { CROP_GUIDES } from "@/lib/crops";
import FertilizerCalculator from "@/components/FertilizerCalculator";

export const metadata = { title: "పంటలు · Crops — Rythu" };

export default function CropsPage() {
  return (
    <div className="mx-auto min-h-dvh max-w-md pb-28 text-stone-900">
      <header className="safe-top rounded-b-[2.25rem] bg-gradient-to-b from-green-700 to-green-800 px-5 pb-6 pt-4 text-white shadow-[var(--shadow-hero)]">
        <h1 className="text-2xl font-bold tracking-tight">🌱 పంటల మార్గదర్శి</h1>
        <p className="mt-0.5 text-sm text-green-100">ఖరీఫ్ · Kharif · భూపాలపల్లి</p>
      </header>

      <div className="space-y-3 p-4 pt-6">
        <FertilizerCalculator />
        <h2 className="px-1 pt-2 text-lg font-bold tracking-tight text-stone-800">పంటల వివరాలు · Crop guide</h2>
        {CROP_GUIDES.map((c) => (
          <details key={c.key} className="card p-4" open={c.key === "paddy"}>
            <summary className="flex cursor-pointer items-center gap-3 text-lg font-semibold">
              <span className="text-2xl" aria-hidden>
                {c.emoji}
              </span>
              <span>
                {c.name_te} <span className="text-sm font-normal text-stone-500">· {c.name_en}</span>
              </span>
            </summary>

            <dl className="mt-3 space-y-2 text-sm">
              <Row label_te="కాలం" label_en="Season" te={c.season_te} en={c.season_en} />
              <Row label_te="నీరు" label_en="Water" te={c.water_te} en={c.water_en} />
              <Row label_te="విత్తడం" label_en="Sowing" te={c.sow_te} en={c.sow_en} />
            </dl>

            <div className="mt-3">
              <p className="text-sm font-medium text-green-800">ముఖ్య సూచనలు · Key tips</p>
              <ul className="mt-1 space-y-1">
                {c.tips_te.map((tip, i) => (
                  <li key={i} className="flex gap-2 text-sm">
                    <span className="text-green-600" aria-hidden>
                      ✓
                    </span>
                    <span>
                      {tip}
                      <span className="block text-xs text-stone-400">{c.tips_en[i]}</span>
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            <p className="mt-3 text-xs text-stone-400">
              సరైన తేదీలు, మోతాదుల కోసం మీ వ్యవసాయ అధికారి (AEO)ని సంప్రదించండి ·{" "}
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

function Row({
  label_te,
  label_en,
  te,
  en,
}: {
  label_te: string;
  label_en: string;
  te: string;
  en: string;
}) {
  return (
    <div className="flex gap-2">
      <dt className="w-20 shrink-0 font-medium text-stone-500">
        {label_te}
        <span className="block text-[10px] text-stone-400">{label_en}</span>
      </dt>
      <dd>
        {te}
        <span className="block text-xs text-stone-400">{en}</span>
      </dd>
    </div>
  );
}
