"""Cell registry: which ~11 km cells farmers actually use, so the pre-warm job knows what to refresh.

``RegisteringProvider`` wraps any WeatherProvider and records the request's cell before delegating —
on cache hits too, otherwise a well-cached cell would look unused and drop out of pre-warming.
Writes are throttled per process (one touch per cell per ``touch_every``), so a busy cell costs one
registry write an hour, not one per request. A registry failure never fails the request.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Protocol
from zoneinfo import ZoneInfo

from rythu_weather.adapters.cache import cache_key
from rythu_weather.domain.models import Forecast, GeoPoint, WeatherProvider

_log = logging.getLogger(__name__)

# A cell counts as active (worth pre-warming) if a farmer used it within this window.
ACTIVE_WINDOW = timedelta(days=14)


def _ist_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Kolkata"))


class CellRegistry(Protocol):
    async def touch(self, cell: str, seen_at: datetime) -> None: ...

    async def active(self, since: datetime) -> list[str]:
        """Cells seen at or after ``since``, most recently seen first."""
        ...

    async def prune(self, before: datetime) -> int:
        """Forget cells not seen since ``before``; return how many were removed."""
        ...


class InMemoryCellRegistry:
    def __init__(self) -> None:
        self._seen: dict[str, datetime] = {}

    async def touch(self, cell: str, seen_at: datetime) -> None:
        if cell not in self._seen or seen_at > self._seen[cell]:
            self._seen[cell] = seen_at

    async def active(self, since: datetime) -> list[str]:
        rows = [(t, c) for c, t in self._seen.items() if t >= since]
        return [c for _, c in sorted(rows, reverse=True)]

    async def prune(self, before: datetime) -> int:
        stale = [c for c, t in self._seen.items() if t < before]
        for c in stale:
            del self._seen[c]
        return len(stale)


class RegisteringProvider:
    """WeatherProvider decorator: note the request's cell in the registry, then delegate."""

    def __init__(
        self,
        inner: WeatherProvider,
        registry: CellRegistry,
        *,
        touch_every: timedelta = timedelta(hours=1),
        clock: Callable[[], datetime] = _ist_now,
    ) -> None:
        self._inner = inner
        self._registry = registry
        self._touch_every = touch_every
        self._clock = clock
        self._last_touch: dict[str, datetime] = {}

    async def fetch(self, point: GeoPoint) -> Forecast:
        await self._maybe_touch(cache_key(point))
        return await self._inner.fetch(point)

    async def _maybe_touch(self, cell: str) -> None:
        now = self._clock()
        last = self._last_touch.get(cell)
        if last is not None and now - last < self._touch_every:
            return
        try:
            await self._registry.touch(cell, now)
            self._last_touch[cell] = now
        except Exception:
            _log.warning("cells.touch_failed", exc_info=True, extra={"fields": {"cell": cell}})
