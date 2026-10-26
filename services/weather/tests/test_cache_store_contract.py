"""One behavioural contract, run against EVERY CacheStore implementation.

The in-memory store always runs. The Azure Table store runs against Azurite (Microsoft's local
Storage emulator); it is skipped when Azurite isn't running locally, but CI sets
RYTHU_REQUIRE_AZURITE=1 so a missing emulator fails the build instead of silently skipping.

    npx azurite@3.37.0 azurite-table --inMemoryPersistence --tableHost 127.0.0.1 --tablePort 10002
"""

from __future__ import annotations

import os
import socket
import uuid
from datetime import timedelta

import pytest

from builders import at, days_from, forecast, hour
from rythu_weather.adapters.cache import CachedProvider, InMemoryCacheStore, cache_key
from rythu_weather.adapters.serde import forecast_from_cache, forecast_to_cache
from rythu_weather.domain.models import Forecast, GeoPoint

# Azurite's documented, public development account — not a secret.
AZURITE = (
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
)


def _azurite_running() -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", 10002)) == 0


def azure_store_or_skip(table: str | None = None):
    if not _azurite_running():
        if os.environ.get("RYTHU_REQUIRE_AZURITE") == "1":
            pytest.fail("RYTHU_REQUIRE_AZURITE=1 but Azurite is not reachable on 127.0.0.1:10002")
        pytest.skip("Azurite not running (see module docstring)")
    from rythu_weather.adapters.azure_table import AzureTableCacheStore

    # A fresh table per test: isolation without cleanup ordering problems.
    return AzureTableCacheStore(AZURITE, table or f"t{uuid.uuid4().hex[:24]}")


@pytest.fixture(params=["in_memory", "azure_table"])
def store(request):
    return InMemoryCacheStore() if request.param == "in_memory" else azure_store_or_skip()


def _value(days: int = 7, start=None) -> dict:
    start = start or at(2026, 7, 15)
    fc = forecast(
        start,
        hourly=[hour(start + timedelta(hours=h), pp=None if h % 5 == 0 else 40, precip=1.25, wind=None)
                for h in range(24 * days)],
        daily=days_from(start.date(), days, pp_max=70, precip_sum=12.5),
    )
    return forecast_to_cache(fc)


async def test_missing_key_is_none(store):
    assert await store.get("18.4,79.9") is None


async def test_put_then_get_round_trips_exactly(store):
    value = _value()
    await store.put("18.4,79.9", value)
    got = await store.get("18.4,79.9")
    assert got == value
    assert isinstance(forecast_from_cache(got), Forecast)  # still a valid forecast, None values intact


async def test_put_replaces_the_previous_value(store):
    await store.put("18.4,79.9", _value(start=at(2026, 7, 15)))
    newer = _value(start=at(2026, 7, 16))
    await store.put("18.4,79.9", newer)
    assert await store.get("18.4,79.9") == newer


async def test_cells_are_isolated(store):
    a, b = cache_key(GeoPoint(18.44, 79.86)), cache_key(GeoPoint(17.38, 78.48))
    await store.put(a, _value(start=at(2026, 7, 15)))
    await store.put(b, _value(start=at(2026, 7, 16)))
    assert (await store.get(a))["generated_at"] != (await store.get(b))["generated_at"]


async def test_a_sixteen_day_forecast_fits(store):
    """Uncompressed this exceeds Table Storage's 64 KiB property limit; the adapter must cope."""
    value = _value(days=16)
    await store.put("18.4,79.9", value)
    assert await store.get("18.4,79.9") == value


async def test_cached_provider_reads_through_the_store(store):
    now = at(2026, 7, 15, 12)
    calls = 0

    class Upstream:
        async def fetch(self, point):
            nonlocal calls
            calls += 1
            return forecast(now, hourly=[hour(now)], daily=days_from(now.date(), 1), fetched_at=now)

    provider = CachedProvider(Upstream(), store, clock=lambda: now)
    await provider.fetch(GeoPoint(18.44, 79.86))  # miss → upstream → put
    hit = await provider.fetch(GeoPoint(18.4489, 79.8571))  # same cell → served from the store
    assert calls == 1
    assert hit.upstream_fetched_at == now


# --- S7: the cell registry and upstream budget share one contract across implementations ----------


@pytest.fixture(params=["in_memory", "azure_table"])
def registry(request):
    from rythu_weather.adapters.cells import InMemoryCellRegistry

    if request.param == "in_memory":
        return InMemoryCellRegistry()
    from rythu_weather.adapters.azure_table import AzureTableCellRegistry, TableAuth

    store = azure_store_or_skip()
    return AzureTableCellRegistry(TableAuth(connection_string=AZURITE), store.table_name)


@pytest.fixture(params=["in_memory", "azure_table"])
def budget(request):
    from rythu_weather.adapters.budget import InMemoryUpstreamBudget

    if request.param == "in_memory":
        return InMemoryUpstreamBudget()
    from rythu_weather.adapters.azure_table import AzureTableUpstreamBudget, TableAuth

    store = azure_store_or_skip()
    return AzureTableUpstreamBudget(TableAuth(connection_string=AZURITE), store.table_name)


async def test_registry_tracks_last_seen_orders_recent_first_and_prunes(registry):
    t0 = at(2026, 10, 1, 9)
    assert await registry.active(t0) == []  # empty (Azure: table not created yet)
    await registry.touch("18.4,79.9", t0)
    await registry.touch("17.4,78.5", t0 + timedelta(hours=2))
    await registry.touch("16.5,80.6", t0 - timedelta(days=30))
    await registry.touch("18.4,79.9", t0 + timedelta(hours=3))  # seen again, later
    assert await registry.active(t0 - timedelta(days=1)) == ["18.4,79.9", "17.4,78.5"]
    assert await registry.prune(t0 - timedelta(days=14)) == 1
    assert "16.5,80.6" not in await registry.active(t0 - timedelta(days=60))


async def test_budget_counts_per_window(budget):
    assert [await budget.try_acquire("2026-10-26T09", 2) for _ in range(3)] == [True, True, False]
    assert await budget.try_acquire("2026-10-26T10", 2) is True  # a fresh hour


async def test_budget_is_exact_under_concurrency(budget):
    """Many instances spending at once must never overspend (Azure: ETag optimistic concurrency)."""
    import asyncio

    results = await asyncio.gather(*(budget.try_acquire("2026-10-26T11", 10) for _ in range(25)),
                                   return_exceptions=True)
    granted = [r for r in results if r is True]
    assert len(granted) <= 10  # never more than the limit
    assert all(r is True or r is False or type(r).__name__ == "BudgetContention" for r in results)
    assert await budget.try_acquire("2026-10-26T11", 10) is (len(granted) < 10)


async def test_a_burst_never_spends_more_than_the_budget(budget):
    """End to end through BudgetedProvider: 25 simultaneous misses, budget 10 → ≤ 10 upstream calls."""
    import asyncio

    from rythu_weather.adapters.budget import BudgetedProvider, BudgetExhausted

    calls = 0

    class Upstream:
        async def fetch(self, point):
            nonlocal calls
            calls += 1
            return forecast(at(2026, 10, 26, 9))

    provider = BudgetedProvider(Upstream(), budget, per_hour=10, clock=lambda: at(2026, 10, 26, 12))
    results = await asyncio.gather(*(provider.fetch(GeoPoint(18.44, 79.86)) for _ in range(25)),
                                   return_exceptions=True)
    assert all(isinstance(r, Forecast | BudgetExhausted) for r in results)
    assert 0 < calls <= 10
