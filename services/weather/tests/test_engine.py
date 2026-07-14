"""Engine tests: data-driven crop / water-source / season scoping and 'only fired' output."""

from __future__ import annotations

from datetime import timedelta

from builders import at, ctx, day, forecast, hours_from
from rythu_weather.domain.engine import evaluate_reads
from rythu_weather.domain.models import Crop, WaterSource
from rythu_weather.domain.rules import DEFERRED_RULE_IDS


def _ids(reads):
    return {r.id for r in reads}


def test_calm_forecast_produces_no_reads():
    # March: outside both the sow and harvest season gates, so only the always-on hourly/daily
    # rules could fire — and a calm forecast fires none.
    now = at(2026, 3, 1, 8)
    fc = forecast(
        now, hourly=hours_from(now, 6, pp=10, wind=5.0, code=1), daily=[day(now.date(), pp_max=10, precip_sum=1.0)]
    )
    assert evaluate_reads(fc, ctx(now, crop=Crop.COTTON)) == ()


def test_crop_scope_harvest_is_paddy_only():
    now = at(2026, 9, 20, 8)  # in the paddy-harvest window
    fc = forecast(now, daily=[day(now.date(), pp_max=70, precip_sum=0.0)])
    assert "harvest-paddy-avoid-rain" not in _ids(evaluate_reads(fc, ctx(now, crop=Crop.COTTON)))
    assert "harvest-paddy-avoid-rain" in _ids(evaluate_reads(fc, ctx(now, crop=Crop.PADDY)))


def test_season_gate_blocks_harvest_in_monsoon():
    fc_july = forecast(at(2026, 7, 15, 8), daily=[day(at(2026, 7, 15).date(), pp_max=70)])
    assert evaluate_reads(fc_july, ctx(at(2026, 7, 15, 8), crop=Crop.PADDY)) == ()  # July < Sep → gated off


def test_water_scope_sow_moisture_is_rainfed_only():
    now = at(2026, 7, 15, 9)
    drizzle = [
        day(now.date(), pp_max=30, precip_sum=8.0),
        day((now + timedelta(days=1)).date(), pp_max=20, precip_sum=7.0),
        day((now + timedelta(days=2)).date(), pp_max=25, precip_sum=6.0),
    ]
    fc = forecast(now, daily=drizzle)
    assert "sow-need-soil-moisture" in _ids(evaluate_reads(fc, ctx(now, water=WaterSource.RAINFED)))
    assert "sow-need-soil-moisture" not in _ids(evaluate_reads(fc, ctx(now, water=WaterSource.BOREWELL)))


def test_excludes_paddy_from_irrigate_skip():
    now = at(2026, 7, 15, 12)
    fc = forecast(now, daily=[day(now.date(), pp_max=70, precip_sum=25.0)])
    assert "irrigate-skip-rain-coming" in _ids(evaluate_reads(fc, ctx(now, crop=Crop.COTTON)))
    assert "irrigate-skip-rain-coming" not in _ids(evaluate_reads(fc, ctx(now, crop=Crop.PADDY)))


def test_deferred_rules_never_emitted():
    now = at(2026, 7, 15, 8)
    # a scenario that would satisfy the deferred cotton spray-window if it were active
    fc = forecast(
        now, hourly=hours_from(now, 24, pp=0, precip=0.0, wind=5.0, code=1), daily=[day(now.date(), pp_max=10)]
    )
    reads = evaluate_reads(fc, ctx(now, crop=Crop.COTTON))
    assert _ids(reads).isdisjoint(DEFERRED_RULE_IDS)


def test_paddy_harvest_season_gate_boundary():
    # Off on Aug 31 (green monsoon paddy), on from Sep 1 — the highest-consequence gate.
    off = forecast(at(2026, 8, 31, 8), daily=[day(at(2026, 8, 31).date(), pp_max=70)])
    assert "harvest-paddy-avoid-rain" not in _ids(evaluate_reads(off, ctx(at(2026, 8, 31, 8), crop=Crop.PADDY)))
    on = forecast(at(2026, 9, 1, 8), daily=[day(at(2026, 9, 1).date(), pp_max=70)])
    assert "harvest-paddy-avoid-rain" in _ids(evaluate_reads(on, ctx(at(2026, 9, 1, 8), crop=Crop.PADDY)))


def test_sow_season_gate_boundary():
    # sow rules active through Aug 15, gated from Aug 16 (probe via the heavy-rain washout rule).
    on = forecast(at(2026, 8, 15, 9), daily=[day(at(2026, 8, 15).date(), pp_max=0, precip_sum=60.0)])
    assert "sow-avoid-before-washout" in _ids(evaluate_reads(on, ctx(at(2026, 8, 15, 9), crop=Crop.COTTON)))
    off = forecast(at(2026, 8, 16, 9), daily=[day(at(2026, 8, 16).date(), pp_max=0, precip_sum=60.0)])
    assert "sow-avoid-before-washout" not in _ids(evaluate_reads(off, ctx(at(2026, 8, 16, 9), crop=Crop.COTTON)))


def test_drainage_rules_do_not_double_fire_across_crops():
    now = at(2026, 7, 15, 9)
    fc = forecast(now, daily=[day(now.date(), pp_max=0, precip_sum=60.0)])
    for crop in (Crop.MAIZE, Crop.RED_GRAM):
        ids = _ids(evaluate_reads(fc, ctx(now, crop=crop)))
        assert "drainage-heavy-rain-maize" in ids
        assert "chilli-waterlogging-drainage" not in ids
    # chilli gets exactly ONE drainage read — its own (tighter) rule, not the maize one
    chilli_ids = _ids(evaluate_reads(fc, ctx(now, crop=Crop.CHILLI)))
    assert "chilli-waterlogging-drainage" in chilli_ids
    assert "drainage-heavy-rain-maize" not in chilli_ids
    for crop in (Crop.COTTON, Crop.PADDY, None):
        ids = _ids(evaluate_reads(fc, ctx(now, crop=crop)))
        assert "drainage-heavy-rain-maize" not in ids
        assert "chilli-waterlogging-drainage" not in ids


def test_chilli_receives_crop_agnostic_reads():
    # A windy morning fires the crop-agnostic spray-wind rule for chilli too.
    now = at(2026, 7, 15, 8)
    fc = forecast(now, hourly=hours_from(at(2026, 7, 15, 0), 24, wind=18.0), daily=[day(now.date(), pp_max=10)])
    assert "spray-wind-drift" in _ids(evaluate_reads(fc, ctx(now, crop=Crop.CHILLI)))
