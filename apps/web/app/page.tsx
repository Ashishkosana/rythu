import WeatherScreen from "@/components/WeatherScreen";
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

  let data: WeatherContract | null = null;
  let error: string | null = null;
  try {
    const res = await fetch(`${API}/weather?crop=${crop}&water=${water}`, { cache: "no-store" });
    data = (await res.json()) as WeatherContract;
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  if (!data) {
    return (
      <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-2 p-8 text-center text-slate-700">
        <p className="text-2xl">🌧️</p>
        <p className="font-semibold">Weather backend not reachable</p>
        <p className="text-sm text-slate-500">
          Start it with{" "}
          <code className="rounded bg-slate-100 px-1">uv run python -m rythu_weather.app.local_server 8001</code>
        </p>
        {error && <p className="text-xs text-slate-400">{error}</p>}
      </main>
    );
  }

  return <WeatherScreen data={data} crop={crop} />;
}
