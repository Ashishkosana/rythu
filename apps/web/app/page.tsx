import WeatherScreen from "@/components/WeatherScreen";
import LocationPicker from "@/components/LocationPicker";
import RestoreLocation from "@/components/RestoreLocation";
import { DEFAULT_PLACE } from "@/lib/locations";
import { isValidCoord } from "@/lib/geocode";
import { COVERAGE_MESSAGE, inCoverage } from "@/lib/coverage";
import type { WeatherContract } from "@/lib/types";

// The Python weather backend. Server-side fetch, so the phone only ever talks to Next.
const API = process.env.WEATHER_API ?? "http://127.0.0.1:8001";
// Cap the wait on the backend (Lambda allows 15 s). Past this, the honest fallback is better than a hang.
const WEATHER_TIMEOUT_MS = 10_000;
const CROPS = new Set(["chilli", "cotton", "paddy", "red_gram", "maize"]);
// Mirror the backend WaterSource enum — validate so we never emit a self-inflicted 400.
const WATERS = new Set(["canal_lift", "tank", "borewell", "rainfed"]);

export const dynamic = "force-dynamic"; // always fetch a fresh forecast

function first(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const sp = await searchParams;
  const rawCrop = first(sp.crop);
  const crop = CROPS.has(rawCrop ?? "") ? (rawCrop as string) : "chilli"; // mirchi = main local crop
  const rawWater = first(sp.water);
  const water = WATERS.has(rawWater ?? "") ? (rawWater as string) : "rainfed";

  // Location: honor ?lat&lon when valid, else fall back to the district HQ.
  const lat = Number(first(sp.lat));
  const lon = Number(first(sp.lon));
  const hasCoords = first(sp.lat) !== undefined && first(sp.lon) !== undefined && isValidCoord(lat, lon);
  const place =
    first(sp.place) ?? (hasCoords ? "ఎంచుకున్న ప్రాంతం · Selected" : `${DEFAULT_PLACE.name_te} · ${DEFAULT_PLACE.name_en}`);

  // Preserved across crop switches so changing crop doesn't reset the location.
  const loc = new URLSearchParams({ water });
  if (hasCoords) {
    loc.set("lat", String(lat));
    loc.set("lon", String(lon));
  }
  loc.set("place", place);
  const locationQuery = loc.toString();

  // Outside the area we serve (old link, or GPS while travelling): say so, and offer the picker
  // so the farmer can choose a Telangana village — never a dead-end error page.
  if (hasCoords && !inCoverage(lat, lon)) return <CoverageNotice place={place} />;

  let data: WeatherContract | null = null;
  // Sent to the backend, which echoes it as X-Request-Id and stamps it on its own log lines,
  // so one id finds this failure on both sides.
  const requestId = crypto.randomUUID();
  let outsideCoverage = false;
  try {
    const params = new URLSearchParams({ crop, water });
    if (hasCoords) {
      params.set("lat", String(lat));
      params.set("lon", String(lon));
    }
    const res = await fetch(`${API}/weather?${params.toString()}`, {
      cache: "no-store",
      headers: { "X-Request-Id": requestId },
      signal: AbortSignal.timeout(WEATHER_TIMEOUT_MS),
    });
    // Backend is the authority on coverage (guards against the two boxes drifting apart).
    if (res.status === 400) {
      const err = (await res.json().catch(() => null)) as { code?: string } | null;
      outsideCoverage = err?.code === "outside_coverage";
    }
    // Any HTTP error (400/429/5xx) must route to the honest fallback, NOT render as a
    // forecast — otherwise the error body slips past and crashes the weather screen.
    if (!res.ok) throw new Error(`weather API ${res.status}`);
    const body = (await res.json()) as WeatherContract;
    if (!Array.isArray(body?.daily)) throw new Error("malformed weather response");
    data = body;
  } catch (err) {
    console.error(JSON.stringify({ event: "weather.fetch_failed", request_id: requestId, error: String(err) }));
    data = null;
  }

  if (outsideCoverage) return <CoverageNotice place={place} />;
  if (!data) {
    return (
      <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-3 p-8 text-center text-stone-700">
        <p className="text-3xl">🌧️</p>
        <p className="font-semibold">వాతావరణ సమాచారం అందుబాటులో లేదు</p>
        <p className="text-sm text-stone-500">కాసేపటి తర్వాత మళ్లీ ప్రయత్నించండి · Please try again shortly</p>
      </main>
    );
  }

  return (
    <>
      <RestoreLocation />
      <WeatherScreen data={data} crop={crop} place={place} locationQuery={locationQuery}>
        <LocationPicker currentPlace={place} />
      </WeatherScreen>
    </>
  );
}

function CoverageNotice({ place }: { place: string }) {
  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center gap-4 p-6 pb-28 text-center text-stone-700">
      <p className="text-3xl" aria-hidden>
        📍
      </p>
      <p className="font-semibold">{COVERAGE_MESSAGE.te}</p>
      <p className="text-sm text-stone-600">{COVERAGE_MESSAGE.en} · మీ ఊరిని ఎంచుకోండి / choose your village</p>
      <div className="text-left">
        <LocationPicker currentPlace={place} />
      </div>
    </main>
  );
}
