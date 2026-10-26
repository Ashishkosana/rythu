"""Composition root: the one place adapters are wired together from settings.

Every transport (Lambda handler, FastAPI app, local dev server, the pre-warm timer) gets its services
from here, so "which cache, which timeout, which budget" is decided once.

On Azure the request path is::

    RegisteringProvider → CachedProvider → BudgetedProvider → OpenMeteoHttpProvider
    (note the cell)       (≤ 30 min hit)   (hourly cap)        (4 s deadline)

and the pre-warm timer refreshes the registry's cells through the raw upstream.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rythu_weather.adapters.budget import BudgetedProvider
from rythu_weather.adapters.cache import CachedProvider, CacheStore, DynamoDbCacheStore
from rythu_weather.adapters.cells import CellRegistry, RegisteringProvider
from rythu_weather.adapters.geocode import (
    CachedGeocoder,
    FallbackGeocoder,
    Geocoder,
    NominatimGeocoder,
    OpenMeteoGeocoder,
)
from rythu_weather.adapters.open_meteo import OpenMeteoHttpProvider
from rythu_weather.app.settings import Settings, get_settings
from rythu_weather.domain.models import WeatherProvider

if TYPE_CHECKING:  # types only — the Azure SDK is never imported on the Lambda path
    from azure.core.credentials_async import AsyncTokenCredential

    from rythu_weather.adapters.azure_table import TableAuth


@dataclass(frozen=True, slots=True)
class PrewarmParts:
    registry: CellRegistry
    store: CacheStore
    upstream: WeatherProvider
    max_cells: int


@dataclass(frozen=True, slots=True)
class Services:
    provider: WeatherProvider
    prewarm: PrewarmParts | None  # only where a shared store exists (Azure)


def build_services(settings: Settings | None = None) -> Services:
    s = settings or get_settings()
    upstream = OpenMeteoHttpProvider(timeout=s.open_meteo_timeout_s)
    if s.azure_tables_endpoint or s.azure_tables_connection_string:
        # Imported lazily: the Azure SDK is not part of the AWS Lambda bundle.
        from rythu_weather.adapters.azure_table import AzureTableCellRegistry, AzureTableUpstreamBudget

        auth = _azure_auth(s)
        store = _azure_store(s)
        registry = AzureTableCellRegistry(auth)
        budget = AzureTableUpstreamBudget(auth)
        budgeted = BudgetedProvider(upstream, budget, per_hour=s.upstream_budget_per_hour)
        provider = RegisteringProvider(CachedProvider(budgeted, store), registry)
        return Services(provider, PrewarmParts(registry, store, upstream, s.prewarm_max_cells))
    if s.cache_table:
        return Services(CachedProvider(upstream, DynamoDbCacheStore(s.cache_table)), None)
    return Services(upstream, None)


def build_provider(settings: Settings | None = None) -> WeatherProvider:
    return build_services(settings).provider


def build_cache_store(s: Settings) -> CacheStore | None:
    if s.azure_tables_endpoint or s.azure_tables_connection_string:
        return _azure_store(s)
    if s.cache_table:
        return DynamoDbCacheStore(s.cache_table)
    return None


_CREDENTIAL: AsyncTokenCredential | None = None


def _azure_auth(s: Settings) -> TableAuth:
    from rythu_weather.adapters.azure_table import TableAuth

    if s.azure_tables_connection_string:
        return TableAuth(connection_string=s.azure_tables_connection_string)
    global _CREDENTIAL
    if _CREDENTIAL is None:
        from azure.identity.aio import DefaultAzureCredential

        # One credential per process: in Azure it is the Function App's managed identity (locally
        # `az login`), and sharing it means one token cache for the cache, registry and budget.
        _CREDENTIAL = DefaultAzureCredential()
    return TableAuth(endpoint=s.azure_tables_endpoint, credential=_CREDENTIAL)


def _azure_store(s: Settings) -> CacheStore:
    from rythu_weather.adapters.azure_table import AzureTableCacheStore

    auth = _azure_auth(s)
    return AzureTableCacheStore(
        auth.connection_string, s.azure_forecast_table, endpoint=auth.endpoint, credential=auth.credential
    )


def build_geocoder() -> Geocoder:
    return CachedGeocoder(FallbackGeocoder(NominatimGeocoder(), OpenMeteoGeocoder()))
