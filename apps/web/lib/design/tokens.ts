// The design tokens' values — the one place colours are chosen. app/globals.css declares the same
// values in @theme (tokens.test.ts fails if they drift), and Tailwind's default palette is switched
// off there, so screens can only use these names (bg-surface-raised, text-ink-secondary, …).
//
// Every pairing the UI uses is listed below and computed at test time: text ≥ 4.5 : 1, meaningful
// graphics (input borders, chart bars) ≥ 3 : 1 — WCAG 2.2 AA, 1.4.3 and 1.4.11. The users read in
// bright sun, often with older eyes, on cheap screens.

export const COLOR = {
  white: "#ffffff",
  black: "#000000",
  // Surfaces
  surface: "#f4f2ec", // warm paper: calm in sunlight
  "surface-raised": "#ffffff", // cards
  "surface-sunken": "#f5f5f4", // wells, tracks, pressed rows
  // Text
  ink: "#1c1917",
  "ink-secondary": "#57534e", // the only secondary tone: no "tertiary" grey that fails contrast
  // Lines
  line: "#e7e5e4", // decorative separators only
  "line-strong": "#78716c", // boundaries someone must see (inputs, outlined buttons)
  // Brand: green-700 is for FILLS (white on it 5.02); text uses brand-ink (green-700 text on the
  // paper surface is 4.48 — just short of AA).
  brand: "#15803d",
  "brand-ink": "#166534",
  "on-brand": "#ffffff",
  "brand-soft": "#dcfce7", // selected tab / positive tint, with brand-ink text
  // Status: background + foreground pairs, plus an accent for bars and chart marks
  "info-bg": "#f0f9ff",
  "info-fg": "#075985",
  "info-accent": "#0284c7",
  "caution-bg": "#fffbeb",
  "caution-fg": "#78350f",
  "caution-accent": "#d97706",
  "act-bg": "#fef2f2",
  "act-fg": "#991b1b",
  "act-accent": "#dc2626",
  "success-bg": "#dcfce7",
  "success-fg": "#166534",
  "warn-bg": "#ffedd5",
  "warn-fg": "#9a3412",
  "neutral-bg": "#e7e5e4",
  "neutral-fg": "#44403c",
  // Hero skies (white text on them) and the green screen headers
  "hero-clear-from": "#0369a1",
  "hero-clear-to": "#047857",
  "hero-cloudy-from": "#475569",
  "hero-cloudy-to": "#334155",
  "hero-rain-from": "#0369a1",
  "hero-rain-via": "#1d4ed8",
  "hero-rain-to": "#1e293b",
  "hero-storm-from": "#334155",
  "hero-storm-via": "#312e81",
  "hero-storm-to": "#0f172a",
  "hero-brand-from": "#166534",
  "hero-brand-to": "#14532d",
} as const;

export type ColorToken = keyof typeof COLOR;

/** Text on a hero: plain white, `soft` = white at this opacity, chips = black at this opacity. */
export const HERO_SOFT_ALPHA = 0.9;
export const HERO_CHIP_ALPHA = 0.15;

export const HERO_STOPS: readonly ColorToken[] = [
  "hero-clear-from", "hero-clear-to", "hero-cloudy-from", "hero-cloudy-to",
  "hero-rain-from", "hero-rain-via", "hero-rain-to", "hero-storm-from", "hero-storm-via", "hero-storm-to",
  "hero-brand-from", "hero-brand-to",
];

/** [foreground, background] pairs the UI uses for text. Checked ≥ 4.5 : 1. */
export const TEXT_PAIRS: readonly (readonly [ColorToken, ColorToken])[] = [
  ...(["surface", "surface-raised", "surface-sunken"] as const).flatMap((bg) => [
    ["ink", bg] as const,
    ["ink-secondary", bg] as const,
    ["brand-ink", bg] as const,
  ]),
  ["on-brand", "brand"],
  ["on-brand", "brand-ink"],
  ["brand-ink", "brand-soft"],
  ["info-fg", "info-bg"],
  ["caution-fg", "caution-bg"],
  ["act-fg", "act-bg"],
  ["success-fg", "success-bg"],
  ["warn-fg", "warn-bg"],
  ["neutral-fg", "neutral-bg"],
  ["white", "ink"], // the offline pill
];

/** [graphic, background] pairs that carry meaning without text. Checked ≥ 3 : 1. */
export const GRAPHIC_PAIRS: readonly (readonly [ColorToken, ColorToken])[] = [
  ["line-strong", "surface-raised"],
  ["line-strong", "surface"],
  ["brand", "surface-raised"],
  ["info-accent", "surface-raised"],
  ["caution-accent", "surface-raised"],
  ["act-accent", "surface-raised"],
];
