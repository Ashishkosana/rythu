import WeatherScreen from "@/components/WeatherScreen";
import LocationPicker from "@/components/LocationPicker";
import { DEFAULT_PLACE } from "@/lib/locations";
import { isValidCoord } from "@/lib/geocode";
import type { WeatherContract } from "@/lib/types";

// The Python weather backend. Server-side fetch, so the phone only ever talks to Next.
const API = process.env.WEATHER_API ?? "http://127.0.0.1:8001";
const CROPS = new Set(["chilli", "cotton", "paddy", "red_gram", "maize"]);

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
  const water = first(sp.water) ?? "rainfed";

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
  let error: string | null = null;
  try {
    const coords = hasCoords ? `&lat=${lat}&lon=${lon}` : "";
    const res = await fetch(`${API}/weather?crop=${crop}&water=${water}${coords}`, { cache: "no-store" });
    data = (await res.json()) as WeatherContract;
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  if (!data) {
    return (
      <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-2 p-8 text-center text-stone-700">
        <p className="text-2xl">🌧️</p>
        <p className="font-semibold">Weather backend not reachable</p>
        {error && <p className="text-xs text-stone-400">{error}</p>}
      </main>
    );
  }

  return (
    <WeatherScreen data={data} crop={crop} locationQuery={locationQuery}>
      <LocationPicker currentPlace={place} />
    </WeatherScreen>
  );
}
