// Typed client for the Rythu API. The browser calls the API directly (CORS); the base URL is
// inlined at build time from NEXT_PUBLIC_API_BASE, defaulting to the local dev server.
// Shapes come from the generated contract types (lib/types.ts), never hand-written.

import type { Crop, WaterSource, WeatherContract } from "./types";

export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8001").replace(/\/+$/, "");

// Past this, the honest "unavailable" screen (or the saved copy) beats a spinner.
export const REQUEST_TIMEOUT_MS = 10_000;

/** The point is outside the area Rythu serves (the backend is the authority). */
export class OutsideCoverage extends Error {
  constructor() {
    super("outside coverage");
    this.name = "OutsideCoverage";
  }
}

/** The API could not answer (network, timeout, 4xx/5xx, malformed body). */
export class ApiUnavailable extends Error {
  constructor(
    message: string,
    readonly requestId: string | null = null,
  ) {
    super(message);
    this.name = "ApiUnavailable";
  }
}

export interface WeatherParams {
  lat: number | null; // null (with lon) = the backend's default place
  lon: number | null;
  crop: Crop;
  water: WaterSource;
}

/** The caller's signal (unmount / superseded query) or our timeout, whichever comes first. */
export function withTimeout(signal: AbortSignal | undefined, ms: number): AbortSignal {
  const timeout = AbortSignal.timeout(ms);
  if (!signal) return timeout;
  if (typeof AbortSignal.any === "function") return AbortSignal.any([signal, timeout]);
  return signal; // very old WebView: the caller's signal still cancels
}

/** fetch() against the API with our timeout; network failures become ApiUnavailable. */
export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const signal = init.signal ?? undefined;
  try {
    return await fetch(`${API_BASE}${path}`, { ...init, signal: withTimeout(signal, REQUEST_TIMEOUT_MS) });
  } catch (err) {
    if (signal?.aborted) throw err; // superseded, not a failure
    throw new ApiUnavailable(`network: ${String(err)}`);
  }
}

export async function getJson(path: string, signal?: AbortSignal): Promise<{ res: Response; body: unknown }> {
  // No custom request headers on purpose: a plain GET needs no CORS preflight (one round trip less).
  const res = await apiFetch(path, { signal });
  const body: unknown = await res.json().catch(() => null);
  return { res, body };
}

export async function fetchWeather(p: WeatherParams, signal?: AbortSignal): Promise<WeatherContract> {
  const q = new URLSearchParams({ crop: p.crop, water: p.water });
  if (p.lat !== null && p.lon !== null) {
    q.set("lat", String(p.lat));
    q.set("lon", String(p.lon));
  }
  const { res, body } = await getJson(`/v1/weather?${q.toString()}`, signal);
  const requestId = res.headers.get("X-Request-Id");
  if (res.status === 400 && (body as { code?: string } | null)?.code === "outside_coverage") {
    throw new OutsideCoverage();
  }
  // Any HTTP error must reach the honest fallback, never render as a forecast.
  if (!res.ok) throw new ApiUnavailable(`weather API ${res.status}`, requestId);
  if (!isWeatherContract(body)) throw new ApiUnavailable("malformed weather response", requestId);
  return body;
}

/** Just enough shape-checking that a proxy's HTML error page can't crash the screen. */
function isWeatherContract(v: unknown): v is WeatherContract {
  const b = v as Partial<WeatherContract> | null;
  return (
    !!b &&
    Array.isArray(b.daily) &&
    Array.isArray(b.hourly_rain) &&
    Array.isArray(b.farming_read) &&
    typeof b.upstream_fetched_at === "string" &&
    typeof b.reliability === "object"
  );
}
