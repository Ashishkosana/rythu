// Honest time on the device. The API stamps when the forecast was fetched upstream
// (upstream_fetched_at); everything time-relative is computed HERE, at the moment it is read,
// because a forecast can sit in the on-device cache for hours. Pure + tested.

import type { DailyPoint, HourlyRain, WeatherContract } from "./types";

/** Same rule as the server's saved copy (S2): older than this is not shown as a forecast. */
export const MAX_SAVED_AGE_MS = 6 * 60 * 60 * 1000;

const HOUR_MS = 60 * 60 * 1000;

/** Milliseconds since the forecast was fetched; clock skew never makes it negative. */
export function ageMs(fetchedAtIso: string, nowMs: number): number {
  const t = Date.parse(fetchedAtIso);
  return Number.isFinite(t) ? Math.max(0, nowMs - t) : Number.POSITIVE_INFINITY;
}

export function isTooOld(data: Pick<WeatherContract, "upstream_fetched_at">, nowMs: number): boolean {
  return ageMs(data.upstream_fetched_at, nowMs) > MAX_SAVED_AGE_MS;
}

/** "8 min ago" / "8 నిమిషాల క్రితం" — the server's buckets (domain/reliability.py), in both languages. */
export function ageLabel(fetchedAtIso: string, nowMs: number, lang: "te" | "en"): string {
  const s = ageMs(fetchedAtIso, nowMs) / 1000;
  if (!Number.isFinite(s)) return lang === "te" ? "తెలియదు" : "unknown";
  if (s < 120) return lang === "te" ? "ఇప్పుడే" : "just now";
  const min = Math.floor(s / 60);
  if (min < 60) return lang === "te" ? `${min} నిమిషాల క్రితం` : `${min} min ago`;
  const hr = Math.floor(s / 3600);
  if (hr < 24) return lang === "te" ? `${hr} గంటల క్రితం` : `${hr} hr ago`;
  const d = new Date(Date.parse(fetchedAtIso));
  return d.toLocaleDateString(lang === "te" ? "te-IN" : "en-IN", { day: "numeric", month: "short" });
}

/** "Source: Open-Meteo (~11 km) · updated 8 min ago" — computed now, not when the server answered. */
export function sourceStamp(data: Pick<WeatherContract, "resolution_km" | "upstream_fetched_at">, nowMs: number, lang: "te" | "en"): string {
  const age = ageLabel(data.upstream_fetched_at, nowMs, lang);
  return lang === "te"
    ? `మూలం: Open-Meteo (~${data.resolution_km} కి.మీ) · ${age} తాజా చేశాం`
    : `Source: Open-Meteo (~${data.resolution_km} km) · updated ${age}`;
}

/** Calendar date (YYYY-MM-DD) of an instant in the forecast's time zone. */
export function localDate(nowMs: number, timeZone: string): string {
  // en-CA formats as YYYY-MM-DD.
  return new Intl.DateTimeFormat("en-CA", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" }).format(
    new Date(nowMs),
  );
}

/**
 * The forecast as it stands NOW: hours that have fully passed and days before today are dropped,
 * so a copy from this morning never shows this morning's rain as "coming". (The server does the
 * same at answer time; this keeps it true while the copy waits in the cache.)
 */
export function asOf<T extends { hourly_rain: HourlyRain[]; daily: DailyPoint[]; timezone: string }>(
  data: T,
  nowMs: number,
): T {
  const hourly = data.hourly_rain.filter((h) => {
    const t = Date.parse(h.time_local);
    return !Number.isFinite(t) || t + HOUR_MS > nowMs; // keep the current hour; keep unparseable rows
  });
  const today = localDate(nowMs, data.timezone || "Asia/Kolkata");
  const daily = data.daily.filter((d) => d.date >= today);
  return { ...data, hourly_rain: hourly, daily };
}
