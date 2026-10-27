import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { contrast, hexToRgb, over } from "./contrast";
import { COLOR, GRAPHIC_PAIRS, HERO_CHIP_ALPHA, HERO_SOFT_ALPHA, HERO_STOPS, TEXT_PAIRS, type ColorToken } from "./tokens";

const rgb = (t: ColorToken) => hexToRgb(COLOR[t]);
const WHITE = hexToRgb("#ffffff");
const BLACK = hexToRgb("#000000");

describe("contrast maths", () => {
  it("matches WCAG's reference values", () => {
    expect(contrast(WHITE, BLACK)).toBeCloseTo(21, 5);
    expect(contrast(hexToRgb("#777777"), WHITE)).toBeCloseTo(4.48, 2);
  });
});

describe("every text pairing the UI uses is ≥ 4.5 : 1 (WCAG 1.4.3)", () => {
  it.each(TEXT_PAIRS.map(([fg, bg]) => [fg, bg, contrast(rgb(fg), rgb(bg))]))("%s on %s → %f", (_fg, _bg, ratio) => {
    expect(ratio).toBeGreaterThanOrEqual(4.5);
  });
});

describe("every meaningful graphic is ≥ 3 : 1 (WCAG 1.4.11)", () => {
  it.each(GRAPHIC_PAIRS.map(([g, bg]) => [g, bg, contrast(rgb(g), rgb(bg))]))("%s on %s → %f", (_g, _bg, ratio) => {
    expect(ratio).toBeGreaterThanOrEqual(3);
  });
});

describe("hero text is readable on every stop of every sky", () => {
  it.each(HERO_STOPS)("%s: white, soft white, and white on a chip", (stop) => {
    const bg = rgb(stop);
    expect(contrast(WHITE, bg)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(over(WHITE, HERO_SOFT_ALPHA, bg), bg)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(WHITE, over(BLACK, HERO_CHIP_ALPHA, bg))).toBeGreaterThanOrEqual(4.5);
  });
});

describe("globals.css declares exactly these tokens", () => {
  const css = readFileSync(new URL("../../app/globals.css", import.meta.url), "utf8");
  const theme = css.slice(css.indexOf("@theme {"));
  const declared = Object.fromEntries(
    [...theme.matchAll(/--color-([a-z0-9-]+):\s*(#[0-9a-f]{6})\s*;/gi)].map((m) => [m[1], m[2]!.toLowerCase()]),
  );

  it("with the same values", () => {
    expect(declared).toEqual(COLOR);
  });

  it("and switches Tailwind's default palette off, so raw colours cannot creep back", () => {
    expect(theme).toMatch(/--color-\*:\s*initial;/);
  });
});
