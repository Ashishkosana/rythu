"""Composition root: the one place adapters are wired together from settings.

Every transport (Lambda handler, FastAPI app, local dev server, the pre-warm timer) gets its services
from here, so "which cache, which timeout, which budget" is decided once.

On Azure the request path is::

    RegisteringProvider → CachedProvider → BudgetedProvider → OpenMeteoHttpProvider
    (note the cell)       (≤ 30 min hit)   (hourly cap)        (4 s deadline)

and the pre-warm timer refreshes the registry's cells through the raw upstream.
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING

from rythu_weather.adapters.budget import BudgetedProvider, InMemoryUpstreamBudget, UpstreamBudget
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
from rythu_weather.app.accounts import InMemoryUserStore, TokenSigner, UserStore
from rythu_weather.app.settings import Settings, get_settings
from rythu_weather.domain.models import WeatherProvider
from rythu_weather.observability import log_event

_log = logging.getLogger(__name__)

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


@dataclass(frozen=True, slots=True)
class Accounts:
    """Device accounts (ADR 0004): where users live, how tokens are signed, how fast devices may join."""

    users: UserStore
    signer: TokenSigner
    registrations: UpstreamBudget
    registrations_per_hour: int


def build_accounts(settings: Settings | None = None) -> Accounts | None:
    """None = accounts switched off (the /v1/me routes answer 503; weather is unaffected)."""
    s = settings or get_settings()
    key = s.token_signing_key
    if s.uses_azure_tables:
        if key is None:
            # Several instances must share one key, so a throwaway key would make tokens fail at random.
            reason = s.token_signing_key_problem or "RYTHU_TOKEN_SIGNING_KEY not set"
            log_event(_log, logging.ERROR, "accounts.disabled", reason=reason)
            return None
        from rythu_weather.adapters.azure_table import AzureTableUpstreamBudget, AzureTableUserStore

        auth = _azure_auth(s)
        users: UserStore = AzureTableUserStore(auth, s.azure_users_table)
        registrations: UpstreamBudget = AzureTableUpstreamBudget(auth)
    else:
        users, registrations = InMemoryUserStore(), InMemoryUpstreamBudget()
    if key is None:
        log_event(_log, logging.WARNING, "accounts.ephemeral_key", note="dev only: tokens die with this process")
        key = secrets.token_bytes(32)
    return Accounts(users, TokenSigner(key), registrations, s.device_registrations_per_hour)
