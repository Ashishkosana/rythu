"""Dry-spell rule (2026 farmer research: water shortage was the year's biggest crop loss)."""

from __future__ import annotations

from builders import at, day, days_from, forecast
from rythu_weather.domain.engine import evaluate_reads
from rythu_weather.domain.models import Crop, FarmerContext, WaterSource
from rythu_weather.domain.rules import DRY_DAY_MM, DRY_SPELL_MAX_PROB, _dry_spell_rainfed

MONSOON = at(2026, 8, 10, 7)


def _ctx(now, water=WaterSource.RAINFED, crop=Crop.COTTON):
    return FarmerContext(now=now, water_source=water, crop=crop)


def _dry(now, n=7, **kw):
    return forecast(now, daily=days_from(now.date(), n, **{"pp_max": 10, "precip_sum": 0.4, **kw}))


def _ids(fc, ctx):
    return {r.id for r in evaluate_reads(fc, ctx)}


def test_a_known_dry_week_fires_with_the_sourced_advice() -> None:
    fired = _dry_spell_rainfed(_dry(MONSOON), _ctx(MONSOON))
    assert fired is not None
    assert "7 days" in fired.headline_en
    for practice in ("inter-cultivation", "top-dressing", "life-saving irrigation"):
        assert practice in fired.detail_en
    assert "అంతర కృషి" in fired.detail_te and "పంట కుంట" in fired.detail_te


def test_one_wet_or_unknown_day_or_a_short_forecast_keeps_it_quiet() -> None:
    wet = [*days_from(MONSOON.date(), 6, pp_max=10, precip_sum=0.4)]
    from datetime import timedelta

    last = MONSOON.date() + timedelta(days=6)
    for bad in (
        day(last, pp_max=10, precip_sum=DRY_DAY_MM),  # 2.5 mm is not a dry day (IMD: < 2.5)
        day(last, pp_max=DRY_SPELL_MAX_PROB, precip_sum=0.0),  # showers likely enough
        day(last, pp_max=None, precip_sum=0.0),  # unknown never counts as dry
        day(last, pp_max=10, precip_sum=None),
    ):
        assert _dry_spell_rainfed(forecast(MONSOON, daily=[*wet, bad]), _ctx(MONSOON)) is None
    assert _dry_spell_rainfed(_dry(MONSOON, n=6), _ctx(MONSOON)) is None  # can't see the whole week


def test_advice_follows_the_water_source_and_only_in_the_monsoon() -> None:
    fc = _dry(MONSOON)
    assert {"dry-spell-rainfed"} <= _ids(fc, _ctx(MONSOON))
    assert "dry-spell-irrigated" not in _ids(fc, _ctx(MONSOON))
    for water in (WaterSource.BOREWELL, WaterSource.CANAL_LIFT, WaterSource.TANK):
        ids = _ids(fc, _ctx(MONSOON, water=water))
        assert "dry-spell-irrigated" in ids and "dry-spell-rainfed" not in ids
    january = at(2027, 1, 10, 7)  # dry weeks are normal after the rains: no alarm
    assert not {"dry-spell-rainfed", "dry-spell-irrigated"} & _ids(_dry(january), _ctx(january))


def test_a_dry_spell_read_is_a_caution_with_sources() -> None:
    [read] = [r for r in evaluate_reads(_dry(MONSOON), _ctx(MONSOON)) if r.id == "dry-spell-rainfed"]
    assert read.severity.value == "caution"
    assert any("pjtsau" in s for s in read.sources) and any("imd.gov.in" in s for s in read.sources)
    assert read.caveat_te  # Telugu caveat present
