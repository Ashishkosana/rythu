"""FastAPI transport: the versioned HTTP API (``/v1``) plus health checks.

Routes are deliberately thin — they collect the inputs and delegate to the transport-neutral
:func:`~rythu_weather.app.weather_request.answer_weather`, exactly like the Lambda handler does.
No business rules live here. The Pydantic models in ``api.schemas`` document the responses for
OpenAPI (``/openapi.json``, interactive docs at ``/docs``); the golden test keeps them honest.

Run locally with ``python -m rythu_weather.app.local_server``. Hosting on Azure Functions comes
in S6 — this app is plain ASGI, so it is portable.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any

from fastapi import FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from rythu_weather.adapters.geocode import Geocoder
from rythu_weather.api.assistant import assistant_router
from rythu_weather.api.me import ApiError, accounts_router, error_response
from rythu_weather.api.schemas import CalendarOut, ErrorBody, GeocodeResults, Health, WeatherContract
from rythu_weather.app.accounts import utc_now
from rythu_weather.app.assistant import Assistant
from rythu_weather.app.calendar_request import answer_calendar
from rythu_weather.app.composition import (
    Accounts,
    Push,
    build_accounts,
    build_assistant,
    build_geocoder,
    build_provider,
    build_push,
)
from rythu_weather.app.geocode_request import MAX_QUERY, MIN_QUERY, answer_geocode
from rythu_weather.app.weather_request import answer_weather
from rythu_weather.domain.models import Crop, WaterSource, WeatherProvider

_CROPS = ", ".join(c.value for c in Crop)
_WATERS = ", ".join(w.value for w in WaterSource)

# Query parameters stay plain strings ON PURPOSE: validation (and its 400 {"error", "code"} body)
# is shared with the Lambda handler in answer_weather, so both transports reject the same inputs
# with the same answer. FastAPI's own 422 validation would make them differ.
Lat = Annotated[str | None, Query(description="Decimal degrees. Give lat and lon together, or neither "
                                              "(defaults to Bhupalpally). Telangana + border only.")]
Lon = Annotated[str | None, Query(description="Decimal degrees. See lat.")]
CropQ = Annotated[str | None, Query(description=f"One of: {_CROPS}. Omit for crop-independent reads only.")]
WaterQ = Annotated[str | None, Query(description=f"One of: {_WATERS}. Default rainfed.")]
PlaceQ = Annotated[
    str | None,
    Query(description=f"Village, town or mandal name ({MIN_QUERY}-{MAX_QUERY} characters). Search on submit, "
                      "not per keystroke."),
]
DateQ = Annotated[
    str | None,
    Query(description="YYYY-MM-DD: sowing date, or transplanting date for paddy and chilli."),
]
RequestId = Annotated[
    str | None,
    Header(alias="X-Request-Id", description="Optional correlation id, echoed back if safe ([A-Za-z0-9._-]{1,128})."),
]


_BUILD: Any = object()  # "build from settings" (accounts may legitimately be None: switched off)


def create_app(
    provider: WeatherProvider | None = None,
    geocoder: Geocoder | None = None,
    accounts: Accounts | None = _BUILD,
    clock: Callable[[], datetime] = utc_now,
    push: Push | None = _BUILD,
    assistant: Assistant | None = _BUILD,
) -> FastAPI:
    """Build the app. Pass fakes in tests; production builds them from settings, once."""
    weather_provider = provider or build_provider()
    place_search = geocoder or build_geocoder()
    device_accounts = build_accounts() if accounts is _BUILD else accounts
    web_push = build_push() if push is _BUILD else push
    ask_rythu = build_assistant() if assistant is _BUILD else assistant
    app = FastAPI(
        title="Rythu API",
        version="1",
        description="Honest weather + farming advice for Telangana farmers.",
        redoc_url=None,
    )

    async def weather(
        lat: Lat = None,
        lon: Lon = None,
        crop: CropQ = None,
        water: WaterQ = None,
        x_request_id: RequestId = None,
    ) -> JSONResponse:
        params = {k: v for k, v in {"lat": lat, "lon": lon, "crop": crop, "water": water}.items() if v is not None}
        result = await answer_weather(params, weather_provider, inbound_request_id=x_request_id)
        return JSONResponse(result.body, status_code=result.status, headers=result.headers)

    responses: dict[int | str, dict[str, object]] = {
        200: {"model": WeatherContract, "description": "Forecast + farming reads, or an honest degraded answer."},
        400: {"model": ErrorBody, "description": "Malformed request, or outside coverage (code=outside_coverage)."},
    }
    app.add_api_route(
        "/v1/weather", weather, methods=["GET"], tags=["weather"], response_model=None, responses=responses,
        summary="Forecast and farming reads for a point",
    )
    # Unversioned alias for the current web app (and the Lambda's path) until clients move to /v1.
    app.add_api_route("/weather", weather, methods=["GET"], response_model=None, include_in_schema=False)

    async def geocode(q: PlaceQ = None, x_request_id: RequestId = None) -> JSONResponse:
        result = await answer_geocode(q, place_search, inbound_request_id=x_request_id)
        return JSONResponse(result.body, status_code=result.status, headers=result.headers)

    app.add_api_route(
        "/v1/geocode", geocode, methods=["GET"], tags=["places"], response_model=None,
        responses={
            200: {"model": GeocodeResults, "description": "Matching places inside coverage (possibly none)."},
            400: {"model": ErrorBody, "description": "Query missing, too short or too long."},
            503: {"model": ErrorBody, "description": "No geocoding source could be asked (code=upstream_unavailable)."},
        },
        summary="Find a village by name (Telangana + border)",
    )

    async def calendar(crop: CropQ = None, date: DateQ = None, x_request_id: RequestId = None) -> JSONResponse:
        result = answer_calendar(crop, date, inbound_request_id=x_request_id)
        return JSONResponse(result.body, status_code=result.status, headers=result.headers)

    app.add_api_route(
        "/v1/calendar", calendar, methods=["GET"], tags=["calendar"], response_model=None,
        responses={
            200: {"model": CalendarOut, "description": "The crop's tasks, dated (stage-based ones last)."},
            400: {"model": ErrorBody, "description": "Unknown crop, or a malformed / out-of-range date."},
        },
        summary="My-Field crop calendar from a sowing or transplanting date",
    )

    app.include_router(accounts_router(device_accounts, clock, web_push))
    app.include_router(assistant_router(device_accounts, ask_rythu, weather_provider, clock))

    async def on_api_error(_request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, ApiError)
        return error_response(exc)

    async def on_invalid_request(_request: Request, exc: Exception) -> JSONResponse:
        # Same 400 {"error", "code"} shape as every other refusal — never FastAPI's 422 — and only the
        # field and the reason, never the submitted value.
        assert isinstance(exc, RequestValidationError)
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(part) for part in first.get("loc", ()) if part != "body")
        message = f"{where}: {first.get('msg', 'invalid')}" if where else "invalid request"
        return error_response(ApiError(400, "bad_request", message))

    app.add_exception_handler(ApiError, on_api_error)
    app.add_exception_handler(RequestValidationError, on_invalid_request)

    @app.get("/healthz", response_model=Health, tags=["ops"], summary="Liveness: the process is up")
    async def healthz() -> JSONResponse:
        # No dependencies checked on purpose: liveness must not fail because Open-Meteo is down.
        return JSONResponse({"status": "ok"}, headers={"Cache-Control": "no-store"})

    # The web app is static (S8) and calls the API from the browser, cross-origin. Every endpoint is
    # public and nothing rides on cookies (future auth is a bearer token), so any origin may read.
    # A plain GET carries no custom header, so it needs no preflight — one round trip less on 3G;
    # the request id is exposed so the app can quote it when something fails.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "PUT", "POST", "DELETE"],  # a preflight for the /v1/me writes
        allow_headers=["Authorization", "Content-Type", "If-Match", "If-None-Match", "X-Request-Id"],
        expose_headers=["ETag", "X-Request-Id"],
        max_age=7200,  # Chromium's ceiling for caching a preflight
    )
    _document_only_real_responses(app)
    return app


def _document_only_real_responses(app: FastAPI) -> None:
    """Drop FastAPI's automatic 422 from the OpenAPI document.

    Every parameter is an optional string and validation answers 400 (shared core), so 422 can
    never be returned. Documenting it would put an impossible error into the generated client types.
    """
    original = app.openapi

    def openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            schema = original()
            for path in schema.get("paths", {}).values():
                for op in path.values():
                    op.get("responses", {}).pop("422", None)
            schemas = schema.get("components", {}).get("schemas", {})
            for name in ("HTTPValidationError", "ValidationError"):
                schemas.pop(name, None)
            app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = openapi  # type: ignore[method-assign]
