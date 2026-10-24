"""Runtime configuration — the ONE place that reads environment variables.

Everything the service can be tuned with lives here, typed and validated at startup, so a bad
value fails the cold start loudly instead of surfacing as odd behaviour on a farmer's request.
Adapters receive plain values from here; they never read ``os.environ`` themselves.

Variables (all optional):

* ``RYTHU_CACHE_TABLE`` — DynamoDB table for the forecast cache; unset = no cache.
* ``RYTHU_OPEN_METEO_TIMEOUT_S`` — total deadline for one Open-Meteo fetch (default 4).
* ``RYTHU_LOG_LEVEL`` — ``DEBUG`` / ``INFO`` / ``WARNING`` / ``ERROR`` (default ``INFO``).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache

_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR"})
# A slow upstream must not eat the request: Open-Meteo normally answers in < 1 s, and the caller
# (Next.js server, then the phone) has its own budget on top of this.
DEFAULT_OPEN_METEO_TIMEOUT_S = 4.0
DEFAULT_LOG_LEVEL = "INFO"


@dataclass(frozen=True, slots=True)
class Settings:
    cache_table: str | None = None
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
        return cls(
            cache_table=e.get("RYTHU_CACHE_TABLE") or None,
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
