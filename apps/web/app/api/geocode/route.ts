// Thin pass-through to the backend's GET /v1/geocode, which owns village search (Nominatim policy,
// coverage filter, caching). It exists only until the static export (S8), when the browser calls
// the API directly; nothing here may grow logic of its own.

export const runtime = "nodejs";

const API = process.env.WEATHER_API ?? "http://127.0.0.1:8001";
// Backend worst case: queue for a turn (3 s) + Nominatim (3 s) + Open-Meteo fallback (3 s).
const TIMEOUT_MS = 10_000;

export async function GET(request: Request): Promise<Response> {
  const q = new URL(request.url).searchParams.get("q") ?? "";
  const requestId = request.headers.get("X-Request-Id") ?? crypto.randomUUID();
  try {
    const res = await fetch(`${API}/v1/geocode?q=${encodeURIComponent(q)}`, {
      headers: { "X-Request-Id": requestId },
      signal: AbortSignal.timeout(TIMEOUT_MS),
      cache: "no-store", // the backend's Cache-Control is passed on to the browser below
    });
    return new Response(await res.text(), {
      status: res.status,
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": res.headers.get("Cache-Control") ?? "no-store",
        "X-Request-Id": res.headers.get("X-Request-Id") ?? requestId,
      },
    });
  } catch {
    return Response.json(
      { error: "village search is unavailable", code: "upstream_unavailable" },
      { status: 502, headers: { "Cache-Control": "no-store", "X-Request-Id": requestId } },
    );
  }
}
