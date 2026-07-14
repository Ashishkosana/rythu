"""AWS Lambda entrypoint behind API Gateway (HTTP API v2): ``GET /weather``.

Parses ``lat``/``lon``/``crop``/``water`` query params, runs the weather slice, and always
returns a truthful JSON body:
* 200 with the forecast contract on success,
* 200 degraded (reliability + note, empty reads) when upstream fails and no cache exists,
* 400 for a malformed request.

The provider is a plain Open-Meteo client, wrapped in the DynamoDB read-through cache when
``RYTHU_CACHE_TABLE`` is set. ``handle_request`` takes the provider explicitly so it is unit
-testable without AWS.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from rythu_weather.adapters.cache import CachedProvider, DynamoDbCacheStore
from rythu_weather.adapters.open_meteo import OpenMeteoHttpProvider
from rythu_weather.app.degraded import degraded_contract
from rythu_weather.app.service import BHUPALPALLY, get_weather
from rythu_weather.domain.models import (
    Crop,
    FarmerContext,
    GeoPoint,
    ProviderError,
    WaterSource,
    WeatherProvider,
)

IST = ZoneInfo("Asia/Kolkata")
_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Cache-Control": "public, max-age=300",
}


class BadRequest(ValueError):
    """A malformed client request → HTTP 400."""


def _query(event: dict[str, Any]) -> dict[str, str]:
    return event.get("queryStringParameters") or {}


def _parse_point(q: dict[str, str]) -> GeoPoint:
    lat, lon = q.get("lat"), q.get("lon")
    if lat is None and lon is None:
        return BHUPALPALLY
    if lat is None or lon is None:
        raise BadRequest("provide both lat and lon, or neither")
    try:
        point = GeoPoint(float(lat), float(lon))
    except ValueError as exc:
        raise BadRequest("lat and lon must be numbers") from exc
    if not (-90.0 <= point.lat <= 90.0 and -180.0 <= point.lon <= 180.0):
        raise BadRequest("lat/lon out of range")
    return point


def _parse_context(q: dict[str, str], now: datetime) -> FarmerContext:
    crop: Crop | None = None
    if q.get("crop"):
        try:
            crop = Crop(q["crop"])
        except ValueError as exc:
            raise BadRequest(f"unknown crop '{q['crop']}'") from exc
    water = WaterSource.RAINFED
    if q.get("water"):
        try:
            water = WaterSource(q["water"])
        except ValueError as exc:
            raise BadRequest(f"unknown water source '{q['water']}'") from exc
    return FarmerContext(now=now, water_source=water, crop=crop)


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {"statusCode": status, "headers": _HEADERS, "body": json.dumps(body, ensure_ascii=False)}


async def handle_request(event: dict[str, Any], provider: WeatherProvider) -> dict[str, Any]:
    now = datetime.now(IST)
    q = _query(event)
    try:
        point = _parse_point(q)
        ctx = _parse_context(q, now)
    except BadRequest as exc:
        return _response(400, {"error": str(exc)})

    try:
        contract = await get_weather(provider, point, ctx)
        return _response(200, contract)
    except ProviderError as exc:
        # No cache to fall back on → honest degraded 200, never a raw 500.
        return _response(200, degraded_contract(point, ctx, reason=str(exc)))


def build_provider() -> WeatherProvider:
    upstream = OpenMeteoHttpProvider()
    table = os.environ.get("RYTHU_CACHE_TABLE")
    if table:
        return CachedProvider(upstream, DynamoDbCacheStore(table))
    return upstream


def handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Lambda entrypoint (sync; wraps the async request handler)."""
    return asyncio.run(handle_request(event, build_provider()))
