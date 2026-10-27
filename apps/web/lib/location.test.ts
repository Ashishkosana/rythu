import { describe, expect, it } from "vitest";
import { DEFAULT_LABEL, locationQuery, resolveLocation } from "./location";

const params = (q: string) => new URLSearchParams(q);
const SAVED = { lat: 18.2378, lon: 79.775, place: "Regonda" };

describe("resolveLocation", () => {
  it("prefers the point in the URL", () => {
    expect(resolveLocation(params("lat=18.33&lon=79.88&place=Kataram"), SAVED)).toEqual({
      lat: 18.33,
      lon: 79.88,
      place: "Kataram",
      outside: false,
    });
  });

  it("flags a URL point outside coverage instead of fetching it", () => {
    expect(resolveLocation(params("lat=13.08&lon=80.27"), SAVED).outside).toBe(true);
  });

  it("falls back to the saved village, then to the backend's default", () => {
    expect(resolveLocation(params(""), SAVED)).toEqual({ ...SAVED, outside: false });
    expect(resolveLocation(params("lat=abc&lon=1"), SAVED).place).toBe("Regonda");
    expect(resolveLocation(params("lat=&lon="), null)).toEqual({ lat: null, lon: null, place: DEFAULT_LABEL, outside: false });
  });

  it("never restores a saved place outside coverage", () => {
    expect(resolveLocation(params(""), { lat: 13.08, lon: 80.27, place: "Chennai" }).lat).toBeNull();
  });
});

describe("locationQuery", () => {
  it("keeps the place and water source across a crop switch", () => {
    const q = new URLSearchParams(locationQuery({ lat: 18.33, lon: 79.88, place: "Kataram", outside: false }, "borewell"));
    expect(Object.fromEntries(q)).toEqual({ water: "borewell", lat: "18.33", lon: "79.88", place: "Kataram" });
  });

  it("omits coordinates for the default place", () => {
    const q = new URLSearchParams(locationQuery({ lat: null, lon: null, place: DEFAULT_LABEL, outside: false }, "rainfed"));
    expect(q.has("lat")).toBe(false);
  });
});
