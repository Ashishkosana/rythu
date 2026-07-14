"""Open-Meteo HTTP adapter — the only place that knows the provider's wire format.

Maps raw Open-Meteo JSON into the domain :class:`Forecast`. The rest of the system never
sees Open-Meteo field names, so adding an ensemble/spread provider later (the Phase-2
honest-confidence badge) touches only this file.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from rythu_weather.domain.geo import haversine_km
from rythu_weather.domain.models import (
    CoordsResolution,
    DailyPoint,
    Forecast,
    ForecastReliability,
    GeoPoint,
    HourlyPoint,
    ProviderError,
)

BASE_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_FIELDS = (
    "precipitation_probability",
    "precipitation",
    "temperature_2m",
    "relative_humidity_2m",
    "weather_code",
    "wind_speed_10m",
)
DAILY_FIELDS = (
    "precipitation_probability_max",
    "precipitation_sum",
    "temperature_2m_max",
    "temperature_2m_min",
    "weather_code",
    "wind_speed_10m_max",
)
DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_FORECAST_DAYS = 7


def _default_clock() -> datetime:
    return datetime.now(ZoneInfo(DEFAULT_TIMEZONE))


def _as_int(v: Any) -> int | None:
    return None if v is None else int(v)


def _as_float(v: Any) -> float | None:
    return None if v is None else float(v)


def _column(block: dict[str, Any], name: str, length: int) -> list[Any]:
    """A metric column normalised to exactly ``length`` items.

    Open-Meteo does not guarantee every metric array matches the ``time`` array, so a missing
    field, a short column (pad with None → unknown), or a long one (truncate) all degrade
    gracefully instead of crashing the mapping with an IndexError.
    """
    values = block.get(name)
    if not isinstance(values, list):
        return [None] * length
    if len(values) < length:
        return values + [None] * (length - len(values))
    return values[:length]


class OpenMeteoHttpProvider:
    """Fetches a normalised Forecast from Open-Meteo.

    Pass a shared ``httpx.AsyncClient`` (e.g. reused across a Lambda invocation) or let the
    provider create and close one per fetch. ``clock`` is injectable so the recorded
    fetch-time is deterministic in tests.
    """

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        *,
        clock: Callable[[], datetime] = _default_clock,
        timeout: float = 10.0,
        forecast_days: int = DEFAULT_FORECAST_DAYS,
    ) -> None:
        self._client = client
        self._clock = clock
        self._timeout = timeout
        self._forecast_days = forecast_days

    def _params(self, point: GeoPoint) -> dict[str, Any]:
        return {
            "latitude": point.lat,
            "longitude": point.lon,
            "hourly": ",".join(HOURLY_FIELDS),
            "daily": ",".join(DAILY_FIELDS),
            "timezone": DEFAULT_TIMEZONE,
            "forecast_days": self._forecast_days,
        }

    async def fetch(self, point: GeoPoint) -> Forecast:
        if self._client is not None:
            data = await self._request(self._client, point)
        else:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                data = await self._request(client, point)
        try:
            return self._map(data, point, self._clock())
        except (KeyError, ValueError, TypeError, IndexError) as exc:
            # Malformed/changed upstream payload (e.g. missing lat/lon) must degrade via the
            # port contract, not escape as a raw 500.
            raise ProviderError(f"Open-Meteo response could not be parsed: {exc!r}") from exc

    async def _request(self, client: httpx.AsyncClient, point: GeoPoint) -> dict[str, Any]:
        try:
            resp = await client.get(BASE_URL, params=self._params(point), timeout=self._timeout)
            resp.raise_for_status()
            payload = resp.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Open-Meteo request failed: {exc}") from exc
        except ValueError as exc:  # invalid JSON
            raise ProviderError(f"Open-Meteo returned invalid JSON: {exc}") from exc
        if not isinstance(payload, dict) or "hourly" not in payload or "daily" not in payload:
            raise ProviderError("Open-Meteo response missing 'hourly'/'daily' blocks")
        return payload

    def _map(self, data: dict[str, Any], requested: GeoPoint, fetched_at: datetime) -> Forecast:
        tz = ZoneInfo(str(data.get("timezone", DEFAULT_TIMEZONE)))
        returned = GeoPoint(lat=float(data["latitude"]), lon=float(data["longitude"]))
        coords = CoordsResolution(
            requested=requested,
            returned=returned,
            elevation_m=float(data.get("elevation", 0.0)),
            snap_distance_km=round(haversine_km(requested, returned), 2),
        )
        return Forecast(
            coords=coords,
            generated_at=fetched_at,
            upstream_fetched_at=fetched_at,
            hourly=self._map_hourly(data["hourly"], tz),
            daily=self._map_daily(data["daily"], tz),
            reliability=ForecastReliability(),
            timezone=str(data.get("timezone", DEFAULT_TIMEZONE)),
        )

    @staticmethod
    def _map_hourly(block: dict[str, Any], tz: ZoneInfo) -> tuple[HourlyPoint, ...]:
        times: Sequence[str] = block.get("time", [])
        n = len(times)
        pp = _column(block, "precipitation_probability", n)
        pr = _column(block, "precipitation", n)
        temp = _column(block, "temperature_2m", n)
        rh = _column(block, "relative_humidity_2m", n)
        wc = _column(block, "weather_code", n)
        ws = _column(block, "wind_speed_10m", n)
        return tuple(
            HourlyPoint(
                time_local=datetime.fromisoformat(times[i]).replace(tzinfo=tz),
                precipitation_probability=_as_int(pp[i]),
                precipitation_mm=_as_float(pr[i]),
                temperature_c=_as_float(temp[i]),
                relative_humidity=_as_int(rh[i]),
                weather_code=_as_int(wc[i]),
                wind_speed_kmh=_as_float(ws[i]),
            )
            for i in range(n)
        )

    @staticmethod
    def _map_daily(block: dict[str, Any], tz: ZoneInfo) -> tuple[DailyPoint, ...]:
        days: Sequence[str] = block.get("time", [])
        n = len(days)
        pp = _column(block, "precipitation_probability_max", n)
        ps = _column(block, "precipitation_sum", n)
        tmax = _column(block, "temperature_2m_max", n)
        tmin = _column(block, "temperature_2m_min", n)
        wc = _column(block, "weather_code", n)
        wmax = _column(block, "wind_speed_10m_max", n)
        return tuple(
            DailyPoint(
                day=date.fromisoformat(days[i]),
                precipitation_probability_max=_as_int(pp[i]),
                precipitation_sum_mm=_as_float(ps[i]),
                temperature_max_c=_as_float(tmax[i]),
                temperature_min_c=_as_float(tmin[i]),
                weather_code=_as_int(wc[i]),
                wind_speed_max_kmh=_as_float(wmax[i]),
            )
            for i in range(n)
        )
