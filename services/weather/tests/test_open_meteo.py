from __future__ import annotations

import httpx
import pytest
import respx

from builders import at
from rythu_weather.adapters.open_meteo import BASE_URL, OpenMeteoHttpProvider
from rythu_weather.app.service import BHUPALPALLY
from rythu_weather.domain.models import GeoPoint, ProviderError

SAMPLE = {
    "latitude": 18.453426,
    "longitude": 79.872795,
    "elevation": 199.0,
    "timezone": "Asia/Kolkata",
    "utc_offset_seconds": 19800,
    "hourly": {
        "time": ["2026-07-15T00:00", "2026-07-15T01:00", "2026-07-15T02:00"],
        "precipitation_probability": [10, None, 30],
        "precipitation": [0.0, 0.1, None],
        "temperature_2m": [28.0, 27.5, 27.0],
        "relative_humidity_2m": [70, 72, None],
        "weather_code": [1, 3, 95],
        "wind_speed_10m": [5.0, None, 12.0],
    },
    "daily": {
        "time": ["2026-07-15", "2026-07-16"],
        "precipitation_probability_max": [40, None],
        "precipitation_sum": [8.0, 20.0],
        "temperature_2m_max": [31.0, 30.0],
        "temperature_2m_min": [24.0, 23.5],
        "weather_code": [80, 95],
        "wind_speed_10m_max": [18.0, 22.0],
    },
}


def _provider() -> OpenMeteoHttpProvider:
    return OpenMeteoHttpProvider(clock=lambda: at(2026, 7, 15, 12))


@respx.mock
async def test_maps_response_and_preserves_nulls_as_unknown():
    respx.route(method="GET", host="api.open-meteo.com").mock(return_value=httpx.Response(200, json=SAMPLE))
    fc = await _provider().fetch(GeoPoint(18.44, 79.86))

    assert len(fc.hourly) == 3
    assert fc.hourly[1].precipitation_probability is None  # null → None, not 0
    assert fc.hourly[1].wind_speed_kmh is None
    assert fc.hourly[2].precipitation_mm is None
    assert fc.hourly[2].weather_code == 95
    # tz-aware Asia/Kolkata (+5:30)
    assert fc.hourly[0].time_local.utcoffset().total_seconds() == 19800
    assert fc.daily[1].precipitation_probability_max is None
    assert fc.upstream_fetched_at == at(2026, 7, 15, 12)


@respx.mock
async def test_coords_snap_is_computed():
    respx.route(method="GET", host="api.open-meteo.com").mock(return_value=httpx.Response(200, json=SAMPLE))
    fc = await _provider().fetch(GeoPoint(18.44, 79.86))
    assert fc.coords.requested == GeoPoint(18.44, 79.86)
    assert fc.coords.returned == GeoPoint(18.453426, 79.872795)
    assert fc.coords.elevation_m == 199.0
    assert 1.0 < fc.coords.snap_distance_km < 4.0  # ~2 km


@respx.mock
async def test_http_error_becomes_provider_error():
    respx.route(method="GET", host="api.open-meteo.com").mock(return_value=httpx.Response(500))
    with pytest.raises(ProviderError):
        await _provider().fetch(GeoPoint(18.44, 79.86))


@respx.mock
async def test_missing_blocks_becomes_provider_error():
    respx.route(method="GET", host="api.open-meteo.com").mock(
        return_value=httpx.Response(200, json={"latitude": 18.4, "longitude": 79.8})
    )
    with pytest.raises(ProviderError):
        await _provider().fetch(GeoPoint(18.44, 79.86))


@respx.mock
async def test_connect_error_becomes_provider_error():
    respx.route(method="GET", host="api.open-meteo.com").mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(ProviderError):
        await _provider().fetch(GeoPoint(18.44, 79.86))


@respx.mock
async def test_short_metric_column_is_padded_not_crashed():
    sample = {**SAMPLE, "hourly": {**SAMPLE["hourly"], "precipitation_probability": [10, 30]}}  # len 2 vs 3
    respx.route(method="GET", host="api.open-meteo.com").mock(return_value=httpx.Response(200, json=sample))
    fc = await _provider().fetch(GeoPoint(18.44, 79.86))
    assert len(fc.hourly) == 3
    assert fc.hourly[2].precipitation_probability is None  # padded to unknown, no IndexError


@respx.mock
async def test_missing_latlon_becomes_provider_error():
    payload = {"hourly": SAMPLE["hourly"], "daily": SAMPLE["daily"]}  # no latitude/longitude
    respx.route(method="GET", host="api.open-meteo.com").mock(return_value=httpx.Response(200, json=payload))
    with pytest.raises(ProviderError):
        await _provider().fetch(GeoPoint(18.44, 79.86))


@pytest.mark.live
async def test_live_open_meteo_bhupalpally():
    """Hits the real API. Run with: uv run pytest -m live"""
    fc = await OpenMeteoHttpProvider().fetch(BHUPALPALLY)
    assert fc.hourly and fc.daily
    assert fc.coords.snap_distance_km >= 0
    assert fc.reliability.show_confidence_rating is False
    assert BASE_URL.startswith("https://")
