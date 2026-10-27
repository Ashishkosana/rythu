// The weather screen's one big number. It is the highest rain chance over the NEXT 12 hours —
// the same window as the hourly bars under it — so it means the same thing at 6 am or 11 pm and
// never repeats rain that already fell this morning (the daily max would). Pure + tested.

import type { HourlyRain } from "./types";

export const HERO_HOURS = 12;

/** Highest known rain chance in the first HERO_HOURS rows (rows start at the current hour). */
export function nextHoursChance(
  hourly: readonly Pick<HourlyRain, "precipitation_probability">[],
): number | null {
  const known = hourly
    .slice(0, HERO_HOURS)
    .map((h) => h.precipitation_probability)
    .filter((p): p is number => p !== null);
  return known.length > 0 ? Math.max(...known) : null;
}
