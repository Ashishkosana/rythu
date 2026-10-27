"""Village search: OpenStreetMap Nominatim first (best coverage of small Indian villages), Open-Meteo's
geocoder as fallback. Results are restricted to Rythu's coverage (Telangana + border).

Nominatim's usage policy (operations.osmfoundation.org/policies/nominatim) asks for: an identifying
User-Agent, at most 1 request/second, caching of results, and NO autocomplete-as-you-type. So the app
searches on submit, and ``CachedGeocoder`` caches per normalised query for a day and serialises upstream
calls ≥ 1 s apart (per process — ample at pilot scale).

Telugu-first: ``namedetails=1`` returns the place's ``name:te`` when OpenStreetMap has it.
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from rythu_weather.domain.coverage import COVERAGE_LAT, COVERAGE_LON, in_coverage
from rythu_weather.observability import log_event

_log = logging.getLogger(__name__)

NOMINATIM = "https://nominatim.openstreetmap.org/search"
OPEN_METEO_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
USER_AGENT = "Rythu/1.0 (free farmer weather app; https://github.com/Ashishkosana/rythu)"
MAX_RESULTS = 8


@dataclass(frozen=True, slots=True)
class Place:
    id: int
    name: str
    lat: float
    lon: float
    admin2: str | None = None  # district
    admin1: str | None = None  # state
    name_te: str | None = None  # Telugu name, when OpenStreetMap has one


def _round(x: float) -> float:
    """4 decimals (~11 m): ample for a village pin, and no false precision."""
    return round(x, 4)


def _num(v: Any) -> float | None:
    """A finite float, or None. (Range is checked by the coverage filter.)"""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _text(d: dict[str, Any], key: str) -> str | None:
    v = d.get(key)
    return v if isinstance(v, str) and v.strip() else None


def _dict(d: dict[str, Any], key: str) -> dict[str, Any]:
    v = d.get(key)
    return v if isinstance(v, dict) else {}


def normalize_nominatim(payload: Any) -> list[Place]:
    """Nominatim jsonv2 + addressdetails + namedetails → places inside coverage."""
    if not isinstance(payload, list):
        return []
    out: list[Place] = []
    for i, raw in enumerate(payload):
        if not isinstance(raw, dict):
            continue
        lat, lon = _num(raw.get("lat")), _num(raw.get("lon"))
        if lat is None or lon is None or not in_coverage(lat, lon):
            continue
        addr, names = _dict(raw, "address"), _dict(raw, "namedetails")
        display = _text(raw, "display_name")
        name = (
            _text(addr, "village") or _text(addr, "hamlet") or _text(addr, "town") or _text(addr, "city")
            or _text(raw, "name") or (display.split(",")[0].strip() if display else None)
        )
        if not name:
            continue
        place_id = raw.get("place_id")
        out.append(Place(
            id=place_id if isinstance(place_id, int) else i,
            name=name,
            lat=_round(lat),
            lon=_round(lon),
            admin2=_text(addr, "state_district") or _text(addr, "county"),
            admin1=_text(addr, "state"),
            name_te=_text(names, "name:te"),
        ))
    return out


def normalize_open_meteo(payload: Any) -> list[Place]:
    """Open-Meteo geocoding JSON → places inside coverage."""
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return []
    out: list[Place] = []
    for i, raw in enumerate(results):
        if not isinstance(raw, dict):
            continue
        lat, lon = raw.get("latitude"), raw.get("longitude")
        name = _text(raw, "name")
        if not (isinstance(lat, int | float) and isinstance(lon, int | float)) or not name:
            continue
        if not in_coverage(float(lat), float(lon)):
            continue
        rid = raw.get("id")
        out.append(Place(
            id=rid if isinstance(rid, int) else i, name=name, lat=_round(float(lat)), lon=_round(float(lon)),
            admin2=_text(raw, "admin2"), admin1=_text(raw, "admin1"),
        ))
    return out


class GeocodeUnavailable(RuntimeError):
    """No source could be asked (all failed, or too busy). Not the same as "nothing found"."""


class Geocoder(Protocol):
    async def search(self, query: str) -> list[Place]: ...


class NominatimGeocoder:
    def __init__(self, *, timeout: float = 3.0) -> None:
        self._timeout = timeout

    async def search(self, query: str) -> list[Place]:
        # viewbox = lon,lat of two corners; bounded=1 spends the result slots on Telangana.
        viewbox = f"{COVERAGE_LON[0]},{COVERAGE_LAT[1]},{COVERAGE_LON[1]},{COVERAGE_LAT[0]}"
        params: dict[str, str | int] = {
            "q": query, "format": "jsonv2", "countrycodes": "in", "limit": MAX_RESULTS,
            "addressdetails": 1, "namedetails": 1, "viewbox": viewbox, "bounded": 1,
        }
        async with httpx.AsyncClient(timeout=self._timeout, headers={"User-Agent": USER_AGENT}) as client:
            resp = await client.get(NOMINATIM, params=params)
            resp.raise_for_status()
            return normalize_nominatim(resp.json())


class OpenMeteoGeocoder:
    def __init__(self, *, timeout: float = 3.0) -> None:
        self._timeout = timeout

    async def search(self, query: str) -> list[Place]:
        params: dict[str, str | int] = {"name": query, "count": MAX_RESULTS, "country": "IN", "language": "en"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(OPEN_METEO_GEOCODE, params=params)
            resp.raise_for_status()
            return normalize_open_meteo(resp.json())


class FallbackGeocoder:
    """Primary first; the fallback only when the primary fails or finds nothing.

    Raises :class:`GeocodeUnavailable` only when every source failed — an empty list means a source
    really answered "nothing here".
    """

    def __init__(self, primary: Geocoder, fallback: Geocoder) -> None:
        self._primary = primary
        self._fallback = fallback

    async def search(self, query: str) -> list[Place]:
        answered = False
        for source, geocoder in (("nominatim", self._primary), ("open_meteo", self._fallback)):
            try:
                places = await geocoder.search(query)
            except Exception as exc:
                log_event(_log, logging.WARNING, "geocode.upstream_failed", source=source, error=repr(exc))
                continue
            if places:
                return places
            answered = True
        if not answered:
            raise GeocodeUnavailable("every geocoding source failed")
        return []


class CachedGeocoder:
    """Per-process cache (a day, LRU) + polite pacing (upstream calls ≥ ``min_interval`` apart).

    Only real hits are cached, so an empty answer (or an upstream blip) is retried next time.
    A request that would queue longer than ``max_wait`` for its turn is refused
    (:class:`GeocodeUnavailable`) instead of piling up behind others.
    """

    def __init__(
        self, inner: Geocoder, *, ttl_s: float = 86_400, max_entries: int = 500,
        min_interval_s: float = 1.0, max_wait_s: float = 3.0,
    ) -> None:
        self._inner = inner
        self._ttl = ttl_s
        self._max = max_entries
        self._interval = min_interval_s
        self._max_wait = max_wait_s
        self._cache: OrderedDict[str, tuple[float, list[Place]]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._last_call = 0.0

    @staticmethod
    def key(query: str) -> str:
        return " ".join(query.casefold().split())

    async def search(self, query: str) -> list[Place]:
        k = self.key(query)
        hit = self._cache.get(k)
        if hit is not None and time.monotonic() - hit[0] < self._ttl:
            self._cache.move_to_end(k)
            return hit[1]
        try:
            await asyncio.wait_for(self._lock.acquire(), timeout=self._max_wait)
        except TimeoutError:
            log_event(_log, logging.WARNING, "geocode.busy")
            raise GeocodeUnavailable("too many searches queued") from None
        try:
            wait = self._interval - (time.monotonic() - self._last_call)
            if wait > 0:
                await asyncio.sleep(wait)
            places = await self._inner.search(query)
        finally:
            self._last_call = time.monotonic()  # a failed call still counts toward the pacing
            self._lock.release()
        if places:
            self._cache[k] = (time.monotonic(), places)
            self._cache.move_to_end(k)
            while len(self._cache) > self._max:
                self._cache.popitem(last=False)
        return places
