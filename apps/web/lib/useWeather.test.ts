import { describe, expect, it } from "vitest";
import { MAX_SAVED_AGE_MS } from "./freshness";
import { contract } from "./test-fixtures";
import type { WeatherParams } from "./api";
import { pickAnswer, weatherKey } from "./useWeather";

const T0 = Date.parse("2026-10-26T09:00:00+05:30");
const GOOD = contract();
const DEGRADED = contract({ degraded: true, note_en: "upstream down", farming_read: [], daily: [] });

describe("pickAnswer", () => {
  it("takes a real answer as is", () => {
    expect(pickAnswer(GOOD, undefined, T0)).toBe(GOOD);
  });

  it("prefers the device's real forecast (≤ 6 h) over a degraded answer, labelled as saved", () => {
    const shown = pickAnswer(DEGRADED, GOOD, T0 + 60_000);
    expect(shown.degraded).toBeUndefined();
    expect(shown.reliability.is_offline_cache).toBe(true);
    expect(GOOD.reliability.is_offline_cache).toBe(false); // the cached object is not mutated
  });

  it("does not resurrect a copy older than 6 h", () => {
    expect(pickAnswer(DEGRADED, GOOD, T0 + MAX_SAVED_AGE_MS + 1)).toBe(DEGRADED);
  });

  it("returns the degraded answer when there is nothing better", () => {
    expect(pickAnswer(DEGRADED, undefined, T0)).toBe(DEGRADED);
    expect(pickAnswer(DEGRADED, DEGRADED, T0)).toBe(DEGRADED);
  });
});

describe("weatherKey", () => {
  it("separates places, crops and water sources", () => {
    const base: WeatherParams = { lat: 18.33, lon: 79.88, crop: "chilli", water: "rainfed" };
    const variants: WeatherParams[] = [base, { ...base, crop: "paddy" }, { ...base, water: "borewell" }, { ...base, lat: 18.34 }];
    const keys = variants.map(
      (p) => JSON.stringify(weatherKey(p)),
    );
    expect(new Set(keys).size).toBe(4);
  });
});
