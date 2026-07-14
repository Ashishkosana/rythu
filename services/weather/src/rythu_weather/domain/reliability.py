"""Honest source + last-updated stamp formatting.

Kept in the domain (pure) so the exact honesty wording is unit-tested. The stamp is
time-relative, so it is computed from ``now`` and ``upstream_fetched_at`` rather than stored
on the Forecast.
"""

from __future__ import annotations

from datetime import datetime


def format_relative_age(now: datetime, fetched_at: datetime) -> str:
    """Human 'how old is our data' label, per the spec buckets.

    ``just now`` (<2 min) · ``N min ago`` (<60 min) · ``N hr ago`` (<24 h) · else ``DD Mon``.
    A future/zero delta clamps to ``just now`` so clock skew never prints a negative age.
    """
    seconds = (now - fetched_at).total_seconds()
    if seconds < 120:
        return "just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes} min ago"
    hours = int(seconds // 3600)
    if hours < 24:
        return f"{hours} hr ago"
    return fetched_at.strftime("%-d %b")


def format_source_stamp(
    now: datetime,
    fetched_at: datetime,
    *,
    resolution_km: int = 11,
    is_offline_cache: bool = False,
) -> str:
    """The full stamp line, e.g. ``Source: Open-Meteo (~11 km) · updated 8 min ago``.

    Always shows ``(~N km)`` so the coarse global-model resolution is never hidden. When
    serving stale cache after a fetch failure, prefixes the offline notice.
    """
    stamp = f"Source: Open-Meteo (~{resolution_km} km) · updated {format_relative_age(now, fetched_at)}"
    if is_offline_cache:
        return f"Offline — showing saved forecast · {stamp}"
    return stamp
