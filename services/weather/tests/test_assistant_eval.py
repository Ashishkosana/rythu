"""The Ask Rythu eval set and its grader, checked offline (no model, no cost):

* every case is well-formed and cites ids that exist, so the set cannot rot as content changes;
* oracle: each case's reference answer, put through the server's real post-processing, PASSES —
  a case no correct answer can pass is a broken case, not a hard one;
* null baseline: the honest "not covered" fallback FAILS every case that expects an answer —
  otherwise the grader is too lenient to mean anything;
* a wrong-but-plausible answer fails.
"""

from __future__ import annotations

import json

import pytest
from ask_rythu_grade import cases, grade, telugu_share

from rythu_weather.app.assistant import WEATHER_CONTEXT_ID, ModelReply, interpret, load_corpus

BY_ID = {i.id: i for i in load_corpus()}
CASES = cases()


def _seen(case: dict, payload: dict) -> tuple[bool, str, list[str]]:
    """What the farmer would see for this model payload — through the real server-side checks."""
    reply = ModelReply(json.dumps(payload, ensure_ascii=False), "end_turn", "claude-opus-5-5")
    a = interpret(reply, BY_ID, case["lang"], had_reads=bool(case.get("reads")))
    ids = [s.id for s in a.sources] + ([WEATHER_CONTEXT_ID] if a.cites_weather else [])
    return a.covered, a.answer, ids


def test_cases_are_well_formed_and_cite_real_content() -> None:
    assert len({c["id"] for c in CASES}) == len(CASES)
    for c in CASES:
        assert c["lang"] in ("te", "en") and 3 <= len(c["question"]) <= 300
        for i in [*c["ids_any"], *c["reference"]["source_ids"]]:
            assert i in BY_ID or i == WEATHER_CONTEXT_ID, f"{c['id']}: unknown id {i}"
    directions = [c["expect_covered"] for c in CASES]
    assert directions.count(True) >= 8 and directions.count(False) >= 4  # both directions, not one-sided
    assert sum(c["lang"] == "te" for c in CASES) >= len(CASES) // 2  # the farmers' language leads


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_oracle_the_reference_answer_passes(case: dict) -> None:
    g = grade(case, *_seen(case, case["reference"]))
    assert g.passed, g.failed_checks


@pytest.mark.parametrize("case", [c for c in CASES if c["expect_covered"]], ids=lambda c: c["id"])
def test_null_baseline_the_fallback_fails_every_answerable_case(case: dict) -> None:
    null = {"covered": False, "answer": "Rythuలో దీనిపై సమాచారం లేదు. 1800-180-1551కు ఫోన్ చేయండి.", "source_ids": []}
    assert not grade(case, *_seen(case, null)).passed


def test_a_wrong_but_plausible_answer_fails() -> None:
    urea = next(c for c in CASES if c["id"] == "urea-mrp-en")
    wrong = {"covered": True, "answer": "A bag of urea costs about ₹300.", "source_ids": ["fertilizer.bag_prices"]}
    assert not grade(urea, *_seen(urea, wrong)).passed
    brand = next(c for c in CASES if c["id"] == "thrips-brand-en")
    named = {"covered": True, "answer": "Use Regent for thrips.", "source_ids": ["pest.chilli_thrips"]}
    assert "must not say" in grade(brand, *_seen(brand, named)).failed_checks[0]
    te = next(c for c in CASES if c["id"] == "redgram-sow-te")
    english = {"covered": True, "answer": "Sow red gram in June–July.", "source_ids": ["crop.red_gram"]}
    assert not grade(te, *_seen(te, english)).passed  # asked in Telugu, answered in English


def test_telugu_share() -> None:
    assert telugu_share("కంది జూన్‌లో") > 0.9 and telugu_share("Sow in June") == 0
    assert 0.3 < telugu_share("AEO దగ్గర చూడండి") < 0.9
