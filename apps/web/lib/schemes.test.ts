import { describe, expect, it } from "vitest";
import { SCHEMES } from "./schemes";

describe("SCHEMES", () => {
  it("has schemes with unique keys", () => {
    expect(SCHEMES.length).toBeGreaterThan(0);
    const keys = SCHEMES.map((s) => s.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it("every scheme has bilingual, non-empty content", () => {
    for (const s of SCHEMES) {
      for (const f of [s.name_te, s.name_en, s.what_te, s.what_en, s.who_te, s.who_en, s.how_te, s.how_en]) {
        expect(f.trim().length, s.key).toBeGreaterThan(0);
      }
    }
  });

  it("links to an official https site", () => {
    for (const s of SCHEMES) {
      expect(s.url.startsWith("https://"), s.key).toBe(true);
      expect(() => new URL(s.url)).not.toThrow();
    }
  });
});
