"""Application orchestration: fetch → run the pure rule engine → serialise the contract.

This wiring is deliberately tiny and provider-agnostic (it depends on the WeatherProvider
port, not a concrete adapter), so the same code runs behind the local demo, the future AWS
Lambda handler, and the test suite.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from rythu_weather.domain.engine import evaluate_reads
from rythu_weather.domain.models import FarmerContext, GeoPoint, WeatherProvider

# Pilot location: Bhupalpally town centre. The ~11 km model snaps this to its grid cell,
# which is surfaced honestly in the response coords.
BHUPALPALLY = GeoPoint(lat=18.44, lon=79.86)


async def get_weather(
    provider: WeatherProvider,
    point: GeoPoint,
    ctx: FarmerContext,
    *,
    hourly_hours: int = 48,
) -> dict[str, Any]:
    """Fetch a forecast for ``point``, evaluate farming reads for ``ctx``, return the contract.

    Raises :class:`ProviderError` if the fetch fails; the caller (Lambda handler) decides
    whether to serve cache or a degraded 200. Imported lazily so ``serialize`` stays a leaf.
    """
    from rythu_weather.app.serialize import forecast_to_contract

    forecast = await provider.fetch(point)
    reads = evaluate_reads(forecast, ctx)
    forecast = replace(forecast, farming_read=reads)
    return forecast_to_contract(forecast, ctx, hourly_hours=hourly_hours)
