import { describe, expect, it } from "vitest";
import { skyKind, skyTheme } from "./sky";

describe("skyKind", () => {
  it("maps WMO codes to the right sky", () => {
    expect(skyKind(0, false)).toBe("clear");
    expect(skyKind(1, false)).toBe("clear");
    expect(skyKind(2, false)).toBe("cloudy");
    expect(skyKind(45, false)).toBe("cloudy"); // fog
    expect(skyKind(61, false)).toBe("rain");
    expect(skyKind(80, false)).toBe("rain"); // showers
    expect(skyKind(95, false)).toBe("storm");
  });

  it("falls back to the wet hint when code is null", () => {
    expect(skyKind(null, true)).toBe("rain");
    expect(skyKind(null, false)).toBe("clear");
  });
});

describe("skyTheme", () => {
  it("returns a gradient + chip + soft class for every kind", () => {
    for (const code of [0, 2, 61, 95]) {
      const t = skyTheme(code, false);
      expect(t.gradient).toContain("bg-gradient");
      expect(t.chip.length).toBeGreaterThan(0);
      expect(t.soft.length).toBeGreaterThan(0);
    }
  });
});
