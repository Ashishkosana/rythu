import { afterEach, describe, expect, it, vi } from "vitest";
import { formatPlaceLabel, isSearchable, isValidCoord, placeName, roundCoord, searchPlaces } from "./geocode";
import { API_BASE } from "./api";
import type { Place } from "./types";

const REGONDA: Place = {
  id: 42,
  name: "Regonda",
  name_te: "రేగొండ",
  admin2: "Bhupalpally",
  admin1: "Telangana",
  lat: 18.2378,
  lon: 79.775,
};

describe("roundCoord", () => {
  it("clamps to 4 decimals", () => {
    expect(roundCoord(18.428712345)).toBe(18.4287);
    expect(roundCoord(79.749)).toBe(79.749);
  });
});

describe("isValidCoord", () => {
  it("accepts in-range coordinates", () => {
    expect(isValidCoord(18.44, 79.86)).toBe(true);
    expect(isValidCoord(-90, 180)).toBe(true);
  });
  it("rejects out-of-range or non-finite", () => {
    expect(isValidCoord(91, 0)).toBe(false);
    expect(isValidCoord(0, 181)).toBe(false);
    expect(isValidCoord(NaN, 0)).toBe(false);
    expect(isValidCoord(0, Infinity)).toBe(false);
  });
});

describe("place names", () => {
  it("shows the Telugu name in Telugu mode when OpenStreetMap has one", () => {
    expect(placeName(REGONDA, "te")).toBe("రేగొండ");
    expect(placeName(REGONDA, "en")).toBe("Regonda");
    expect(placeName({ name: "Kataram", name_te: null }, "te")).toBe("Kataram");
  });

  it("appends the district when it differs from the name", () => {
    expect(formatPlaceLabel(REGONDA)).toBe("Regonda, Bhupalpally");
    expect(formatPlaceLabel(REGONDA, "te")).toBe("రేగొండ, Bhupalpally");
  });

  it("shows only the name when the district matches or is absent", () => {
    expect(formatPlaceLabel({ name: "Bhupalpally", name_te: null, admin2: "Bhupalpally" })).toBe("Bhupalpally");
    expect(formatPlaceLabel({ name: "Warangal", name_te: null, admin2: null })).toBe("Warangal");
  });
});

describe("isSearchable", () => {
  it("mirrors the API's 2–60 characters after trimming", () => {
    expect(isSearchable("  a ")).toBe(false);
    expect(isSearchable("ab")).toBe(true);
    expect(isSearchable("x".repeat(60))).toBe(true);
    expect(isSearchable("x".repeat(61))).toBe(false);
  });
});

describe("searchPlaces", () => {
  afterEach(() => vi.unstubAllGlobals());

  function stubFetch(impl: () => Promise<Response>) {
    const fetchMock = vi.fn((url: string) => (void url, impl()));
    vi.stubGlobal("fetch", fetchMock);
    return fetchMock;
  }

  it("asks the API once, with the trimmed query", async () => {
    const fetchMock = stubFetch(async () => Response.json({ results: [REGONDA] }));
    expect(await searchPlaces("  Regonda ")).toEqual({ ok: true, places: [REGONDA] });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0]![0]).toBe(`${API_BASE}/v1/geocode?q=Regonda`);
  });

  it("tells 'nothing found' apart from 'could not search'", async () => {
    stubFetch(async () => Response.json({ results: [] }));
    expect(await searchPlaces("Atlantis")).toEqual({ ok: true, places: [] });

    stubFetch(async () => Response.json({ error: "x" }, { status: 502 }));
    expect(await searchPlaces("Regonda")).toEqual({ ok: false });

    stubFetch(async () => Promise.reject(new TypeError("offline")));
    expect(await searchPlaces("Regonda")).toEqual({ ok: false });

    stubFetch(async () => new Response("<html>proxy error</html>", { status: 200 }));
    expect(await searchPlaces("Regonda")).toEqual({ ok: false });

    stubFetch(async () => Response.json({ nope: true }));
    expect(await searchPlaces("Regonda")).toEqual({ ok: false });
  });

  it("does not call the API for a query it would reject", async () => {
    const fetchMock = stubFetch(async () => Response.json({ results: [] }));
    expect(await searchPlaces(" a ")).toEqual({ ok: true, places: [] });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
