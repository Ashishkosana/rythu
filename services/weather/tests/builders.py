"""Tiny builders for constructing forecasts in tests.

Defaults are deliberately BENIGN (no rain, low wind, clear sky) so a rule only fires when a
test explicitly sets its trigger — keeping each test's intent obvious.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from rythu_weather.domain.models import (
    CoordsResolution,
    Crop,
    DailyPoint,
    FarmerContext,
    Forecast,
    GeoPoint,
    HourlyPoint,
    WaterSource,
)

IST = ZoneInfo("Asia/Kolkata")

_COORDS = CoordsResolution(
    requested=GeoPoint(18.44, 79.86),
    returned=GeoPoint(18.453426, 79.872795),
    elevation_m=199.0,
    snap_distance_km=2.01,
)


def at(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=IST)


def hour(
    t: datetime,
    *,
    pp: int | None = 0,
    precip: float | None = 0.0,
    temp: float | None = 28.0,
    rh: int | None = 70,
    code: int | None = 1,
    wind: float | None = 3.0,
) -> HourlyPoint:
    return HourlyPoint(t, pp, precip, temp, rh, code, wind)


def hours_from(start: datetime, n: int, **kw: object) -> list[HourlyPoint]:
    return [hour(start + timedelta(hours=i), **kw) for i in range(n)]  # type: ignore[arg-type]


def day(
    d: date,
    *,
    pp_max: int | None = 0,
    precip_sum: float | None = 0.0,
    tmax: float | None = 30.0,
    tmin: float | None = 24.0,
    code: int | None = 1,
    wind_max: float | None = 5.0,
) -> DailyPoint:
    return DailyPoint(d, pp_max, precip_sum, tmax, tmin, code, wind_max)


def days_from(start: date, n: int, **kw: object) -> list[DailyPoint]:
    return [day(start + timedelta(days=i), **kw) for i in range(n)]  # type: ignore[arg-type]


def forecast(
    now: datetime,
    *,
    hourly: list[HourlyPoint] | None = None,
    daily: list[DailyPoint] | None = None,
    fetched_at: datetime | None = None,
) -> Forecast:
    fa = fetched_at or now
    return Forecast(
        coords=_COORDS,
        generated_at=fa,
        upstream_fetched_at=fa,
        hourly=tuple(hourly or ()),
        daily=tuple(daily or ()),
    )


def ctx(
    now: datetime,
    *,
    crop: Crop | None = None,
    water: WaterSource = WaterSource.RAINFED,
) -> FarmerContext:
    return FarmerContext(now=now, water_source=water, crop=crop)
