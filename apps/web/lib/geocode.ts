// Village/town search via Open-Meteo's free geocoding API (no key, covers India).
// The pure helpers (normalizeGeoResults, roundCoord, isValidCoord, formatPlaceLabel)
// are unit-tested in geocode.test.ts; searchPlaces is the thin network wrapper.

export interface GeoResult {
  id: number;
  name: string;
  admin2?: string; // district
  admin1?: string; // state
  lat: number;
  lon: number;
}

const GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search";

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

/** "Regonda, Bhupalpally" — name + district when the district differs from the name. */
export function formatPlaceLabel(r: Pick<GeoResult, "name" | "admin2">): string {
  return r.admin2 && r.admin2 !== r.name ? `${r.name}, ${r.admin2}` : r.name;
}

/** Pure: turn the raw geocoding JSON into typed, valid results (drops malformed rows). */
export function normalizeGeoResults(json: unknown): GeoResult[] {
  const results = (json as { results?: unknown })?.results;
  if (!Array.isArray(results)) return [];
  const out: GeoResult[] = [];
  for (const raw of results) {
    const r = raw as Record<string, unknown>;
    const lat = typeof r.latitude === "number" ? r.latitude : NaN;
    const lon = typeof r.longitude === "number" ? r.longitude : NaN;
    if (typeof r.name !== "string" || !isValidCoord(lat, lon)) continue;
    out.push({
      id: typeof r.id === "number" ? r.id : out.length,
      name: r.name,
      admin2: typeof r.admin2 === "string" ? r.admin2 : undefined,
      admin1: typeof r.admin1 === "string" ? r.admin1 : undefined,
      lat: roundCoord(lat),
      lon: roundCoord(lon),
    });
  }
  return out;
}

/** Search Indian places by name. Returns [] on any failure (caller shows "no results"). */
export async function searchPlaces(query: string, signal?: AbortSignal): Promise<GeoResult[]> {
  const q = query.trim();
  if (q.length < 2) return [];
  const url = `${GEOCODE_URL}?name=${encodeURIComponent(q)}&count=8&country=IN&language=en`;
  try {
    const res = await fetch(url, { signal });
    if (!res.ok) return [];
    return normalizeGeoResults(await res.json());
  } catch {
    return [];
  }
}
