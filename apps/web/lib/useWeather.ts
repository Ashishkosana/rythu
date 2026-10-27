"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchWeather, type WeatherParams } from "./api";
import { isTooOld } from "./freshness";
import type { WeatherContract } from "./types";

export function weatherKey(p: WeatherParams) {
  return ["weather", p.lat, p.lon, p.crop, p.water] as const;
}

/** A saved copy, labelled as one (the screen shows "offline — showing saved forecast"). */
export function asSavedCopy(data: WeatherContract): WeatherContract {
  return { ...data, reliability: { ...data.reliability, is_offline_cache: true } };
}

/** What to show when the API answers: its answer — unless it is degraded and the device holds better. */
export function pickAnswer(fresh: WeatherContract, prev: WeatherContract | undefined, nowMs: number): WeatherContract {
  if (!fresh.degraded) return fresh;
  return prev && !prev.degraded && !isTooOld(prev, nowMs) ? asSavedCopy(prev) : fresh;
}

/**
 * The forecast for a place + crop. Instant from the on-device copy, refreshed in the background.
 *
 * - If the API can only offer a degraded answer but the device still holds a real forecast ≤ 6 h
 *   old, the device copy is the more useful truth — shown, and labelled as saved.
 * - Switching crop keeps the previous crop's data as a placeholder (same place → same weather);
 *   the screen hides that placeholder's crop advice until the real answer arrives.
 */
export function useWeather(p: WeatherParams) {
  const qc = useQueryClient();
  return useQuery({
    queryKey: weatherKey(p),
    queryFn: async ({ signal, queryKey }) => {
      const fresh = await fetchWeather(p, signal);
      return pickAnswer(fresh, qc.getQueryData<WeatherContract>(queryKey), Date.now());
    },
    placeholderData: (prev, prevQuery) => {
      const k = prevQuery?.queryKey;
      return prev && k && k[1] === p.lat && k[2] === p.lon && k[4] === p.water ? prev : undefined;
    },
  });
}
