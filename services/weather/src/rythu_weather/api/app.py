"""FastAPI transport: the versioned HTTP API (``/v1``) plus health checks.

Routes are deliberately thin — they collect the inputs and delegate to the transport-neutral
:func:`~rythu_weather.app.weather_request.answer_weather`, exactly like the Lambda handler does.
No business rules live here. The Pydantic models in ``api.schemas`` document the responses for
OpenAPI (``/openapi.json``, interactive docs at ``/docs``); the golden test keeps them honest.

Run locally with ``python -m rythu_weather.app.local_server``. Hosting on Azure Functions comes
in S6 — this app is plain ASGI, so it is portable.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import FastAPI, Header, Query
from fastapi.responses import JSONResponse

from rythu_weather.api.schemas import ErrorBody, Health, WeatherContract
from rythu_weather.app.composition import build_provider
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
RequestId = Annotated[
    str | None,
    Header(alias="X-Request-Id", description="Optional correlation id, echoed back if safe ([A-Za-z0-9._-]{1,128})."),
]


def create_app(provider: WeatherProvider | None = None) -> FastAPI:
    """Build the app. Pass a provider in tests; production builds one from settings, once."""
    weather_provider = provider or build_provider()
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

    @app.get("/healthz", response_model=Health, tags=["ops"], summary="Liveness: the process is up")
    async def healthz() -> JSONResponse:
        # No dependencies checked on purpose: liveness must not fail because Open-Meteo is down.
        return JSONResponse({"status": "ok"}, headers={"Cache-Control": "no-store"})

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
