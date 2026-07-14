import { describe, expect, it } from "vitest";
import { CROP_GUIDES } from "./crops";

// Backend Crop enum (services/weather domain) — keys must stay in sync.
const BACKEND_CROPS = ["cotton", "paddy", "red_gram", "maize", "chilli"].sort();

describe("CROP_GUIDES", () => {
  it("covers exactly the backend pilot crop set", () => {
    expect(CROP_GUIDES.map((c) => c.key).sort()).toEqual(BACKEND_CROPS);
  });

  it("every card has bilingual, non-empty fields", () => {
    for (const c of CROP_GUIDES) {
      for (const f of [c.name_te, c.name_en, c.season_te, c.season_en, c.water_te, c.water_en, c.sow_te, c.sow_en, c.emoji]) {
        expect(f.trim().length, `${c.key}`).toBeGreaterThan(0);
      }
    }
  });

  it("tips are paired te/en and non-empty", () => {
    for (const c of CROP_GUIDES) {
      expect(c.tips_te.length, c.key).toBeGreaterThan(0);
      expect(c.tips_te.length).toBe(c.tips_en.length);
    }
  });

  it("cites an https source", () => {
    for (const c of CROP_GUIDES) {
      expect(c.source.startsWith("https://"), c.key).toBe(true);
    }
  });
});
