"""Transport-neutral handling of ``GET /v1/calendar?crop=&date=``: validate → plan → shape → log.

The answer depends only on (crop, date) and the deployed content, so it is public and cacheable; the
farmer's own fields are private and live in their profile (``/v1/me/profile``), not here.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from rythu_weather.app.weather_request import HttpResult, base_headers
from rythu_weather.domain.calendar import CALENDARS, ScheduledTask, plan
from rythu_weather.domain.models import Crop
from rythu_weather.observability import log_event, request_context, resolve_request_id

_log = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")
# A season's tasks run ~5 months; allow last year's crop and a planned sowing, not arbitrary dates.
MAX_PAST = timedelta(days=400)
MAX_AHEAD = timedelta(days=60)
_CACHE = "public, max-age=86400"


def _iso(d: date | None) -> str | None:
    return d.isoformat() if d is not None else None


def _task(t: ScheduledTask) -> dict[str, Any]:
    s = t.spec
    return {
        "id": s.id,
        "kind": s.kind.value,
        "start": _iso(t.start),
        "end": _iso(t.end),
        "start_day": s.start_day,
        "end_day": s.end_day,
        "title_te": s.title_te,
        "title_en": s.title_en,
        "detail_te": s.detail_te,
        "detail_en": s.detail_en,
        "stage_te": s.stage_te or None,
        "stage_en": s.stage_en or None,
        "source": s.source,
        "needs_verification": s.needs_verification,
    }


def reference_date_problem(value: date, today: date) -> str | None:
    """Why a sowing/transplanting date is refused, or None. Shared with the profile's fields."""
    if value < today - MAX_PAST:
        return f"must be within the last {MAX_PAST.days} days"
    if value > today + MAX_AHEAD:
        return f"must be at most {MAX_AHEAD.days} days ahead"
    return None


def answer_calendar(
    crop: str | None, when: str | None, *, today: date | None = None, inbound_request_id: str | None = None
) -> HttpResult:
    request_id = resolve_request_id(inbound_request_id)
    with request_context(request_id):
        today = today or datetime.now(IST).date()
        problem: str | None = None
        try:
            crop_ = Crop(crop or "")
        except ValueError:
            problem = f"crop must be one of: {', '.join(c.value for c in Crop)}"
        try:
            ref = date.fromisoformat(when or "")
        except ValueError:
            problem = problem or "date must be YYYY-MM-DD"
        else:
            problem = problem or (f"date {p}" if (p := reference_date_problem(ref, today)) else None)
        if problem is not None:
            log_event(_log, logging.INFO, "calendar.request", status=400, outcome="bad_request")
            error = {"error": problem, "code": "bad_request"}
            return HttpResult(400, error, base_headers(request_id, cache_control="no-store"))
        body = {
            "crop": crop_.value,
            "reference": CALENDARS[crop_].reference.value,
            "reference_date": ref.isoformat(),
            "tasks": [_task(t) for t in plan(crop_, ref)],
        }
        log_event(_log, logging.INFO, "calendar.request", status=200, outcome="ok", crop=crop_.value)
        return HttpResult(200, body, base_headers(request_id, cache_control=_CACHE))
