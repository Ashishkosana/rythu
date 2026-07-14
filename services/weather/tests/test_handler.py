from __future__ import annotations

import json

from builders import at, days_from, forecast, hours_from
from rythu_weather.adapters.fake import FailingProvider, FakeProvider
from rythu_weather.app.handler import handle_request

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
