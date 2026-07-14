// Village/town search. The client calls our own /api/geocode route (see
// app/api/geocode/route.ts), which queries OpenStreetMap (Nominatim) first —
// far better coverage of small Indian villages than GeoNames — and falls back
// to Open-Meteo. The pure normalizers + helpers here are unit-tested in
// geocode.test.ts; only the tiny fetch wrapper touches the network.

export interface GeoResult {
  id: number;
  name: string;
  admin2?: string; // district
  admin1?: string; // state
  lat: number;
  lon: number;
}

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

/** Pure: normalize Open-Meteo geocoding JSON → typed, valid results. */
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

/** Pure: normalize OpenStreetMap Nominatim (jsonv2 + addressdetails) → results. */
export function normalizeNominatim(json: unknown): GeoResult[] {
  if (!Array.isArray(json)) return [];
  const out: GeoResult[] = [];
  for (const raw of json) {
    const r = raw as Record<string, unknown>;
    const lat = typeof r.lat === "string" ? parseFloat(r.lat) : NaN;
    const lon = typeof r.lon === "string" ? parseFloat(r.lon) : NaN;
    if (!isValidCoord(lat, lon)) continue;
    const addr = (r.address as Record<string, unknown>) ?? {};
    const pick = (k: string): string | undefined =>
      typeof addr[k] === "string" ? (addr[k] as string) : undefined;
    const name =
      pick("village") ??
      pick("hamlet") ??
      pick("town") ??
      pick("city") ??
      (typeof r.name === "string" && r.name ? r.name : undefined) ??
      (typeof r.display_name === "string" ? r.display_name.split(",")[0]!.trim() : undefined);
    if (!name) continue;
    out.push({
      id: typeof r.place_id === "number" ? r.place_id : out.length,
      name,
      admin2: pick("state_district") ?? pick("county"),
      admin1: pick("state"),
      lat: roundCoord(lat),
      lon: roundCoord(lon),
    });
  }
  return out;
}

/** Search Indian villages via our /api/geocode route. Returns [] on any failure. */
export async function searchPlaces(query: string, signal?: AbortSignal): Promise<GeoResult[]> {
  const q = query.trim();
  if (q.length < 2) return [];
  try {
    const res = await fetch(`/api/geocode?q=${encodeURIComponent(q)}`, { signal });
    if (!res.ok) return [];
    const data = (await res.json()) as { results?: unknown };
    return Array.isArray(data.results) ? (data.results as GeoResult[]) : [];
  } catch {
    return [];
  }
}
