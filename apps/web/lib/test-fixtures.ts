// Test-only builders (imported by *.test.ts, never by the app).

import type { WeatherContract } from "./types";

export function contract(over: Partial<WeatherContract> = {}): WeatherContract {
  return {
    source: "open-meteo",
    model_note: "",
    resolution_km: 11,
    timezone: "Asia/Kolkata",
    coords: {
      requested: { lat: 18.43, lon: 79.86 },
      returned: { lat: 18.4, lon: 79.9 },
      elevation_m: 250,
      snap_distance_km: 3.2,
    },
    generated_at: "2026-10-26T09:00:00+05:30",
    upstream_fetched_at: "2026-10-26T09:00:00+05:30",
    reliability: {
      show_confidence_rating: false,
      resolution_km: 11,
      disclaimer_en: "Forecasts can be wrong.",
      source_stamp_en: "Source: Open-Meteo (~11 km) · updated just now",
      is_offline_cache: false,
    },
    farmer_context: { crop: "chilli", water_source: "rainfed" },
    farming_read: [],
    hourly_rain: [],
    daily: [],
    ...over,
  };
}
