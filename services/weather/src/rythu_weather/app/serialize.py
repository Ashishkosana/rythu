"""Serialise a domain Forecast into the typed, honest JSON contract our API returns.

This is the ONLY place the wire shape is defined. It never leaks raw Open-Meteo fields, it
never emits a confidence score, and it always attaches the source/last-updated stamp.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from rythu_weather.domain.models import (
    DailyPoint,
    FarmerContext,
    FarmingRead,
    Forecast,
    HourlyPoint,
)
from rythu_weather.domain.reliability import format_source_stamp
from rythu_weather.domain.wmo import lookup


def _hourly_slice(forecast: Forecast, now: datetime, hours: int) -> list[HourlyPoint]:
    """Hourly rows from the current hour forward, capped at ``hours`` (default 48)."""
    start = now.replace(minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=hours)
    return [h for h in forecast.hourly if start <= h.time_local < end]


def _read_json(read: FarmingRead) -> dict[str, Any]:
    # rule_confidence is intentionally NOT serialised — it is internal metadata, not a
    # farmer-facing reliability score (honest-framing guardrail).
    return {
        "id": read.id,
        "action": read.action.value,
        "crop": read.crop,
        "severity": read.severity.value,
        "triggered": read.triggered,
        "headline_en": read.headline_en,
        "detail_en": read.detail_en,
        "caveat_en": read.caveat_en,
        "window_note": read.window_note,
        "sources": list(read.sources),
    }


def _hourly_json(h: HourlyPoint) -> dict[str, Any]:
    cond = lookup(h.weather_code)
    return {
        "time_local": h.time_local.isoformat(),
        "precipitation_probability": h.precipitation_probability,
        "precipitation_mm": h.precipitation_mm,
        "temperature_c": h.temperature_c,
        "relative_humidity": h.relative_humidity,
        "wind_speed_kmh": h.wind_speed_kmh,
        "weather_code": h.weather_code,
        "category": cond.category.value,
        "emoji": cond.emoji,
    }


def _daily_json(d: DailyPoint) -> dict[str, Any]:
    cond = lookup(d.weather_code)
    return {
        "date": d.day.isoformat(),
        "precipitation_probability_max": d.precipitation_probability_max,
        "precipitation_sum_mm": d.precipitation_sum_mm,
        "temperature_max_c": d.temperature_max_c,
        "temperature_min_c": d.temperature_min_c,
        "wind_speed_max_kmh": d.wind_speed_max_kmh,
        "weather_code": d.weather_code,
        "category": cond.category.value,
        "emoji": cond.emoji,
        "farm_note": cond.farm_note,
    }


def forecast_to_contract(
    forecast: Forecast,
    ctx: FarmerContext,
    *,
    hourly_hours: int = 48,
) -> dict[str, Any]:
    """Build the API response body for a fully-evaluated Forecast."""
    rel = forecast.reliability
    stamp = format_source_stamp(
        ctx.now,
        forecast.upstream_fetched_at,
        resolution_km=rel.resolution_km,
        is_offline_cache=rel.is_offline_cache,
    )
    coords = forecast.coords
    return {
        "source": rel.source,
        "model_note": rel.model_note,
        "resolution_km": rel.resolution_km,
        "timezone": forecast.timezone,
        "coords": {
            "requested": {"lat": coords.requested.lat, "lon": coords.requested.lon},
            "returned": {"lat": coords.returned.lat, "lon": coords.returned.lon},
            "elevation_m": coords.elevation_m,
            "snap_distance_km": coords.snap_distance_km,
        },
        "generated_at": forecast.generated_at.isoformat(),
        "upstream_fetched_at": forecast.upstream_fetched_at.isoformat(),
        "reliability": {
            "show_confidence_rating": rel.show_confidence_rating,
            "resolution_km": rel.resolution_km,
            "disclaimer_en": rel.disclaimer_en,
            "source_stamp_en": stamp,
            "is_offline_cache": rel.is_offline_cache,
        },
        "farmer_context": {
            "crop": ctx.crop.value if ctx.crop is not None else None,
            "water_source": ctx.water_source.value,
        },
        "farming_read": [_read_json(r) for r in forecast.farming_read],
        "hourly_rain": [_hourly_json(h) for h in _hourly_slice(forecast, ctx.now, hourly_hours)],
        "daily": [_daily_json(d) for d in forecast.daily],
    }
