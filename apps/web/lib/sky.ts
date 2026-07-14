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
  gradient: string; // tailwind bg gradient classes
  chip: string; // translucent control on the sky
  soft: string; // faint text on the sky
}

const THEMES: Record<SkyKind, SkyTheme> = {
  clear: {
    gradient: "bg-gradient-to-b from-sky-400 via-sky-500 to-emerald-500",
    chip: "bg-white/25",
    soft: "text-white/85",
  },
  cloudy: {
    gradient: "bg-gradient-to-b from-slate-400 via-slate-500 to-slate-600",
    chip: "bg-white/20",
    soft: "text-white/80",
  },
  rain: {
    gradient: "bg-gradient-to-b from-sky-700 via-blue-700 to-slate-800",
    chip: "bg-white/20",
    soft: "text-white/80",
  },
  storm: {
    gradient: "bg-gradient-to-b from-slate-700 via-indigo-900 to-slate-900",
    chip: "bg-white/20",
    soft: "text-white/75",
  },
};

export function skyTheme(weatherCode: number | null, wet: boolean): SkyTheme {
  return THEMES[skyKind(weatherCode, wet)];
}
