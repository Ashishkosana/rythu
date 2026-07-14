"use client";

import { useState } from "react";
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
}: {
  data: WeatherContract;
  crop: string;
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

  return (
    <div className="mx-auto min-h-dvh max-w-md bg-slate-50 pb-10 text-slate-900">
      {/* top bar */}
      <div className="flex items-center justify-between bg-green-700 px-4 py-3 text-xs text-white">
        <span className="font-bold">🌾 Rythu · {t.place}</span>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-white/20 px-2 py-0.5">{t.sellNothing}</span>
          <button
            onClick={() => setLang((v) => (v === "te" ? "en" : "te"))}
            className="rounded-full bg-white px-2 py-0.5 font-bold text-green-700"
          >
            {lang === "te" ? "English" : "తెలుగు"}
          </button>
        </div>
      </div>

      {/* crop selector */}
      <div className="flex gap-2 overflow-x-auto px-4 py-3">
        {CROPS.map((c) => (
          <a
            key={c}
            href={`/?crop=${c}`}
            className={`flex shrink-0 items-center gap-1 rounded-full border px-3 py-1 text-sm ${
              c === crop ? "border-green-600 bg-green-600 text-white" : "border-slate-300 bg-white"
            }`}
          >
            <span>{CROP_LABEL[c].emoji}</span>
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
          {/* honest weather hero */}
          <div className="mx-4 rounded-3xl bg-gradient-to-br from-sky-500 to-indigo-600 p-5 text-white">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm opacity-90">{t.chanceToday}</p>
                <p className="mt-1 text-5xl font-bold">
                  {chance ?? "–"}
                  {chance !== null && <span className="text-2xl">%</span>} {emoji}
                </p>
              </div>
              <p className="text-3xl font-semibold">{temp !== null ? `${Math.round(temp)}°` : "–"}</p>
            </div>
            {data.reliability.is_offline_cache && (
              <p className="mt-2 inline-block rounded-full bg-white/20 px-2 py-0.5 text-[11px]">📴 {t.offline}</p>
            )}
            <p className="mt-3 text-[11px] leading-snug opacity-90">⚠️ {data.reliability.disclaimer_en}</p>
          </div>

          {/* hourly bars */}
          <section className="mx-4 mt-4 rounded-2xl border border-slate-200 bg-white p-4">
            <p className="mb-2 text-xs text-slate-500">{t.hourly}</p>
            <div className="flex items-end gap-1" style={{ height: 64 }}>
              {bars.map((h, i) => {
                const p = h.precipitation_probability ?? 0;
                return (
                  <div key={i} className="flex flex-1 flex-col items-center justify-end">
                    <div
                      className="w-full rounded-t bg-sky-400"
                      style={{ height: `${Math.max(4, (p / maxProb) * 100)}%` }}
                      title={`${p}%`}
                    />
                    <span className="mt-1 text-[9px] text-slate-400">
                      {new Date(h.time_local).getHours()}
                    </span>
                  </div>
                );
              })}
            </div>
          </section>

          {/* farming reads */}
          <section className="mx-4 mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-bold">
                {CROP_LABEL[crop]?.emoji} {t.advice}
              </p>
            </div>
            {lang === "te" && data.farming_read.length > 0 && (
              <p className="text-[11px] text-slate-400">ℹ️ {t.adviceEnglishNote}</p>
            )}
            {data.farming_read.length === 0 ? (
              <p className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-500">
                ✅ {t.noAdvice}
              </p>
            ) : (
              data.farming_read.map((r) => <ReadCard key={r.id} read={r} lang={lang} />)
            )}
          </section>

          {/* 7-day */}
          <section className="mx-4 mt-4 rounded-2xl border border-slate-200 bg-white p-2">
            <p className="px-2 py-1 text-sm font-bold">{t.week}</p>
            <div className="divide-y divide-slate-100">
              {data.daily.map((d) => (
                <div key={d.date} className="flex items-center justify-between px-2 py-2 text-sm">
                  <span className="w-10 text-slate-500">
                    {new Date(d.date).toLocaleDateString(lang === "te" ? "te-IN" : "en-IN", { weekday: "short" })}
                  </span>
                  <span className="text-xl">{d.emoji}</span>
                  <span className="w-14 text-right text-sky-600">
                    {d.precipitation_probability_max ?? "–"}%
                  </span>
                  <span className="w-16 text-right text-slate-500">
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
      <p className="mt-4 px-5 text-center text-[11px] leading-snug text-slate-400">
        {data.reliability.source_stamp_en}
        <br />
        📍 {data.coords.returned.lat.toFixed(3)}, {data.coords.returned.lon.toFixed(3)} · ~
        {data.coords.snap_distance_km} km from your pin
      </p>
    </div>
  );
}
