"""A read-through cache in front of a WeatherProvider — the "mandatory proxy cache".

Two jobs:
1. Cut Open-Meteo calls (its free tier is ~10k/day) — serve a cached forecast while it is fresh.
2. Honest offline resilience — if upstream fails and we hold a (stale) cached forecast, serve
   it flagged ``is_offline_cache=True`` so the client shows "Offline — showing saved forecast".

The cache stores the RAW provider forecast (pre rule-engine), so one entry serves all crops.
Storage is behind a small ``CacheStore`` port: an in-memory fake for tests, DynamoDB in prod.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from rythu_weather.adapters.serde import forecast_from_cache, forecast_to_cache
from rythu_weather.domain.models import Forecast, GeoPoint, ProviderError, WeatherProvider


def cache_key(point: GeoPoint) -> str:
    """Grid-rounded key so nearby pins share a cache entry (the model is ~11 km anyway)."""
    return f"{round(point.lat, 2)},{round(point.lon, 2)}"


class CacheStore(Protocol):
    """Port for the cache backend. Values are :func:`forecast_to_cache` dicts."""

    async def get(self, key: str) -> dict[str, Any] | None: ...

    async def put(self, key: str, value: dict[str, Any]) -> None: ...


class InMemoryCacheStore:
    """Process-local cache backend for tests/local runs."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}

    async def get(self, key: str) -> dict[str, Any] | None:
        return self._data.get(key)

    async def put(self, key: str, value: dict[str, Any]) -> None:
        self._data[key] = value


def _ist_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Kolkata"))


class CachedProvider:
    """WeatherProvider decorator implementing read-through + stale-on-failure semantics."""

    def __init__(
        self,
        upstream: WeatherProvider,
        store: CacheStore,
        *,
        ttl_minutes: int = 30,
        clock: Callable[[], datetime] = _ist_now,
    ) -> None:
        self._upstream = upstream
        self._store = store
        self._ttl = timedelta(minutes=ttl_minutes)
        self._clock = clock

    async def fetch(self, point: GeoPoint) -> Forecast:
        key = cache_key(point)
        cached = await self._store.get(key)

        if cached is not None:
            fc = forecast_from_cache(cached)
            if self._clock() - fc.upstream_fetched_at < self._ttl:
                return fc  # fresh enough — serve without hitting upstream

        try:
            fresh = await self._upstream.fetch(point)
        except ProviderError:
            if cached is not None:
                # Upstream down but we have a saved forecast — serve it, honestly flagged.
                stale = forecast_from_cache(cached)
                return replace(stale, reliability=replace(stale.reliability, is_offline_cache=True))
            raise

        await self._store.put(key, forecast_to_cache(fresh))
        return fresh


@dataclass(frozen=True, slots=True)
class DynamoDbCacheStore:
    """DynamoDB-backed cache. boto3 is imported lazily (the Lambda runtime provides it, and
    tests need not install it). Expects a table with partition key ``pk`` and a numeric
    ``ttl`` attribute enabled as the table's TTL for automatic expiry."""

    table_name: str
    ttl_seconds: int = 6 * 3600
    clock: Callable[[], datetime] = _ist_now

    def _table(self) -> Any:
        import boto3

        return boto3.resource("dynamodb").Table(self.table_name)

    async def get(self, key: str) -> dict[str, Any] | None:
        import json

        resp = self._table().get_item(Key={"pk": key})
        item = resp.get("Item")
        if item is None:
            return None
        payload = item.get("payload")
        return json.loads(payload) if isinstance(payload, str) else None

    async def put(self, key: str, value: dict[str, Any]) -> None:
        import json

        expires = int(self.clock().timestamp()) + self.ttl_seconds
        self._table().put_item(Item={"pk": key, "payload": json.dumps(value), "ttl": expires})
