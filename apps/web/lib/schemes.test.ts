import { describe, expect, it } from "vitest";
import { SCHEMES } from "./schemes";

const STATUSES = ["active", "verify", "at_risk", "closed", "suspended"];
const LEVELS = ["central", "state"];

describe("SCHEMES", () => {
  it("has schemes with unique keys", () => {
    expect(SCHEMES.length).toBeGreaterThanOrEqual(15);
    const keys = SCHEMES.map((s) => s.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it("every scheme has valid status, level, and priority", () => {
    for (const s of SCHEMES) {
      expect(STATUSES, s.key).toContain(s.status);
      expect(LEVELS, s.key).toContain(s.level);
      expect(s.priority, s.key).toBeGreaterThanOrEqual(1);
      expect(s.priority, s.key).toBeLessThanOrEqual(5);
    }
  });

  it("every scheme has bilingual, non-empty core content", () => {
    for (const s of SCHEMES) {
      for (const f of [s.name_te, s.name_en, s.what_te, s.what_en, s.who_te, s.who_en, s.how_te, s.how_en]) {
        expect(f.trim().length, s.key).toBeGreaterThan(0);
      }
    }
  });

  it("honesty notes, when present, are bilingual", () => {
    for (const s of SCHEMES) {
      if (s.honesty_te || s.honesty_en) {
        expect(s.honesty_te?.trim().length, s.key).toBeGreaterThan(0);
        expect(s.honesty_en?.trim().length, s.key).toBeGreaterThan(0);
      }
    }
  });

  it("links to an official https site", () => {
    for (const s of SCHEMES) {
      expect(s.url.startsWith("https://"), s.key).toBe(true);
      expect(() => new URL(s.url)).not.toThrow();
    }
  });

  it("Rythu Bandhu is retired — no stale reference; Rythu Bharosa points to its portal", () => {
    const blob = JSON.stringify(SCHEMES).toLowerCase();
    expect(blob).not.toContain("bandhu");
    const rb = SCHEMES.find((s) => s.key === "rythu_bharosa");
    expect(rb?.url).toContain("rythubharosa.telangana.gov.in");
  });

  it("covers key gaps the research flagged", () => {
    const keys = SCHEMES.map((s) => s.key);
    for (const k of ["rythu_bima", "free_ag_power", "indiramma_atmiya_bharosa", "pm_kisan", "pmfby", "kcc"]) {
      expect(keys, `missing ${k}`).toContain(k);
    }
  });
});
