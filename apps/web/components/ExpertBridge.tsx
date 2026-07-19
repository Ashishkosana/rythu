"use client";

// The human fallback: when the app can't help, a farmer should reach a real,
// FREE expert by voice. Kisan Call Centre (1800-180-1551) + the local Rythu
// Vedika / AEO. No funnel, no charge — on-brand ("we sell you nothing").

import { pick, useLang } from "@/lib/lang";

export default function ExpertBridge() {
  const { lang } = useLang();
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2">
        <span className="text-2xl" aria-hidden>👨‍🌾</span>
        <div>
          <h2 className="text-lg font-bold leading-tight">{pick(lang, "నిపుణుడితో మాట్లాడండి", "Talk to a real expert")}</h2>
          <p className="text-xs text-stone-500">{pick(lang, "ఉచితం", "Free")}</p>
        </div>
      </div>

      <p className="mt-2 text-sm text-stone-600">
        {pick(
          lang,
          "యాప్‌లో సమాధానం దొరకకపోతే, ఉచిత కిసాన్ కాల్ సెంటర్‌కు ఫోన్ చేయండి — తెలుగులో మాట్లాడవచ్చు.",
          "If the app can't help, call the free Kisan Call Centre — you can speak in Telugu.",
        )}
      </p>

      <a
        href="tel:18001801551"
        className="mt-3 flex w-full items-center justify-center gap-2 rounded-2xl bg-green-700 py-3.5 text-lg font-bold text-white"
      >
        📞 1800-180-1551
      </a>

      <p className="mt-3 text-xs leading-relaxed text-stone-500">
        {pick(
          lang,
          "లేదా మీ గ్రామ వ్యవసాయ విస్తరణ అధికారి (AEO) / రైతు వేదికను సంప్రదించండి. పురుగు కనిపిస్తే ఫోటో తీసి వారికి చూపించండి.",
          "Or contact your village Agriculture Officer (AEO) / Rythu Vedika. If you see a pest, take a photo and show them.",
        )}
      </p>
    </div>
  );
}
