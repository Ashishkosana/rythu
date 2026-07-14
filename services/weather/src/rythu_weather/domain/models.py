"""Pure domain models for the Rythu weather slice.

Everything here is provider-agnostic and side-effect free: no network, no filesystem,
no environment variables, and crucially **no clock** — the current time is always passed in
via ``FarmerContext.now``. That keeps every forward-looking rule ("next 6 hours", "this
morning") deterministic and unit-testable, which matters because this advice goes to real
farmers where a wrong call can cost a crop.

See ``docs/weather-slice-spec.md`` for the verified reasoning behind each field.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Protocol


class FarmAction(StrEnum):
    """The farm operation a rule advises on. Lets the UI group reads by activity."""

    SPRAY = "spray"
    IRRIGATE = "irrigate"
    SOW = "sow"
    HARVEST = "harvest"
    FIELDWORK = "fieldwork"


class Crop(StrEnum):
    """The pilot crop set for Bhupalpally Kharif."""

    COTTON = "cotton"
    PADDY = "paddy"
    RED_GRAM = "red_gram"
    MAIZE = "maize"


class WaterSource(StrEnum):
    """Farmer's water source — the #1 crop-advice input. Scopes rules as data, not code."""

    CANAL_LIFT = "canal_lift"
    TANK = "tank"
    BOREWELL = "borewell"
    RAINFED = "rainfed"


class WMOCategory(StrEnum):
    """Coarse bucket for a WMO ``weather_code`` (icon/colour grouping + storm guard)."""

    CLEAR = "clear"
    CLOUD = "cloud"
    FOG = "fog"
    DRIZZLE = "drizzle"
    RAIN = "rain"
    SHOWERS = "showers"
    THUNDERSTORM = "thunderstorm"


class Severity(StrEnum):
    """UI emphasis for a read — NOT a certainty claim about the weather."""

    INFO = "info"
    CAUTION = "caution"
    ACT = "act"


@dataclass(frozen=True, slots=True)
class WMOCondition:
    """Static lookup value for one WMO code. Pure data — no logic."""

    code: int
    en_short: str
    category: WMOCategory
    emoji: str
    farm_note: str


@dataclass(frozen=True, slots=True)
class GeoPoint:
    """An immutable lat/lon pair (decimal degrees)."""

    lat: float
    lon: float


@dataclass(frozen=True, slots=True)
class CoordsResolution:
    """Honesty object capturing the grid snap: what we asked for vs what the model answered."""

    requested: GeoPoint
    returned: GeoPoint
    elevation_m: float
    snap_distance_km: float


@dataclass(frozen=True, slots=True)
class HourlyPoint:
    """One hourly forecast row in Asia/Kolkata local time.

    Every metric is Optional because Open-Meteo can return ``null``; ``None`` means
    UNKNOWN, never zero.
    """

    time_local: datetime
    precipitation_probability: int | None
    precipitation_mm: float | None
    temperature_c: float | None
    relative_humidity: int | None
    weather_code: int | None
    wind_speed_kmh: float | None


@dataclass(frozen=True, slots=True)
class DailyPoint:
    """One daily (7-day) forecast row in Asia/Kolkata. Optional metrics; ``None`` = unknown."""

    day: date
    precipitation_probability_max: int | None
    precipitation_sum_mm: float | None
    temperature_max_c: float | None
    temperature_min_c: float | None
    weather_code: int | None
    wind_speed_max_kmh: float | None


@dataclass(frozen=True, slots=True)
class ForecastReliability:
    """The honesty framing block that REPLACES any confidence badge.

    In v0 ``show_confidence_rating`` is hard-wired False: the basic deterministic endpoint
    has no spread, so any confidence label would be fabricated. The source/last-updated
    stamp is intentionally NOT stored here (it is time-relative) — it is computed at
    serialisation time from ``now`` and ``Forecast.upstream_fetched_at``.
    """

    source: str = "Open-Meteo"
    resolution_km: int = 11
    show_confidence_rating: bool = False
    model_note: str = "global (~11 km deterministic) — not convective-cell resolving; can miss local monsoon showers"
    disclaimer_en: str = (
        "General-area forecast (~11 km) — it can be wrong. Rain % shows the chance, not a promise; watch the sky too."
    )
    is_offline_cache: bool = False


@dataclass(frozen=True, slots=True)
class FarmingRead:
    """One evaluated farming advisory produced by a rule against a Forecast + FarmerContext.

    Farmer-facing text is honesty-framed and probability-worded. ``rule_confidence`` is
    INTERNAL metadata and is deliberately never serialised as a per-forecast confidence meter.
    """

    id: str
    action: FarmAction
    crop: str
    severity: Severity
    headline_en: str
    caveat_en: str
    detail_en: str = ""
    window_note: str | None = None
    sources: tuple[str, ...] = ()
    rule_confidence: str = "medium"
    triggered: bool = True


@dataclass(frozen=True, slots=True)
class Forecast:
    """Domain aggregate root: an honest, normalised forecast for one point.

    Built pure from provider data (with ``farming_read`` empty); the pure rule engine fills
    ``farming_read`` afterwards via :func:`dataclasses.replace`.
    """

    coords: CoordsResolution
    generated_at: datetime
    upstream_fetched_at: datetime
    hourly: tuple[HourlyPoint, ...]
    daily: tuple[DailyPoint, ...]
    reliability: ForecastReliability = ForecastReliability()
    farming_read: tuple[FarmingRead, ...] = ()
    timezone: str = "Asia/Kolkata"


@dataclass(frozen=True, slots=True)
class FarmerContext:
    """Pure input to the rule engine: the farmer/field profile + the evaluation clock.

    ``now`` is injected (never read from the environment) so the domain stays testable and
    side-effect free. It is a tz-aware Asia/Kolkata datetime that defines every forward
    "next 6h / next 3d / this morning" window.
    """

    now: datetime
    water_source: WaterSource
    crop: Crop | None = None


@dataclass(frozen=True, slots=True)
class Fired:
    """What a rule's predicate returns when it fires: the dynamic, per-forecast text.

    Static text (caveat, sources, severity, confidence) lives on :class:`RuleSpec`; only the
    numbers-in-the-headline part is computed here, keeping predicates small and pure.
    """

    headline_en: str
    detail_en: str = ""
    window_note: str | None = None


# A rule predicate: pure, no I/O, no clock beyond ``ctx.now``. Returns ``Fired`` or ``None``.
Predicate = Callable[["Forecast", "FarmerContext"], "Fired | None"]

# Inclusive calendar window as ((start_month, start_day), (end_month, end_day)).
SeasonWindow = tuple[tuple[int, int], tuple[int, int]]


@dataclass(frozen=True, slots=True)
class RuleSpec:
    """Data-driven descriptor for one farming-read rule.

    Scoping (crops / water source / season) is DATA so the engine stays a table of rules +
    small pure predicates rather than a tangle of ``if`` branches. ``applies_to_crops=None``
    means "runs for any crop" (subject to ``excludes_crops``).
    """

    id: str
    action: FarmAction
    crop_label: str  # what to show as FarmingRead.crop ("any" or a specific crop)
    severity: Severity
    confidence: str
    caveat_en: str
    sources: tuple[str, ...]
    predicate: Predicate
    applies_to_crops: frozenset[Crop] | None = None
    excludes_crops: frozenset[Crop] = field(default_factory=frozenset)
    applies_to_water_sources: frozenset[WaterSource] | None = None
    season: SeasonWindow | None = None


class WeatherProvider(Protocol):
    """Hexagonal PORT for fetching a normalised Forecast.

    The domain/app depend only on this Protocol; adapters (Open-Meteo HTTP, a cache
    decorator, a fake for tests) implement it. The returned Forecast has an empty
    ``farming_read`` — the pure engine fills it. Implementations raise
    :class:`ProviderError` on failure so the app layer can fall back to cache.
    """

    async def fetch(self, point: GeoPoint) -> Forecast: ...


class ProviderError(RuntimeError):
    """Raised by a WeatherProvider when it cannot return a Forecast."""
