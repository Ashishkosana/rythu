"""Pre-warm: keep every active cell's forecast fresh in the cache, so farmers almost never wait on
Open-Meteo (the < 3 s on 3G target) and upstream calls scale with cells, not with farmers.

Runs on a timer (every 20 minutes, ``function_app.py``). Each run:
1. forgets cells nobody used for ``ACTIVE_WINDOW`` (14 days),
2. takes the most recently used cells, at most ``max_cells`` (the quota guard — see settings),
3. refreshes each one whose cached copy is older than ``refresh_after`` (15 min), a few at a time.

It calls the RAW upstream, not the budgeted one: its spend is bounded by ``max_cells`` instead, and it
must not starve on-demand misses of their budget. One failing cell never stops the run.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from rythu_weather.adapters.cache import CacheStore, cell_from_key
from rythu_weather.adapters.cells import ACTIVE_WINDOW, CellRegistry
from rythu_weather.adapters.serde import forecast_from_cache, forecast_to_cache
from rythu_weather.domain.models import WeatherProvider
from rythu_weather.observability import log_event

_log = logging.getLogger(__name__)

REFRESH_AFTER = timedelta(minutes=15)  # with a 20-minute schedule, a served copy is ≤ ~20 min old
CONCURRENCY = 4  # polite to Open-Meteo, and plenty for tens of cells


@dataclass(frozen=True, slots=True)
class PrewarmReport:
    active: int
    refreshed: int
    already_fresh: int
    failed: int
    pruned: int
    over_cap: int


async def prewarm(
    registry: CellRegistry,
    store: CacheStore,
    upstream: WeatherProvider,
    *,
    now: datetime,
    max_cells: int,
    refresh_after: timedelta = REFRESH_AFTER,
) -> PrewarmReport:
    since = now - ACTIVE_WINDOW
    pruned = await registry.prune(since)
    cells = await registry.active(since)
    over_cap = max(0, len(cells) - max_cells)
    cells = cells[:max_cells]
    gate = asyncio.Semaphore(CONCURRENCY)

    async def one(cell: str) -> str:
        async with gate:
            if await _is_fresh(store, cell, now, refresh_after):
                return "fresh"
            try:
                forecast = await upstream.fetch(cell_from_key(cell))
                await store.put(cell, forecast_to_cache(forecast))
            except Exception:
                _log.warning("prewarm.cell_failed", exc_info=True, extra={"fields": {"cell": cell}})
                return "failed"
            return "refreshed"

    outcomes = await asyncio.gather(*(one(c) for c in cells))
    report = PrewarmReport(
        active=len(cells),
        refreshed=outcomes.count("refreshed"),
        already_fresh=outcomes.count("fresh"),
        failed=outcomes.count("failed"),
        pruned=pruned,
        over_cap=over_cap,
    )
    level = logging.WARNING if report.failed or report.over_cap else logging.INFO
    log_event(_log, level, "prewarm.run", **{k: getattr(report, k) for k in report.__slots__})
    return report


async def _is_fresh(store: CacheStore, cell: str, now: datetime, refresh_after: timedelta) -> bool:
    try:
        item = await store.get(cell)
        if item is None:
            return False
        return now - forecast_from_cache(item).upstream_fetched_at < refresh_after
    except Exception:
        return False  # unreadable or malformed → refresh it
