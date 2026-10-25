import { describe, expect, it } from "vitest";
import { CROPS, WATER_SOURCES, isCrop, isWaterSource } from "./types";

describe("runtime enum guards (lists are compile-checked against the generated backend enums)", () => {
  it("accepts every listed value and nothing else", () => {
    for (const c of CROPS) expect(isCrop(c)).toBe(true);
    for (const w of WATER_SOURCES) expect(isWaterSource(w)).toBe(true);
    for (const bad of [undefined, "", "banana", "CHILLI", "chilli "]) {
      expect(isCrop(bad)).toBe(false);
      expect(isWaterSource(bad)).toBe(false);
    }
  });

  it("keeps chilli first (the default crop and first chip)", () => {
    expect(CROPS[0]).toBe("chilli");
  });
});
