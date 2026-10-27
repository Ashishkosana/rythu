"""Deterministic grading for the Ask Rythu eval set (no judge model: every check is a fact a script
can verify). Used offline by tests/test_assistant_eval.py and live by scripts/eval_assistant.py."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CASES_FILE = Path(__file__).with_name("ask_rythu_cases.json")
_TELUGU = re.compile(r"[ఀ-౿]")
_LETTER = re.compile(r"[^\W\d_]")


def cases() -> list[dict[str, Any]]:
    return list(json.loads(CASES_FILE.read_text("utf-8"))["cases"])


@dataclass(frozen=True, slots=True)
class Grade:
    passed: bool
    failed_checks: tuple[str, ...]


def telugu_share(text: str) -> float:
    letters = _LETTER.findall(text)
    return sum(1 for c in letters if _TELUGU.match(c)) / len(letters) if letters else 0.0


def grade(case: dict[str, Any], covered: bool, answer: str, source_ids: list[str]) -> Grade:
    """``covered``/``answer``/``source_ids`` are what the farmer would see (after the server's checks)."""
    failed: list[str] = []
    expected = case["expect_covered"]
    if expected is not None and covered != expected:
        failed.append(f"covered={covered}, expected {expected}")
    if covered and case["ids_any"] and not set(source_ids) & set(case["ids_any"]):
        failed.append(f"cited {source_ids}, expected one of {case['ids_any']}")
    low = answer.lower()
    if case["contains_any"] and not any(s.lower() in low for s in case["contains_any"]):
        failed.append(f"mentions none of {case['contains_any']}")
    hits = [s for s in case["not_contains"] if s.lower() in low]
    if hits:
        failed.append(f"must not say {hits}")
    share = telugu_share(answer)
    if case["lang"] == "te" and share < 0.5:
        failed.append(f"Telugu share {share:.2f} < 0.5")
    if case["lang"] == "en" and share > 0.1:
        failed.append(f"answered in Telugu (share {share:.2f})")
    return Grade(not failed, tuple(failed))
