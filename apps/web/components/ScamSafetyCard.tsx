"use client";

// 2026: fake "PM-Kisan" APKs spread on WhatsApp emptied farmers' bank accounts. The defence is a few
// habits, said plainly where farmers look for scheme money, plus the number to call the same day.

import { CYBER_CRIME, CYBER_CRIME_PORTAL } from "@/lib/helplines";
import { pick, useLang } from "@/lib/lang";

const HABITS: { te: string; en: string }[] = [
  {
    te: "WhatsApp / SMSలో వచ్చే APK ఫైల్‌ను ఎప్పుడూ ఇన్‌స్టాల్ చేయకండి — \"PM-కిసాన్\" అని ఉన్నా సరే. అది మీ బ్యాంకు డబ్బు దోచుకుంటుంది.",
    en: "Never install an APK file sent on WhatsApp or SMS — even if it says \"PM-Kisan\". It can empty your bank account.",
  },
  {
    te: "Rythu, ప్రభుత్వ యాప్‌లు Play Store నుంచి మాత్రమే వేసుకోండి.",
    en: "Install Rythu and government apps only from the Play Store.",
  },
  {
    te: "OTP, UPI PIN ఎవరికీ చెప్పకండి — ఫోన్ చేసింది అధికారి అని చెప్పినా.",
    en: "Never tell anyone your OTP or UPI PIN — even a caller who says they are an officer.",
  },
];

export default function ScamSafetyCard() {
  const { lang } = useLang();
  return (
    <section aria-labelledby="scam-safety" className="card p-4">
      <div className="flex items-center gap-2">
        <span className="text-2xl" aria-hidden>🛡️</span>
        <h2 id="scam-safety" className="text-lg font-bold leading-snug">
          {pick(lang, "మోసాల నుంచి జాగ్రత్త", "Beware of scams")}
        </h2>
      </div>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm">
        {HABITS.map((h) => (
          <li key={h.en}>{pick(lang, h.te, h.en)}</li>
        ))}
      </ul>
      <p className="mt-3 rounded-xl bg-act-bg px-3 py-2 text-sm font-semibold text-act-fg">
        {pick(
          lang,
          "మోసపోతే వెంటనే 1930కు ఫోన్ చేయండి — త్వరగా చెబితే డబ్బు ఆపే అవకాశం ఉంటుంది.",
          "Cheated? Call 1930 at once — the sooner you report, the better the chance to stop the money.",
        )}
      </p>
      <div className="mt-3 flex gap-2">
        <a
          href={CYBER_CRIME.tel}
          className="tap flex flex-1 items-center justify-center gap-2 rounded-xl bg-brand py-2.5 text-sm font-semibold text-white"
        >
          📞 {CYBER_CRIME.display}
        </a>
        <a
          href={CYBER_CRIME_PORTAL}
          target="_blank"
          rel="noopener noreferrer"
          className="tap flex flex-1 items-center justify-center rounded-xl border border-brand py-2.5 text-sm font-semibold text-brand-ink"
        >
          cybercrime.gov.in
        </a>
      </div>
    </section>
  );
}
