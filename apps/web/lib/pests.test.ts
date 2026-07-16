import { describe, expect, it } from "vitest";
import { PESTS } from "./pests";
import { CROP_DOSES } from "./agronomy";

describe("PESTS", () => {
  it("has unique keys and covers the pilot crops", () => {
    const keys = PESTS.map((p) => p.key);
    expect(new Set(keys).size).toBe(keys.length);
    const crops = new Set(PESTS.map((p) => p.cropKey));
    for (const c of ["paddy", "cotton", "maize", "red_gram", "chilli"]) {
      expect(crops.has(c), `no pest for ${c}`).toBe(true);
    }
  });

  it("every cropKey maps to a real crop", () => {
    const valid = new Set(CROP_DOSES.map((c) => c.key));
    for (const p of PESTS) expect(valid.has(p.cropKey), p.key).toBe(true);
  });

  it("every pest has full bilingual, actionable content + official source", () => {
    for (const p of PESTS) {
      for (const f of [p.name_te, p.name_en, p.symptom_te, p.threshold_te, p.ipmFirst_te, p.chemical_te]) {
        expect(f.trim().length, p.key).toBeGreaterThan(0);
      }
      expect(p.source.startsWith("https://"), p.key).toBe(true);
    }
  });

  it("only the verified paddy row is not flagged for local verification", () => {
    const bph = PESTS.find((p) => p.key === "paddy_bph")!;
    expect(bph.needsVerification).toBe(false);
    for (const p of PESTS.filter((x) => x.key !== "paddy_bph")) {
      expect(p.needsVerification, p.key).toBe(true);
    }
  });
});
