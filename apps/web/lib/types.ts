// The weather API contract, as the web app sees it. Every type here is DERIVED from
// lib/api.gen.ts, which is generated from the backend's OpenAPI document
// (services/weather/openapi.json) — never edit shapes by hand. To change the contract:
//   1. change the backend (app/serialize.py + api/schemas.py; the golden test keeps them equal)
//   2. cd services/weather && uv run python -m rythu_weather.api.openapi_export
//   3. cd apps/web && npm run gen:api
// CI fails if either generated file is stale.

import type { components } from "./api.gen";

type Schemas = components["schemas"];

export type WeatherContract = Schemas["WeatherContract"];
export type FarmingRead = Schemas["FarmingReadOut"];
export type HourlyRain = Schemas["HourlyRainOut"];
export type DailyPoint = Schemas["DailyOut"];
export type Reliability = Schemas["Reliability"];
export type Severity = Schemas["Severity"];
export type FarmAction = Schemas["FarmAction"];
export type Crop = Schemas["Crop"];
export type WaterSource = Schemas["WaterSource"];
export type ApiError = Schemas["ErrorBody"];

// Runtime lists (types vanish at runtime), in display order. Checked against the backend enums
// both ways: `satisfies` rejects a value the backend doesn't know, and the Exhaustive check
// fails to compile if the backend adds a crop or water source the app doesn't list yet.
export const CROPS = ["chilli", "cotton", "paddy", "red_gram", "maize"] as const satisfies readonly Crop[];
export const WATER_SOURCES = ["canal_lift", "tank", "borewell", "rainfed"] as const satisfies readonly WaterSource[];

type Exhaustive<All, Listed> = [Exclude<All, Listed>] extends [never] ? true : Exclude<All, Listed>;
const cropsComplete: Exhaustive<Crop, (typeof CROPS)[number]> = true;
const watersComplete: Exhaustive<WaterSource, (typeof WATER_SOURCES)[number]> = true;
void cropsComplete;
void watersComplete;

export function isCrop(v: string | undefined): v is Crop {
  return (CROPS as readonly string[]).includes(v ?? "");
}

export function isWaterSource(v: string | undefined): v is WaterSource {
  return (WATER_SOURCES as readonly string[]).includes(v ?? "");
}
