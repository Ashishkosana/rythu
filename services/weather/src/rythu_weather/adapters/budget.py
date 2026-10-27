"""Global upstream budget: a hard cap on on-demand Open-Meteo calls per hour, shared by all instances.

The binding constraint at Rythu's scale is not CPU but the shared upstream quota (Open-Meteo's free
tier is ~10,000 calls/day). Pre-warming keeps cells served from cache; this caps what cache misses can
spend, so neither a traffic spike nor someone scripting coordinates can exhaust the quota for every
farmer (a bulkhead, in Nygard's *Release It!* terms).

``BudgetedProvider`` sits between the cache and upstream. When the hour's budget is spent it raises
``ProviderError``, and ``CachedProvider`` does what it does for any upstream failure: serve the saved
copy (≤ 6 h, flagged) or answer an honest degraded 200.

The window is a fixed clock hour, keyed ``YYYY-MM-DDTHH`` in IST: simple, and good enough — the worst
case at an hour boundary is 2× the budget in a short burst, still far inside the daily quota.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Protocol
from zoneinfo import ZoneInfo

from rythu_weather.domain.models import Forecast, GeoPoint, ProviderError, WeatherProvider
from rythu_weather.observability import log_event

_log = logging.getLogger(__name__)


def _ist_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Kolkata"))


def window_key(now: datetime) -> str:
    return now.strftime("%Y-%m-%dT%H")


class UpstreamBudget(Protocol):
    async def try_acquire(self, window: str, limit: int) -> bool:
        """Spend one call from ``window`` if fewer than ``limit`` were spent; report whether it was."""
        ...


class InMemoryUpstreamBudget:
    def __init__(self) -> None:
        self._spent: dict[str, int] = {}

    async def try_acquire(self, window: str, limit: int) -> bool:
        if self._spent.get(window, 0) >= limit:
            return False
        self._spent[window] = self._spent.get(window, 0) + 1
        return True


class BudgetExhausted(ProviderError):
    """The hour's upstream budget is spent; treated by callers like any upstream failure."""


class BudgetContention(RuntimeError):
    """Too many concurrent writers on one budget window. That is heavy demand — exactly when the cap
    matters — so BudgetedProvider treats it as a refusal, not as a storage failure to fail open on."""


class BudgetedProvider:
    """WeatherProvider decorator that spends one budget unit per upstream call."""

    def __init__(
        self,
        upstream: WeatherProvider,
        budget: UpstreamBudget,
        *,
        per_hour: int,
        clock: Callable[[], datetime] = _ist_now,
    ) -> None:
        self._upstream = upstream
        self._budget = budget
        self._per_hour = per_hour
        self._clock = clock

    async def fetch(self, point: GeoPoint) -> Forecast:
        window = window_key(self._clock())
        try:
            allowed = await self._budget.try_acquire(window, self._per_hour)
        except BudgetContention as exc:
            # Too many concurrent spenders = a burst: refuse (measured: failing open here let 15–18 of
            # 25 simultaneous misses through a budget of 10).
            log_event(_log, logging.WARNING, "budget.contention", window=window)
            raise BudgetExhausted(f"upstream budget contended for {window}") from exc
        except Exception:
            # Fail OPEN: the budget guards against abuse; a storage hiccup must not take weather away
            # from every farmer. Logged so a persistently broken budget is visible.
            _log.warning("budget.check_failed", exc_info=True, extra={"fields": {"window": window}})
            allowed = True
        if not allowed:
            log_event(_log, logging.WARNING, "budget.exhausted", window=window, per_hour=self._per_hour)
            raise BudgetExhausted(f"upstream budget of {self._per_hour}/hour exhausted for {window}")
        return await self._upstream.fetch(point)
