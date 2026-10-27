from __future__ import annotations

import pytest

from builders import at, day, forecast, hours_from
from rythu_weather.adapters.fake import FailingProvider, FakeProvider
from rythu_weather.app.service import get_weather
from rythu_weather.domain.models import Crop, FarmerContext, GeoPoint, ProviderError, WaterSource

POINT = GeoPoint(18.44, 79.86)


async def test_get_weather_runs_engine_and_serialises():
    now = at(2026, 7, 15, 8)
    fc = forecast(
        now,
        hourly=hours_from(at(2026, 7, 15, 0), 24, wind=18.0),  # windy morning → spray-wind fires
        daily=[day(now.date(), pp_max=10, precip_sum=1.0)],
    )
    ctx = FarmerContext(now=now, water_source=WaterSource.RAINFED, crop=Crop.COTTON)
    contract = await get_weather(FakeProvider(fc), POINT, ctx)
    ids = {r["id"] for r in contract["farming_read"]}
    assert "spray-wind-drift" in ids


async def test_get_weather_propagates_provider_error():
    now = at(2026, 7, 15, 8)
    ctx = FarmerContext(now=now, water_source=WaterSource.RAINFED)
    with pytest.raises(ProviderError):
        await get_weather(FailingProvider(), POINT, ctx)


async def test_each_farmer_gets_their_own_pin_and_snap_distance():
    """One cached cell forecast serves many farmers; coords must be per request, not the first requester's."""
    now = at(2026, 7, 15, 8)
    fc = forecast(now, daily=[day(now.date())])  # returned grid point 18.453426, 79.872795
    ctx = FarmerContext(now=now, water_source=WaterSource.RAINFED)
    near = await get_weather(FakeProvider(fc), GeoPoint(18.4534, 79.8728), ctx)
    far = await get_weather(FakeProvider(fc), GeoPoint(18.40, 79.83), ctx)
    assert near["coords"]["requested"] == {"lat": 18.4534, "lon": 79.8728}
    assert near["coords"]["snap_distance_km"] < 0.1
    assert far["coords"]["requested"] == {"lat": 18.40, "lon": 79.83}
    assert 7.0 < far["coords"]["snap_distance_km"] < 7.5  # ≈ 7.3 km — honest, not the 2.01 km of the fixture
    assert near["coords"]["returned"] == far["coords"]["returned"]
