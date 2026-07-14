"""Chilli (mirchi) rule tests: weather logic (predicates) + season month-gating (engine)."""

from __future__ import annotations

from datetime import timedelta

from builders import at, day, forecast, hour, hours_from
from rythu_weather.domain.engine import evaluate_reads
from rythu_weather.domain.models import Crop, FarmerContext, WaterSource
from rythu_weather.domain.rules import (
    _chilli_anthracnose,
    _chilli_drainage,
    _chilli_harvest_drying,
    _chilli_heat_flowerdrop,
    _chilli_thrips,
)


def _ctx(now, crop=Crop.CHILLI, water=WaterSource.RAINFED):
    return FarmerContext(now=now, water_source=water, crop=crop)


def _ids(reads):
    return {r.id for r in reads}


# --- drainage (fire-on-risk, no season gate) ----------------------------------------------


def test_chilli_drainage_boundaries():
    now = at(2026, 7, 15, 9)
    assert _chilli_drainage(forecast(now, daily=[day(now.date(), pp_max=0, precip_sum=40.0)]), _ctx(now)) is not None
    assert _chilli_drainage(forecast(now, daily=[day(now.date(), pp_max=0, precip_sum=39.0)]), _ctx(now)) is None
    # softer 25 mm needs high probability
    assert _chilli_drainage(forecast(now, daily=[day(now.date(), pp_max=70, precip_sum=25.0)]), _ctx(now)) is not None
    assert _chilli_drainage(forecast(now, daily=[day(now.date(), pp_max=50, precip_sum=25.0)]), _ctx(now)) is None


def test_chilli_drainage_skips_unknown_days():
    now = at(2026, 7, 15, 9)
    assert _chilli_drainage(forecast(now, daily=[day(now.date(), pp_max=0, precip_sum=None)]), _ctx(now)) is None


# --- heat / flower-drop (needs 2 consecutive hot days, rain suppresses) -------------------


def test_chilli_heat_needs_two_consecutive_hot_days():
    now = at(2026, 10, 1, 9)
    d0, d1 = now.date(), (now + timedelta(days=1)).date()
    two_hot = forecast(now, daily=[day(d0, tmax=36.0), day(d1, tmax=36.0)])
    assert _chilli_heat_flowerdrop(two_hot, _ctx(now)) is not None
    one_hot = forecast(now, daily=[day(d0, tmax=36.0), day(d1, tmax=30.0)])
    assert _chilli_heat_flowerdrop(one_hot, _ctx(now)) is None


def test_chilli_heat_suppressed_when_rain_coming():
    now = at(2026, 10, 1, 9)
    d0, d1 = now.date(), (now + timedelta(days=1)).date()
    hot_but_wet = forecast(now, daily=[day(d0, tmax=36.0, pp_max=70), day(d1, tmax=36.0)])
    assert _chilli_heat_flowerdrop(hot_but_wet, _ctx(now)) is None


# --- harvest / drying (rain during harvest season) ----------------------------------------


def test_chilli_harvest_fires_on_low_rain_threshold():
    now = at(2026, 12, 1, 9)
    assert (
        _chilli_harvest_drying(forecast(now, daily=[day(now.date(), pp_max=0, precip_sum=5.0)]), _ctx(now)) is not None
    )
    assert (
        _chilli_harvest_drying(forecast(now, daily=[day(now.date(), pp_max=60, precip_sum=0.0)]), _ctx(now)) is not None
    )
    assert _chilli_harvest_drying(forecast(now, daily=[day(now.date(), pp_max=50, precip_sum=4.0)]), _ctx(now)) is None


# --- anthracnose scout (6h humid run + a wet hour, next 48h) -------------------------------


def _humid_run(now, hours, *, precip_at=None):
    return [
        hour(now + timedelta(hours=i), rh=90, temp=25.0, precip=(0.5 if i == precip_at else 0.0), code=1)
        for i in range(hours)
    ]


def test_chilli_anthracnose_fires_on_humid_wet_run():
    now = at(2026, 10, 1, 6)
    fc = forecast(now, hourly=_humid_run(now, 6, precip_at=2))
    assert _chilli_anthracnose(fc, _ctx(now)) is not None


def test_chilli_anthracnose_needs_actual_wetting():
    now = at(2026, 10, 1, 6)
    fc = forecast(now, hourly=_humid_run(now, 6))  # humid but bone-dry → no leaf wetness
    assert _chilli_anthracnose(fc, _ctx(now)) is None


def test_chilli_anthracnose_needs_six_consecutive_hours():
    now = at(2026, 10, 1, 6)
    short = [*_humid_run(now, 5, precip_at=1), hour(now + timedelta(hours=5), rh=50, temp=25.0)]
    assert _chilli_anthracnose(forecast(now, hourly=short), _ctx(now)) is None


# --- thrips scout (dry warm spell, majority-dry afternoons) --------------------------------


def _dry_days(now, n, **kw):
    return [day((now + timedelta(days=i)).date(), pp_max=10, precip_sum=0.0, tmax=32.0, **kw) for i in range(n)]


def test_chilli_thrips_fires_on_dry_warm_spell():
    now = at(2026, 2, 1, 6)  # Rabi, in thrips months
    fc = forecast(now, hourly=hours_from(now, 72, rh=50), daily=_dry_days(now, 3))
    assert _chilli_thrips(fc, _ctx(now)) is not None


def test_chilli_thrips_silent_on_wet_or_unknown_day():
    now = at(2026, 2, 1, 6)
    wet = forecast(
        now,
        hourly=hours_from(now, 72, rh=50),
        daily=[
            day(now.date(), pp_max=10, precip_sum=0.0, tmax=32.0),
            day((now + timedelta(days=1)).date(), pp_max=10, precip_sum=5.0, tmax=32.0),  # a wet day
            day((now + timedelta(days=2)).date(), pp_max=10, precip_sum=0.0, tmax=32.0),
        ],
    )
    assert _chilli_thrips(wet, _ctx(now)) is None


def test_chilli_thrips_silent_when_afternoons_humid():
    now = at(2026, 2, 1, 6)
    fc = forecast(now, hourly=hours_from(now, 72, rh=75), daily=_dry_days(now, 3))
    assert _chilli_thrips(fc, _ctx(now)) is None


# --- season month-gating (engine) ---------------------------------------------------------


def test_chilli_heat_gated_to_flowering_months():
    hot = lambda now: forecast(  # noqa: E731
        now,
        daily=[day(now.date(), tmax=38.0), day((now + timedelta(days=1)).date(), tmax=38.0)],
    )
    july = at(2026, 7, 1, 9)
    assert "chilli-heat-flowerdrop" not in _ids(evaluate_reads(hot(july), _ctx(july)))
    october = at(2026, 10, 1, 9)
    assert "chilli-heat-flowerdrop" in _ids(evaluate_reads(hot(october), _ctx(october)))


def test_chilli_scout_rules_are_active_and_seasonal():
    # anthracnose (Oct) fires as a scout read through the engine
    now = at(2026, 10, 1, 6)
    fc = forecast(now, hourly=_humid_run(now, 6, precip_at=2))
    assert "chilli-anthracnose-humid-wet-fruiting" in _ids(evaluate_reads(fc, _ctx(now)))
    # ...but not in July (out of season)
    july = at(2026, 7, 1, 6)
    fc_july = forecast(july, hourly=_humid_run(july, 6, precip_at=2))
    assert "chilli-anthracnose-humid-wet-fruiting" not in _ids(evaluate_reads(fc_july, _ctx(july)))
