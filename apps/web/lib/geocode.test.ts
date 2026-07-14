import { describe, expect, it } from "vitest";
import {
  formatPlaceLabel,
  isValidCoord,
  normalizeGeoResults,
  normalizeNominatim,
  roundCoord,
} from "./geocode";

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

describe("formatPlaceLabel", () => {
  it("appends the district when it differs from the name", () => {
    expect(formatPlaceLabel({ name: "Regonda", admin2: "Bhupalpally" })).toBe(
      "Regonda, Bhupalpally",
    );
  });
  it("shows only the name when district matches or is absent", () => {
    expect(formatPlaceLabel({ name: "Bhupalpally", admin2: "Bhupalpally" })).toBe("Bhupalpally");
    expect(formatPlaceLabel({ name: "Warangal" })).toBe("Warangal");
  });
});

describe("normalizeGeoResults", () => {
  it("maps valid rows and rounds coordinates", () => {
    const out = normalizeGeoResults({
      results: [
        { id: 1, name: "Regonda", admin2: "Bhupalpally", admin1: "Telangana", latitude: 18.23781, longitude: 79.77502 },
      ],
    });
    expect(out).toEqual([
      { id: 1, name: "Regonda", admin2: "Bhupalpally", admin1: "Telangana", lat: 18.2378, lon: 79.775 },
    ]);
  });

  it("drops rows with missing name or bad coordinates", () => {
    const out = normalizeGeoResults({
      results: [
        { id: 1, latitude: 18.4, longitude: 79.8 }, // no name
        { id: 2, name: "Bad", latitude: 999, longitude: 79.8 }, // out of range
        { id: 3, name: "Good", latitude: 18.5, longitude: 79.7 },
      ],
    });
    expect(out.map((r) => r.name)).toEqual(["Good"]);
  });

  it("returns [] for malformed input", () => {
    expect(normalizeGeoResults(null)).toEqual([]);
    expect(normalizeGeoResults({})).toEqual([]);
    expect(normalizeGeoResults({ results: "nope" })).toEqual([]);
  });
});

describe("normalizeNominatim", () => {
  it("prefers village name from address details and parses string coords", () => {
    const out = normalizeNominatim([
      {
        place_id: 42,
        lat: "18.23781",
        lon: "79.77502",
        display_name: "Regonda, Bhupalpally, Telangana, India",
        address: { village: "Regonda", state_district: "Bhupalpally", state: "Telangana" },
      },
    ]);
    expect(out).toEqual([
      { id: 42, name: "Regonda", admin2: "Bhupalpally", admin1: "Telangana", lat: 18.2378, lon: 79.775 },
    ]);
  });

  it("falls back through hamlet/town/city then display_name", () => {
    const out = normalizeNominatim([
      { place_id: 1, lat: "18.5", lon: "79.7", address: { hamlet: "Tinyville", state: "Telangana" } },
      { place_id: 2, lat: "18.6", lon: "79.8", display_name: "Nowhere, X", address: {} },
    ]);
    expect(out.map((r) => r.name)).toEqual(["Tinyville", "Nowhere"]);
  });

  it("drops rows with invalid coordinates and handles non-arrays", () => {
    expect(normalizeNominatim([{ place_id: 1, lat: "999", lon: "79", address: { village: "Bad" } }])).toEqual([]);
    expect(normalizeNominatim(null)).toEqual([]);
    expect(normalizeNominatim({ results: [] })).toEqual([]);
  });
});
