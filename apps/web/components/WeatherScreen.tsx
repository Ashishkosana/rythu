"use client";

import { useState, useSyncExternalStore, type ReactNode } from "react";
import type { FarmingRead, WeatherContract } from "@/lib/types";
import { speak, weatherSpeech } from "@/lib/speak";
import { loadLang, saveLang } from "@/lib/prefs";
import { skyTheme } from "@/lib/sky";

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
    sellNothing: "మేము ఏదీ అమ్మము",
    chanceToday: "ఈరోజు వర్షం అవకాశం",
    rainLikely: "వర్షం రావచ్చు",
    rainLow: "వర్షం అవకాశం తక్కువ",
    hourlyDry: "రాబోయే గంటల్లో వర్షం అవకాశం తక్కువ",
    hourly: "రాబోయే గంటల వర్ష అవకాశం",
    adviceFor: "సలహా",
    noAdvice: "ఇప్పుడు ప్రత్యేక హెచ్చరిక ఏమీ లేదు.",
    week: "7 రోజుల వాతావరణం",
    adviceEnglishNote: "సలహా ప్రస్తుతం ఇంగ్లీష్‌లో (తెలుగు త్వరలో)",
    why: "ఎందుకు?",
    offline: "ఆఫ్‌లైన్ — సేవ్ చేసిన సమాచారం",
    degraded: "వాతావరణ సమాచారం అందుబాటులో లేదు — కాసేపటి తర్వాత చూడండి.",
    listen: "వినండి",
  },
  en: {
    sellNothing: "We sell you nothing",
    chanceToday: "Chance of rain today",
    rainLikely: "Rain likely",
    rainLow: "Low chance of rain",
    hourlyDry: "Little rain expected in the next hours",
    hourly: "Rain in the next hours",
    adviceFor: "advice",
    noAdvice: "No specific warning right now.",
    week: "7-day outlook",
    adviceEnglishNote: "Advice is in English for now (Telugu coming)",
    why: "Why?",
    offline: "Offline — showing saved forecast",
    degraded: "Weather data unavailable — please check again shortly.",
    listen: "Listen",
  },
} as const;

const SEV_STYLES: Record<string, { bar: string; tint: string }> = {
  info: { bar: "bg-sky-500", tint: "bg-sky-50" },
  caution: { bar: "bg-amber-500", tint: "bg-amber-50" },
  act: { bar: "bg-red-500", tint: "bg-red-50" },
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
  const sev = SEV_STYLES[read.severity] ?? SEV_STYLES.info;
  return (
    <div className="card flex overflow-hidden">
      <div className={`w-1.5 shrink-0 ${sev.bar}`} aria-hidden />
      <div className="flex-1 p-4">
        <div className="flex items-start gap-2.5">
          <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-lg ${sev.tint}`}>
            {ACTION_ICON[read.action] ?? "•"}
          </span>
          <p className="font-semibold leading-snug text-stone-900">{read.headline_en}</p>
        </div>
        {read.detail_en && <p className="mt-2 text-sm leading-relaxed text-stone-500">{read.detail_en}</p>}
        <button
          onClick={() => setOpen((v) => !v)}
          className="mt-2.5 text-sm font-semibold text-green-700"
        >
          {L[lang].why} {open ? "▲" : "▼"}
        </button>
        {open && (
          <div className="mt-2 space-y-1.5 rounded-xl bg-stone-50 p-3 text-sm text-stone-600">
            <p>⚠️ {read.caveat_en}</p>
            {read.window_note && <p className="text-stone-400">🕑 {read.window_note}</p>}
          </div>
        )}
      </div>
    </div>
  );
}

function SectionTitle({ children }: { children: ReactNode }) {
  return <h2 className="mb-2.5 px-1 text-lg font-bold tracking-tight text-stone-800">{children}</h2>;
}

export default function WeatherScreen({
  data,
  crop,
  place,
  locationQuery,
  children,
}: {
  data: WeatherContract;
  crop: string;
  place: string;
  locationQuery: string;
  children?: ReactNode;
}) {
  const savedLang = useSyncExternalStore(
    () => () => {},
    () => loadLang(),
    () => null,
  );
  const [override, setOverride] = useState<Lang | null>(null);
  const lang: Lang = override ?? savedLang ?? "te";
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
  const sky = skyTheme(today?.weather_code ?? null, wet);
  const maxDayProb = Math.max(10, ...data.daily.map((d) => d.precipitation_probability_max ?? 0));

  return (
    <div className="mx-auto min-h-dvh max-w-md pb-28 text-stone-900">
      {/* ── Dynamic sky hero ─────────────────────────────────────── */}
      <div className={`safe-top rounded-b-[2.25rem] px-4 pb-6 pt-3 text-white shadow-[var(--shadow-hero)] ${sky.gradient}`}>
        {/* brand row */}
        <div className="flex items-center justify-between">
          <span className="text-base font-bold tracking-tight">🌾 రైతు</span>
          <div className="flex items-center gap-2">
            <span className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${sky.chip}`}>
              ✓ {t.sellNothing}
            </span>
            <button
              onClick={() => {
                const next: Lang = lang === "te" ? "en" : "te";
                saveLang(next);
                setOverride(next);
              }}
              className="h-8 w-8 rounded-full bg-white text-sm font-bold text-green-800"
            >
              {lang === "te" ? "A" : "అ"}
            </button>
          </div>
        </div>

        {/* location */}
        {children && <div className="mt-3">{children}</div>}

        {data.degraded ? (
          <div className="mt-5 rounded-2xl bg-white/15 p-6 text-center font-medium">🌧️ {t.degraded}</div>
        ) : (
          <>
            {/* the one answer, big */}
            <div className="mt-5 flex items-end justify-between">
              <div>
                <p className={`text-sm font-medium ${sky.soft}`}>{t.chanceToday}</p>
                <p className="flex items-start font-bold leading-[0.9]">
                  <span className="text-8xl tabular-nums">{chance ?? "–"}</span>
                  {chance !== null && <span className="mt-2 text-4xl">%</span>}
                </p>
                <p className="mt-1 text-lg font-semibold">{wet ? t.rainLikely : t.rainLow}</p>
              </div>
              <div className="pb-1 text-right">
                <p className="text-7xl leading-none">{emoji}</p>
                <p className="mt-1 text-4xl font-semibold tabular-nums">
                  {temp !== null ? `${Math.round(temp)}°` : "–"}
                </p>
              </div>
            </div>

            <button
              onClick={() => speak(weatherSpeech({ place, chance, temp, wet }), "te")}
              className={`mt-4 flex w-full items-center justify-center gap-2 rounded-2xl py-3 text-base font-semibold ${sky.chip}`}
            >
              🔊 {t.listen}
            </button>

            {data.reliability.is_offline_cache && (
              <p className={`mt-3 inline-block rounded-full px-2.5 py-0.5 text-xs ${sky.chip}`}>📴 {t.offline}</p>
            )}
            <p className={`mt-3 text-[11px] leading-snug ${sky.soft}`}>⚠️ {data.reliability.disclaimer_en}</p>
          </>
        )}
      </div>

      {!data.degraded && (
        <div className="space-y-6 px-4 pt-6">
          {/* hourly */}
          <section>
            <div className="card p-4">
              <p className="mb-3 text-sm font-medium text-stone-500">{t.hourly}</p>
              {hasRainBars ? (
                <div className="flex items-end gap-1.5" style={{ height: 104 }}>
                  {bars.map((h, i) => {
                    const p = h.precipitation_probability ?? 0;
                    return (
                      <div key={i} className="flex flex-1 flex-col items-center justify-end gap-1">
                        <span className="text-[10px] font-semibold text-sky-700">{p >= 20 ? `${p}` : ""}</span>
                        <div
                          className="w-full rounded-full bg-gradient-to-t from-sky-500 to-sky-300"
                          style={{ height: `${Math.max(4, (p / maxProb) * 100)}%` }}
                          title={`${p}%`}
                        />
                        {/* Parse the hour from the ISO string (YYYY-MM-DDTHH:..) — using
                            new Date().getHours() would render the server's UTC hour on SSR
                            and the device's local hour on the client → hydration mismatch. */}
                        <span className="text-[11px] text-stone-400">{Number(h.time_local.slice(11, 13))}</span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="flex items-center gap-3 rounded-2xl bg-amber-50 px-4 py-5 text-amber-900">
                  <span className="text-3xl" aria-hidden>☀️</span>
                  <p className="text-sm font-medium">{t.hourlyDry}</p>
                </div>
              )}
            </div>
          </section>

          {/* advice for a crop */}
          <section>
            <SectionTitle>
              {CROP_LABEL[crop]?.emoji} {CROP_LABEL[crop]?.[lang]} {t.adviceFor}
            </SectionTitle>
            {/* crop selector */}
            <div className="mb-3 flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
              {CROPS.map((c) => (
                <a
                  key={c}
                  href={`/?crop=${c}&${locationQuery}`}
                  className={`flex shrink-0 items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                    c === crop
                      ? "bg-green-700 text-white shadow-[var(--shadow-1)]"
                      : "bg-white text-stone-700 shadow-[var(--shadow-1)]"
                  }`}
                >
                  <span className="text-base">{CROP_LABEL[c].emoji}</span>
                  {CROP_LABEL[c][lang]}
                </a>
              ))}
            </div>
            <div className="space-y-3">
              {lang === "te" && data.farming_read.length > 0 && (
                <p className="px-1 text-[11px] text-stone-400">ℹ️ {t.adviceEnglishNote}</p>
              )}
              {data.farming_read.length === 0 ? (
                <p className="card p-4 text-sm text-stone-500">✅ {t.noAdvice}</p>
              ) : (
                data.farming_read.map((r) => <ReadCard key={r.id} read={r} lang={lang} />)
              )}
            </div>
          </section>

          {/* 7-day */}
          <section>
            <SectionTitle>{t.week}</SectionTitle>
            <div className="card overflow-hidden">
              <div className="divide-y divide-stone-100">
                {data.daily.map((d) => {
                  const p = d.precipitation_probability_max ?? 0;
                  return (
                    <div key={d.date} className="flex items-center gap-3 px-4 py-3">
                      <span className="w-11 font-medium text-stone-600">
                        {new Date(d.date).toLocaleDateString(lang === "te" ? "te-IN" : "en-IN", { weekday: "short" })}
                      </span>
                      <span className="w-8 text-center text-2xl">{d.emoji}</span>
                      <div className="flex flex-1 items-center gap-2">
                        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-stone-100">
                          <div className="h-full rounded-full bg-sky-400" style={{ width: `${(p / maxDayProb) * 100}%` }} />
                        </div>
                        <span className="w-9 text-right text-sm font-semibold text-sky-700 tabular-nums">{p}%</span>
                      </div>
                      <span className="w-16 text-right text-stone-500 tabular-nums">
                        {d.temperature_max_c !== null ? Math.round(d.temperature_max_c) : "–"}° /{" "}
                        {d.temperature_min_c !== null ? Math.round(d.temperature_min_c) : "–"}°
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>

          {/* honest source stamp */}
          <p className="px-2 text-center text-xs leading-relaxed text-stone-400">
            {data.reliability.source_stamp_en}
            <br />
            📍 {data.coords.returned.lat.toFixed(3)}, {data.coords.returned.lon.toFixed(3)} · ~
            {data.coords.snap_distance_km} km from your pin
          </p>
        </div>
      )}
    </div>
  );
}
