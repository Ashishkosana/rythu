from __future__ import annotations

import json
from datetime import timedelta

import pytest

from builders import at, day, forecast, hour
from rythu_weather.adapters.cache import CachedProvider, InMemoryCacheStore, cache_key
from rythu_weather.adapters.fake import FailingProvider
from rythu_weather.adapters.serde import forecast_from_cache, forecast_to_cache
from rythu_weather.domain.models import Forecast, GeoPoint, ProviderError

POINT = GeoPoint(18.44, 79.86)


class CountingProvider:
    def __init__(self, fc: Forecast) -> None:
        self.fc = fc
        self.calls = 0

    async def fetch(self, point: GeoPoint) -> Forecast:
        self.calls += 1
        return self.fc


def _sample(now):
    return forecast(
        now,
        hourly=[hour(now, pp=None, precip=0.5, wind=None), hour(now + timedelta(hours=1), pp=60)],
        daily=[day(now.date(), pp_max=None, precip_sum=8.0)],
        fetched_at=now,
    )


def test_serde_round_trip_is_lossless_and_json_safe():
    fc = _sample(at(2026, 7, 15, 12))
    restored = forecast_from_cache(json.loads(json.dumps(forecast_to_cache(fc))))
    assert restored == fc  # includes None values, tz-aware datetimes, coords


def test_cache_key_is_grid_rounded():
    assert cache_key(GeoPoint(18.4412, 79.8629)) == cache_key(GeoPoint(18.44, 79.86))


async def test_fresh_cache_is_served_without_calling_upstream():
    now = at(2026, 7, 15, 12)
    upstream = CountingProvider(_sample(now))
    provider = CachedProvider(upstream, InMemoryCacheStore(), ttl_minutes=30, clock=lambda: now)
    await provider.fetch(POINT)  # miss → fetch + store
    await provider.fetch(POINT)  # fresh hit → no second upstream call
    assert upstream.calls == 1


async def test_stale_cache_triggers_refetch():
    now = at(2026, 7, 15, 12)
    store = InMemoryCacheStore()
    upstream = CountingProvider(_sample(now))
    CachedProvider(upstream, store, ttl_minutes=30, clock=lambda: now)
    await CachedProvider(upstream, store, ttl_minutes=30, clock=lambda: now).fetch(POINT)  # populate
    later = CachedProvider(upstream, store, ttl_minutes=30, clock=lambda: now + timedelta(hours=1))
    await later.fetch(POINT)  # cache stale → refetch
    assert upstream.calls == 2


async def test_upstream_failure_serves_stale_cache_flagged_offline():
    now = at(2026, 7, 15, 12)
    store = InMemoryCacheStore()
    await store.put(cache_key(POINT), forecast_to_cache(_sample(now)))
    provider = CachedProvider(FailingProvider(), store, ttl_minutes=30, clock=lambda: now + timedelta(hours=2))
    fc = await provider.fetch(POINT)
    assert fc.reliability.is_offline_cache is True


async def test_upstream_failure_without_cache_raises():
    now = at(2026, 7, 15, 12)
    provider = CachedProvider(FailingProvider(), InMemoryCacheStore(), clock=lambda: now)
    with pytest.raises(ProviderError):
        await provider.fetch(POINT)


class BrokenStore:
    """Simulates a DynamoDB store whose reads/writes raise (throttle, AccessDenied, …)."""

    def __init__(self, *, fail_get: bool = False, fail_put: bool = False) -> None:
        self.fail_get = fail_get
        self.fail_put = fail_put

    async def get(self, key):
        if self.fail_get:
            raise RuntimeError("dynamo throttled")
        return None

    async def put(self, key, value):
        if self.fail_put:
            raise RuntimeError("dynamo write throttled")


async def test_store_read_failure_falls_through_to_upstream():
    now = at(2026, 7, 15, 12)
    upstream = CountingProvider(_sample(now))
    provider = CachedProvider(upstream, BrokenStore(fail_get=True), clock=lambda: now)
    fc = await provider.fetch(POINT)  # get() raises → miss → upstream, no crash
    assert upstream.calls == 1
    assert fc.reliability.is_offline_cache is False


async def test_store_write_failure_still_returns_fresh_forecast():
    now = at(2026, 7, 15, 12)
    upstream = CountingProvider(_sample(now))
    provider = CachedProvider(upstream, BrokenStore(fail_put=True), clock=lambda: now)
    fc = await provider.fetch(POINT)  # put() raises but the forecast is already fetched
    assert fc == _sample(now)


async def test_malformed_cache_item_is_treated_as_miss():
    now = at(2026, 7, 15, 12)
    store = InMemoryCacheStore()
    await store.put(cache_key(POINT), {"garbage": True})  # not a valid forecast blob
    upstream = CountingProvider(_sample(now))
    provider = CachedProvider(upstream, store, clock=lambda: now)
    fc = await provider.fetch(POINT)  # deserialize fails → miss → upstream
    assert upstream.calls == 1
    assert fc == _sample(now)
