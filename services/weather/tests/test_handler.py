from __future__ import annotations

import json
import logging

import pytest

from builders import at, days_from, forecast, hours_from
from rythu_weather.adapters.fake import FailingProvider, FakeProvider
from rythu_weather.app.handler import build_provider, handle_request
from rythu_weather.app.settings import Settings
from rythu_weather.domain.models import Forecast, GeoPoint

_FC = forecast(
    at(2026, 7, 15, 8),
    hourly=hours_from(at(2026, 7, 15, 0), 48, wind=18.0),
    daily=days_from(at(2026, 7, 15).date(), 7),
)


def _body(resp):
    return json.loads(resp["body"])


async def test_happy_path_returns_200_contract():
    resp = await handle_request({"queryStringParameters": {"crop": "cotton", "water": "rainfed"}}, FakeProvider(_FC))
    assert resp["statusCode"] == 200
    body = _body(resp)
    assert "reliability" in body and body["reliability"]["show_confidence_rating"] is False
    assert isinstance(body["farming_read"], list)
    assert body["farmer_context"] == {"crop": "cotton", "water_source": "rainfed"}


async def test_defaults_to_bhupalpally_and_rainfed_when_no_params():
    resp = await handle_request({}, FakeProvider(_FC))
    assert resp["statusCode"] == 200
    assert _body(resp)["farmer_context"]["water_source"] == "rainfed"


async def test_provider_failure_returns_degraded_200():
    resp = await handle_request({"queryStringParameters": {"crop": "cotton"}}, FailingProvider())
    assert resp["statusCode"] == 200
    body = _body(resp)
    assert body["degraded"] is True
    assert body["farming_read"] == []
    assert body["reliability"]["disclaimer_en"]  # honesty framing still present
    assert body["reliability"]["source_stamp_en"].startswith("No live forecast")


async def test_unknown_crop_is_400():
    resp = await handle_request({"queryStringParameters": {"crop": "banana"}}, FakeProvider(_FC))
    assert resp["statusCode"] == 400
    assert "banana" in _body(resp)["error"]


async def test_bad_coordinates_are_400():
    resp = await handle_request({"queryStringParameters": {"lat": "abc", "lon": "1"}}, FakeProvider(_FC))
    assert resp["statusCode"] == 400
    resp2 = await handle_request({"queryStringParameters": {"lat": "18.4"}}, FakeProvider(_FC))
    assert resp2["statusCode"] == 400  # lon missing


async def test_out_of_range_coordinates_are_400():
    resp = await handle_request({"queryStringParameters": {"lat": "200", "lon": "0"}}, FakeProvider(_FC))
    assert resp["statusCode"] == 400


# --- observability & response hygiene (S1) ------------------------------------------------


class ExplodingProvider:
    """A bug (not an outage) somewhere below the handler."""

    async def fetch(self, point: GeoPoint) -> Forecast:
        raise ZeroDivisionError("bug in a rule")


def _events(caplog, name):
    return [r for r in caplog.records if r.getMessage() == name]


@pytest.fixture
def info_logs(caplog):
    caplog.set_level(logging.INFO, logger="rythu_weather")
    return caplog


async def test_every_response_carries_a_request_id():
    for provider in (FakeProvider(_FC), FailingProvider()):
        resp = await handle_request({"queryStringParameters": {"crop": "cotton"}}, provider)
        assert len(resp["headers"]["X-Request-Id"]) == 32
    bad = await handle_request({"queryStringParameters": {"crop": "banana"}}, FakeProvider(_FC))
    assert bad["headers"]["X-Request-Id"]


async def test_safe_caller_request_id_is_propagated_case_insensitively():
    event = {"queryStringParameters": {}, "headers": {"X-Request-ID": "next-abc.123"}}
    resp = await handle_request(event, FakeProvider(_FC))
    assert resp["headers"]["X-Request-Id"] == "next-abc.123"


async def test_unsafe_caller_request_id_is_replaced():
    event = {"queryStringParameters": {}, "headers": {"x-request-id": "evil\ninjected log line"}}
    resp = await handle_request(event, FakeProvider(_FC))
    assert "\n" not in resp["headers"]["X-Request-Id"]
    assert resp["headers"]["X-Request-Id"] != "evil\ninjected log line"


async def test_api_gateway_request_id_is_used_when_no_header():
    event = {"queryStringParameters": {}, "requestContext": {"requestId": "apigw-Xyz_1"}}
    resp = await handle_request(event, FakeProvider(_FC))
    assert resp["headers"]["X-Request-Id"] == "apigw-Xyz_1"


async def test_degraded_body_does_not_leak_internal_reason_and_is_not_cacheable(info_logs):
    resp = await handle_request({"queryStringParameters": {}}, FailingProvider("upstream https://secret.internal 500"))
    body = _body(resp)
    assert body["degraded"] is True
    assert "reason" not in body
    assert "secret.internal" not in resp["body"]
    assert resp["headers"]["Cache-Control"] == "no-store"
    # …but the reason is logged, tied to the request id.
    [degraded] = _events(info_logs, "weather.degraded")
    assert degraded.levelno == logging.WARNING
    assert "secret.internal" in degraded.fields["reason"]


async def test_successful_forecast_stays_cacheable():
    resp = await handle_request({"queryStringParameters": {}}, FakeProvider(_FC))
    assert resp["headers"]["Cache-Control"] == "public, max-age=300"


async def test_unexpected_exception_degrades_for_the_farmer_but_logs_error_with_traceback(info_logs):
    resp = await handle_request({"queryStringParameters": {"crop": "chilli"}}, ExplodingProvider())
    assert resp["statusCode"] == 200
    assert _body(resp)["degraded"] is True
    assert "bug in a rule" not in resp["body"]
    [err] = _events(info_logs, "weather.unhandled_error")
    assert err.levelno == logging.ERROR
    assert err.exc_info is not None and err.exc_info[0] is ZeroDivisionError
    [summary] = _events(info_logs, "weather.request")
    assert summary.fields["outcome"] == "error"


async def test_one_summary_line_per_request_with_coarse_location_only(info_logs):
    event = {"queryStringParameters": {"lat": "18.4567", "lon": "79.8765", "crop": "cotton"}}
    await handle_request(event, FakeProvider(_FC))
    [summary] = _events(info_logs, "weather.request")
    f = summary.fields
    assert f["status"] == 200 and f["outcome"] == "ok" and f["crop"] == "cotton" and f["water"] == "rainfed"
    assert f["cell"] == "18.5,79.9"  # ~11 km — never the farmer's exact pin
    assert isinstance(f["latency_ms"], float) and isinstance(f["reads"], int)
    assert "18.4567" not in " ".join(r.getMessage() + str(getattr(r, "fields", "")) for r in info_logs.records)


async def test_bad_request_is_summarised_as_such(info_logs):
    await handle_request({"queryStringParameters": {"crop": "banana"}}, FakeProvider(_FC))
    [summary] = _events(info_logs, "weather.request")
    assert summary.fields["status"] == 400 and summary.fields["outcome"] == "bad_request"


def test_build_provider_uses_settings():
    plain = build_provider(Settings(open_meteo_timeout_s=2.0))
    assert type(plain).__name__ == "OpenMeteoHttpProvider"
    assert plain._timeout == 2.0  # type: ignore[attr-defined]
    cached = build_provider(Settings(cache_table="t"))
    assert type(cached).__name__ == "CachedProvider"


# --- S2d: coverage = Telangana + border ------------------------------------------------------


@pytest.mark.parametrize(
    ("lat", "lon"),
    [("18.44", "79.86"), ("17.385", "78.4867"), ("19.92", "78.53"), ("15.85", "78.0"), ("16.5", "80.6")],
)
async def test_points_in_telangana_and_its_border_are_served(lat, lon):
    resp = await handle_request({"queryStringParameters": {"lat": lat, "lon": lon}}, FakeProvider(_FC))
    assert resp["statusCode"] == 200


@pytest.mark.parametrize(("lat", "lon"), [("40.71", "-74.0"), ("13.08", "80.27"), ("19.07", "72.88"), ("21.0", "79.0")])
async def test_points_outside_coverage_get_a_clear_400(lat, lon):
    resp = await handle_request({"queryStringParameters": {"lat": lat, "lon": lon}}, FakeProvider(_FC))
    assert resp["statusCode"] == 400
    body = _body(resp)
    assert body["code"] == "outside_coverage"
    assert "Telangana" in body["error"]
