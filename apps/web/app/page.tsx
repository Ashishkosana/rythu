import WeatherScreen from "@/components/WeatherScreen";
import LocationPicker from "@/components/LocationPicker";
import RestoreLocation from "@/components/RestoreLocation";
import { DEFAULT_PLACE } from "@/lib/locations";
import { isValidCoord } from "@/lib/geocode";
import type { WeatherContract } from "@/lib/types";

// The Python weather backend. Server-side fetch, so the phone only ever talks to Next.
const API = process.env.WEATHER_API ?? "http://127.0.0.1:8001";
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

  let data: WeatherContract | null = null;
  try {
    const params = new URLSearchParams({ crop, water });
    if (hasCoords) {
      params.set("lat", String(lat));
      params.set("lon", String(lon));
    }
    const res = await fetch(`${API}/weather?${params.toString()}`, { cache: "no-store" });
    // Any HTTP error (400/429/5xx) must route to the honest fallback, NOT render as a
    // forecast — otherwise the error body slips past and crashes the weather screen.
    if (!res.ok) throw new Error(`weather API ${res.status}`);
    const body = (await res.json()) as WeatherContract;
    if (!Array.isArray(body?.daily)) throw new Error("malformed weather response");
    data = body;
  } catch {
    data = null;
  }

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
