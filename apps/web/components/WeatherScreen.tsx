"use client";

import { useState, type ReactNode } from "react";
import type { FarmingRead, WeatherContract } from "@/lib/types";

type Lang = "te" | "en";

const CROPS = ["chilli", "cotton", "paddy", "red_gram", "maize"] as const;

const CROP_LABEL: Record<string, { te: string; en: string; emoji: string }> = {
  chilli: { te: "మిర్చి", en: "Chilli", emoji: "🌶️" },
  cotton: { te: "పత్తి", en: "Cotton", emoji: "🧺" },
  paddy: { te: "వరి", en: "Paddy", emoji: "🌾" },
  red_gram: { te: "కంది", en: "Red gram", emoji: "🫛" },
  maize: { te: "మొక్కజొన్న", en: "Maize", emoji: "🌽" },
};

const L = {
  te: {
    place: "భూపాలపల్లి",
    sellNothing: "మేము ఏదీ అమ్మము",
    chanceToday: "ఈరోజు వర్షం అవకాశం",
    rainLikely: "వర్షం రావచ్చు",
    rainLow: "వర్షం అవకాశం తక్కువ",
    hourlyDry: "రాబోయే గంటల్లో వర్షం అవకాశం తక్కువ",
    hourly: "రాబోయే గంటల్లో వర్ష అవకాశం",
    advice: "రైతు సలహా",
    noAdvice: "ఇప్పుడు ప్రత్యేక హెచ్చరిక ఏమీ లేదు.",
    week: "7 రోజుల వాతావరణం",
    adviceEnglishNote: "సలహా ప్రస్తుతం ఇంగ్లీష్‌లో (తెలుగు త్వరలో)",
    why: "ఎందుకు?",
    offline: "ఆఫ్‌లైన్ — సేవ్ చేసిన సమాచారం",
    degraded: "వాతావరణ సమాచారం అందుబాటులో లేదు — కాసేపటి తర్వాత చూడండి.",
  },
  en: {
    place: "Bhupalpally",
    sellNothing: "We sell you nothing",
    chanceToday: "Chance of rain today",
    rainLikely: "Rain likely",
    rainLow: "Low chance of rain",
    hourlyDry: "Little rain expected in the next hours",
    hourly: "Rain chance in the next hours",
    advice: "Farmer advice",
    noAdvice: "No specific warning right now.",
    week: "7-day outlook",
    adviceEnglishNote: "Advice is in English for now (Telugu coming)",
    why: "Why?",
    offline: "Offline — showing saved forecast",
    degraded: "Weather data unavailable — please check again shortly.",
  },
} as const;

const SEV_STYLES: Record<string, string> = {
  info: "border-sky-300 bg-sky-50 text-sky-900",
  caution: "border-amber-300 bg-amber-50 text-amber-900",
  act: "border-red-300 bg-red-50 text-red-900",
};

const ACTION_ICON: Record<string, string> = {
  spray: "💦",
  irrigate: "🚿",
  sow: "🌱",
  harvest: "🧺",
  fieldwork: "🚜",
  scout: "🔍",
};

function ReadCard({ read, lang }: { read: FarmingRead; lang: Lang }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`rounded-2xl border p-4 ${SEV_STYLES[read.severity] ?? SEV_STYLES.info}`}>
      <p className="font-semibold leading-snug">
        <span className="mr-1">{ACTION_ICON[read.action] ?? "•"}</span>
        {read.headline_en}
      </p>
      {read.detail_en && <p className="mt-1 text-sm opacity-80">{read.detail_en}</p>}
      <button onClick={() => setOpen((v) => !v)} className="mt-2 text-xs font-semibold underline underline-offset-2">
        {L[lang].why} {open ? "▲" : "▼"}
      </button>
      {open && (
        <div className="mt-2 space-y-1 text-xs opacity-90">
          <p>⚠️ {read.caveat_en}</p>
          {read.window_note && <p className="opacity-70">🕑 {read.window_note}</p>}
        </div>
      )}
    </div>
  );
}

export default function WeatherScreen({
  data,
  crop,
  locationQuery,
  children,
}: {
  data: WeatherContract;
  crop: string;
  locationQuery: string;
  children?: ReactNode;
}) {
  const [lang, setLang] = useState<Lang>("te");
  const t = L[lang];
  const today = data.daily[0];
  const now = data.hourly_rain[0];
  const chance = today?.precipitation_probability_max ?? null;
  const temp = now?.temperature_c ?? today?.temperature_max_c ?? null;
  const emoji = today?.emoji ?? "🌦️";
  const bars = data.hourly_rain.slice(0, 12);
  const maxProb = Math.max(10, ...bars.map((h) => h.precipitation_probability ?? 0));
  const wet = (chance ?? 0) >= 50;
  const hasRainBars = bars.some((h) => (h.precipitation_probability ?? 0) >= 10);

  return (
    <div className="mx-auto min-h-dvh max-w-md pb-28 text-stone-900">
      {/* app header */}
      <header className="safe-top sticky top-0 z-20 bg-green-800 text-white shadow-sm">
        <div className="flex items-center justify-between px-4 py-3">
          <span className="text-lg font-bold tracking-tight">🌾 రైతు</span>
          <div className="flex items-center gap-2 text-xs">
            <span className="rounded-full bg-white/15 px-2.5 py-1 font-medium">✓ {t.sellNothing}</span>
            <button
              onClick={() => setLang((v) => (v === "te" ? "en" : "te"))}
              className="rounded-full bg-white px-3 py-1 font-bold text-green-800"
            >
              {lang === "te" ? "A" : "అ"}
            </button>
          </div>
        </div>
      </header>

      {/* location picker */}
      {children && <div className="px-4 pt-3">{children}</div>}

      {/* crop selector */}
      <div className="flex gap-2 overflow-x-auto px-4 py-3 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {CROPS.map((c) => (
          <a
            key={c}
            href={`/?crop=${c}&${locationQuery}`}
            className={`flex shrink-0 items-center gap-1.5 rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
              c === crop
                ? "border-green-700 bg-green-700 text-white shadow-sm"
                : "border-stone-300 bg-white text-stone-700"
            }`}
          >
            <span className="text-base">{CROP_LABEL[c].emoji}</span>
            {CROP_LABEL[c][lang]}
          </a>
        ))}
      </div>

      {data.degraded ? (
        <div className="mx-4 rounded-2xl border border-amber-300 bg-amber-50 p-6 text-center text-amber-900">
          🌧️ {t.degraded}
        </div>
      ) : (
        <>
          {/* honest weather hero — color + verdict shift with the rain chance */}
          <div
            className={`mx-4 rounded-3xl p-5 text-white shadow-md ${
              wet
                ? "bg-gradient-to-br from-sky-600 to-blue-700"
                : "bg-gradient-to-br from-emerald-500 to-green-700"
            }`}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium opacity-90">{t.chanceToday}</p>
                <p className="mt-1 flex items-baseline gap-1 font-bold leading-none">
                  <span className="text-7xl">{chance ?? "–"}</span>
                  {chance !== null && <span className="text-3xl">%</span>}
                </p>
                <p className="mt-2 text-base font-semibold">{wet ? t.rainLikely : t.rainLow}</p>
              </div>
              <div className="text-right">
                <p className="text-6xl leading-none">{emoji}</p>
                <p className="mt-1 text-3xl font-semibold">
                  {temp !== null ? `${Math.round(temp)}°` : "–"}
                </p>
              </div>
            </div>
            {data.reliability.is_offline_cache && (
              <p className="mt-3 inline-block rounded-full bg-white/20 px-2.5 py-0.5 text-xs">📴 {t.offline}</p>
            )}
            <p className="mt-3 border-t border-white/20 pt-2 text-xs leading-snug opacity-90">
              ⚠️ {data.reliability.disclaimer_en}
            </p>
          </div>

          {/* hourly bars — with an honest empty state when there's little rain */}
          <section className="mx-4 mt-4 rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
            <p className="mb-3 text-sm font-medium text-stone-500">{t.hourly}</p>
            {hasRainBars ? (
              <div className="flex items-end gap-1.5" style={{ height: 96 }}>
                {bars.map((h, i) => {
                  const p = h.precipitation_probability ?? 0;
                  return (
                    <div key={i} className="flex flex-1 flex-col items-center justify-end gap-1">
                      <span className="text-[10px] font-semibold text-sky-700">{p >= 20 ? `${p}` : ""}</span>
                      <div
                        className="w-full rounded-t-md bg-gradient-to-t from-sky-500 to-sky-300"
                        style={{ height: `${Math.max(3, (p / maxProb) * 100)}%` }}
                        title={`${p}%`}
                      />
                      <span className="text-[11px] text-stone-400">{new Date(h.time_local).getHours()}</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex items-center gap-3 rounded-xl bg-amber-50 px-4 py-5 text-amber-900">
                <span className="text-3xl" aria-hidden>
                  ☀️
                </span>
                <p className="text-sm font-medium">{t.hourlyDry}</p>
              </div>
            )}
          </section>

          {/* farming reads */}
          <section className="mx-4 mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-bold">
                {CROP_LABEL[crop]?.emoji} {t.advice}
              </p>
            </div>
            {lang === "te" && data.farming_read.length > 0 && (
              <p className="text-[11px] text-stone-400">ℹ️ {t.adviceEnglishNote}</p>
            )}
            {data.farming_read.length === 0 ? (
              <p className="rounded-2xl border border-stone-200 bg-white p-4 text-sm text-stone-500 shadow-sm">
                ✅ {t.noAdvice}
              </p>
            ) : (
              data.farming_read.map((r) => <ReadCard key={r.id} read={r} lang={lang} />)
            )}
          </section>

          {/* 7-day */}
          <section className="mx-4 mt-4 overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
            <p className="border-b border-stone-100 px-4 py-3 text-sm font-bold">{t.week}</p>
            <div className="divide-y divide-stone-100">
              {data.daily.map((d) => (
                <div key={d.date} className="flex items-center justify-between px-4 py-3">
                  <span className="w-12 font-medium text-stone-600">
                    {new Date(d.date).toLocaleDateString(lang === "te" ? "te-IN" : "en-IN", { weekday: "short" })}
                  </span>
                  <span className="text-2xl">{d.emoji}</span>
                  <span className="w-14 text-right font-semibold text-sky-700">
                    {d.precipitation_probability_max ?? "–"}%
                  </span>
                  <span className="w-20 text-right text-stone-500">
                    {d.temperature_max_c !== null ? Math.round(d.temperature_max_c) : "–"}° /{" "}
                    {d.temperature_min_c !== null ? Math.round(d.temperature_min_c) : "–"}°
                  </span>
                </div>
              ))}
            </div>
          </section>
        </>
      )}

      {/* honest source stamp */}
      <p className="mt-4 px-5 text-center text-xs leading-snug text-stone-400">
        {data.reliability.source_stamp_en}
        <br />
        📍 {data.coords.returned.lat.toFixed(3)}, {data.coords.returned.lon.toFixed(3)} · ~
        {data.coords.snap_distance_km} km from your pin
      </p>
    </div>
  );
}
