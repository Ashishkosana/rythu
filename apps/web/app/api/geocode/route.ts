import { normalizeGeoResults, normalizeNominatim, type GeoResult } from "@/lib/geocode";

// Server-side village search. OSM (Nominatim) has the best coverage of small
// Indian villages; Open-Meteo is the fallback. Proxying here lets us send a
// proper User-Agent (OSM policy), cache for a day, and swap providers without
// touching the client.

export const runtime = "nodejs";

const NOMINATIM = "https://nominatim.openstreetmap.org/search";
const OPEN_METEO = "https://geocoding-api.open-meteo.com/v1/search";
const DAY = 86400;

async function fromNominatim(q: string): Promise<GeoResult[]> {
  const url = `${NOMINATIM}?q=${encodeURIComponent(q)}&format=jsonv2&countrycodes=in&limit=8&addressdetails=1`;
  const res = await fetch(url, {
    headers: {
      // OSM usage policy requires an identifying User-Agent.
      "User-Agent": "Rythu/1.0 (farmer weather app; github.com/Ashishkosana/rythu)",
      "Accept-Language": "en",
    },
    next: { revalidate: DAY },
  });
  if (!res.ok) return [];
  return normalizeNominatim(await res.json());
}

async function fromOpenMeteo(q: string): Promise<GeoResult[]> {
  const url = `${OPEN_METEO}?name=${encodeURIComponent(q)}&count=8&country=IN&language=en`;
  const res = await fetch(url, { next: { revalidate: DAY } });
  if (!res.ok) return [];
  return normalizeGeoResults(await res.json());
}

export async function GET(request: Request): Promise<Response> {
  const q = new URL(request.url).searchParams.get("q")?.trim() ?? "";
  // Village names are short — bound the query so this can't be abused as an open,
  // unbounded proxy to Nominatim/Open-Meteo.
  if (q.length < 2 || q.length > 60) return Response.json({ results: [] });

  let results: GeoResult[] = [];
  try {
    results = await fromNominatim(q);
  } catch {
    /* fall through to Open-Meteo */
  }
  if (results.length === 0) {
    try {
      results = await fromOpenMeteo(q);
    } catch {
      /* return empty */
    }
  }

  // Only cache real hits — don't let empty/garbage queries pin an empty result set.
  const cacheControl =
    results.length > 0
      ? "public, max-age=86400, stale-while-revalidate=604800"
      : "no-store";
  return Response.json({ results }, { headers: { "Cache-Control": cacheControl } });
}
