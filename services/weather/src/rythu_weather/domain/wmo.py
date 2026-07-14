"""Static WMO weather-code → plain label/emoji/farm-note table.

Covers the codes that actually occur in monsoon Telangana. Telugu labels are added at the
UI layer; this stays English + language-neutral data.
"""

from __future__ import annotations

from rythu_weather.domain.models import WMOCategory, WMOCondition

_CONDITIONS: tuple[WMOCondition, ...] = (
    WMOCondition(
        0,
        "Clear sky",
        WMOCategory.CLEAR,
        "☀️",
        "Dry and sunny; good for spraying, weeding and drying grain — check soil moisture.",
    ),
    WMOCondition(
        1,
        "Mainly clear",
        WMOCategory.CLEAR,
        "🌤️",
        "Mostly dry; suitable for spraying and drying — still check the hourly rain chance first.",
    ),
    WMOCondition(
        2,
        "Partly cloudy",
        WMOCategory.CLOUD,
        "⛅",
        "Usually OK for field work; watch the hourly rain probability before spraying.",
    ),
    WMOCondition(
        3,
        "Overcast",
        WMOCategory.CLOUD,
        "☁️",
        "Full cloud raises humidity and leaf-disease risk; delay spraying if rain looks likely.",
    ),
    WMOCondition(
        45, "Fog", WMOCategory.FOG, "🌫️", "Fog and dew wet the canopy — wait for leaves to dry before spraying."
    ),
    WMOCondition(
        48,
        "Fog with rime",
        WMOCategory.FOG,
        "🌫️",
        "Heavy moisture on leaves; hold off spraying and scout for fungal disease once it clears.",
    ),
    WMOCondition(
        51,
        "Light drizzle",
        WMOCategory.DRIZZLE,
        "🌦️",
        "Light drizzle washes off sprays and slows drying — postpone pesticide use.",
    ),
    WMOCondition(
        53,
        "Moderate drizzle",
        WMOCategory.DRIZZLE,
        "🌦️",
        "Skip spraying (product will wash off); check that field drains are clear.",
    ),
    WMOCondition(
        55,
        "Dense drizzle",
        WMOCategory.DRIZZLE,
        "🌧️",
        "Long wetting favours leaf disease; avoid spraying and keep harvested grain covered.",
    ),
    WMOCondition(
        61,
        "Slight rain",
        WMOCategory.RAIN,
        "🌧️",
        "Light rain helps sowing, but delay spraying and top-dressing fertiliser until it clears.",
    ),
    WMOCondition(
        63,
        "Moderate rain",
        WMOCategory.RAIN,
        "🌧️",
        "Pause field operations; keep paddy bunds and field drains open to avoid waterlogging.",
    ),
    WMOCondition(
        65,
        "Heavy rain",
        WMOCategory.RAIN,
        "🌧️",
        "Waterlogging and lodging risk — open drains and delay all spraying and fertiliser.",
    ),
    WMOCondition(
        80,
        "Slight rain showers",
        WMOCategory.SHOWERS,
        "🌦️",
        "Brief on-off showers likely; plan spraying for dry gaps and watch the hourly forecast.",
    ),
    WMOCondition(
        81,
        "Moderate rain showers",
        WMOCategory.SHOWERS,
        "🌧️",
        "Intermittent showers — avoid spraying and fertiliser, and keep drainage clear.",
    ),
    WMOCondition(
        82,
        "Violent rain showers",
        WMOCategory.SHOWERS,
        "🌧️",
        "Heavy downpours risk erosion and waterlogging on red/chalka soil; secure drainage.",
    ),
    WMOCondition(
        95,
        "Thunderstorm",
        WMOCategory.THUNDERSTORM,
        "⛈️",
        "Lightning and gusty rain — stay off open fields for safety and delay all field work.",
    ),
    WMOCondition(
        96,
        "Thunderstorm with slight hail",
        WMOCategory.THUNDERSTORM,
        "⛈️",
        "Hail can damage cotton bolls and maize; avoid the field (hail forecast is unreliable).",
    ),
    WMOCondition(
        99,
        "Thunderstorm with heavy hail",
        WMOCategory.THUNDERSTORM,
        "⛈️",
        "Severe hail and wind can flatten crops — stay safe indoors and assess damage after.",
    ),
)

WMO_TABLE: dict[int, WMOCondition] = {c.code: c for c in _CONDITIONS}

# Codes that mean a thunderstorm — used by the fieldwork storm guard.
THUNDERSTORM_CODES: frozenset[int] = frozenset({95, 96, 99})

_UNKNOWN = WMOCondition(-1, "Unknown", WMOCategory.CLOUD, "❓", "No sky condition reported.")


def lookup(code: int | None) -> WMOCondition:
    """Return the condition for a WMO code, or a safe 'Unknown' placeholder."""
    if code is None:
        return _UNKNOWN
    return WMO_TABLE.get(code, _UNKNOWN)
