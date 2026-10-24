"""A read-through cache in front of a WeatherProvider — the "mandatory proxy cache".

Two jobs:
1. Cut Open-Meteo calls (its free tier is ~10k/day) — serve a cached forecast while it is fresh.
2. Honest offline resilience — if upstream fails and we hold a (stale) cached forecast, serve
   it flagged ``is_offline_cache=True`` so the client shows "Offline — showing saved forecast".

The cache stores the RAW provider forecast (pre rule-engine), so one entry serves all crops.
Storage is behind a small ``CacheStore`` port: an in-memory fake for tests, DynamoDB in prod.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from rythu_weather.adapters.serde import forecast_from_cache, forecast_to_cache
from rythu_weather.domain.models import Forecast, GeoPoint, ProviderError, WeatherProvider
from rythu_weather.observability import log_event

_log = logging.getLogger(__name__)


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
        cached = await self._safe_get(key)  # Forecast | None; a broken cache is just a miss

        if cached is not None:
            age = self._clock() - cached.upstream_fetched_at
            if age < self._ttl:
                self._result(key, "hit", age)
                return cached  # fresh enough — serve without hitting upstream

        try:
            fresh = await self._upstream.fetch(point)
        except ProviderError:
            if cached is not None:
                # Upstream down but we have a saved forecast — serve it, honestly flagged.
                self._result(key, "stale_served", self._clock() - cached.upstream_fetched_at)
                return replace(cached, reliability=replace(cached.reliability, is_offline_cache=True))
            self._result(key, "miss_upstream_failed", None)
            raise

        self._result(key, "miss" if cached is None else "refreshed", None)
        await self._safe_put(key, fresh)
        return fresh

    @staticmethod
    def _result(key: str, result: str, age: timedelta | None) -> None:
        age_s = None if age is None else round(age.total_seconds())
        log_event(_log, logging.INFO, "cache.result", key=key, result=result, age_s=age_s)

    async def _safe_get(self, key: str) -> Forecast | None:
        """Read + deserialize the cache. ANY failure (DynamoDB throttle/error, or a
        malformed/legacy item) is treated as a cache miss — never a 500 — but is logged,
        so a silently broken cache shows up as a stream of warnings, not just higher cost."""
        try:
            item = await self._store.get(key)
        except Exception:
            _log.warning("cache.read_failed", exc_info=True, extra={"fields": {"key": key}})
            return None
        if item is None:
            return None
        try:
            return forecast_from_cache(item)
        except (KeyError, IndexError, TypeError, ValueError):
            _log.warning("cache.item_malformed", exc_info=True, extra={"fields": {"key": key}})
            return None

    async def _safe_put(self, key: str, fresh: Forecast) -> None:
        """Best-effort write — a cache write failure must not fail the request."""
        try:
            await self._store.put(key, forecast_to_cache(fresh))
        except Exception:
            _log.warning("cache.write_failed", exc_info=True, extra={"fields": {"key": key}})


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
        from botocore.config import Config

        # botocore defaults are 60 s connect/read with up to 10 legacy-mode retries for DynamoDB —
        # far beyond the Lambda's 15 s budget. The cache is an optimisation, so fail fast and let
        # the request fall through to upstream (reads) or carry on (writes). Worst case per call:
        # 2 attempts x (1 s + 1 s) = 4 s; get + Open-Meteo (4 s) + put = 12 s < 15 s Lambda timeout.
        config = Config(connect_timeout=1, read_timeout=1, retries={"max_attempts": 2, "mode": "standard"})
        return boto3.resource("dynamodb", config=config).Table(self.table_name)

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
