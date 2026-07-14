from __future__ import annotations

import json
from dataclasses import replace

from builders import at, days_from, forecast, hours_from
from rythu_weather.app.serialize import forecast_to_contract
from rythu_weather.domain.models import (
    Crop,
    FarmAction,
    FarmerContext,
    FarmingRead,
    ForecastReliability,
    Severity,
    WaterSource,
)

_READ = FarmingRead(
    id="spray-rain-washoff",
    action=FarmAction.SPRAY,
    crop="any",
    severity=Severity.CAUTION,
    headline_en="Rain possible (70% chance) — wait to spray.",
    caveat_en="Forecast can be wrong; watch the sky.",
    detail_en="Sprays need dry hours.",
    sources=("https://sprayers101.com/rainfastness-pesticide/",),
    rule_confidence="high",
)


def _contract():
    now = at(2026, 7, 15, 12, 8)
    fc = forecast(
        now,
        hourly=hours_from(at(2026, 7, 15, 0), 72),  # more than 48 → must be sliced
        daily=days_from(at(2026, 7, 15).date(), 7),
        fetched_at=at(2026, 7, 15, 12, 0),
    )
    fc = replace(fc, farming_read=(_READ,))
    ctx = FarmerContext(now=now, water_source=WaterSource.RAINFED, crop=Crop.COTTON)
    return forecast_to_contract(fc, ctx)


def test_contract_has_expected_top_level_keys():
    c = _contract()
    assert set(c) >= {
        "source",
        "model_note",
        "resolution_km",
        "timezone",
        "coords",
        "generated_at",
        "upstream_fetched_at",
        "reliability",
        "farmer_context",
        "farming_read",
        "hourly_rain",
        "daily",
    }


def test_no_confidence_score_is_ever_serialised():
    c = _contract()
    assert c["reliability"]["show_confidence_rating"] is False
    # internal rule_confidence must not leak anywhere in the payload
    assert "rule_confidence" not in json.dumps(c)
    assert "rule_confidence" not in c["farming_read"][0]


def test_source_stamp_and_coords_are_honest():
    c = _contract()
    assert c["reliability"]["source_stamp_en"] == "Source: Open-Meteo (~11 km) · updated 8 min ago"
    assert c["coords"]["requested"] != c["coords"]["returned"]  # grid snap is disclosed
    assert c["coords"]["snap_distance_km"] > 0


def test_hourly_is_sliced_to_48():
    c = _contract()
    assert len(c["hourly_rain"]) == 48
    assert len(c["daily"]) == 7


def test_read_carries_caveat_and_sources():
    read = _contract()["farming_read"][0]
    assert read["caveat_en"]
    assert read["sources"]
    assert read["action"] == "spray"


def test_offline_cache_is_disclosed():
    now = at(2026, 7, 15, 12, 0)
    fc = forecast(
        now,
        hourly=hours_from(at(2026, 7, 15, 0), 24),
        daily=days_from(at(2026, 7, 15).date(), 3),
        fetched_at=at(2026, 7, 14, 12, 0),
    )
    fc = replace(fc, reliability=ForecastReliability(is_offline_cache=True))
    ctx = FarmerContext(now=now, water_source=WaterSource.RAINFED)
    c = forecast_to_contract(fc, ctx)
    assert c["reliability"]["is_offline_cache"] is True
    assert c["reliability"]["source_stamp_en"].startswith("Offline —")


def test_hourly_slice_is_forward_only():
    from datetime import datetime as _dt

    now = at(2026, 7, 15, 12, 8)
    fc = forecast(now, hourly=hours_from(at(2026, 7, 15, 0), 72), daily=days_from(at(2026, 7, 15).date(), 7))
    ctx = FarmerContext(now=now, water_source=WaterSource.RAINFED)
    c = forecast_to_contract(fc, ctx)
    start = now.replace(minute=0, second=0, microsecond=0)
    assert c["hourly_rain"][0]["time_local"] == "2026-07-15T12:00:00+05:30"  # current hour, not array start
    assert all(_dt.fromisoformat(h["time_local"]) >= start for h in c["hourly_rain"])
