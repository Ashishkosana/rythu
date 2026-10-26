import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { COVERAGE, COVERAGE_MESSAGE, inCoverage } from "./coverage";

describe("coverage box", () => {
  it("matches the backend's (services/weather/.../domain/coverage.py)", () => {
    const py = readFileSync(
      new URL("../../../services/weather/src/rythu_weather/domain/coverage.py", import.meta.url),
      "utf8",
    );
    const pair = (name: string) => {
      const m = py.match(new RegExp(String.raw`^${name} = \(([\d.]+), ([\d.]+)\)`, "m"));
      if (!m) throw new Error(`${name} not found in coverage.py`);
      return [Number(m[1]), Number(m[2])];
    };
    expect(pair("COVERAGE_LAT")).toEqual([COVERAGE.latMin, COVERAGE.latMax]);
    expect(pair("COVERAGE_LON")).toEqual([COVERAGE.lonMin, COVERAGE.lonMax]);
  });
});

describe("inCoverage (Telangana + border)", () => {
  it.each([
    ["Bhupalpally", 18.44, 79.86],
    ["Hyderabad", 17.385, 78.4867],
    ["Adilabad (north edge)", 19.92, 78.53],
    ["Vijayawada (border margin, AP)", 16.5, 80.6],
  ])("serves %s", (_name, lat, lon) => {
    expect(inCoverage(lat, lon)).toBe(true);
  });

  it.each([
    ["Chennai", 13.08, 80.27],
    ["Mumbai", 19.07, 72.88],
    ["Nagpur", 21.15, 79.09],
    ["New York", 40.71, -74.0],
  ])("rejects %s", (_name, lat, lon) => {
    expect(inCoverage(lat, lon)).toBe(false);
  });

  it("rejects non-numbers", () => {
    expect(inCoverage(NaN, 79)).toBe(false);
    expect(inCoverage(18, Infinity)).toBe(false);
  });

  it("has a bilingual message", () => {
    expect(COVERAGE_MESSAGE.te).toContain("తెలంగాణ");
    expect(COVERAGE_MESSAGE.en).toContain("Telangana");
  });
});
