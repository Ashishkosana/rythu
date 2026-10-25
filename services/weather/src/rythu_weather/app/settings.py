"""Runtime configuration — the ONE place that reads environment variables.

Everything the service can be tuned with lives here, typed and validated at startup, so a bad
value fails the cold start loudly instead of surfacing as odd behaviour on a farmer's request.
Adapters receive plain values from here; they never read ``os.environ`` themselves.

Variables (all optional):

* ``RYTHU_CACHE_TABLE`` — DynamoDB table for the forecast cache (AWS).
* ``RYTHU_AZURE_TABLES_CONNECTION_STRING`` — Azure Table Storage connection string for the forecast
  cache (Azure; Azurite locally). SECRET: never logged, never in ``repr``. In Azure it comes from a
  Key Vault reference (S6).
* ``RYTHU_AZURE_FORECAST_TABLE`` — table name for the Azure forecast cache (default ``forecast``).
* ``RYTHU_OPEN_METEO_TIMEOUT_S`` — total deadline for one Open-Meteo fetch (default 4).
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
DEFAULT_AZURE_FORECAST_TABLE = "forecast"
# Azure table names: 3–63 alphanumerics, starting with a letter.
_AZURE_TABLE_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]{2,62}")


@dataclass(frozen=True, slots=True)
class Settings:
    cache_table: str | None = None
    # repr=False: a connection string carries the account key and must never reach a log line.
    azure_tables_connection_string: str | None = field(default=None, repr=False)
    azure_forecast_table: str = DEFAULT_AZURE_FORECAST_TABLE
    open_meteo_timeout_s: float = DEFAULT_OPEN_METEO_TIMEOUT_S
    log_level: str = DEFAULT_LOG_LEVEL

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        """Parse and validate settings. Raises ``ValueError`` naming the bad variable."""
        e = os.environ if env is None else env
        timeout = _positive_float(e, "RYTHU_OPEN_METEO_TIMEOUT_S", DEFAULT_OPEN_METEO_TIMEOUT_S)
        level = e.get("RYTHU_LOG_LEVEL", DEFAULT_LOG_LEVEL).strip().upper()
        if level not in _LOG_LEVELS:
            raise ValueError(f"RYTHU_LOG_LEVEL must be one of {sorted(_LOG_LEVELS)}, got {level!r}")
        dynamo = e.get("RYTHU_CACHE_TABLE") or None
        azure = (e.get("RYTHU_AZURE_TABLES_CONNECTION_STRING") or "").strip() or None
        if dynamo and azure:
            raise ValueError("set RYTHU_CACHE_TABLE (DynamoDB) or RYTHU_AZURE_TABLES_CONNECTION_STRING, not both")
        table = (e.get("RYTHU_AZURE_FORECAST_TABLE") or DEFAULT_AZURE_FORECAST_TABLE).strip()
        if not _AZURE_TABLE_NAME.fullmatch(table):
            raise ValueError(
                f"RYTHU_AZURE_FORECAST_TABLE must be 3-63 letters/digits starting with a letter, got {table!r}"
            )
        return cls(
            cache_table=dynamo,
            azure_tables_connection_string=azure,
            azure_forecast_table=table,
            open_meteo_timeout_s=timeout,
            log_level=level,
        )


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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide settings, parsed once per cold start."""
    return Settings.from_env()
