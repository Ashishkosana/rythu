"""AWS Lambda entrypoint behind API Gateway (HTTP API v2): ``GET /weather``.

Parses ``lat``/``lon``/``crop``/``water`` query params, runs the weather slice, and always
returns a truthful JSON body:
* 200 with the forecast contract on success,
* 200 degraded (reliability + note, empty reads) when upstream fails and no cache exists,
* 400 for a malformed request.

Every response carries ``X-Request-Id`` (the caller's, if it sent a safe one), and every request
ends with one ``weather.request`` summary log line. An unexpected exception still degrades to an
honest 200 for the farmer, but is logged at ERROR with its traceback so a bug can't hide behind
"the weather service is down".

The provider is a plain Open-Meteo client, wrapped in the DynamoDB read-through cache when
``RYTHU_CACHE_TABLE`` is set. ``handle_request`` takes the provider explicitly so it is unit
-testable without AWS.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from rythu_weather.adapters.cache import CachedProvider, DynamoDbCacheStore
from rythu_weather.adapters.open_meteo import OpenMeteoHttpProvider
from rythu_weather.app.degraded import degraded_contract
from rythu_weather.app.service import BHUPALPALLY, get_weather
from rythu_weather.app.settings import Settings, get_settings
from rythu_weather.domain.models import (
    Crop,
    FarmerContext,
    GeoPoint,
    ProviderError,
    WaterSource,
    WeatherProvider,
)
from rythu_weather.observability import configure_logging, log_event, request_context, resolve_request_id

_log = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")
_BASE_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
}
_CACHEABLE = "public, max-age=300"
# A degraded answer must not be cached by anything in between: the next try may well succeed.
_NOT_CACHEABLE = "no-store"


class BadRequest(ValueError):
    """A malformed client request → HTTP 400."""


def _query(event: dict[str, Any]) -> dict[str, str]:
    return event.get("queryStringParameters") or {}


def _inbound_request_id(event: dict[str, Any]) -> str | None:
    """Caller-supplied ``X-Request-Id`` (headers are case-insensitive), else API Gateway's id."""
    headers = event.get("headers") or {}
    for name, value in headers.items():
        if name.lower() == "x-request-id":
            return str(value)
    request_context_ = event.get("requestContext") or {}
    rid = request_context_.get("requestId")
    return str(rid) if rid else None


def _cell(point: GeoPoint) -> str:
    """~11 km cell for logs — enough to debug a region, too coarse to locate a farm."""
    return f"{round(point.lat, 1)},{round(point.lon, 1)}"


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


def _response(status: int, body: dict[str, Any], *, request_id: str, cacheable: bool) -> dict[str, Any]:
    headers = {
        **_BASE_HEADERS,
        "Cache-Control": _CACHEABLE if cacheable else _NOT_CACHEABLE,
        "X-Request-Id": request_id,
    }
    return {"statusCode": status, "headers": headers, "body": json.dumps(body, ensure_ascii=False)}


async def handle_request(event: dict[str, Any], provider: WeatherProvider) -> dict[str, Any]:
    request_id = resolve_request_id(_inbound_request_id(event))
    with request_context(request_id):
        started = time.perf_counter()
        resp, summary = await _handle(event, provider, request_id)
        log_event(
            _log, logging.INFO, "weather.request",
            status=resp["statusCode"], latency_ms=round((time.perf_counter() - started) * 1000, 1), **summary,
        )
        return resp


async def _handle(
    event: dict[str, Any], provider: WeatherProvider, request_id: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run one request; return the response plus the fields for the summary log line."""
    now = datetime.now(IST)
    q = _query(event)
    try:
        point = _parse_point(q)
        ctx = _parse_context(q, now)
    except BadRequest as exc:
        return _response(400, {"error": str(exc)}, request_id=request_id, cacheable=True), {
            "outcome": "bad_request",
            "error": str(exc),
        }

    summary: dict[str, Any] = {
        "cell": _cell(point),
        "crop": ctx.crop.value if ctx.crop is not None else None,
        "water": ctx.water_source.value,
    }
    try:
        contract = await get_weather(provider, point, ctx)
    except ProviderError as exc:
        # No cache to fall back on → honest degraded 200, never a raw 500.
        log_event(_log, logging.WARNING, "weather.degraded", reason=str(exc))
        return _degraded(point, ctx, request_id), {**summary, "outcome": "degraded"}
    except Exception:
        # A bug, not an outage: the farmer still gets an honest degraded screen, but we log the
        # traceback at ERROR so it is visible (and alertable) instead of masquerading as downtime.
        _log.exception("weather.unhandled_error")
        return _degraded(point, ctx, request_id), {**summary, "outcome": "error"}

    summary["outcome"] = "offline_cache" if contract["reliability"]["is_offline_cache"] else "ok"
    summary["reads"] = len(contract["farming_read"])
    return _response(200, contract, request_id=request_id, cacheable=True), summary


def _degraded(point: GeoPoint, ctx: FarmerContext, request_id: str) -> dict[str, Any]:
    return _response(200, degraded_contract(point, ctx), request_id=request_id, cacheable=False)


def build_provider(settings: Settings | None = None) -> WeatherProvider:
    s = settings or get_settings()
    upstream = OpenMeteoHttpProvider(timeout=s.open_meteo_timeout_s)
    if s.cache_table:
        return CachedProvider(upstream, DynamoDbCacheStore(s.cache_table))
    return upstream


def handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Lambda entrypoint (sync; wraps the async request handler)."""
    configure_logging(get_settings().log_level)
    return asyncio.run(handle_request(event, build_provider()))
