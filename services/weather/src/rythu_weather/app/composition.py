"""Composition root: the one place adapters are wired together from settings.

Every transport (Lambda handler, FastAPI app, local dev server) gets its provider from here, so
"which cache, which timeout" is decided once.
"""

from __future__ import annotations

from rythu_weather.adapters.cache import CachedProvider, DynamoDbCacheStore
from rythu_weather.adapters.open_meteo import OpenMeteoHttpProvider
from rythu_weather.app.settings import Settings, get_settings
from rythu_weather.domain.models import WeatherProvider


def build_provider(settings: Settings | None = None) -> WeatherProvider:
    s = settings or get_settings()
    upstream = OpenMeteoHttpProvider(timeout=s.open_meteo_timeout_s)
    if s.cache_table:
        return CachedProvider(upstream, DynamoDbCacheStore(s.cache_table))
    return upstream
