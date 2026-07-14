"""Per-rule predicate tests: boundaries, removed-leg regressions, None-handling.

Predicates are exercised directly (scope/season filtering is covered in test_engine.py).
"""

from __future__ import annotations

from datetime import timedelta

from builders import at, day, forecast, hour, hours_from

# builders.ctx isn't imported to avoid shadowing; make a local context helper.
from rythu_weather.domain.models import FarmerContext, WaterSource
from rythu_weather.domain.rules import (
    _drainage_heavy_rain,
    _fieldwork_storm,
    _harvest_paddy,
    _irrigate_skip,
    _sow_avoid_washout,
    _sow_need_moisture,
    _spray_rain_washoff,
    _spray_wind_drift,
)


def _ctx(now, crop=None, water=WaterSource.RAINFED):
    return FarmerContext(now=now, water_source=water, crop=crop)


# --- spray-rain-washoff -------------------------------------------------------------------


def test_spray_rain_prob_boundary_60():
    now = at(2026, 7, 15, 8)
    assert _spray_rain_washoff(forecast(now, hourly=hours_from(now, 6, pp=59, precip=0.0)), _ctx(now)) is None
    fired = _spray_rain_washoff(forecast(now, hourly=hours_from(now, 6, pp=60, precip=0.0)), _ctx(now))
    assert fired is not None and "60%" in fired.headline_en


def test_spray_rain_single_light_shower_half_mm():
    now = at(2026, 7, 15, 8)
    # one hour of 0.5 mm, window sum stays < 2 mm → fires on the per-hour leg
    hrs = [hour(now, pp=0, precip=0.5), *hours_from(now + timedelta(hours=1), 5, pp=0, precip=0.0)]
    assert _spray_rain_washoff(forecast(now, hourly=hrs), _ctx(now)) is not None
    hrs_ok = [hour(now, pp=0, precip=0.4), *hours_from(now + timedelta(hours=1), 5, pp=0, precip=0.0)]
    assert _spray_rain_washoff(forecast(now, hourly=hrs_ok), _ctx(now)) is None


def test_spray_rain_accumulation_leg():
    now = at(2026, 7, 15, 8)
    assert (
        _spray_rain_washoff(forecast(now, hourly=hours_from(now, 6, pp=0, precip=0.34)), _ctx(now)) is not None
    )  # ~2.04
    assert _spray_rain_washoff(forecast(now, hourly=hours_from(now, 6, pp=0, precip=0.30)), _ctx(now)) is None  # 1.8


def test_spray_rain_ignores_rain_already_fallen_before_now():
    """Regression: the removed backward-looking calendar-day leg must not resurface."""
    now = at(2026, 7, 15, 12)
    hrs = [hour(at(2026, 7, 15, 9), pp=100, precip=50.0), *hours_from(now, 6, pp=0, precip=0.0)]
    assert _spray_rain_washoff(forecast(now, hourly=hrs), _ctx(now)) is None


def test_spray_rain_unknown_data_does_not_fire():
    now = at(2026, 7, 15, 8)
    hrs = hours_from(now, 6, pp=None, precip=None)
    assert _spray_rain_washoff(forecast(now, hourly=hrs), _ctx(now)) is None
    assert _spray_rain_washoff(forecast(now, hourly=[]), _ctx(now)) is None


# --- spray-wind-drift ---------------------------------------------------------------------


def test_spray_wind_boundary_15():
    now = at(2026, 7, 15, 5)  # before 10:00 → today's morning window
    calm = forecast(now, hourly=hours_from(at(2026, 7, 15, 0), 24, wind=14.0))
    assert _spray_wind_drift(calm, _ctx(now)) is None
    windy = forecast(now, hourly=hours_from(at(2026, 7, 15, 0), 24, wind=15.0))
    fired = _spray_wind_drift(windy, _ctx(now))
    assert fired is not None and "this morning" in fired.headline_en


def test_spray_wind_unknown_does_not_warn():
    now = at(2026, 7, 15, 5)
    fc = forecast(now, hourly=hours_from(at(2026, 7, 15, 0), 24, wind=None))
    assert _spray_wind_drift(fc, _ctx(now)) is None


def test_spray_wind_uses_tomorrow_when_morning_passed():
    now = at(2026, 7, 15, 18)  # evening → checks tomorrow morning
    only_today = forecast(now, hourly=hours_from(at(2026, 7, 15, 0), 24, wind=30.0))
    assert _spray_wind_drift(only_today, _ctx(now)) is None  # no tomorrow data
    with_tomorrow = forecast(now, hourly=hours_from(at(2026, 7, 16, 0), 24, wind=30.0))
    fired = _spray_wind_drift(with_tomorrow, _ctx(now))
    assert fired is not None and "tomorrow morning" in fired.headline_en


# --- irrigate-skip ------------------------------------------------------------------------


def test_irrigate_skip_needs_amount_and_probability_same_day():
    now = at(2026, 7, 15, 12)
    good = forecast(now, daily=[day(now.date(), pp_max=70, precip_sum=25.0)])
    fired = _irrigate_skip(good, _ctx(now))
    assert fired is not None and "25 mm" in fired.headline_en and "70%" in fired.headline_en


def test_irrigate_skip_rejects_prob_only_and_amount_only():
    now = at(2026, 7, 15, 12)
    prob_only = forecast(now, daily=[day(now.date(), pp_max=90, precip_sum=5.0)])
    assert _irrigate_skip(prob_only, _ctx(now)) is None
    amount_low = forecast(now, daily=[day(now.date(), pp_max=50, precip_sum=25.0)])
    assert _irrigate_skip(amount_low, _ctx(now)) is None


def test_irrigate_skip_never_pairs_across_days():
    now = at(2026, 7, 15, 12)
    fc = forecast(
        now,
        daily=[
            day(now.date(), pp_max=40, precip_sum=25.0),
            day((now + timedelta(days=1)).date(), pp_max=80, precip_sum=5.0),
        ],
    )
    assert _irrigate_skip(fc, _ctx(now)) is None


# --- sow-need-soil-moisture ---------------------------------------------------------------


def test_sow_moisture_fires_on_drizzle_days():
    now = at(2026, 7, 15, 9)
    fc = forecast(
        now,
        daily=[
            day(now.date(), pp_max=30, precip_sum=8.0),
            day((now + timedelta(days=1)).date(), pp_max=20, precip_sum=7.0),
            day((now + timedelta(days=2)).date(), pp_max=25, precip_sum=6.0),
        ],
    )
    assert _sow_need_moisture(fc, _ctx(now)) is not None  # largest single day 8 < 20


def test_sow_moisture_silent_when_a_good_day_exists():
    now = at(2026, 7, 15, 9)
    fc = forecast(
        now,
        daily=[
            day(now.date(), pp_max=30, precip_sum=22.0),  # one good soaking day
            day((now + timedelta(days=1)).date(), pp_max=20, precip_sum=2.0),
            day((now + timedelta(days=2)).date(), pp_max=25, precip_sum=2.0),
        ],
    )
    assert _sow_need_moisture(fc, _ctx(now)) is None


def test_sow_moisture_conservative_on_unknown_probability():
    now = at(2026, 7, 15, 9)
    fc = forecast(
        now,
        daily=[
            day(now.date(), pp_max=None, precip_sum=8.0),
            day((now + timedelta(days=1)).date(), pp_max=20, precip_sum=7.0),
            day((now + timedelta(days=2)).date(), pp_max=25, precip_sum=6.0),
        ],
    )
    assert _sow_need_moisture(fc, _ctx(now)) is None  # don't advise "wait" on incomplete data


# --- sow-avoid-before-washout -------------------------------------------------------------


def test_sow_washout_fires_on_amount_only():
    now = at(2026, 7, 15, 9)
    assert _sow_avoid_washout(forecast(now, daily=[day(now.date(), pp_max=0, precip_sum=45.0)]), _ctx(now)) is not None
    assert _sow_avoid_washout(forecast(now, daily=[day(now.date(), pp_max=0, precip_sum=39.0)]), _ctx(now)) is None


def test_sow_washout_ignores_high_probability_light_rain():
    now = at(2026, 7, 15, 9)
    fc = forecast(now, daily=[day(now.date(), pp_max=95, precip_sum=6.0)])
    assert _sow_avoid_washout(fc, _ctx(now)) is None  # removed prob-only branch


# --- harvest-paddy ------------------------------------------------------------------------


def test_harvest_paddy_fires_protectively():
    now = at(2026, 9, 20, 8)
    assert _harvest_paddy(forecast(now, daily=[day(now.date(), pp_max=60, precip_sum=0.0)]), _ctx(now)) is not None
    assert _harvest_paddy(forecast(now, daily=[day(now.date(), pp_max=0, precip_sum=12.0)]), _ctx(now)) is not None
    assert _harvest_paddy(forecast(now, daily=[day(now.date(), pp_max=50, precip_sum=5.0)]), _ctx(now)) is None


# --- fieldwork-storm ----------------------------------------------------------------------


def test_fieldwork_fires_on_thunderstorm_code():
    now = at(2026, 7, 15, 8)
    hrs = [hour(now, pp=10, code=95, wind=5.0), *hours_from(now + timedelta(hours=1), 5)]
    fired = _fieldwork_storm(forecast(now, hourly=hrs), _ctx(now))
    assert fired is not None and fired.headline_en.startswith("Thunderstorms")


def test_fieldwork_fires_on_rain_or_high_wind():
    now = at(2026, 7, 15, 8)
    assert _fieldwork_storm(forecast(now, hourly=hours_from(now, 6, pp=60)), _ctx(now)) is not None
    assert _fieldwork_storm(forecast(now, hourly=hours_from(now, 6, wind=30.0)), _ctx(now)) is not None


def test_fieldwork_silent_when_calm():
    now = at(2026, 7, 15, 8)
    assert _fieldwork_storm(forecast(now, hourly=hours_from(now, 6, pp=30, wind=10.0, code=2)), _ctx(now)) is None


def test_fieldwork_joins_multiple_reasons():
    now = at(2026, 7, 15, 8)
    hrs = hours_from(now, 6, pp=70, wind=35.0, code=95)
    fired = _fieldwork_storm(forecast(now, hourly=hrs), _ctx(now))
    assert fired is not None and "and" in fired.headline_en


# --- drainage-heavy-rain ------------------------------------------------------------------


def test_drainage_hard_amount_boundary_50():
    now = at(2026, 7, 15, 9)
    assert (
        _drainage_heavy_rain(forecast(now, daily=[day(now.date(), pp_max=0, precip_sum=50.0)]), _ctx(now)) is not None
    )
    assert _drainage_heavy_rain(forecast(now, daily=[day(now.date(), pp_max=0, precip_sum=49.0)]), _ctx(now)) is None


def test_drainage_soft_amount_needs_high_probability():
    now = at(2026, 7, 15, 9)
    assert (
        _drainage_heavy_rain(forecast(now, daily=[day(now.date(), pp_max=70, precip_sum=35.0)]), _ctx(now)) is not None
    )
    assert _drainage_heavy_rain(forecast(now, daily=[day(now.date(), pp_max=69, precip_sum=35.0)]), _ctx(now)) is None


def test_drainage_ignores_high_probability_light_rain():
    now = at(2026, 7, 15, 9)
    assert _drainage_heavy_rain(forecast(now, daily=[day(now.date(), pp_max=90, precip_sum=10.0)]), _ctx(now)) is None


# --- forward-only / None regressions (from adversarial review) -----------------------------


def test_spray_wind_ignores_wind_already_passed_this_morning():
    # now 09:00: strong wind at 06:00-08:00 (past), calm from 09:00 → must NOT warn
    now = at(2026, 7, 15, 9)
    hrs = [*hours_from(at(2026, 7, 15, 6), 3, wind=25.0), hour(at(2026, 7, 15, 9), wind=5.0)]
    assert _spray_wind_drift(forecast(now, hourly=hrs), _ctx(now)) is None


def test_spray_wind_warns_on_wind_still_ahead_this_morning():
    now = at(2026, 7, 15, 8)
    hrs = hours_from(at(2026, 7, 15, 6), 4, wind=20.0)  # 06-09; 08 & 09 are still ahead
    fired = _spray_wind_drift(forecast(now, hourly=hrs), _ctx(now))
    assert fired is not None and "this morning" in fired.headline_en


def test_sow_moisture_conservative_on_unknown_amount():
    now = at(2026, 7, 15, 9)
    fc = forecast(
        now,
        daily=[
            day(now.date(), pp_max=10, precip_sum=None),  # unknown amount could hide a soaker
            day((now + timedelta(days=1)).date(), pp_max=10, precip_sum=8.0),
            day((now + timedelta(days=2)).date(), pp_max=10, precip_sum=6.0),
        ],
    )
    assert _sow_need_moisture(fc, _ctx(now)) is None  # never advise "wait" on incomplete rainfall
