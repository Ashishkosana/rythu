import { describe, expect, it } from "vitest";
import { HERO_HOURS, nextHoursChance } from "./hero";

const row = (p: number | null) => ({ precipitation_probability: p });

describe("nextHoursChance", () => {
  it("is the highest known chance in the next 12 hourly rows", () => {
    expect(nextHoursChance([row(10), row(null), row(55), row(30)])).toBe(55);
  });

  it("ignores rows beyond the window (e.g. rain tomorrow afternoon)", () => {
    const rows = [...Array(HERO_HOURS).fill(row(5)), row(95)];
    expect(nextHoursChance(rows)).toBe(5);
  });

  it("never shows rain that already fell: the backend's rows start at the current hour", () => {
    // Only the rows passed in count — there is no daily (whole-day) fallback.
    expect(nextHoursChance([row(0), row(5)])).toBe(5);
  });

  it("is null (shown as –) when nothing is known", () => {
    expect(nextHoursChance([])).toBeNull();
    expect(nextHoursChance([row(null), row(null)])).toBeNull();
  });
});
