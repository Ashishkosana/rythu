from __future__ import annotations

import json
import logging
import sys
import types
from datetime import timedelta

import pytest

from builders import at, day, forecast, hour
from rythu_weather.adapters.cache import CachedProvider, DynamoDbCacheStore, InMemoryCacheStore, cache_key
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


# --- observability (S1) --------------------------------------------------------------------


def _results(caplog):
    return [(r.fields["result"], r.fields["age_s"]) for r in caplog.records if r.getMessage() == "cache.result"]


async def test_every_lookup_logs_its_result(caplog):
    caplog.set_level(logging.INFO, logger="rythu_weather")
    now = at(2026, 7, 15, 12)
    store = InMemoryCacheStore()
    upstream = CountingProvider(_sample(now))
    await CachedProvider(upstream, store, clock=lambda: now).fetch(POINT)  # empty → miss
    await CachedProvider(upstream, store, clock=lambda: now + timedelta(minutes=10)).fetch(POINT)  # hit
    await CachedProvider(upstream, store, clock=lambda: now + timedelta(hours=1)).fetch(POINT)  # stale → refresh
    later = now + timedelta(hours=3)
    await CachedProvider(FailingProvider(), store, clock=lambda: later).fetch(POINT)  # upstream down → stale served
    with pytest.raises(ProviderError):
        await CachedProvider(FailingProvider(), InMemoryCacheStore(), clock=lambda: now).fetch(POINT)

    assert _results(caplog) == [
        ("miss", None),
        ("hit", 600),
        ("refreshed", None),
        ("stale_served", 3 * 3600),  # refreshed copy was fetched at `now` (the sample's fixed fetch time)
        ("miss_upstream_failed", None),
    ]


async def test_store_failures_are_logged_not_swallowed(caplog):
    caplog.set_level(logging.INFO, logger="rythu_weather")
    now = at(2026, 7, 15, 12)
    upstream = CountingProvider(_sample(now))
    await CachedProvider(upstream, BrokenStore(fail_get=True, fail_put=True), clock=lambda: now).fetch(POINT)
    warnings = {r.getMessage(): r for r in caplog.records if r.levelno == logging.WARNING}
    assert set(warnings) == {"cache.read_failed", "cache.write_failed"}
    assert warnings["cache.read_failed"].fields == {"key": cache_key(POINT)}
    assert warnings["cache.read_failed"].exc_info is not None  # traceback kept for diagnosis


async def test_malformed_item_is_logged(caplog):
    caplog.set_level(logging.INFO, logger="rythu_weather")
    store = InMemoryCacheStore()
    await store.put(cache_key(POINT), {"garbage": True})
    now = at(2026, 7, 15, 12)
    await CachedProvider(CountingProvider(_sample(now)), store, clock=lambda: now).fetch(POINT)
    assert any(r.getMessage() == "cache.item_malformed" for r in caplog.records)


def test_dynamodb_client_fails_fast(monkeypatch):
    """botocore defaults (60 s timeouts, many retries) would exceed the Lambda's 15 s budget."""
    captured = {}

    class Config:
        def __init__(self, **kw):
            captured.update(kw)

    class Resource:
        def Table(self, name):
            return ("table", name)

    def resource(service, config=None):
        captured["service"] = service
        captured["config"] = config
        return Resource()

    botocore = types.ModuleType("botocore")
    botocore_config = types.ModuleType("botocore.config")
    botocore_config.Config = Config
    boto3 = types.ModuleType("boto3")
    boto3.resource = resource
    monkeypatch.setitem(sys.modules, "boto3", boto3)
    monkeypatch.setitem(sys.modules, "botocore", botocore)
    monkeypatch.setitem(sys.modules, "botocore.config", botocore_config)

    assert DynamoDbCacheStore("rythu-cache")._table() == ("table", "rythu-cache")
    assert captured["service"] == "dynamodb"
    assert isinstance(captured["config"], Config)
    assert captured["retries"] == {"max_attempts": 2, "mode": "standard"}
    # Worst case get + put must leave room for the 4 s Open-Meteo deadline inside the 15 s Lambda timeout.
    per_call_s = captured["retries"]["max_attempts"] * (captured["connect_timeout"] + captured["read_timeout"])
    assert 2 * per_call_s + 4 < 15


# --- S2c: a saved forecast older than 6 h is never served -------------------------------------


async def _offline_fetch(age: timedelta):
    """Upstream down; the store holds a copy fetched `age` ago."""
    fetched = at(2026, 10, 22, 20)
    store = InMemoryCacheStore()
    await store.put(cache_key(POINT), forecast_to_cache(_sample(fetched)))
    return await CachedProvider(FailingProvider(), store, clock=lambda: fetched + age).fetch(POINT)


async def test_offline_copy_under_six_hours_is_served_flagged():
    fc = await _offline_fetch(timedelta(hours=5, minutes=59))
    assert fc.reliability.is_offline_cache is True


@pytest.mark.parametrize("age", [timedelta(hours=6), timedelta(days=2)])
async def test_offline_copy_six_hours_or_older_is_not_served(age):
    """DynamoDB TTL deletes lazily (up to ~48 h late), so expiry is enforced in code."""
    with pytest.raises(ProviderError):
        await _offline_fetch(age)


async def test_expired_copy_is_replaced_when_upstream_is_up(caplog):
    caplog.set_level(logging.INFO, logger="rythu_weather")
    fetched = at(2026, 10, 22, 20)
    store = InMemoryCacheStore()
    await store.put(cache_key(POINT), forecast_to_cache(_sample(fetched)))
    now = fetched + timedelta(days=2)
    upstream = CountingProvider(_sample(now))
    fc = await CachedProvider(upstream, store, clock=lambda: now).fetch(POINT)
    assert upstream.calls == 1 and fc.upstream_fetched_at == now
    [expired] = [r for r in caplog.records if r.getMessage() == "cache.expired"]
    assert expired.fields["age_s"] == 2 * 86400
