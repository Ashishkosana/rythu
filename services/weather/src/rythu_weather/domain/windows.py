"""Pure helpers for selecting forecast windows and handling missing (None) values.

Two opposite None behaviours are encoded here on purpose (see the spec):

* Fire-on-risk rules ("rain is coming → don't spray") must NOT fire on unknown data —
  ``any_at_or_above`` simply ignores ``None``.
* All-clear checks ("wind is OK → you may spray") must treat unknown conservatively —
  ``all_below`` returns False the moment any value is ``None``, so a missing reading never
  produces a false all-clear.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
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


def longest_run(points: list[HourlyPoint], predicate: Callable[[HourlyPoint], bool]) -> int:
    """Longest streak of CONSECUTIVE points satisfying ``predicate``.

    The predicate must return False on unknown (None) metrics, so a missing reading breaks the
    run rather than silently extending it (used for the anthracnose humid-wet spell check).
    """
    best = current = 0
    for p in points:
        current = current + 1 if predicate(p) else 0
        best = max(best, current)
    return best


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
    """Up to ``days`` daily points from today (``now``'s date) forward, in order — FORWARD-only.

    Open-Meteo's daily row for today aggregates the WHOLE calendar day, including hours already
    gone; at 21:00 it still says "45 mm" for rain that fell at 03:00. So today's row is rebuilt
    from the hourly rows that are still ahead (see :func:`_rest_of_today`). When nothing of today
    remains, today is dropped. When the forecast has no hourly rows dated today at all, past and
    future cannot be told apart and the daily row is kept as-is.
    """
    today = now.date()
    upcoming: list[DailyPoint] = []
    for d in forecast.daily:
        if d.day < today:
            continue
        if d.day == today:
            rest = _rest_of_today(forecast, now, d)
            if rest is None:
                continue
            d = rest
        upcoming.append(d)
    return upcoming[:days]


def calendar_days(forecast: Forecast, now: datetime, days: int) -> list[DailyPoint]:
    """Up to ``days`` WHOLE calendar days from today, today's row including hours already gone.

    Only for questions about accumulated state rather than upcoming events — e.g. "is there enough
    soil moisture to sow?", where rain that fell this morning counts. Event warnings ("heavy rain
    is coming") must use :func:`next_days`.
    """
    today = now.date()
    return [d for d in forecast.daily if d.day >= today][:days]


def _rest_of_today(forecast: Forecast, now: datetime, daily_today: DailyPoint) -> DailyPoint | None:
    """Today's daily row recomputed over ``now .. midnight`` from hourly data.

    Returns ``daily_today`` unchanged when there is no hourly coverage of today, and ``None`` when
    today is covered but no hour of it remains. Rain amount follows the module's unknown rule: if
    any remaining hour's amount is unknown, today's amount is unknown (``None``), never a partial
    sum that could read as "only light rain".
    """
    today = now.date()
    if not any(h.time_local.date() == today for h in forecast.hourly):
        return daily_today
    rest = [h for h in forecast.hourly if h.time_local.date() == today and h.time_local >= now]
    if not rest:
        return None
    amounts = [h.precipitation_mm for h in rest]
    temps = present(h.temperature_c for h in rest)
    return DailyPoint(
        day=today,
        precipitation_probability_max=_max_int(h.precipitation_probability for h in rest),
        precipitation_sum_mm=None if any(a is None for a in amounts) else sum_present(amounts),
        temperature_max_c=float(max(temps)) if temps else None,
        temperature_min_c=float(min(temps)) if temps else None,
        weather_code=daily_today.weather_code,
        wind_speed_max_kmh=_max_float(h.wind_speed_kmh for h in rest),
    )


def _max_int(values: Iterable[int | None]) -> int | None:
    known = [v for v in values if v is not None]
    return max(known) if known else None


def _max_float(values: Iterable[float | None]) -> float | None:
    known = [v for v in values if v is not None]
    return max(known) if known else None
