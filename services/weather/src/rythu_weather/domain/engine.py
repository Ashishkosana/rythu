"""The pure rule engine: apply data-driven scope filters, then run each rule's predicate.

Only rules that actually FIRE produce a :class:`FarmingRead`. We deliberately do not emit
"all-clear" reads in v0 — the verified spec warns that a false all-clear ("no warning shown")
is more dangerous than silence for a coarse model that misses local showers.
"""

from __future__ import annotations

from datetime import date

from rythu_weather.domain.models import (
    FarmerContext,
    FarmingRead,
    Fired,
    Forecast,
    RuleSpec,
    SeasonWindow,
)
from rythu_weather.domain.rules import ACTIVE_RULES


def _crop_in_scope(spec: RuleSpec, ctx: FarmerContext) -> bool:
    if ctx.crop is not None and ctx.crop in spec.excludes_crops:
        return False
    if spec.applies_to_crops is None:
        return True  # "any" rule — runs regardless of selected crop
    if ctx.crop is None:
        return False  # a crop-specific rule needs a chosen crop
    return ctx.crop in spec.applies_to_crops


def _water_in_scope(spec: RuleSpec, ctx: FarmerContext) -> bool:
    if spec.applies_to_water_sources is None:
        return True
    return ctx.water_source in spec.applies_to_water_sources


def _in_season(window: SeasonWindow | None, today: date) -> bool:
    if window is None:
        return True
    # Compare (month, day) tuples directly — avoids Feb-29 date-construction errors and
    # correctly handles a window that wraps the new year (e.g. Nov→Feb).
    start, end = window
    cur = (today.month, today.day)
    if start <= end:
        return start <= cur <= end
    return cur >= start or cur <= end


def _build_read(spec: RuleSpec, fired: Fired) -> FarmingRead:
    return FarmingRead(
        id=spec.id,
        action=spec.action,
        crop=spec.crop_label,
        severity=spec.severity,
        headline_en=fired.headline_en,
        detail_en=fired.detail_en,
        caveat_en=spec.caveat_en,
        headline_te=fired.headline_te,
        detail_te=fired.detail_te,
        caveat_te=spec.caveat_te,
        window_note=fired.window_note,
        sources=spec.sources,
        rule_confidence=spec.confidence,
        triggered=True,
    )


def evaluate_reads(forecast: Forecast, ctx: FarmerContext) -> tuple[FarmingRead, ...]:
    """Run every in-scope active rule against the forecast; return the reads that fired."""
    reads: list[FarmingRead] = []
    for spec in ACTIVE_RULES:
        if not _crop_in_scope(spec, ctx):
            continue
        if not _water_in_scope(spec, ctx):
            continue
        if not _in_season(spec.season, ctx.now.date()):
            continue
        if spec.months is not None and ctx.now.month not in spec.months:
            continue
        fired = spec.predicate(forecast, ctx)
        if fired is None:
            continue
        reads.append(_build_read(spec, fired))
    return tuple(reads)
