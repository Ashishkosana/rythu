"""Runtime configuration — the ONE place that reads environment variables.

Everything the service can be tuned with lives here, typed and validated at startup, so a bad
value fails the cold start loudly instead of surfacing as odd behaviour on a farmer's request.
Adapters receive plain values from here; they never read ``os.environ`` themselves.

Variables (all optional):

* ``RYTHU_CACHE_TABLE`` — DynamoDB table for the forecast cache (AWS).
* ``RYTHU_AZURE_TABLES_ENDPOINT`` — Azure Table Storage endpoint (``https://<account>.table.core.windows.net``),
  authenticated with the app's managed identity — no secret anywhere. This is how Azure runs.
* ``RYTHU_AZURE_TABLES_CONNECTION_STRING`` — alternative for local dev against Azurite. SECRET: never
  logged, never in ``repr``.
* ``RYTHU_AZURE_FORECAST_TABLE`` — table name for the Azure forecast cache (default ``forecast``).
* ``RYTHU_OPEN_METEO_TIMEOUT_S`` — total deadline for one Open-Meteo fetch (default 4).
* ``RYTHU_UPSTREAM_BUDGET_PER_HOUR`` — on-demand Open-Meteo calls allowed per hour across all instances
  (default 120). Beyond it, misses serve the saved copy or an honest degraded answer.
* ``RYTHU_PREWARM_MAX_CELLS`` — most cells the 20-minute pre-warm refreshes (default 60).
* ``RYTHU_TOKEN_SIGNING_KEY`` — HMAC key for device tokens (ADR 0004), ≥ 32 characters. SECRET: in Azure
  it is a Key Vault reference resolved by the platform; never logged, never in ``repr``. Unset locally →
  a throwaway key per process (tokens die with it); unset in Azure → device accounts are switched off.
* ``RYTHU_AZURE_USERS_TABLE`` — table for device accounts and profiles (default ``users``).
* ``RYTHU_DEVICE_REGISTRATIONS_PER_HOUR`` — new device accounts allowed per hour, all instances
  together (default 30): a pilot needs a handful; a script filling the table does not get far.
* ``RYTHU_VAPID_KEY_ID`` — Key Vault key (``https://<vault>.vault.azure.net/keys/<name>``) that signs
  Web Push VAPID tokens; the private key never leaves Key Vault. Unset locally → a throwaway key per
  process; unset in Azure → push alerts are switched off.
* ``RYTHU_VAPID_SUBJECT`` — contact for push services (``https://…`` or ``mailto:…``; default the repo).

Quota arithmetic (Open-Meteo free tier ≈ 10,000 calls/day; tests keep the worst case under 80 %):
pre-warm 60 cells × 3 runs/h × 24 h = 4,320 + on-demand 120/h × 24 h = 2,880 → 7,200/day.
* ``RYTHU_LOG_LEVEL`` — ``DEBUG`` / ``INFO`` / ``WARNING`` / ``ERROR`` (default ``INFO``).

At most one cache backend may be configured; neither means no cache.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import lru_cache

_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR"})
# A slow upstream must not eat the request: Open-Meteo normally answers in < 1 s, and the caller
# (Next.js server, then the phone) has its own budget on top of this.
DEFAULT_OPEN_METEO_TIMEOUT_S = 4.0
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_UPSTREAM_BUDGET_PER_HOUR = 120
DEFAULT_PREWARM_MAX_CELLS = 60
DEFAULT_AZURE_FORECAST_TABLE = "forecast"
DEFAULT_AZURE_USERS_TABLE = "users"
DEFAULT_DEVICE_REGISTRATIONS_PER_HOUR = 30
MIN_TOKEN_KEY_CHARS = 32
DEFAULT_VAPID_SUBJECT = "https://github.com/Ashishkosana/rythu"
# Azure table names: 3–63 alphanumerics, starting with a letter.
_AZURE_TABLE_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]{2,62}")


@dataclass(frozen=True, slots=True)
class Settings:
    cache_table: str | None = None
    azure_tables_endpoint: str | None = None
    # repr=False: a connection string carries the account key and must never reach a log line.
    azure_tables_connection_string: str | None = field(default=None, repr=False)
    azure_forecast_table: str = DEFAULT_AZURE_FORECAST_TABLE
    open_meteo_timeout_s: float = DEFAULT_OPEN_METEO_TIMEOUT_S
    log_level: str = DEFAULT_LOG_LEVEL
    upstream_budget_per_hour: int = DEFAULT_UPSTREAM_BUDGET_PER_HOUR
    prewarm_max_cells: int = DEFAULT_PREWARM_MAX_CELLS
    # repr=False: the token signing key is the service's one real secret.
    token_signing_key: bytes | None = field(default=None, repr=False)
    # Why the key is missing, when that is a platform state rather than a choice (safe to log).
    token_signing_key_problem: str | None = None
    azure_users_table: str = DEFAULT_AZURE_USERS_TABLE
    device_registrations_per_hour: int = DEFAULT_DEVICE_REGISTRATIONS_PER_HOUR
    vapid_key_id: str | None = None
    vapid_subject: str = DEFAULT_VAPID_SUBJECT

    @property
    def uses_azure_tables(self) -> bool:
        return self.azure_tables_endpoint is not None or self.azure_tables_connection_string is not None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        """Parse and validate settings. Raises ``ValueError`` naming the bad variable."""
        e = os.environ if env is None else env
        timeout = _positive_float(e, "RYTHU_OPEN_METEO_TIMEOUT_S", DEFAULT_OPEN_METEO_TIMEOUT_S)
        level = e.get("RYTHU_LOG_LEVEL", DEFAULT_LOG_LEVEL).strip().upper()
        if level not in _LOG_LEVELS:
            raise ValueError(f"RYTHU_LOG_LEVEL must be one of {sorted(_LOG_LEVELS)}, got {level!r}")
        dynamo = e.get("RYTHU_CACHE_TABLE") or None
        endpoint = (e.get("RYTHU_AZURE_TABLES_ENDPOINT") or "").strip() or None
        azure = (e.get("RYTHU_AZURE_TABLES_CONNECTION_STRING") or "").strip() or None
        backends = [n for n, v in (("RYTHU_CACHE_TABLE", dynamo), ("RYTHU_AZURE_TABLES_ENDPOINT", endpoint),
                                   ("RYTHU_AZURE_TABLES_CONNECTION_STRING", azure)) if v]
        if len(backends) > 1:
            raise ValueError(f"set at most one cache backend, not both: {' and '.join(backends)}")
        if endpoint and not endpoint.startswith("https://"):
            raise ValueError("RYTHU_AZURE_TABLES_ENDPOINT must be an https:// URL")
        table = _table_name(e, "RYTHU_AZURE_FORECAST_TABLE", DEFAULT_AZURE_FORECAST_TABLE)
        return cls(
            cache_table=dynamo,
            azure_tables_endpoint=endpoint,
            azure_tables_connection_string=azure,
            azure_forecast_table=table,
            open_meteo_timeout_s=timeout,
            log_level=level,
            upstream_budget_per_hour=_bounded_int(
                e, "RYTHU_UPSTREAM_BUDGET_PER_HOUR", DEFAULT_UPSTREAM_BUDGET_PER_HOUR, 1, 400
            ),
            prewarm_max_cells=_bounded_int(e, "RYTHU_PREWARM_MAX_CELLS", DEFAULT_PREWARM_MAX_CELLS, 0, 100),
            token_signing_key=_signing_key(e),
            token_signing_key_problem=_signing_key_problem(e),
            azure_users_table=_table_name(e, "RYTHU_AZURE_USERS_TABLE", DEFAULT_AZURE_USERS_TABLE),
            device_registrations_per_hour=_bounded_int(
                e, "RYTHU_DEVICE_REGISTRATIONS_PER_HOUR", DEFAULT_DEVICE_REGISTRATIONS_PER_HOUR, 1, 1000
            ),
            vapid_key_id=_vapid_key_id(e),
            vapid_subject=_vapid_subject(e),
        )


def _table_name(env: Mapping[str, str], name: str, default: str) -> str:
    table = (env.get(name) or default).strip()
    if not _AZURE_TABLE_NAME.fullmatch(table):
        raise ValueError(f"{name} must be 3-63 letters/digits starting with a letter, got {table!r}")
    return table


def _signing_key(env: Mapping[str, str]) -> bytes | None:
    raw = (env.get("RYTHU_TOKEN_SIGNING_KEY") or "").strip()
    if not raw:
        return None
    if _unresolved_reference(raw):
        return None  # never sign with the reference's own (public) text; see _signing_key_problem
    if len(raw) < MIN_TOKEN_KEY_CHARS:
        raise ValueError(f"RYTHU_TOKEN_SIGNING_KEY must be at least {MIN_TOKEN_KEY_CHARS} characters")
    return raw.encode("utf-8")


def _vapid_key_id(env: Mapping[str, str]) -> str | None:
    raw = (env.get("RYTHU_VAPID_KEY_ID") or "").strip()
    if not raw:
        return None
    if not re.fullmatch(r"https://[a-z0-9-]+\.vault\.azure\.net/keys/[A-Za-z0-9-]+(/[0-9a-f]{32})?", raw):
        raise ValueError("RYTHU_VAPID_KEY_ID must be a Key Vault key URL (https://<vault>.vault.azure.net/keys/<name>)")
    return raw


def _vapid_subject(env: Mapping[str, str]) -> str:
    raw = (env.get("RYTHU_VAPID_SUBJECT") or DEFAULT_VAPID_SUBJECT).strip()
    if not (raw.startswith("https://") or raw.startswith("mailto:")):
        raise ValueError("RYTHU_VAPID_SUBJECT must start with https:// or mailto: (RFC 8292)")
    return raw


def _unresolved_reference(raw: str) -> bool:
    # When the platform cannot resolve a Key Vault reference, the app sees the reference text itself.
    return raw.startswith("@Microsoft.KeyVault(")


def _signing_key_problem(env: Mapping[str, str]) -> str | None:
    # Usually the first minutes of a fresh deployment (the role assignment still propagating), so it
    # switches accounts off instead of failing the cold start — weather keeps working meanwhile.
    if _unresolved_reference((env.get("RYTHU_TOKEN_SIGNING_KEY") or "").strip()):
        return "unresolved Key Vault reference: does the app's identity have 'Key Vault Secrets User' on the vault?"
    return None


def _positive_float(env: Mapping[str, str], name: str, default: float) -> float:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw!r}") from exc
    if not 0 < value <= 60:
        raise ValueError(f"{name} must be in (0, 60], got {value}")
    return value


def _bounded_int(env: Mapping[str, str], name: str, default: int, lo: int, hi: int) -> int:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a whole number, got {raw!r}") from exc
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be in [{lo}, {hi}], got {value}")
    return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide settings, parsed once per cold start."""
    return Settings.from_env()
