// Apple-Weather-style dynamic sky: the hero background reflects the real
// conditions (WMO weather code). Pure + tested. Returns a Tailwind gradient
// class plus a matching accent for controls, so the whole hero reads as one
// coherent "material" instead of a flat colour block.

export type SkyKind = "clear" | "cloudy" | "rain" | "storm";

/** Map a WMO weather code (+ rain flag as a hint) to a sky kind. */
export function skyKind(weatherCode: number | null, wet: boolean): SkyKind {
  const c = weatherCode ?? (wet ? 61 : 1);
  if (c >= 95) return "storm"; // thunderstorm
  if (c >= 51) return "rain"; // drizzle / rain / showers / snow
  if (c >= 45) return "cloudy"; // fog
  if (c >= 2) return "cloudy"; // partly cloudy / overcast
  return "clear"; // 0–1 clear / mainly clear
}

export interface SkyTheme {
  gradient: string; // tailwind bg gradient classes (design tokens: hero-*)
  chip: string; // control on the sky: a darkening veil, so white text on it stays ≥ 4.5 : 1
  soft: string; // secondary text on the sky
}

// Every stop is checked against white, soft white and white-on-chip in lib/design/tokens.test.ts.
// (The old clear and cloudy skies put white text on sky-400 / slate-400: 2.1–2.6 : 1.)
const CHIP = "bg-black/15";
const SOFT = "text-white/90";

const THEMES: Record<SkyKind, SkyTheme> = {
  clear: { gradient: "bg-gradient-to-b from-hero-clear-from to-hero-clear-to", chip: CHIP, soft: SOFT },
  cloudy: { gradient: "bg-gradient-to-b from-hero-cloudy-from to-hero-cloudy-to", chip: CHIP, soft: SOFT },
  rain: { gradient: "bg-gradient-to-b from-hero-rain-from via-hero-rain-via to-hero-rain-to", chip: CHIP, soft: SOFT },
  storm: { gradient: "bg-gradient-to-b from-hero-storm-from via-hero-storm-via to-hero-storm-to", chip: CHIP, soft: SOFT },
};

export function skyTheme(weatherCode: number | null, wet: boolean): SkyTheme {
  return THEMES[skyKind(weatherCode, wet)];
}
