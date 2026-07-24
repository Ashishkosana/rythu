"""Telugu farming-advice coverage: every rule must ship a Telugu caveat, and a fired
read must carry a Telugu headline/detail distinct from the English (so the app can
show a Telugu farmer real advice, not an English fallback)."""

from __future__ import annotations

from builders import at, day, forecast, hours_from
from rythu_weather.domain.models import FarmerContext, WaterSource
from rythu_weather.domain.rules import (
    ACTIVE_RULES,
    _harvest_paddy,
    _spray_rain_washoff,
    _spray_wind_drift,
)


def _ctx(now, crop=None, water=WaterSource.RAINFED):
    return FarmerContext(now=now, water_source=water, crop=crop)


def test_every_active_rule_has_a_telugu_caveat():
    missing = [r.id for r in ACTIVE_RULES if not r.caveat_te.strip()]
    assert missing == [], f"rules missing Telugu caveat: {missing}"


def test_spray_rain_read_is_bilingual():
    now = at(2026, 7, 15, 8)
    fired = _spray_rain_washoff(forecast(now, hourly=hours_from(now, 6, pp=60, precip=0.0)), _ctx(now))
    assert fired is not None
    assert fired.headline_te.strip() and fired.headline_te != fired.headline_en
    assert fired.detail_te.strip()
    assert "60%" in fired.headline_te  # the interpolated number survives translation


def test_wind_and_harvest_reads_carry_telugu():
    now = at(2026, 7, 15, 8)
    wind = _spray_wind_drift(forecast(now, hourly=hours_from(now, 6, wind=20.0)), _ctx(now))
    assert wind is not None and wind.headline_te.strip()

    rainy = forecast(now, daily=[day(now.date(), pp_max=70, precip_sum=12.0)])
    harvest = _harvest_paddy(rainy, _ctx(now))
    assert harvest is not None and harvest.headline_te.strip() and harvest.headline_te != harvest.headline_en
