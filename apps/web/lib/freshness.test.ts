import { describe, expect, it } from "vitest";
import { MAX_SAVED_AGE_MS, ageLabel, ageMs, asOf, isTooOld, localDate, sourceStamp } from "./freshness";
import type { DailyPoint, HourlyRain } from "./types";

const FETCHED = "2026-10-26T09:00:00+05:30";
const T0 = Date.parse(FETCHED);
const MIN = 60_000;
const HOUR = 60 * MIN;

describe("age", () => {
  it("is measured on the device and never negative", () => {
    expect(ageMs(FETCHED, T0 + 8 * MIN)).toBe(8 * MIN);
    expect(ageMs(FETCHED, T0 - 5 * MIN)).toBe(0); // device clock behind the server's
    expect(ageMs("garbage", T0)).toBe(Number.POSITIVE_INFINITY);
  });

  it("uses the server's buckets, in both languages", () => {
    expect(ageLabel(FETCHED, T0 + 90_000, "en")).toBe("just now");
    expect(ageLabel(FETCHED, T0 + 8 * MIN, "en")).toBe("8 min ago");
    expect(ageLabel(FETCHED, T0 + 8 * MIN, "te")).toBe("8 నిమిషాల క్రితం");
    expect(ageLabel(FETCHED, T0 + 3 * HOUR + 59 * MIN, "en")).toBe("3 hr ago");
    expect(ageLabel(FETCHED, T0 + 3 * HOUR, "te")).toBe("3 గంటల క్రితం");
    expect(ageLabel(FETCHED, T0 + 30 * HOUR, "en")).toMatch(/26 Oct/);
  });

  it("stamps the source with the age at the moment of reading", () => {
    const data = { resolution_km: 11, upstream_fetched_at: FETCHED };
    expect(sourceStamp(data, T0 + 8 * MIN, "en")).toBe("Source: Open-Meteo (~11 km) · updated 8 min ago");
    expect(sourceStamp(data, T0 + 20 * MIN, "en")).toBe("Source: Open-Meteo (~11 km) · updated 20 min ago");
    expect(sourceStamp(data, T0, "te")).toContain("Open-Meteo (~11 కి.మీ)");
  });

  it("treats a copy older than 6 hours as too old to show", () => {
    expect(isTooOld({ upstream_fetched_at: FETCHED }, T0 + MAX_SAVED_AGE_MS)).toBe(false);
    expect(isTooOld({ upstream_fetched_at: FETCHED }, T0 + MAX_SAVED_AGE_MS + 1)).toBe(true);
    expect(isTooOld({ upstream_fetched_at: "garbage" }, T0)).toBe(true);
  });
});

describe("asOf", () => {
  const hour = (iso: string, p: number): HourlyRain => ({
    time_local: iso,
    precipitation_probability: p,
    precipitation_mm: 0,
    temperature_c: 30,
    relative_humidity: 60,
    wind_speed_kmh: 5,
    weather_code: 0,
    category: "clear",
    emoji: "☀️",
  });
  const day = (date: string): DailyPoint => ({
    date,
    precipitation_probability_max: 10,
    precipitation_sum_mm: 0,
    temperature_max_c: 32,
    temperature_min_c: 22,
    wind_speed_max_kmh: 10,
    weather_code: 0,
    category: "clear",
    emoji: "☀️",
    farm_note: "",
  });
  const data = {
    timezone: "Asia/Kolkata",
    hourly_rain: [
      hour("2026-10-26T09:00:00+05:30", 90), // this morning's rain …
      hour("2026-10-26T10:00:00+05:30", 80),
      hour("2026-10-26T11:00:00+05:30", 10),
      hour("2026-10-26T12:00:00+05:30", 5),
    ],
    daily: [day("2026-10-26"), day("2026-10-27"), day("2026-10-28")],
  };

  it("drops hours that have passed but keeps the current one", () => {
    const at = Date.parse("2026-10-26T11:30:00+05:30");
    expect(asOf(data, at).hourly_rain.map((h) => h.precipitation_probability)).toEqual([10, 5]);
  });

  it("drops days before today in the forecast's time zone (not the device's)", () => {
    // 00:30 IST on the 27th is still the 26th in UTC.
    const at = Date.parse("2026-10-27T00:30:00+05:30");
    expect(localDate(at, "Asia/Kolkata")).toBe("2026-10-27");
    expect(asOf(data, at).daily.map((d) => d.date)).toEqual(["2026-10-27", "2026-10-28"]);
  });

  it("changes nothing for a fresh copy", () => {
    const at = Date.parse("2026-10-26T09:05:00+05:30");
    expect(asOf(data, at)).toEqual(data);
  });
});
