"""Typed wire contract for the HTTP API (Pydantic → OpenAPI → generated TypeScript in S4).

These models DESCRIBE the JSON that ``app.serialize`` / ``app.degraded`` produce; they do not
produce it. ``tests/test_contract_schema.py`` (the golden test) proves the two agree exactly:
every model forbids unknown fields and every real response round-trips unchanged, so adding a
field in the serializer without declaring it here fails CI.

Field docs are written for the TypeScript/client side — they end up in OpenAPI and the generated
types. Timestamps are ISO-8601 strings with offset (e.g. ``2026-07-14T09:00:00+05:30``), kept as
strings so the exact wire text is preserved.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from rythu_weather.domain.models import Crop, FarmAction, Severity, WaterSource, WMOCategory


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LatLon(_Strict):
    lat: float
    lon: float


class Coords(_Strict):
    requested: LatLon = Field(description="The farmer's pin.")
    returned: LatLon = Field(description="The model grid point that answered.")
    elevation_m: float
    snap_distance_km: float = Field(description="Distance from the farmer's pin to the grid point.")


class Reliability(_Strict):
    show_confidence_rating: Literal[False] = Field(
        description="Always false: a deterministic model has no honest confidence to show."
    )
    resolution_km: int
    disclaimer_en: str
    source_stamp_en: str = Field(description="Source, resolution and data age, e.g. 'updated 8 min ago'.")
    is_offline_cache: bool = Field(description="True when serving a saved copy because upstream is down.")


class FarmerContextOut(_Strict):
    crop: Crop | None
    water_source: WaterSource


class FarmingReadOut(_Strict):
    id: str
    action: FarmAction
    crop: str = Field(description="'any' or a crop id.")
    severity: Severity = Field(description="UI emphasis, NOT a certainty claim.")
    triggered: bool
    headline_en: str
    detail_en: str
    caveat_en: str
    headline_te: str = Field(description="Empty string = fall back to the English field.")
    detail_te: str
    caveat_te: str
    window_note: str | None
    sources: list[str]


class HourlyRainOut(_Strict):
    time_local: str
    precipitation_probability: int | None = Field(description="Percent; null = unknown, never zero.")
    precipitation_mm: float | None
    temperature_c: float | None
    relative_humidity: int | None
    wind_speed_kmh: float | None
    weather_code: int | None
    category: WMOCategory
    emoji: str


class DailyOut(_Strict):
    date: str = Field(description="Local calendar date, YYYY-MM-DD. Never earlier than today.")
    precipitation_probability_max: int | None
    precipitation_sum_mm: float | None
    temperature_max_c: float | None
    temperature_min_c: float | None
    wind_speed_max_kmh: float | None
    weather_code: int | None
    category: WMOCategory
    emoji: str
    farm_note: str


class WeatherContract(_Strict):
    """``GET /v1/weather`` 200 body — a forecast, or an honest degraded answer (``degraded: true``)."""

    source: str
    model_note: str
    resolution_km: int
    timezone: str
    coords: Coords
    generated_at: str
    upstream_fetched_at: str
    reliability: Reliability
    farmer_context: FarmerContextOut
    farming_read: list[FarmingReadOut]
    hourly_rain: list[HourlyRainOut] = Field(description="From the current hour forward, up to 48 rows.")
    daily: list[DailyOut]
    # Present only on a degraded response (upstream down and no saved copy ≤ 6 h old).
    degraded: Literal[True] | None = None
    note_en: str | None = None


class ErrorBody(_Strict):
    """400 body. ``code`` is stable and machine-readable; ``error`` is for humans/logs."""

    error: str
    code: Literal["bad_request", "outside_coverage"]


class Health(_Strict):
    status: Literal["ok"]
