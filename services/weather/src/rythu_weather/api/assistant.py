"""``POST /v1/assistant/ask`` — Ask Rythu (S17).

Who: a device token (the same anonymous device account as profile sync; the user id comes only from
the verified token). How much: ``per_device_per_day`` answered questions per phone and ``daily_cap``
for everyone, counted in IST days; a failed answer costs the farmer nothing. Off: the kill switch
(``RYTHU_ASSISTANT_ENABLED``) or a missing key → 503 ``assistant_off``, and the app shows the Kisan
Call Centre. The question text is never logged — only that one was answered, how, and what it cost.

No ``from __future__ import annotations`` here: FastAPI must resolve the route's ``User`` dependency,
which is defined inside the router function, at import time.
"""

import logging
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta
from typing import Annotated, Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from rythu_weather.api.me import ApiError, bearer_user, err_doc, pseudonym
from rythu_weather.api.schemas import AskIn, AskOut, AskSourceOut, HelplineOut
from rythu_weather.app.assistant import KISAN_CALL_CENTRE, Assistant, AssistantUnavailable
from rythu_weather.app.composition import Accounts
from rythu_weather.app.weather_request import answer_weather
from rythu_weather.domain.models import WeatherProvider
from rythu_weather.observability import log_event

_log = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")
HELPLINE = HelplineOut(display=KISAN_CALL_CENTRE, tel="tel:" + KISAN_CALL_CENTRE.replace("-", ""))


def _until_midnight_ist(now: datetime) -> int:
    local = now.astimezone(IST)
    midnight = (local + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(60, int((midnight - local).total_seconds()))


async def todays_reads(body: AskIn, provider: WeatherProvider) -> Sequence[Mapping[str, Any]] | None:
    """The farming reads that fire today for the farmer's village + crop; None if unknown."""
    if body.lat is None or body.lon is None:
        return None
    params = {"lat": str(body.lat), "lon": str(body.lon), "water": body.water.value}
    if body.crop is not None:
        params["crop"] = body.crop.value
    result = await answer_weather(params, provider)
    if result.status != 200 or result.body.get("degraded"):
        return None  # outside coverage or upstream down: say "not available", never guess
    return [r for r in result.body.get("farming_read", []) if r.get("triggered")]


def assistant_router(
    accounts: Accounts | None, assistant: Assistant | None, provider: WeatherProvider,
    clock: Callable[[], datetime],
) -> APIRouter:
    router = APIRouter(tags=["assistant"])
    User = Annotated[str, Depends(bearer_user(accounts, clock))]

    @router.post(
        "/v1/assistant/ask", response_model=AskOut, summary="Ask Rythu: an answer only from Rythu's checked content",
        responses={
            401: err_doc("No or bad device token."),
            429: err_doc("Today's questions are used up (this phone, or everyone)."),
            503: err_doc("Switched off (code=assistant_off), or the model can't answer right now."),
        },
    )
    async def ask(body: AskIn, user: User) -> JSONResponse:
        if assistant is None:
            raise ApiError(503, "assistant_off", "Ask Rythu is switched off; call the Kisan Call Centre")
        assert accounts is not None  # a verified user implies accounts
        now = clock()
        day = now.astimezone(IST).date().isoformat()
        try:
            mine, everyone = await accounts.users.assistant_usage(user, day)
        except Exception as exc:
            log_event(_log, logging.ERROR, "assistant.quota_failed", error=repr(exc))
            raise ApiError(503, "unavailable", "please try again shortly") from exc
        wait = {"Retry-After": str(_until_midnight_ist(now))}
        if mine >= assistant.per_device_per_day:
            raise ApiError(429, "rate_limited", "today's questions are used up; ask again tomorrow", wait)
        if everyone >= assistant.daily_cap:
            raise ApiError(429, "rate_limited", "Ask Rythu has answered all it can today; ask again tomorrow", wait)

        started = time.perf_counter()
        reads = await todays_reads(body, provider)
        try:
            answer = await assistant.ask(body.question.strip(), body.lang, crop=body.crop, reads=reads)
        except AssistantUnavailable as exc:
            raise ApiError(503, "unavailable", "Ask Rythu can't answer right now; try again shortly") from exc
        try:
            await accounts.users.record_assistant_use(user, day)
        except Exception as exc:  # the farmer has the answer; a lost count is not their problem
            log_event(_log, logging.WARNING, "assistant.count_failed", error=repr(exc))
        log_event(
            _log, logging.INFO, "assistant.answered", user=pseudonym(user), covered=answer.covered,
            sources=len(answer.sources), weather=answer.cites_weather, model=answer.model,
            cost_usd=answer.cost_usd, latency_ms=round((time.perf_counter() - started) * 1000, 1),
        )
        out = AskOut(
            covered=answer.covered,
            answer=answer.answer,
            sources=[AskSourceOut(id=s.id, title=s.title, url=s.source, needs_verification=s.needs_verification)
                     for s in answer.sources],
            used_todays_weather=answer.cites_weather,
            remaining_today=max(0, assistant.per_device_per_day - mine - 1),
            helpline=HELPLINE,
        )
        return JSONResponse(out.model_dump(mode="json"), headers={"Cache-Control": "no-store"})

    return router
