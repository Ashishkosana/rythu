// Mirrors the JSON contract from the Rythu weather service (services/weather).
// Kept in sync by hand for v0; a generated client can replace this later.

export type Severity = "info" | "caution" | "act";

export interface FarmingRead {
  id: string;
  action: string;
  crop: string;
  severity: Severity;
  triggered: boolean;
  headline_en: string;
  detail_en: string;
  caveat_en: string;
  window_note: string | null;
  sources: string[];
}

export interface HourlyRain {
  time_local: string;
  precipitation_probability: number | null;
  precipitation_mm: number | null;
  temperature_c: number | null;
  relative_humidity: number | null;
  wind_speed_kmh: number | null;
  weather_code: number | null;
  category: string;
  emoji: string;
}

export interface DailyPoint {
  date: string;
  precipitation_probability_max: number | null;
  precipitation_sum_mm: number | null;
  temperature_max_c: number | null;
  temperature_min_c: number | null;
  wind_speed_max_kmh: number | null;
  weather_code: number | null;
  category: string;
  emoji: string;
  farm_note: string;
}

export interface Reliability {
  show_confidence_rating: boolean;
  resolution_km: number;
  disclaimer_en: string;
  source_stamp_en: string;
  is_offline_cache: boolean;
}

export interface WeatherContract {
  source: string;
  model_note: string;
  resolution_km: number;
  timezone: string;
  coords: {
    requested: { lat: number; lon: number };
    returned: { lat: number; lon: number };
    elevation_m: number;
    snap_distance_km: number;
  };
  generated_at: string;
  upstream_fetched_at: string;
  reliability: Reliability;
  farmer_context: { crop: string | null; water_source: string };
  farming_read: FarmingRead[];
  hourly_rain: HourlyRain[];
  daily: DailyPoint[];
  // present only on a degraded response
  degraded?: boolean;
  note_en?: string;
}
