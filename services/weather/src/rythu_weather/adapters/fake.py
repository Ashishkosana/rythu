"""In-memory WeatherProvider for tests and local demos (no network)."""

from __future__ import annotations

from dataclasses import dataclass

from rythu_weather.domain.models import Forecast, GeoPoint, ProviderError


@dataclass(frozen=True, slots=True)
class FakeProvider:
    """Returns a preset Forecast, ignoring the point. Implements the WeatherProvider port."""

    forecast: Forecast

    async def fetch(self, point: GeoPoint) -> Forecast:
        return self.forecast


@dataclass(frozen=True, slots=True)
class FailingProvider:
    """Always raises ProviderError — used to test the degraded-fetch path."""

    message: str = "simulated upstream failure"

    async def fetch(self, point: GeoPoint) -> Forecast:
        raise ProviderError(self.message)
