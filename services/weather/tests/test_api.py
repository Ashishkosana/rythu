"""The FastAPI transport must answer exactly like the Lambda handler (they share answer_weather)."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest

from builders import days_from, forecast, hours_from
from rythu_weather.adapters.fake import FailingProvider, FakeProvider
from rythu_weather.api.app import create_app
from rythu_weather.app.handler import handle_request
from rythu_weather.domain.models import Forecast, GeoPoint

_NOW = datetime.now(ZoneInfo("Asia/Kolkata")).replace(minute=0, second=0, microsecond=0)
_FC = forecast(
    _NOW - timedelta(minutes=10),
    hourly=hours_from(_NOW, 48, pp=75, precip=1.2, code=61, wind=18.0),
    daily=days_from(_NOW.date(), 7, pp_max=80, precip_sum=25.0, code=61),
)


class ExplodingProvider:
    async def fetch(self, point: GeoPoint) -> Forecast:
        raise ZeroDivisionError("bug in a rule")


async def _api(provider, path: str, params: dict[str, str], headers: dict[str, str] | None = None):
    transport = httpx.ASGITransport(app=create_app(provider))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path, params=params, headers=headers or {})


CASES = [
    ("happy chilli", FakeProvider(_FC), {"crop": "chilli"}),
    ("pin + water", FakeProvider(_FC), {"lat": "18.33", "lon": "79.88", "crop": "paddy", "water": "borewell"}),
    ("no params", FakeProvider(_FC), {}),
    ("empty crop = none", FakeProvider(_FC), {"crop": ""}),
    ("unknown crop", FakeProvider(_FC), {"crop": "banana"}),
    ("half coords", FakeProvider(_FC), {"lat": "18.4"}),
    ("not a number", FakeProvider(_FC), {"lat": "abc", "lon": "1"}),
    ("outside coverage", FakeProvider(_FC), {"lat": "13.08", "lon": "80.27"}),
    ("upstream down", FailingProvider(), {"crop": "cotton"}),
    ("bug below", ExplodingProvider(), {"crop": "maize"}),
]


def _comparable(body: dict) -> dict:
    """A degraded body is stamped with the wall-clock time of the call; drop only those two fields."""
    if body.get("degraded"):
        return {k: v for k, v in body.items() if k not in ("generated_at", "upstream_fetched_at")}
    return body


@pytest.mark.parametrize(("name", "provider", "params"), CASES, ids=[c[0] for c in CASES])
@pytest.mark.parametrize("path", ["/v1/weather", "/weather"])
async def test_fastapi_answers_exactly_like_the_lambda(name, provider, params, path):
    rid = "parity-" + re.sub(r"[^A-Za-z0-9._-]", "-", name)  # a safe id, so both sides echo it
    api = await _api(provider, path, params, {"X-Request-Id": rid})
    lam = await handle_request({"queryStringParameters": params, "headers": {"x-request-id": rid}}, provider)

    assert api.status_code == lam["statusCode"]
    assert _comparable(api.json()) == _comparable(json.loads(lam["body"]))
    for header in ("Content-Type", "Cache-Control", "Access-Control-Allow-Origin", "X-Request-Id"):
        assert api.headers[header] == lam["headers"][header], header


async def test_healthz_is_dependency_free():
    # Upstream is down, yet the process is alive: liveness must say so.
    resp = await _api(FailingProvider(), "/healthz", {})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert resp.headers["Cache-Control"] == "no-store"


async def test_openapi_documents_v1_and_hides_the_legacy_alias():
    doc = (await _api(FakeProvider(_FC), "/openapi.json", {})).json()
    assert set(doc["paths"]) == {
        "/v1/weather", "/v1/geocode", "/v1/calendar", "/v1/devices", "/v1/sessions", "/v1/me/profile", "/v1/me",
        "/healthz",
    }
    op = doc["paths"]["/v1/weather"]["get"]
    assert {p["name"] for p in op["parameters"]} == {"lat", "lon", "crop", "water", "X-Request-Id"}
    ok = op["responses"]["200"]["content"]["application/json"]["schema"]
    assert ok["$ref"].endswith("/WeatherContract")
    bad = op["responses"]["400"]["content"]["application/json"]["schema"]
    assert bad["$ref"].endswith("/ErrorBody")
    schemas = doc["components"]["schemas"]
    assert set(schemas["Severity"]["enum"]) == {"info", "caution", "act"}  # enums reach the TS types in S4
    assert "farming_read" in schemas["WeatherContract"]["properties"]


def test_lambda_does_not_import_fastapi_or_pydantic():
    """build_lambda.sh bundles only httpx; the Lambda path must stay free of the API stack."""
    code = (
        "import sys, rythu_weather.app.handler; "
        "print([m for m in ('fastapi', 'pydantic', 'starlette') if m in sys.modules])"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "[]"


async def test_openapi_documents_only_responses_that_can_happen():
    """Validation answers 400 (shared core); FastAPI's automatic 422 can never occur, so it isn't documented."""
    doc = (await _api(FakeProvider(_FC), "/openapi.json", {})).json()
    assert set(doc["paths"]["/v1/weather"]["get"]["responses"]) == {"200", "400"}
    assert "HTTPValidationError" not in doc["components"]["schemas"]
    # …and garbage input really does get the documented 400, not a 422.
    resp = await _api(FakeProvider(_FC), "/v1/weather", {"lat": "x", "lon": "y", "crop": "?" * 500})
    assert resp.status_code == 400


async def test_browser_can_call_cross_origin_without_a_preflight_and_read_the_request_id():
    transport = httpx.ASGITransport(app=create_app(FakeProvider(_FC)))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/v1/weather", params={"crop": "chilli"}, headers={"Origin": "https://rythu.example"})
        assert resp.status_code == 200
        assert resp.headers["Access-Control-Allow-Origin"] == "*"
        assert "x-request-id" in resp.headers["Access-Control-Expose-Headers"].lower()

        pre = await client.options(
            "/v1/weather",
            headers={
                "Origin": "https://rythu.example",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "x-request-id",
            },
        )
        assert pre.status_code == 200
        assert pre.headers["Access-Control-Max-Age"] == "7200"
