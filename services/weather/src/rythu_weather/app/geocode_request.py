"""Transport-neutral handling of ``GET /v1/geocode?q=``: validate → search → shape → log.

Search runs on submit, never per keystroke (Nominatim policy); the geocoder caches and paces upstream.
The query itself is not logged — a village name is a location — only its length and the outcome.

* 200 ``{"results": [...]}`` — a source answered (an empty list really means "nothing found"),
* 400 ``bad_request`` — query missing, too short or too long,
* 503 ``upstream_unavailable`` — no source could be asked; the app says "try again", not "not found".
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict

from rythu_weather.adapters.geocode import Geocoder, GeocodeUnavailable
from rythu_weather.app.weather_request import HttpResult, base_headers
from rythu_weather.observability import log_event, request_context, resolve_request_id

_log = logging.getLogger(__name__)

MIN_QUERY, MAX_QUERY = 2, 60
# Real hits are stable for a day; an empty answer is not cached anywhere, so a retry can succeed.
_HIT_CACHE = "public, max-age=86400, stale-while-revalidate=604800"


async def answer_geocode(query: str | None, geocoder: Geocoder, *, inbound_request_id: str | None = None) -> HttpResult:
    request_id = resolve_request_id(inbound_request_id)
    with request_context(request_id):
        started = time.perf_counter()
        q = (query or "").strip()
        if not MIN_QUERY <= len(q) <= MAX_QUERY:
            result = HttpResult(
                400,
                {"error": f"q must be {MIN_QUERY}-{MAX_QUERY} characters", "code": "bad_request"},
                base_headers(request_id, cache_control="no-store"),
            )
            outcome, count = "bad_request", 0
        else:
            result, outcome, count = await _search(q, geocoder, request_id)
        log_event(
            _log, logging.INFO, "geocode.request", status=result.status, outcome=outcome, results=count,
            query_length=len(q), latency_ms=round((time.perf_counter() - started) * 1000, 1),
        )
        return result


async def _search(q: str, geocoder: Geocoder, request_id: str) -> tuple[HttpResult, str, int]:
    try:
        places = await geocoder.search(q)
    except GeocodeUnavailable as exc:
        log_event(_log, logging.WARNING, "geocode.unavailable", reason=str(exc))
        return _unavailable(request_id), "unavailable", 0
    except Exception:
        _log.exception("geocode.unhandled_error")  # a bug, not an outage: visible at ERROR
        return _unavailable(request_id), "error", 0
    body = {"results": [asdict(p) for p in places]}
    headers = base_headers(request_id, cache_control=_HIT_CACHE if places else "no-store")
    return HttpResult(200, body, headers), ("ok" if places else "empty"), len(places)


def _unavailable(request_id: str) -> HttpResult:
    body = {"error": "village search is unavailable right now", "code": "upstream_unavailable"}
    return HttpResult(503, body, base_headers(request_id, cache_control="no-store"))
