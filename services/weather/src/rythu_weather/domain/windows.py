"""Pure helpers for selecting forecast windows and handling missing (None) values.

Two opposite None behaviours are encoded here on purpose (see the spec):

* Fire-on-risk rules ("rain is coming → don't spray") must NOT fire on unknown data —
  ``any_at_or_above`` simply ignores ``None``.
* All-clear checks ("wind is OK → you may spray") must treat unknown conservatively —
  ``all_below`` returns False the moment any value is ``None``, so a missing reading never
  produces a false all-clear.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, time, timedelta

from rythu_weather.domain.models import DailyPoint, Forecast, HourlyPoint

# --- numeric helpers over Optional values -------------------------------------------------

Number = float | int


def present(values: Iterable[Number | None]) -> list[Number]:
    """Drop ``None`` (unknown) values."""
    return [v for v in values if v is not None]


def any_at_or_above(values: Iterable[Number | None], threshold: Number) -> bool:
    """True if any KNOWN value is >= threshold. Unknown values are ignored (no false fire)."""
    return any(v >= threshold for v in values if v is not None)


def all_below(values: Iterable[Number | None], threshold: Number) -> bool:
    """True only if every value is KNOWN and < threshold.

    Any ``None`` makes this False — a missing reading disqualifies an all-clear.
    """
    seen = False
    for v in values:
        if v is None:
            return False
        seen = True
        if v >= threshold:
            return False
    return seen


def sum_present(values: Iterable[Number | None]) -> float:
    """Sum of known values (unknown treated as absent, not zero-with-meaning)."""
    return float(sum(present(values)))


def max_present(values: Iterable[Number | None]) -> Number | None:
    """Largest known value, or None if all unknown."""
    known = present(values)
    return max(known) if known else None


# --- hourly window selection --------------------------------------------------------------


def hours_in(forecast: Forecast, start: datetime, end: datetime) -> list[HourlyPoint]:
    """Hourly points with ``start <= time_local < end`` (selected by timestamp, not index).

    Selecting by timestamp is essential: the array may not begin at hour 0 and a window can
    span midnight.
    """
    return [h for h in forecast.hourly if start <= h.time_local < end]


def next_hours(forecast: Forecast, now: datetime, hours: int) -> list[HourlyPoint]:
    """Forward window ``now .. now + hours``. Every returned point is guaranteed >= now."""
    return hours_in(forecast, now, now + timedelta(hours=hours))


def choose_morning_day(now: datetime) -> date:
    """The day whose 06:00–10:00 spray window we should check: today if it hasn't passed,
    otherwise tomorrow."""
    if now.time() < time(10, 0):
        return now.date()
    return (now + timedelta(days=1)).date()


def morning_hours(forecast: Forecast, day: date) -> list[HourlyPoint]:
    """Hourly points on ``day`` within the recommended early-morning spray window (06:00–10:00)."""
    lo, hi = time(6, 0), time(10, 0)
    return [h for h in forecast.hourly if h.time_local.date() == day and lo <= h.time_local.time() < hi]


# --- daily window selection ---------------------------------------------------------------


def next_days(forecast: Forecast, now: datetime, days: int) -> list[DailyPoint]:
    """Up to ``days`` daily points from today (``now``'s date) forward, in order."""
    today = now.date()
    upcoming = [d for d in forecast.daily if d.day >= today]
    return upcoming[:days]
