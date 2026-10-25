"""Composition root: the one place adapters are wired together from settings.

Every transport (Lambda handler, FastAPI app, local dev server) gets its provider from here, so
"which cache, which timeout" is decided once.
"""

from __future__ import annotations

from rythu_weather.adapters.cache import CachedProvider, CacheStore, DynamoDbCacheStore
from rythu_weather.adapters.open_meteo import OpenMeteoHttpProvider
from rythu_weather.app.settings import Settings, get_settings
from rythu_weather.domain.models import WeatherProvider


def build_cache_store(s: Settings) -> CacheStore | None:
    if s.azure_tables_endpoint:
        # Imported lazily: the Azure SDK is not part of the AWS Lambda bundle.
        from azure.identity.aio import DefaultAzureCredential

        from rythu_weather.adapters.azure_table import AzureTableCacheStore

        # In Azure this resolves to the Function App's managed identity; locally to `az login`.
        return AzureTableCacheStore(
            table_name=s.azure_forecast_table, endpoint=s.azure_tables_endpoint, credential=DefaultAzureCredential()
        )
    if s.azure_tables_connection_string:
        from rythu_weather.adapters.azure_table import AzureTableCacheStore

        return AzureTableCacheStore(s.azure_tables_connection_string, s.azure_forecast_table)
    if s.cache_table:
        return DynamoDbCacheStore(s.cache_table)
    return None


def build_provider(settings: Settings | None = None) -> WeatherProvider:
    s = settings or get_settings()
    upstream = OpenMeteoHttpProvider(timeout=s.open_meteo_timeout_s)
    store = build_cache_store(s)
    return CachedProvider(upstream, store) if store is not None else upstream
