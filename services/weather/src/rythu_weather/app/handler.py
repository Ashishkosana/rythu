"""AWS Lambda entrypoint behind API Gateway (HTTP API v2): ``GET /weather``.

A thin adapter: it pulls the query string and request id out of the API Gateway event, delegates to
the transport-neutral :func:`~rythu_weather.app.weather_request.answer_weather` (shared with the
FastAPI app), and turns the result back into a Lambda proxy response.

The provider is a plain Open-Meteo client, wrapped in the DynamoDB read-through cache when
``RYTHU_CACHE_TABLE`` is set. ``handle_request`` takes the provider explicitly so it is unit
-testable without AWS.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from rythu_weather.app.composition import build_provider
from rythu_weather.app.settings import get_settings
from rythu_weather.app.weather_request import answer_weather
from rythu_weather.domain.models import WeatherProvider
from rythu_weather.observability import configure_logging

__all__ = ["build_provider", "handle_request", "handler"]


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


async def handle_request(event: dict[str, Any], provider: WeatherProvider) -> dict[str, Any]:
    result = await answer_weather(_query(event), provider, inbound_request_id=_inbound_request_id(event))
    return {"statusCode": result.status, "headers": result.headers, "body": json.dumps(result.body, ensure_ascii=False)}


def handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Lambda entrypoint (sync; wraps the async request handler)."""
    configure_logging(get_settings().log_level)
    return asyncio.run(handle_request(event, build_provider()))
