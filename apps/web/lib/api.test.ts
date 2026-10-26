import { afterEach, describe, expect, it, vi } from "vitest";
import { API_BASE, ApiUnavailable, OutsideCoverage, fetchWeather } from "./api";
import { contract } from "./test-fixtures";

const P = { lat: 18.33, lon: 79.88, crop: "chilli", water: "rainfed" } as const;

function stubFetch(impl: (url: string, init?: RequestInit) => Promise<Response>) {
  const fetchMock = vi.fn(impl);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("fetchWeather", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("asks /v1/weather with a plain GET (no custom headers → no CORS preflight)", async () => {
    const fetchMock = stubFetch(async () => Response.json(contract()));
    expect(await fetchWeather(P)).toEqual(contract());
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe(`${API_BASE}/v1/weather?crop=chilli&water=rainfed&lat=18.33&lon=79.88`);
    expect(init?.headers).toBeUndefined();
    expect(init?.signal).toBeInstanceOf(AbortSignal);
  });

  it("omits lat/lon for the default place", async () => {
    const fetchMock = stubFetch(async () => Response.json(contract()));
    await fetchWeather({ ...P, lat: null, lon: null });
    expect(fetchMock.mock.calls[0]![0]).toBe(`${API_BASE}/v1/weather?crop=chilli&water=rainfed`);
  });

  it("turns outside_coverage into its own error", async () => {
    stubFetch(async () => Response.json({ error: "x", code: "outside_coverage" }, { status: 400 }));
    await expect(fetchWeather(P)).rejects.toBeInstanceOf(OutsideCoverage);
  });

  it("never lets an error body or a broken body through as a forecast", async () => {
    stubFetch(async () => Response.json({ error: "x" }, { status: 503, headers: { "X-Request-Id": "r-1" } }));
    const err = await fetchWeather(P).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiUnavailable);
    expect((err as ApiUnavailable).requestId).toBe("r-1");

    stubFetch(async () => new Response("<html>gateway</html>", { status: 200 }));
    await expect(fetchWeather(P)).rejects.toBeInstanceOf(ApiUnavailable);

    stubFetch(async () => Response.json({ daily: [] }));
    await expect(fetchWeather(P)).rejects.toBeInstanceOf(ApiUnavailable);

    stubFetch(async () => Promise.reject(new TypeError("Failed to fetch")));
    await expect(fetchWeather(P)).rejects.toBeInstanceOf(ApiUnavailable);
  });

  it("lets a caller's abort through as an abort, not an outage", async () => {
    stubFetch(async (_url, init) => {
      init?.signal?.throwIfAborted();
      return Response.json(contract());
    });
    const ctrl = new AbortController();
    ctrl.abort();
    const err = await fetchWeather(P, ctrl.signal).catch((e: unknown) => e);
    expect(err).not.toBeInstanceOf(ApiUnavailable);
  });
});
