from __future__ import annotations

from datetime import timedelta

from builders import at, day, forecast, hour, hours_from
from rythu_weather.domain.windows import (
    all_below,
    any_at_or_above,
    choose_morning_day,
    max_present,
    morning_hours,
    next_days,
    next_hours,
    sum_present,
)


def test_any_at_or_above_ignores_none():
    assert any_at_or_above([None, 10, 59], 60) is False
    assert any_at_or_above([None, 60], 60) is True
    assert any_at_or_above([None, None], 1) is False  # unknown never fires


def test_all_below_rejects_none_conservatively():
    assert all_below([10, 20, 30], 60) is True
    assert all_below([10, 60], 60) is False
    assert all_below([10, None], 60) is False  # a missing value disqualifies the all-clear
    assert all_below([], 60) is False  # nothing seen → not a valid all-clear


def test_sum_and_max_present():
    assert sum_present([1.0, None, 2.5]) == 3.5
    assert max_present([None, 4, 9, None]) == 9
    assert max_present([None, None]) is None


def test_next_hours_is_forward_only_and_crosses_midnight():
    now = at(2026, 7, 15, 22, 30)
    # hours spanning 20:00 today .. 03:00 tomorrow
    hrs = [hour(at(2026, 7, 15, 20)), hour(at(2026, 7, 15, 23)), hour(at(2026, 7, 16, 1)), hour(at(2026, 7, 16, 4))]
    fc = forecast(now, hourly=hrs)
    window = next_hours(fc, now, 6)  # 22:30 .. 04:30
    times = [h.time_local.hour for h in window]
    assert times == [23, 1, 4]  # 20:00 (before now) excluded; midnight crossed
    assert all(h.time_local >= now for h in window)


def test_choose_morning_day():
    assert choose_morning_day(at(2026, 7, 15, 6)) == at(2026, 7, 15).date()
    assert choose_morning_day(at(2026, 7, 15, 9, 59)) == at(2026, 7, 15).date()
    assert choose_morning_day(at(2026, 7, 15, 10)) == at(2026, 7, 16).date()  # window passed → tomorrow
    assert choose_morning_day(at(2026, 7, 15, 18)) == at(2026, 7, 16).date()


def test_morning_hours_filters_window_and_day():
    now = at(2026, 7, 15, 5)
    hrs = hours_from(at(2026, 7, 15, 0), 24)
    fc = forecast(now, hourly=hrs)
    m = morning_hours(fc, at(2026, 7, 15).date())
    assert [h.time_local.hour for h in m] == [6, 7, 8, 9]  # 06:00 <= t < 10:00


def test_next_days_from_today_forward():
    now = at(2026, 7, 15, 12)
    ds = [day(at(2026, 7, 14).date()), *[day(at(2026, 7, 15 + i).date()) for i in range(4)]]
    fc = forecast(now, daily=ds)
    picked = next_days(fc, now, 3)
    assert [d.day.day for d in picked] == [15, 16, 17]  # yesterday dropped, capped at 3


# --- S2a: "today" means the REST of today, not the whole calendar day -------------------------


def _wet_morning_forecast(now):
    """45 mm fell 02:00–05:00 today; dry afterwards. Daily[0] is Open-Meteo's WHOLE-day aggregate."""
    day0 = at(2026, 7, 14)
    hourly = [
        hour(day0 + timedelta(hours=h), pp=90 if 2 <= h <= 5 else 5, precip=11.25 if 2 <= h <= 5 else 0.0,
             temp=38.0 if h == 14 else 27.0)
        for h in range(72)
    ]
    later = [day(at(2026, 7, 15 + i).date()) for i in range(6)]
    daily = [day(day0.date(), pp_max=90, precip_sum=45.0, tmax=38.0), *later]
    return forecast(now, hourly=hourly, daily=daily)


def test_today_is_derived_from_remaining_hours_once_rain_has_passed():
    now = at(2026, 7, 14, 21)
    today, tomorrow, *_ = next_days(_wet_morning_forecast(now), now, 3)
    assert today.day == now.date()
    assert today.precipitation_sum_mm == 0.0  # the morning's 45 mm is in the past
    assert today.precipitation_probability_max == 5
    assert today.temperature_max_c == 27.0  # the 14:00 peak has passed too
    assert tomorrow.day.day == 15  # later days keep Open-Meteo's daily values


def test_before_the_rain_today_still_counts_it():
    now = at(2026, 7, 14, 1)
    today = next_days(_wet_morning_forecast(now), now, 1)[0]
    assert today.precipitation_sum_mm == 45.0
    assert today.precipitation_probability_max == 90
    assert today.temperature_max_c == 38.0


def test_today_is_dropped_when_no_hour_of_it_remains():
    now = at(2026, 7, 14, 23, 30)  # last row (23:00) is already past
    picked = next_days(_wet_morning_forecast(now), now, 2)
    assert [d.day.day for d in picked] == [15, 16]


def test_unknown_remaining_rain_makes_todays_amount_unknown_not_zero():
    now = at(2026, 7, 14, 21)
    day0 = at(2026, 7, 14)
    hourly = [hour(day0 + timedelta(hours=h), precip=None if h == 22 else 0.0) for h in range(24)]
    fc = forecast(now, hourly=hourly, daily=[day(day0.date(), precip_sum=45.0)])
    assert next_days(fc, now, 1)[0].precipitation_sum_mm is None


def test_without_hourly_coverage_for_today_the_daily_row_is_kept():
    """No hourly rows dated today → we can't separate past from future; keep the daily value."""
    now = at(2026, 7, 14, 21)
    fc = forecast(now, daily=[day(at(2026, 7, 14).date(), precip_sum=45.0, pp_max=90)])
    today = next_days(fc, now, 1)[0]
    assert today.precipitation_sum_mm == 45.0 and today.precipitation_probability_max == 90
