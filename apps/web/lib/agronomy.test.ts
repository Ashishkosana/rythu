import { describe, expect, it } from "vitest";
import { CROP_DOSES, computeForArea, fertilizerFor } from "./agronomy";

describe("fertilizerFor — NPK kg → Urea/DAP/MOP", () => {
  it("matches the verified paddy worked example (per acre 48.6:24.3:16.2)", () => {
    const r = fertilizerFor(48.6, 24.3, 16.2);
    // From docs/agronomy-data.md: DAP ≈ 52.8 kg, Urea ≈ 85 kg, MOP = 27 kg
    expect(r.dapKg).toBeCloseTo(52.8, 0);
    expect(r.mopKg).toBeCloseTo(27.0, 0);
    expect(r.ureaKg).toBeCloseTo(85.0, 0);
  });

  it("subtracts the N that DAP already supplies (no nitrogen overdose)", () => {
    // If DAP's N were ignored, urea for 48.6 N would be ~105.7 kg; correct is ~85.
    const r = fertilizerFor(48.6, 24.3, 16.2);
    const naiveUrea = 48.6 / 0.46;
    expect(r.ureaKg).toBeLessThan(naiveUrea - 15);
  });

  it("delivers exactly the requested N when reconstructed", () => {
    const n = 48.6;
    const r = fertilizerFor(n, 24.3, 16.2);
    const nDelivered = r.dapKg * 0.18 + r.ureaKg * 0.46;
    expect(nDelivered).toBeCloseTo(n, 0);
  });

  it("never returns negative urea when DAP over-supplies N", () => {
    const r = fertilizerFor(5, 50, 5); // high P, low N
    expect(r.ureaKg).toBeGreaterThanOrEqual(0);
  });

  it("handles zero nutrients", () => {
    const r = fertilizerFor(0, 0, 0);
    expect(r.ureaKg).toBe(0);
    expect(r.dapKg).toBe(0);
    expect(r.mopKg).toBe(0);
  });
});

describe("computeForArea", () => {
  it("scales linearly with area", () => {
    const paddy = CROP_DOSES.find((c) => c.key === "paddy")!;
    const one = computeForArea(paddy, 1);
    const two = computeForArea(paddy, 2);
    expect(two.ureaKg).toBeCloseTo(one.ureaKg * 2, 1);
  });
});

describe("CROP_DOSES data integrity", () => {
  it("covers the 5 pilot crops with positive doses", () => {
    expect(CROP_DOSES.map((c) => c.key).sort()).toEqual(
      ["chilli", "cotton", "maize", "paddy", "red_gram"],
    );
    for (const c of CROP_DOSES) {
      expect(c.n, c.key).toBeGreaterThan(0);
      expect(c.p, c.key).toBeGreaterThan(0);
      expect(c.k, c.key).toBeGreaterThan(0);
      expect(c.source.startsWith("https://"), c.key).toBe(true);
    }
  });

  it("only paddy is high-confidence & verified; the rest need local verification", () => {
    const paddy = CROP_DOSES.find((c) => c.key === "paddy")!;
    expect(paddy.confidence).toBe("high");
    expect(paddy.needsVerification).toBe(false);
    for (const c of CROP_DOSES.filter((x) => x.key !== "paddy")) {
      expect(c.needsVerification, c.key).toBe(true);
    }
  });
});
