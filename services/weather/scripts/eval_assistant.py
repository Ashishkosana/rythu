"""Live eval for Ask Rythu: the real prompt and model on evals/ask_rythu_cases.json. COSTS MONEY.

    RYTHU_ANTHROPIC_API_KEY=... uv run python scripts/eval_assistant.py              # plan + estimate only
    RYTHU_ANTHROPIC_API_KEY=... uv run python scripts/eval_assistant.py --yes-spend  # run it

Same entry point as production (``Assistant`` + ``ClaudeAnswerModel``: same prompt, schema, cache,
effort). Graded by ``evals/ask_rythu_grade.py`` — deterministic checks, no judge model. Writes
``evals/runs/<UTC time>/``: ``results.jsonl`` (one graded row per case and rep, with tokens, cost,
served model, latency; a reply cut off at max_tokens is marked ``truncated``, a refusal ``refusal``),
``errors.jsonl`` (attempts that produced nothing to grade — never scored as failures) and
``summary.json``. Run sequentially so the cached corpus is reused.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "evals"))

from ask_rythu_grade import cases, grade  # noqa: E402

from rythu_weather.adapters.claude import ClaudeAnswerModel  # noqa: E402
from rythu_weather.app.assistant import (  # noqa: E402
    WEATHER_CONTEXT_ID,
    Assistant,
    AssistantUnavailable,
    ModelReply,
    cost_usd,
    load_corpus,
)
from rythu_weather.app.settings import DEFAULT_ASSISTANT_MODEL  # noqa: E402
from rythu_weather.domain.models import Crop  # noqa: E402


class Recording:
    """Keeps the raw reply (tokens, stop reason, served model) that ``Assistant.ask`` digests."""

    def __init__(self, inner: ClaudeAnswerModel) -> None:
        self.inner = inner
        self.last: ModelReply | None = None

    async def complete(self, system: str, user: str, schema: dict[str, Any]) -> ModelReply:
        self.last = await self.inner.complete(system, user, schema)
        return self.last


async def run(args: argparse.Namespace) -> int:
    selected = [c for c in cases() if not args.only or c["id"] in args.only.split(",")]
    calls = len(selected) * args.reps
    print(f"{calls} calls: {len(selected)} cases × {args.reps} rep(s) on {args.model}, effort {args.effort}.")
    print("Rough cost: the first call writes the cached corpus (~25k tokens); later calls read it. With "
          "Claude Opus 5.5 at low effort expect a few US cents per call — check summary.json for the real number.")
    if not args.yes_spend:
        print("Nothing sent. Add --yes-spend to run.")
        return 2
    key = os.environ.get("RYTHU_ANTHROPIC_API_KEY", "").strip()
    if not key:
        print("RYTHU_ANTHROPIC_API_KEY is not set.", file=sys.stderr)
        return 2

    model = Recording(ClaudeAnswerModel(key, args.model, args.effort))
    bot = Assistant(model, load_corpus(), per_device_per_day=0, daily_cap=0)
    out = HERE / "evals" / "runs" / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out.mkdir(parents=True)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for rep in range(args.reps):
        for case in selected:
            model.last = None
            started = time.perf_counter()
            try:
                answer = await bot.ask(case["question"], case["lang"],
                                       crop=Crop(case["crop"]) if case.get("crop") else None, reads=case.get("reads"))
            except AssistantUnavailable as exc:
                errors.append({"case": case["id"], "rep": rep, "class": type(exc.__cause__).__name__})
                continue
            raw = model.last
            assert raw is not None
            ids = [s.id for s in answer.sources] + ([WEATHER_CONTEXT_ID] if answer.cites_weather else [])
            g = grade(case, answer.covered, answer.answer, ids)
            rows.append({
                "case": case["id"], "rep": rep, "passed": g.passed, "failed_checks": list(g.failed_checks),
                "expect_covered": case["expect_covered"], "covered": answer.covered, "source_ids": ids,
                "answer": answer.answer, "stop_reason": raw.stop_reason,
                "status": "truncated" if raw.stop_reason == "max_tokens" else
                          "refusal" if raw.stop_reason == "refusal" else "ok",
                "served_model": raw.model, "model_mismatch": raw.model != args.model,
                "usage": {"input": raw.input_tokens, "output": raw.output_tokens,
                          "cache_read": raw.cache_read_tokens, "cache_write": raw.cache_write_tokens},
                "cost_usd": cost_usd(raw), "latency_s": round(time.perf_counter() - started, 2),
            })
            mark = "PASS" if g.passed else "FAIL " + "; ".join(g.failed_checks)
            print(f"[{rep}] {case['id']:<22} {mark}")

    (out / "results.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf-8")
    (out / "errors.jsonl").write_text("".join(json.dumps(e) + "\n" for e in errors), "utf-8")
    per_rep = [statistics.fmean(r["passed"] for r in rows if r["rep"] == k) for k in range(args.reps)
               if any(r["rep"] == k for r in rows)]
    costs = [r["cost_usd"] for r in rows if r["cost_usd"] is not None]
    usage = [r["usage"] for r in rows]
    summary = {
        "model": args.model, "effort": args.effort, "cases": len(selected), "reps": args.reps,
        "scored": len(rows), "errors": len(errors),
        "pass_rate": statistics.fmean(r["passed"] for r in rows) if rows else None,
        "pass_rate_per_rep": per_rep,
        "pass_rate_sd": statistics.stdev(per_rep) if len(per_rep) > 1 else None,
        "by_direction": {str(d): statistics.fmean(r["passed"] for r in rows if r["expect_covered"] is d)
                         for d in (True, False, None) if any(r["expect_covered"] is d for r in rows)},
        "truncated": sum(r["status"] == "truncated" for r in rows),
        "refusals": sum(r["status"] == "refusal" for r in rows),
        "model_mismatches": sum(r["model_mismatch"] for r in rows),
        "cost_usd_total": round(sum(costs), 4),
        "cost_usd_per_answer": round(statistics.fmean(costs), 5) if costs else None,
        "cache_read_share": (sum(u["cache_read"] for u in usage) /
                             max(1, sum(u["input"] + u["cache_read"] + u["cache_write"] for u in usage))),
        "mean_latency_s": round(statistics.fmean(r["latency_s"] for r in rows), 2) if rows else None,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), "utf-8")
    print(json.dumps(summary, indent=2))
    print(f"→ {out}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--yes-spend", action="store_true", help="actually call the model (costs money)")
    p.add_argument("--model", default=DEFAULT_ASSISTANT_MODEL)
    p.add_argument("--effort", default="low", choices=["low", "medium", "high"])
    p.add_argument("--reps", type=int, default=1)
    p.add_argument("--only", default="", help="comma-separated case ids")
    return asyncio.run(run(p.parse_args()))


if __name__ == "__main__":
    sys.exit(main())
