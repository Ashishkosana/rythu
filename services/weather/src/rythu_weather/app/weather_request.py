"""Transport-neutral handling of one weather request: parse → validate → answer → log.

Both transports — the AWS Lambda handler (``app.handler``) and the FastAPI app (``api.app``) — are
thin adapters over :func:`answer_weather`, so they cannot drift: same validation, same coverage,
same degraded policy, same headers, same log lines. Nothing here knows about Lambda events,
ASGI or Pydantic.

Always a truthful JSON body:
* 200 with the forecast contract on success,
* 200 degraded (reliability + note, empty reads) when upstream fails and no cache exists,
* 400 ``{"error", "code"}`` for a request we won't serve.

Every response carries ``X-Request-Id`` (the caller's, if safe), and every request ends with one
``weather.request`` summary log line. An unexpected exception still degrades to an honest 200 for
the farmer, but is logged at ERROR with its traceback so a bug can't hide behind "the weather
service is down".
"""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from rythu_weather.app.degraded import degraded_contract
from rythu_weather.app.service import BHUPALPALLY, get_weather
from rythu_weather.domain.coverage import in_coverage
from rythu_weather.domain.models import Crop, FarmerContext, GeoPoint, ProviderError, WaterSource, WeatherProvider
from rythu_weather.observability import log_event, request_context, resolve_request_id

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
    """A client request we won't serve → HTTP 400 with a stable machine-readable ``code``."""

    def __init__(self, message: str, code: str = "bad_request") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class HttpResult:
    """What any transport needs to send: status, JSON-able body, headers."""

    status: int
    body: dict[str, Any]
    headers: dict[str, str]


def cell(point: GeoPoint) -> str:
    """~11 km cell for logs — enough to debug a region, too coarse to locate a farm."""
    return f"{round(point.lat, 1)},{round(point.lon, 1)}"


def parse_point(q: Mapping[str, str]) -> GeoPoint:
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
    if not in_coverage(point.lat, point.lon):
        raise BadRequest("Rythu currently covers Telangana only", code="outside_coverage")
    return point


def parse_context(q: Mapping[str, str], now: datetime) -> FarmerContext:
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


def base_headers(request_id: str, *, cache_control: str) -> dict[str, str]:
    """Headers every JSON response carries (shared with the other endpoints)."""
    return {**_BASE_HEADERS, "Cache-Control": cache_control, "X-Request-Id": request_id}


def _result(status: int, body: dict[str, Any], *, request_id: str, cacheable: bool) -> HttpResult:
    cache_control = _CACHEABLE if cacheable else _NOT_CACHEABLE
    return HttpResult(status, body, base_headers(request_id, cache_control=cache_control))


async def answer_weather(
    params: Mapping[str, str], provider: WeatherProvider, *, inbound_request_id: str | None = None
) -> HttpResult:
    """Answer one ``GET /weather``-style request. Never raises for request-level problems."""
    request_id = resolve_request_id(inbound_request_id)
    with request_context(request_id):
        started = time.perf_counter()
        result, summary = await _answer(params, provider, request_id)
        log_event(
            _log, logging.INFO, "weather.request",
            status=result.status, latency_ms=round((time.perf_counter() - started) * 1000, 1), **summary,
        )
        return result


async def _answer(
    q: Mapping[str, str], provider: WeatherProvider, request_id: str
) -> tuple[HttpResult, dict[str, Any]]:
    """Run one request; return the result plus the fields for the summary log line."""
    now = datetime.now(IST)
    try:
        point = parse_point(q)
        ctx = parse_context(q, now)
    except BadRequest as exc:
        body = {"error": str(exc), "code": exc.code}
        return _result(400, body, request_id=request_id, cacheable=True), {
            "outcome": exc.code,
            "error": str(exc),
        }

    summary: dict[str, Any] = {
        "cell": cell(point),
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
    return _result(200, contract, request_id=request_id, cacheable=True), summary


def _degraded(point: GeoPoint, ctx: FarmerContext, request_id: str) -> HttpResult:
    return _result(200, degraded_contract(point, ctx), request_id=request_id, cacheable=False)
