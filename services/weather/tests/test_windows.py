from __future__ import annotations

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
