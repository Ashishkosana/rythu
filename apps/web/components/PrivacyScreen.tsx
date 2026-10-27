"use client";

// The privacy policy (Play Store requires one). Every line must match what the code does — when a
// feature changes what leaves the phone, change this page in the same commit.

import Link from "next/link";
import LangToggle from "@/components/LangToggle";
import { pick, useLang } from "@/lib/lang";

const UPDATED = "2026-10-27";

const SECTIONS: { te: string; en: string; body_te: string[]; body_en: string[] }[] = [
  {
    te: "సంక్షిప్తంగా",
    en: "In short",
    body_te: [
      "Rythu ఏమీ అమ్మదు, ప్రకటనలు చూపదు, మిమ్మల్ని ట్రాక్ చేయదు. మీ సమాచారాన్ని ఎవరికీ అమ్మదు.",
      "మీరు \"Rythu సర్వర్‌లో కాపీ\" ఆన్ చేయకపోతే మీ వివరాలు మీ ఫోన్‌లోనే ఉంటాయి.",
    ],
    body_en: [
      "Rythu sells nothing, shows no ads and has no trackers. It never sells your data.",
      "Unless you switch on \"Copy on Rythu's server\", your details stay on your phone.",
    ],
  },
  {
    te: "మీ ఫోన్‌లో",
    en: "On your phone",
    body_te: [
      "మీ గ్రామం, పంట, నీటి వసతి, భాష, మీ పొలాలు (పేరు, పంట, విత్తిన తేదీ), చివరి వాతావరణ సమాచారం మీ ఫోన్‌లో ఉంటాయి — యాప్ ఆఫ్‌లైన్‌లోనూ పనిచేయడానికి.",
      "\"నా వివరాలు\" → \"ఈ ఫోన్ నుండి కూడా అంతా తొలగించండి\" తో ఇవన్నీ తొలగించవచ్చు.",
    ],
    body_en: [
      "Your village, crop, water source, language, your fields (name, crop, sowing date) and the last forecast are kept on your phone, so the app works offline.",
      "\"My data\" → \"Also clear everything on this phone\" removes all of it.",
    ],
  },
  {
    te: "వాతావరణం, గ్రామం వెతకడం",
    en: "Weather and village search",
    body_te: [
      "వాతావరణం చూపడానికి యాప్ మా సర్వర్‌కు ప్రాంతం గుర్తులు (latitude/longitude), మీ పంట, నీటి వసతి పంపుతుంది. GPS వాడితే ప్రాంతాన్ని ~1 కి.మీ.కు గుండ్రం చేసి పంపుతుంది — మీరు నిలబడిన చోటు కాదు.",
      "మా సర్వర్ Open-Meteo నుంచి వాతావరణం, OpenStreetMap (Nominatim) / Open-Meteo నుంచి గ్రామం పేర్లు తెస్తుంది. వాళ్లకు మా సర్వర్ కనిపిస్తుంది, మీ ఫోన్ కాదు.",
    ],
    body_en: [
      "To show the weather, the app sends our server the place's coordinates, your crop and your water source. A GPS position is rounded to about 1 km first — never the spot where you stand.",
      "Our server gets the forecast from Open-Meteo and village names from OpenStreetMap (Nominatim) and Open-Meteo. They see our server, not your phone.",
    ],
  },
  {
    te: "Rythu సర్వర్‌లో కాపీ (మీరు ఆన్ చేస్తేనే)",
    en: "Copy on server (only if you switch it on)",
    body_te: [
      "ఆన్ చేస్తే: ఒక యాదృచ్ఛిక ఖాతా నంబరు (మీ పేరు, ఫోన్ నంబరు కాదు), మీ గ్రామం, పంట, నీటి వసతి, భాష, పొలాలు మా సర్వర్‌లో ఉంటాయి — హెచ్చరికలు పంపడానికి, ఫోన్ పోయినా తిరిగి పొందడానికి.",
      "\"నా వివరాలు\" → \"సర్వర్ నుండి నా వివరాలు తొలగించండి\" నొక్కితే వెంటనే అన్నీ (హెచ్చరికల వివరాలతో సహా) తొలగిపోతాయి.",
    ],
    body_en: [
      "If you switch it on, our server keeps a random account number (not your name or phone number), your village, crop, water source, language and fields — to send alerts and to restore them on a new phone.",
      "\"My data\" → \"Delete my data from Rythu's server\" removes all of it at once, alert records included.",
    ],
  },
  {
    te: "హెచ్చరికలు (మీరు ఆన్ చేస్తేనే)",
    en: "Alerts (only if you switch them on)",
    body_te: [
      "హెచ్చరికలు ఆన్ చేస్తే మీ ఫోన్ యొక్క push చిరునామా (Google push సేవ ఇచ్చేది) మా సర్వర్‌లో ఉంటుంది, ఏ హెచ్చరిక ఎప్పుడు పంపామో రికార్డు ఉంటుంది — ఒకే హెచ్చరిక రెండుసార్లు రాకుండా.",
      "హెచ్చరికలు ఆఫ్ చేసినా, సర్వర్ కాపీ తొలగించినా ఇవి తొలగిపోతాయి.",
    ],
    body_en: [
      "If you switch alerts on, our server keeps your phone's push address (issued by Google's push service) and a record of which alerts were sent, so none arrives twice.",
      "Switching alerts off, or deleting the server copy, removes them.",
    ],
  },
  {
    te: "సాంకేతిక లాగ్‌లు",
    en: "Technical logs",
    body_te: [
      "సమస్యలు సరిచేయడానికి మా సర్వర్ సాంకేతిక లాగ్‌లు (సమయం, అడిగిన చిరునామా — అందులో ప్రాంతం గుర్తులు, లోపాలు) 30 రోజులు ఉంచుతుంది. మీ IP చిరునామా వాటిలో నిల్వ చేయబడదు.",
    ],
    body_en: [
      "To fix problems our server keeps technical logs (time, the address requested — which includes the place's coordinates — and errors) for 30 days. Your IP address is not stored in them.",
    ],
  },
  {
    te: "ఇతరులు",
    en: "Who else is involved",
    body_te: [
      "మా సర్వర్ Microsoft Azure మీద నడుస్తుంది. హెచ్చరికలు Google push సేవ ద్వారా వస్తాయి. యాప్ Google Play ద్వారా వస్తుంది. వీళ్లు మా తరఫున మాత్రమే పనిచేస్తారు.",
      "ఈ యాప్ పిల్లల కోసం కాదు.",
    ],
    body_en: [
      "Our server runs on Microsoft Azure. Alerts travel through Google's push service. The app is distributed through Google Play. They act only on our behalf.",
      "The app is not directed at children.",
    ],
  },
  {
    te: "సంప్రదించండి",
    en: "Contact",
    body_te: ["ప్రశ్నలకు Play Storeలో Rythu పేజీలో ఉన్న డెవలపర్ ఈమెయిల్‌కు రాయండి. ఈ పేజీ మారితే తేదీ మారుతుంది."],
    body_en: ["Questions: write to the developer email on Rythu's Play Store page. If this page changes, the date below changes."],
  },
];

export default function PrivacyScreen() {
  const { lang } = useLang();
  return (
    <main className="mx-auto min-h-dvh w-full max-w-md pb-28 text-ink">
      <header className="safe-top rounded-b-[2.25rem] bg-gradient-to-b from-hero-brand-from to-hero-brand-to px-5 pb-6 pt-4 text-white shadow-hero">
        <div className="flex items-start justify-between gap-2">
          <h1 className="text-2xl font-bold tracking-tight">🔒 {pick(lang, "గోప్యతా విధానం", "Privacy policy")}</h1>
          <LangToggle light />
        </div>
      </header>
      <div className="space-y-3 p-4 pt-6">
        {SECTIONS.map((s) => (
          <section key={s.en} className="card p-4">
            <h2 className="text-lg font-bold leading-snug">{pick(lang, s.te, s.en)}</h2>
            {(lang === "te" ? s.body_te : s.body_en).map((line) => (
              <p key={line} className="mt-2 text-sm leading-relaxed">
                {line}
              </p>
            ))}
          </section>
        ))}
        <p className="px-2 text-center text-sm text-ink-secondary">
          {pick(lang, `చివరి మార్పు: ${UPDATED}`, `Last updated: ${UPDATED}`)}
        </p>
        <Link
          href="/account/"
          className="tap mx-auto flex w-fit items-center px-4 text-sm font-semibold text-brand-ink underline underline-offset-4"
        >
          {pick(lang, "నా వివరాలు", "My data")}
        </Link>
      </div>
    </main>
  );
}
