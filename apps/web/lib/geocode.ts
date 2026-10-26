// Village/town search. The backend's GET /v1/geocode does the real work (OpenStreetMap Nominatim
// first, Open-Meteo fallback, coverage filter, a day's cache, ≤ 1 upstream call/second). The app
// searches on SUBMIT, never per keystroke: Nominatim's usage policy forbids autocomplete, and a
// farmer on 3G is better served by one request than by six.
//
import { ApiUnavailable, getJson } from "./api";
import type { Lang } from "./lang";
import type { Place } from "./types";

/** Clamp to 4 decimals (~11 m) — matches the weather grid's honest resolution. */
export function roundCoord(n: number): number {
  return Math.round(n * 1e4) / 1e4;
}

export function isValidCoord(lat: number, lon: number): boolean {
  return (
    Number.isFinite(lat) &&
    Number.isFinite(lon) &&
    lat >= -90 &&
    lat <= 90 &&
    lon >= -180 &&
    lon <= 180
  );
}

/** The place's name in the farmer's language: Telugu when OpenStreetMap has it, else the English name. */
export function placeName(r: Pick<Place, "name" | "name_te">, lang: Lang): string {
  return lang === "te" && r.name_te ? r.name_te : r.name;
}

/** "Regonda, Bhupalpally" — name + district when the district differs from the name. */
export function formatPlaceLabel(r: Pick<Place, "name" | "name_te" | "admin2">, lang: Lang = "en"): string {
  const name = placeName(r, lang);
  return r.admin2 && r.admin2 !== r.name ? `${name}, ${r.admin2}` : name;
}

export const MIN_QUERY = 2;
export const MAX_QUERY = 60;

/** Can this text be searched? (Mirrors the API's 2–60 characters, after trimming.) */
export function isSearchable(query: string): boolean {
  const n = query.trim().length;
  return n >= MIN_QUERY && n <= MAX_QUERY;
}

/** "Nothing found" and "could not search" are different answers for the farmer. */
export type SearchOutcome = { ok: true; places: Place[] } | { ok: false };

export async function searchPlaces(query: string, signal?: AbortSignal): Promise<SearchOutcome> {
  if (!isSearchable(query)) return { ok: true, places: [] };
  try {
    const { res, body } = await getJson(`/v1/geocode?q=${encodeURIComponent(query.trim())}`, signal);
    const results = (body as { results?: unknown } | null)?.results;
    return res.ok && Array.isArray(results) ? { ok: true, places: results as Place[] } : { ok: false };
  } catch (err) {
    if (err instanceof ApiUnavailable) return { ok: false };
    throw err; // aborted by the caller (a newer search) — not ours to report
  }
}
