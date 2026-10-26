"use client";

import { useId, useState, type ReactNode } from "react";
import { CROPS, type Crop, type FarmAction, type FarmingRead, type Severity, type WeatherContract } from "@/lib/types";
import { speak, weatherSpeech } from "@/lib/speak";
import { useLang } from "@/lib/lang";
import LangToggle from "@/components/LangToggle";
import { skyTheme } from "@/lib/sky";
import { HERO_HOURS, nextHoursChance } from "@/lib/hero";
import { sourceStamp } from "@/lib/freshness";
import Link from "next/link";
import Icon from "@/components/ui/Icon";

type Lang = "te" | "en";

// Keyed by the backend's Crop enum: a crop added on the backend without a label won't compile.
const CROP_LABEL: Record<Crop, { te: string; en: string; emoji: string }> = {
  chilli: { te: "మిర్చి", en: "Chilli", emoji: "🌶️" },
  cotton: { te: "పత్తి", en: "Cotton", emoji: "🧺" },
  paddy: { te: "వరి", en: "Paddy", emoji: "🌾" },
  red_gram: { te: "కంది", en: "Red gram", emoji: "🌿" }, // not 🫛: an empty box before Android 13
  maize: { te: "మొక్కజొన్న", en: "Maize", emoji: "🌽" },
};

const L = {
  te: {
    title: "వాతావరణం",
    hour: "సమయం",
    chance: "వర్షం అవకాశం",
    sellNothing: "మేము ఏదీ అమ్మము",
    chanceNext: "రాబోయే 12 గంటల్లో వర్షం అవకాశం",
    rainLikely: "వర్షం రావచ్చు",
    rainLow: "వర్షం అవకాశం తక్కువ",
    hourlyDry: "రాబోయే గంటల్లో వర్షం అవకాశం తక్కువ",
    hourly: "రాబోయే గంటల వర్ష అవకాశం",
    adviceFor: "సలహా",
    noAdvice: "ఇప్పుడు ప్రత్యేక హెచ్చరిక ఏమీ లేదు.",
    week: "7 రోజుల వాతావరణం",
    why: "ఎందుకు?",
    offline: "ఆఫ్‌లైన్ — సేవ్ చేసిన సమాచారం",
    degraded: "వాతావరణ సమాచారం అందుబాటులో లేదు — కాసేపటి తర్వాత చూడండి.",
    listen: "వినండి",
  },
  en: {
    title: "Weather",
    hour: "Time",
    chance: "Chance of rain",
    sellNothing: "We sell you nothing",
    chanceNext: "Chance of rain, next 12 hours",
    rainLikely: "Rain likely",
    rainLow: "Low chance of rain",
    hourlyDry: "Little rain expected in the next hours",
    hourly: "Rain in the next hours",
    adviceFor: "advice",
    noAdvice: "No specific warning right now.",
    week: "7-day outlook",
    why: "Why?",
    offline: "Offline — showing saved forecast",
    degraded: "Weather data unavailable — please check again shortly.",
    listen: "Listen",
  },
} as const;

const SEV_STYLES: Record<Severity, { bar: string; tint: string }> = {
  info: { bar: "bg-info-accent", tint: "bg-info-bg" },
  caution: { bar: "bg-caution-accent", tint: "bg-caution-bg" },
  act: { bar: "bg-act-accent", tint: "bg-act-bg" },
};

const ACTION_ICON: Record<FarmAction, string> = {
  spray: "💦",
  irrigate: "🚿",
  sow: "🌱",
  harvest: "🧺",
  fieldwork: "🚜",
  scout: "🔍",
};

function ReadCard({ read, lang }: { read: FarmingRead; lang: Lang }) {
  const [open, setOpen] = useState(false);
  const whyId = useId();
  const sev = SEV_STYLES[read.severity] ?? SEV_STYLES.info;
  // Show Telugu when the app is in Telugu AND the backend supplied it; else English.
  const te = (teVal: string | undefined, enVal: string) => (lang === "te" && teVal ? teVal : enVal);
  const headline = te(read.headline_te, read.headline_en);
  const detail = te(read.detail_te, read.detail_en);
  const caveat = te(read.caveat_te, read.caveat_en);
  return (
    <div className="card flex overflow-hidden">
      <div className={`w-1.5 shrink-0 ${sev.bar}`} aria-hidden />
      <div className="flex-1 p-4">
        <div className="flex items-start gap-2.5">
          <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-lg ${sev.tint}`}>
            {ACTION_ICON[read.action] ?? "•"}
          </span>
          <p className="font-semibold text-ink">{headline}</p>
        </div>
        {detail && <p className="mt-2 text-sm leading-relaxed text-ink-secondary">{detail}</p>}
        <button
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls={whyId}
          className="tap -ml-2 mt-1 flex items-center gap-1 px-2 text-sm font-semibold text-brand-ink"
        >
          {L[lang].why}
          <Icon name="chevron-down" size={18} className={open ? "rotate-180" : ""} />
        </button>
        {open && (
          <div id={whyId} className="mt-1 space-y-1.5 rounded-xl bg-surface-sunken p-3 text-sm text-ink-secondary">
            <p>⚠️ {caveat}</p>
            {read.window_note && <p className="text-ink-secondary">🕑 {read.window_note}</p>}
          </div>
        )}
      </div>
    </div>
  );
}

function SectionTitle({ children }: { children: ReactNode }) {
  return <h2 className="mb-2.5 px-1 text-lg font-bold tracking-tight text-ink">{children}</h2>;
}

export default function WeatherScreen({
  data,
  crop,
  place,
  locationQuery,
  nowMs,
  offline,
  adviceLoading,
  children,
}: {
  data: WeatherContract; // already trimmed to "now" (lib/freshness.ts asOf)
  crop: Crop;
  place: string;
  locationQuery: string;
  nowMs: number; // the device clock, for the "updated N min ago" stamp
  offline: boolean; // showing a saved copy (server's or this device's)
  adviceLoading: boolean; // the advice shown belongs to the previous crop: hide it
  children?: ReactNode;
}) {
  const { lang } = useLang(); // app-wide language
  const t = L[lang];

  const today = data.daily[0];
  const now = data.hourly_rain[0];
  const chance = nextHoursChance(data.hourly_rain);
  const temp = now?.temperature_c ?? today?.temperature_max_c ?? null;
  const emoji = today?.emoji ?? "🌦️";
  const bars = data.hourly_rain.slice(0, HERO_HOURS);
  const maxProb = Math.max(10, ...bars.map((h) => h.precipitation_probability ?? 0));
  const wet = (chance ?? 0) >= 50;
  const hasRainBars = bars.some((h) => (h.precipitation_probability ?? 0) >= 10);
  const sky = skyTheme(today?.weather_code ?? null, wet);
  const maxDayProb = Math.max(10, ...data.daily.map((d) => d.precipitation_probability_max ?? 0));

  return (
    <main className="mx-auto min-h-dvh w-full max-w-md pb-28 text-ink">
      <h1 className="sr-only">
        {t.title} · {place}
      </h1>
      {/* ── Dynamic sky hero ─────────────────────────────────────── */}
      <div className={`safe-top rounded-b-[2.25rem] px-4 pb-6 pt-3 text-white shadow-hero ${sky.gradient}`}>
        {/* brand row */}
        <div className="flex items-center justify-between">
          <span className="text-base font-bold tracking-tight" lang="te">
            🌾 రైతు
          </span>
          <div className="flex items-center gap-2">
            <span className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-caption font-medium ${sky.chip}`}>
              <Icon name="check" size={14} /> {t.sellNothing}
            </span>
            <LangToggle light />
          </div>
        </div>

        {/* location */}
        {children && <div className="mt-3">{children}</div>}

        {data.degraded ? (
          <div className="mt-5 rounded-2xl bg-black/15 p-6 text-center font-medium">🌧️ {t.degraded}</div>
        ) : (
          <>
            {/* the one answer, big */}
            <div className="mt-5 flex items-end justify-between">
              <div>
                <p className={`text-sm font-medium ${sky.soft}`}>{t.chanceNext}</p>
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
              className={`tap mt-4 flex w-full items-center justify-center gap-2 rounded-2xl py-3 text-base font-semibold ${sky.chip}`}
            >
              <Icon name="volume-2" size={22} /> {t.listen}
            </button>

            {offline && (
              <p className={`mt-3 inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-caption ${sky.chip}`}>
                <Icon name="wifi-off" size={14} /> {t.offline}
              </p>
            )}
            <p className={`mt-3 text-caption ${sky.soft}`} lang="en">
              ⚠️ {data.reliability.disclaimer_en}
            </p>
          </>
        )}
      </div>

      {!data.degraded && (
        <div className="space-y-6 px-4 pt-6">
          {/* hourly */}
          <section>
            <div className="card p-4">
              <p className="mb-3 text-sm font-medium text-ink-secondary" aria-hidden>
                {t.hourly}
              </p>
              <table className="sr-only">
                <caption>{t.hourly}</caption>
                <thead>
                  <tr>
                    <th scope="col">{t.hour}</th>
                    <th scope="col">{t.chance}</th>
                  </tr>
                </thead>
                <tbody>
                  {bars.map((h) => (
                    <tr key={h.time_local}>
                      <td>{h.time_local.slice(11, 16)}</td>
                      <td>{h.precipitation_probability === null ? "–" : `${h.precipitation_probability}%`}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {hasRainBars ? (
                <div className="flex items-end gap-1.5" style={{ height: 104 }} aria-hidden>
                  {bars.map((h, i) => {
                    const p = h.precipitation_probability ?? 0;
                    return (
                      <div key={i} className="flex h-full flex-1 flex-col items-center gap-1">
                        <span className="text-caption font-semibold text-info-fg">{p >= 20 ? `${p}` : ""}</span>
                        {/* The bar's % height needs a parent of definite height: this flex-1 slot. */}
                        <div className="flex w-full flex-1 items-end">
                          <div
                            className="w-full rounded-full bg-info-accent"
                            style={{ height: `${Math.max(4, (p / maxProb) * 100)}%` }}
                            title={`${p}%`}
                          />
                        </div>
                        {/* The hour as printed in the forecast's own time zone (IST), whatever
                            the device's zone: YYYY-MM-DDTHH:.. */}
                        <span className="text-caption text-ink-secondary">{Number(h.time_local.slice(11, 13))}</span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="flex items-center gap-3 rounded-2xl bg-caution-bg px-4 py-5 text-caution-fg">
                  <span className="text-3xl" aria-hidden>☀️</span>
                  <p className="text-sm font-medium">{t.hourlyDry}</p>
                </div>
              )}
            </div>
          </section>

          {/* advice for a crop */}
          <section>
            <SectionTitle>
              {CROP_LABEL[crop].emoji} {CROP_LABEL[crop][lang]} {t.adviceFor}
            </SectionTitle>
            {/* crop selector */}
            <div className="mb-3 flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
              {CROPS.map((c) => (
                <Link
                  key={c}
                  href={`/?crop=${c}&${locationQuery}`}
                  replace
                  scroll={false}
                  aria-current={c === crop ? "true" : undefined}
                  className={`tap flex shrink-0 items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                    c === crop
                      ? "bg-brand text-white shadow-1"
                      : "bg-surface-raised text-ink shadow-1"
                  }`}
                >
                  <span className="text-base">{CROP_LABEL[c].emoji}</span>
                  {CROP_LABEL[c][lang]}
                </Link>
              ))}
            </div>
            <div className="space-y-3">
              {adviceLoading ? (
                <>
                  <div className="card h-20 animate-pulse motion-reduce:animate-none" />
                  <div className="card h-20 animate-pulse motion-reduce:animate-none" />
                </>
              ) : data.farming_read.length === 0 ? (
                <p className="card p-4 text-sm text-ink-secondary">✅ {t.noAdvice}</p>
              ) : (
                data.farming_read.map((r) => <ReadCard key={r.id} read={r} lang={lang} />)
              )}
            </div>
          </section>

          {/* 7-day */}
          <section>
            <SectionTitle>{t.week}</SectionTitle>
            <div className="card overflow-hidden">
              <div className="divide-y divide-line">
                {data.daily.map((d) => {
                  const p = d.precipitation_probability_max ?? 0;
                  return (
                    <div key={d.date} className="flex items-center gap-3 px-4 py-3">
                      <span className="w-11 font-medium text-ink-secondary">
                        {new Date(d.date).toLocaleDateString(lang === "te" ? "te-IN" : "en-IN", {
                          weekday: "short",
                          timeZone: "UTC", // "YYYY-MM-DD" parses as UTC midnight: name THAT day
                        })}
                      </span>
                      <span className="w-8 text-center text-2xl">{d.emoji}</span>
                      <div className="flex flex-1 items-center gap-2">
                        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-sunken">
                          <div className="h-full rounded-full bg-info-accent" style={{ width: `${(p / maxDayProb) * 100}%` }} />
                        </div>
                        <span className="w-9 text-right text-sm font-semibold text-info-fg tabular-nums">{p}%</span>
                      </div>
                      <span className="w-16 text-right text-ink-secondary tabular-nums">
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
          <p className="px-2 text-center text-caption leading-relaxed text-ink-secondary">
            {sourceStamp(data, nowMs, lang)}
            <br />
            📍 {data.coords.returned.lat.toFixed(3)}, {data.coords.returned.lon.toFixed(3)} · ~
            {data.coords.snap_distance_km} km from your pin
          </p>
        </div>
      )}
    </main>
  );
}
