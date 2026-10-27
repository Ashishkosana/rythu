"""The crop calendar says exactly what docs/agronomy-data.md says — no more, no less."""

from __future__ import annotations

import re
from datetime import date

import pytest

from rythu_weather.domain.calendar import CALENDARS, Reference, TaskKind, plan
from rythu_weather.domain.models import Crop

TELUGU = re.compile(r"[ఀ-౿]")
# Active ingredients named in the research's IPM table: a calendar reminder must never become a spray.
PESTICIDES = ("imidacloprid", "pymetrozine", "buprofezin", "flonicamid", "thiodicarb", "chlorantraniliprole",
              "spinetoram", "emamectin", "indoxacarb", "spinosad", "acetamiprid", "fipronil", "chlorfenapyr")


def _days(crop: Crop, kind: TaskKind) -> list[int | None]:
    return sorted((t.start_day for t in CALENDARS[crop].tasks if t.kind is kind), key=lambda d: (d is None, d or 0))


def test_every_pilot_crop_has_a_calendar_keyed_to_the_right_date() -> None:
    assert set(CALENDARS) == set(Crop)
    transplanted = {c for c, cal in CALENDARS.items() if cal.reference is Reference.TRANSPLANTING}
    assert transplanted == {Crop.PADDY, Crop.CHILLI}  # DAT / DAP in the sources; the rest are DAS


def test_fertilizer_timing_matches_the_research() -> None:
    # agronomy-data.md "Split timing (apply exactly as stated)".
    assert _days(Crop.PADDY, TaskKind.FERTILIZER) == [0, 25, 55]  # basal, ~25–30 DAT, ~55–60 DAT
    assert _days(Crop.COTTON, TaskKind.FERTILIZER) == [0, 30, 60, 90]  # P basal; N+K at 30/60/90 DAS
    assert _days(Crop.MAIZE, TaskKind.FERTILIZER) == [0, 25, 45]  # ¼N+P+K basal; ~25 and ~45 DAS
    assert _days(Crop.RED_GRAM, TaskKind.FERTILIZER) == [0]  # all basal, no top-dressing in kharif
    assert _days(Crop.CHILLI, TaskKind.FERTILIZER) == [0, 30, 60, 90]  # basal; N at 30/60/90 DAP


def test_scouting_windows_match_the_research() -> None:
    cotton = _days(Crop.COTTON, TaskKind.SCOUT)
    assert cotton == [45, 90, 105, 120, 135, 150]  # traps from 45 DAS; monitor 90/105/120/135/150 DAS
    # Red gram's pod borer is tied to flowering; the sources give no day count, so there is no date.
    [pod_borer] = [t for t in CALENDARS[Crop.RED_GRAM].tasks if t.kind is TaskKind.SCOUT]
    assert pod_borer.start_day is None and pod_borer.stage_en and TELUGU.search(pod_borer.stage_te)


def test_verification_flags_follow_the_research_table() -> None:
    # Paddy rows are needs_verification=false; cotton, maize, red gram and chilli rows are true.
    for crop, cal in CALENDARS.items():
        expected = crop is not Crop.PADDY
        assert {t.needs_verification for t in cal.tasks if "pjtsau.edu.in" not in t.source} == {expected}, crop


@pytest.mark.parametrize("crop", list(Crop))
def test_every_task_is_sourced_bilingual_and_never_a_spray(crop: Crop) -> None:
    ids = [t.id for t in CALENDARS[crop].tasks]
    assert len(ids) == len(set(ids))
    for t in CALENDARS[crop].tasks:
        assert t.source.startswith("https://"), t.id
        assert TELUGU.search(t.title_te) and TELUGU.search(t.detail_te), t.id
        assert t.title_en and t.detail_en, t.id
        text = f"{t.title_en} {t.detail_en} {t.title_te} {t.detail_te}".lower()
        assert not any(p in text for p in PESTICIDES), t.id
        if t.start_day is not None and t.end_day is not None:
            assert t.end_day >= t.start_day


def test_plan_dates_tasks_from_the_reference_date() -> None:
    tasks = plan(Crop.COTTON, date(2026, 6, 20))
    by_id = {t.spec.id: t for t in tasks}
    assert by_id["cotton.basal"].start == date(2026, 6, 20)
    assert by_id["cotton.split1"].start == date(2026, 7, 20)
    assert by_id["cotton.pbw.traps"].start == date(2026, 8, 4)
    assert by_id["cotton.pbw.check150"].start == date(2026, 11, 17)
    starts = [t.start for t in tasks]
    assert starts == sorted(starts)  # chronological


def test_open_ended_and_stage_based_tasks() -> None:
    paddy = {t.spec.id: t for t in plan(Crop.PADDY, date(2026, 7, 1))}
    assert paddy["paddy.bph"].start == date(2026, 7, 26) and paddy["paddy.bph"].end is None  # from then on
    assert paddy["paddy.weeds"].end == date(2026, 8, 10)  # first 40 days
    red_gram = plan(Crop.RED_GRAM, date(2026, 6, 25))
    assert red_gram[-1].spec.id == "red_gram.pod_borer" and red_gram[-1].start is None  # stage-based last


# --- HTTP ------------------------------------------------------------------------------------------

from rythu_weather.api.schemas import CalendarOut, ErrorBody  # noqa: E402
from rythu_weather.app.calendar_request import answer_calendar  # noqa: E402

TODAY = date(2026, 10, 27)


def test_calendar_answer_is_the_documented_shape_and_cacheable() -> None:
    res = answer_calendar("chilli", "2026-08-01", today=TODAY)
    assert res.status == 200
    out = CalendarOut.model_validate(res.body)
    assert (out.reference, out.reference_date) == ("transplanting", "2026-08-01")
    fertilizer = [t.start for t in out.tasks if t.kind == "fertilizer"]
    assert fertilizer == ["2026-08-01", "2026-08-31", "2026-09-30", "2026-10-30"]  # basal, 30/60/90 DAP
    assert res.headers["Cache-Control"] == "public, max-age=86400"


@pytest.mark.parametrize(
    ("crop", "when", "needle"),
    [
        ("banana", "2026-08-01", "crop must be one of"),
        (None, "2026-08-01", "crop must be one of"),
        ("paddy", "01-08-2026", "YYYY-MM-DD"),
        ("paddy", None, "YYYY-MM-DD"),
        ("paddy", "2025-01-01", "last 400 days"),
        ("paddy", "2027-01-15", "60 days ahead"),
    ],
)
def test_calendar_refuses_bad_input(crop, when, needle) -> None:
    res = answer_calendar(crop, when, today=TODAY)
    assert res.status == 400
    assert ErrorBody.model_validate(res.body).code == "bad_request"
    assert needle in res.body["error"]
    assert res.headers["Cache-Control"] == "no-store"
