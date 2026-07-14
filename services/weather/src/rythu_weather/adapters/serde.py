"""Lossless (de)serialisation of a raw domain Forecast for caching.

This is the CACHE wire format — the full provider-level forecast BEFORE the rule engine runs
(no ``farming_read``), so one cached entry serves every crop/water context. It is distinct
from ``app.serialize`` (the client contract). JSON-safe: datetimes/dates are ISO strings.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from rythu_weather.domain.models import (
    CoordsResolution,
    DailyPoint,
    Forecast,
    ForecastReliability,
    GeoPoint,
    HourlyPoint,
)


def _hourly_to(h: HourlyPoint) -> dict[str, Any]:
    return {
        "t": h.time_local.isoformat(),
        "pp": h.precipitation_probability,
        "pr": h.precipitation_mm,
        "temp": h.temperature_c,
        "rh": h.relative_humidity,
        "wc": h.weather_code,
        "ws": h.wind_speed_kmh,
    }


def _daily_to(d: DailyPoint) -> dict[str, Any]:
    return {
        "d": d.day.isoformat(),
        "ppm": d.precipitation_probability_max,
        "ps": d.precipitation_sum_mm,
        "tx": d.temperature_max_c,
        "tn": d.temperature_min_c,
        "wc": d.weather_code,
        "wx": d.wind_speed_max_kmh,
    }


def forecast_to_cache(fc: Forecast) -> dict[str, Any]:
    """Serialise the raw forecast (without farming_read) to a JSON-safe dict."""
    return {
        "coords": {
            "req": [fc.coords.requested.lat, fc.coords.requested.lon],
            "ret": [fc.coords.returned.lat, fc.coords.returned.lon],
            "elev": fc.coords.elevation_m,
            "snap": fc.coords.snap_distance_km,
        },
        "generated_at": fc.generated_at.isoformat(),
        "upstream_fetched_at": fc.upstream_fetched_at.isoformat(),
        "timezone": fc.timezone,
        "reliability": {
            "source": fc.reliability.source,
            "resolution_km": fc.reliability.resolution_km,
            "show_confidence_rating": fc.reliability.show_confidence_rating,
            "model_note": fc.reliability.model_note,
            "disclaimer_en": fc.reliability.disclaimer_en,
            "is_offline_cache": fc.reliability.is_offline_cache,
        },
        "hourly": [_hourly_to(h) for h in fc.hourly],
        "daily": [_daily_to(d) for d in fc.daily],
    }


def forecast_from_cache(data: dict[str, Any]) -> Forecast:
    """Rehydrate a Forecast from :func:`forecast_to_cache` output."""
    c = data["coords"]
    coords = CoordsResolution(
        requested=GeoPoint(c["req"][0], c["req"][1]),
        returned=GeoPoint(c["ret"][0], c["ret"][1]),
        elevation_m=c["elev"],
        snap_distance_km=c["snap"],
    )
    r = data["reliability"]
    reliability = ForecastReliability(
        source=r["source"],
        resolution_km=r["resolution_km"],
        show_confidence_rating=r["show_confidence_rating"],
        model_note=r["model_note"],
        disclaimer_en=r["disclaimer_en"],
        is_offline_cache=r["is_offline_cache"],
    )
    hourly = tuple(
        HourlyPoint(
            time_local=datetime.fromisoformat(h["t"]),
            precipitation_probability=h["pp"],
            precipitation_mm=h["pr"],
            temperature_c=h["temp"],
            relative_humidity=h["rh"],
            weather_code=h["wc"],
            wind_speed_kmh=h["ws"],
        )
        for h in data["hourly"]
    )
    daily = tuple(
        DailyPoint(
            day=date.fromisoformat(d["d"]),
            precipitation_probability_max=d["ppm"],
            precipitation_sum_mm=d["ps"],
            temperature_max_c=d["tx"],
            temperature_min_c=d["tn"],
            weather_code=d["wc"],
            wind_speed_max_kmh=d["wx"],
        )
        for d in data["daily"]
    )
    return Forecast(
        coords=coords,
        generated_at=datetime.fromisoformat(data["generated_at"]),
        upstream_fetched_at=datetime.fromisoformat(data["upstream_fetched_at"]),
        hourly=hourly,
        daily=daily,
        reliability=reliability,
        timezone=data["timezone"],
    )
