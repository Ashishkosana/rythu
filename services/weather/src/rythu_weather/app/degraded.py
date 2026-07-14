"""Build an honest degraded response when we have no forecast at all.

Used when upstream fails and there is no cached forecast to fall back on. We still return 200
with the reliability block and an explicit note (never a raw 500), so the screen can always
show something truthful rather than a broken state.
"""

from __future__ import annotations

from typing import Any

from rythu_weather.app.serialize import forecast_to_contract
from rythu_weather.domain.models import (
    CoordsResolution,
    FarmerContext,
    Forecast,
    ForecastReliability,
    GeoPoint,
)


def degraded_contract(point: GeoPoint, ctx: FarmerContext, *, reason: str) -> dict[str, Any]:
    coords = CoordsResolution(requested=point, returned=point, elevation_m=0.0, snap_distance_km=0.0)
    empty = Forecast(
        coords=coords,
        generated_at=ctx.now,
        upstream_fetched_at=ctx.now,
        hourly=(),
        daily=(),
        reliability=ForecastReliability(),
    )
    contract = forecast_to_contract(empty, ctx)
    contract["degraded"] = True
    contract["note_en"] = "We couldn't reach the weather service just now. Please check again shortly."
    contract["reason"] = reason
    # Don't imply freshness we don't have.
    contract["reliability"]["source_stamp_en"] = "No live forecast available — please try again shortly."
    return contract
