"""S7: cell registry, upstream budget, pre-warm — behaviour, wiring and quota arithmetic."""

from __future__ import annotations

import logging
from datetime import timedelta

import pytest

from builders import at, days_from, forecast, hour
from rythu_weather.adapters.budget import BudgetedProvider, BudgetExhausted, InMemoryUpstreamBudget, window_key
from rythu_weather.adapters.cache import CachedProvider, InMemoryCacheStore, cache_key, cell_from_key
from rythu_weather.adapters.cells import InMemoryCellRegistry, RegisteringProvider
from rythu_weather.adapters.fake import FailingProvider
from rythu_weather.adapters.serde import forecast_to_cache
from rythu_weather.app.composition import build_services
from rythu_weather.app.prewarm import prewarm
from rythu_weather.app.settings import (
    DEFAULT_PREWARM_MAX_CELLS,
    DEFAULT_UPSTREAM_BUDGET_PER_HOUR,
    Settings,
)
from rythu_weather.app.weather_request import answer_weather
from rythu_weather.domain.models import GeoPoint, ProviderError

NOW = at(2026, 10, 26, 9)


class Counting:
    """Upstream double: counts calls, can fail for chosen cells, stamps fetch time."""

    def __init__(self, now=NOW, fail_cells=()):
        self.calls: list[GeoPoint] = []
        self.now = now
        self.fail_cells = set(fail_cells)

    async def fetch(self, point):
        self.calls.append(point)
        if cache_key(point) in self.fail_cells:
            raise ProviderError("boom")
        return forecast(self.now, hourly=[hour(self.now)], daily=days_from(self.now.date(), 1), fetched_at=self.now)


# --- quota arithmetic -----------------------------------------------------------------------------


def test_default_worst_case_stays_under_80_percent_of_open_meteo_free_tier():
    prewarm_calls = DEFAULT_PREWARM_MAX_CELLS * 3 * 24  # every 20 minutes
    on_demand = DEFAULT_UPSTREAM_BUDGET_PER_HOUR * 24
    assert prewarm_calls + on_demand <= 0.8 * 10_000


def test_settings_bound_the_quota_knobs():
    s = Settings.from_env({"RYTHU_UPSTREAM_BUDGET_PER_HOUR": "50", "RYTHU_PREWARM_MAX_CELLS": "10"})
    assert (s.upstream_budget_per_hour, s.prewarm_max_cells) == (50, 10)
    for env in ({"RYTHU_UPSTREAM_BUDGET_PER_HOUR": "0"}, {"RYTHU_UPSTREAM_BUDGET_PER_HOUR": "401"},
                {"RYTHU_PREWARM_MAX_CELLS": "101"}, {"RYTHU_PREWARM_MAX_CELLS": "lots"}):
        with pytest.raises(ValueError, match=next(iter(env))):
            Settings.from_env(env)


# --- registry ------------------------------------------------------------------------------------


def test_cell_key_round_trips():
    for p in (GeoPoint(18.44, 79.86), GeoPoint(17.0, 80.0), GeoPoint(15.75, 77.12)):
        assert cache_key(cell_from_key(cache_key(p))) == cache_key(p)


async def test_requests_register_their_cell_throttled_per_hour():
    registry = InMemoryCellRegistry()
    clock = [NOW]
    touches = []

    class Spy(InMemoryCellRegistry):
        async def touch(self, cell, seen_at):
            touches.append(cell)
            await registry.touch(cell, seen_at)

    provider = RegisteringProvider(Counting(), Spy(), clock=lambda: clock[0])
    for _ in range(5):
        await provider.fetch(GeoPoint(18.44, 79.86))  # same cell, many requests
    clock[0] = NOW + timedelta(minutes=61)
    await provider.fetch(GeoPoint(18.4489, 79.8571))  # same cell, an hour later
    assert touches == ["18.4,79.9", "18.4,79.9"]
    assert await registry.active(NOW - timedelta(days=1)) == ["18.4,79.9"]


async def test_a_broken_registry_never_fails_the_request(caplog):
    class Broken(InMemoryCellRegistry):
        async def touch(self, cell, seen_at):
            raise RuntimeError("table down")

    caplog.set_level(logging.WARNING, logger="rythu_weather")
    fc = await RegisteringProvider(Counting(), Broken(), clock=lambda: NOW).fetch(GeoPoint(18.44, 79.86))
    assert fc.upstream_fetched_at == NOW
    assert any(r.getMessage() == "cells.touch_failed" for r in caplog.records)


# --- budget --------------------------------------------------------------------------------------


async def test_budget_allows_n_calls_per_hour_then_refuses():
    upstream, clock = Counting(), [NOW]
    provider = BudgetedProvider(upstream, InMemoryUpstreamBudget(), per_hour=3, clock=lambda: clock[0])
    for _ in range(3):
        await provider.fetch(GeoPoint(18.44, 79.86))
    with pytest.raises(BudgetExhausted):
        await provider.fetch(GeoPoint(18.44, 79.86))
    assert len(upstream.calls) == 3
    clock[0] = NOW + timedelta(hours=1)  # a new window
    await provider.fetch(GeoPoint(18.44, 79.86))
    assert len(upstream.calls) == 4


async def test_budget_fails_open_when_its_store_breaks(caplog):
    class Broken(InMemoryUpstreamBudget):
        async def try_acquire(self, window, limit):
            raise RuntimeError("table down")

    caplog.set_level(logging.WARNING, logger="rythu_weather")
    upstream = Counting()
    await BudgetedProvider(upstream, Broken(), per_hour=1, clock=lambda: NOW).fetch(GeoPoint(18.44, 79.86))
    assert len(upstream.calls) == 1
    assert any(r.getMessage() == "budget.check_failed" for r in caplog.records)


async def test_exhausted_budget_serves_the_saved_copy_or_an_honest_degraded_answer():
    budget = InMemoryUpstreamBudget()
    for _ in range(2):
        await budget.try_acquire(window_key(NOW), 2)  # the hour is already spent
    store = InMemoryCacheStore()
    older = NOW - timedelta(hours=2)
    saved_copy = forecast(older, hourly=[hour(older)], daily=days_from(older.date(), 1), fetched_at=older)
    await store.put("18.4,79.9", forecast_to_cache(saved_copy))
    provider = CachedProvider(BudgetedProvider(Counting(), budget, per_hour=2, clock=lambda: NOW), store,
                              clock=lambda: NOW)

    saved = await provider.fetch(GeoPoint(18.44, 79.86))  # cell with a saved copy
    assert saved.reliability.is_offline_cache is True and saved.upstream_fetched_at == older

    resp = await answer_weather({"lat": "17.38", "lon": "78.48"}, provider)  # cell with nothing saved
    assert resp.status == 200 and resp.body["degraded"] is True


# --- pre-warm ------------------------------------------------------------------------------------


async def _registry_with(*cells_and_ages):
    registry = InMemoryCellRegistry()
    for cell, age in cells_and_ages:
        await registry.touch(cell, NOW - age)
    return registry


async def test_prewarm_refreshes_stale_and_missing_cells_and_skips_fresh_ones():
    store = InMemoryCacheStore()
    fresh_at, stale_at = NOW - timedelta(minutes=5), NOW - timedelta(minutes=40)
    await store.put("18.4,79.9", forecast_to_cache(forecast(fresh_at, fetched_at=fresh_at)))
    await store.put("17.4,78.5", forecast_to_cache(forecast(stale_at, fetched_at=stale_at)))
    registry = await _registry_with(("18.4,79.9", timedelta(hours=1)), ("17.4,78.5", timedelta(hours=2)),
                                    ("16.5,80.6", timedelta(days=1)))  # last one never cached
    upstream = Counting()
    report = await prewarm(registry, store, upstream, now=NOW, max_cells=10)
    assert (report.refreshed, report.already_fresh, report.failed) == (2, 1, 0)
    assert sorted(cache_key(p) for p in upstream.calls) == ["16.5,80.6", "17.4,78.5"]
    assert {p.lat for p in upstream.calls} == {16.5, 17.4}  # asked for the cell centre


async def test_prewarm_caps_cells_most_recent_first_and_prunes_forgotten_ones():
    registry = await _registry_with(("18.4,79.9", timedelta(hours=1)), ("17.4,78.5", timedelta(hours=5)),
                                    ("16.5,80.6", timedelta(days=20)))  # unused for 20 days
    upstream = Counting()
    report = await prewarm(registry, InMemoryCacheStore(), upstream, now=NOW, max_cells=1)
    assert [cache_key(p) for p in upstream.calls] == ["18.4,79.9"]  # the most recently used
    assert (report.active, report.over_cap, report.pruned) == (1, 1, 1)
    assert await registry.active(NOW - timedelta(days=30)) == ["18.4,79.9", "17.4,78.5"]


async def test_one_failing_cell_does_not_stop_the_run(caplog):
    caplog.set_level(logging.INFO, logger="rythu_weather")
    registry = await _registry_with(("18.4,79.9", timedelta(hours=1)), ("17.4,78.5", timedelta(hours=2)))
    store = InMemoryCacheStore()
    report = await prewarm(registry, store, Counting(fail_cells={"18.4,79.9"}), now=NOW, max_cells=10)
    assert (report.refreshed, report.failed) == (1, 1)
    assert await store.get("17.4,78.5") is not None
    [run] = [r for r in caplog.records if r.getMessage() == "prewarm.run"]
    assert run.levelno == logging.WARNING and run.fields["failed"] == 1


# --- wiring --------------------------------------------------------------------------------------


def test_azure_wiring_chains_registry_cache_budget_upstream():
    conn = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=eA==;TableEndpoint=http://127.0.0.1:1/x;"
    s = Settings.from_env({"RYTHU_AZURE_TABLES_CONNECTION_STRING": conn})
    services = build_services(s)
    chain, p = [], services.provider
    while p is not None:
        chain.append(type(p).__name__)
        p = getattr(p, "_inner", None) or getattr(p, "_upstream", None)
    assert chain == ["RegisteringProvider", "CachedProvider", "BudgetedProvider", "OpenMeteoHttpProvider"]
    assert services.prewarm is not None
    assert type(services.prewarm.upstream).__name__ == "OpenMeteoHttpProvider"  # pre-warm bypasses the budget


def test_aws_and_bare_wiring_have_no_prewarm():
    assert build_services(Settings(cache_table="dyn")).prewarm is None
    bare = build_services(Settings())
    assert bare.prewarm is None and type(bare.provider).__name__ == "OpenMeteoHttpProvider"


async def test_failing_upstream_with_exhausted_budget_still_never_500s():
    resp = await answer_weather({"crop": "chilli"}, BudgetedProvider(FailingProvider(), InMemoryUpstreamBudget(),
                                                                     per_hour=0, clock=lambda: NOW))
    assert resp.status == 200 and resp.body["degraded"] is True


async def test_contention_is_a_refusal_not_a_fail_open():
    """Measured on Azurite: failing open on contention let 15-18 of 25 simultaneous misses through a
    budget of 10. Contention means a burst, which is exactly when the cap must hold."""
    from rythu_weather.adapters.budget import BudgetContention

    class Contended(InMemoryUpstreamBudget):
        async def try_acquire(self, window, limit):
            raise BudgetContention("too many writers")

    upstream = Counting()
    with pytest.raises(BudgetExhausted):
        await BudgetedProvider(upstream, Contended(), per_hour=10, clock=lambda: NOW).fetch(GeoPoint(18.44, 79.86))
    assert upstream.calls == []


@pytest.mark.parametrize("window", ["devices#2026-10-29T06", "a/b", "a\\b", "a?b", "a\tb", ""])
async def test_budget_windows_must_be_valid_table_row_keys(window):
    """Azure Table Storage answers 400 for these (the Azurite emulator doesn't), so every budget refuses them."""
    with pytest.raises(ValueError, match="row key"):
        await InMemoryUpstreamBudget().try_acquire(window, 1)
