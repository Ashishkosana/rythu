"""Village search: normalisers (ported from the web app), upstream requests, fallback, cache + pacing, API."""

from __future__ import annotations

import asyncio
import json
import time

import httpx
import pytest
import respx

from rythu_weather.adapters.fake import FakeProvider
from rythu_weather.adapters.geocode import (
    NOMINATIM,
    OPEN_METEO_GEOCODE,
    USER_AGENT,
    CachedGeocoder,
    FallbackGeocoder,
    GeocodeUnavailable,
    NominatimGeocoder,
    OpenMeteoGeocoder,
    Place,
    normalize_nominatim,
    normalize_open_meteo,
)
from rythu_weather.api.app import create_app
from rythu_weather.api.schemas import ErrorBody, GeocodeResults
from rythu_weather.domain.coverage import in_coverage

REGONDA = Place(id=42, name="Regonda", lat=18.2378, lon=79.775, admin2="Bhupalpally", admin1="Telangana",
                name_te="రేగొండ")


# --- coverage --------------------------------------------------------------------------------------


def test_coverage_is_telangana_plus_border() -> None:
    assert in_coverage(18.33, 79.88)  # Regonda
    assert in_coverage(17.385, 78.4867)  # Hyderabad
    assert not in_coverage(13.08, 80.27)  # Chennai
    assert not in_coverage(float("nan"), 79.0)
    assert not in_coverage(18.0, float("inf"))


# --- normalisers -----------------------------------------------------------------------------------


def test_nominatim_prefers_village_parses_string_coords_and_keeps_telugu_name() -> None:
    out = normalize_nominatim([{
        "place_id": 42, "lat": "18.23781", "lon": "79.77502",
        "display_name": "Regonda, Bhupalpally, Telangana, India",
        "address": {"village": "Regonda", "state_district": "Bhupalpally", "state": "Telangana"},
        "namedetails": {"name": "Regonda", "name:te": "రేగొండ"},
    }])
    assert out == [REGONDA]


def test_nominatim_falls_back_through_hamlet_town_city_then_display_name() -> None:
    out = normalize_nominatim([
        {"place_id": 1, "lat": "18.5", "lon": "79.7", "address": {"hamlet": "Tinyville", "state": "Telangana"}},
        {"place_id": 2, "lat": "18.6", "lon": "79.8", "display_name": "Nowhere, X", "address": {}},
        {"place_id": 3, "lat": "18.7", "lon": "79.9", "address": {"county": "Mulugu"}, "name": "Eturnagaram"},
    ])
    assert [(p.name, p.name_te, p.admin2) for p in out] == [
        ("Tinyville", None, None), ("Nowhere", None, None), ("Eturnagaram", None, "Mulugu"),
    ]


def test_nominatim_drops_bad_rows_and_tolerates_junk() -> None:
    assert normalize_nominatim([{"place_id": 1, "lat": "999", "lon": "79", "address": {"village": "Bad"}}]) == []
    assert normalize_nominatim([{"place_id": 1, "lat": "NaN", "lon": "79", "address": {"village": "Bad"}}]) == []
    assert normalize_nominatim([{"place_id": 1, "lat": "18.5", "lon": "79.7"}]) == []  # no name at all
    assert normalize_nominatim([{"place_id": 1, "lat": "13.08", "lon": "80.27", "name": "Chennai"}]) == []
    assert normalize_nominatim(None) == []
    assert normalize_nominatim({"results": []}) == []
    assert normalize_nominatim(["nope", 3]) == []
    # A missing/odd place_id falls back to the row index rather than dropping a good place.
    assert normalize_nominatim([{"place_id": "x", "lat": "18.5", "lon": "79.7", "name": "A"}])[0].id == 0


def test_open_meteo_maps_rows_rounds_and_filters() -> None:
    out = normalize_open_meteo({"results": [
        {"id": 1, "name": "Regonda", "admin2": "Bhupalpally", "admin1": "Telangana",
         "latitude": 18.23781, "longitude": 79.77502},
        {"id": 2, "latitude": 18.4, "longitude": 79.8},  # no name
        {"id": 3, "name": "Bad", "latitude": 999, "longitude": 79.8},
        {"id": 4, "name": "Chennai", "latitude": 13.08, "longitude": 80.27},
        {"id": 5, "name": "Str", "latitude": "18.4", "longitude": "79.8"},  # strings are not this API's shape
    ]})
    assert out == [Place(id=1, name="Regonda", lat=18.2378, lon=79.775, admin2="Bhupalpally", admin1="Telangana")]
    assert normalize_open_meteo(None) == []
    assert normalize_open_meteo({}) == []
    assert normalize_open_meteo({"results": "nope"}) == []


# --- upstream requests -----------------------------------------------------------------------------


@respx.mock
async def test_nominatim_request_follows_usage_policy() -> None:
    route = respx.get(NOMINATIM).mock(return_value=httpx.Response(200, json=[]))
    assert await NominatimGeocoder().search("Regonda") == []
    req = route.calls.last.request
    assert req.headers["User-Agent"] == USER_AGENT
    q = req.url.params
    assert q["q"] == "Regonda"
    assert q["bounded"] == "1"
    assert q["viewbox"] == "77.1,20.0,81.5,15.7"
    assert q["namedetails"] == "1"
    assert q["countrycodes"] == "in"


@respx.mock
async def test_open_meteo_request_shape() -> None:
    route = respx.get(OPEN_METEO_GEOCODE).mock(return_value=httpx.Response(200, json={}))
    assert await OpenMeteoGeocoder().search("Regonda") == []
    q = route.calls.last.request.url.params
    assert (q["name"], q["country"]) == ("Regonda", "IN")


@respx.mock
async def test_upstream_http_error_raises() -> None:
    respx.get(NOMINATIM).mock(return_value=httpx.Response(429))
    with pytest.raises(httpx.HTTPStatusError):
        await NominatimGeocoder().search("Regonda")


# --- fallback --------------------------------------------------------------------------------------


class Fixed:
    def __init__(self, places: list[Place] | Exception, delay: float = 0.0) -> None:
        self.places = places
        self.delay = delay
        self.calls: list[str] = []

    async def search(self, query: str) -> list[Place]:
        self.calls.append(query)
        if self.delay:
            await asyncio.sleep(self.delay)
        if isinstance(self.places, Exception):
            raise self.places
        return self.places


async def test_fallback_only_when_primary_fails_or_finds_nothing(caplog: pytest.LogCaptureFixture) -> None:
    other = Place(id=1, name="Regonda", lat=18.2, lon=79.8)
    primary, fallback = Fixed([REGONDA]), Fixed([other])
    assert await FallbackGeocoder(primary, fallback).search("r") == [REGONDA]
    assert fallback.calls == []

    assert await FallbackGeocoder(Fixed([]), fallback).search("r") == [other]
    assert await FallbackGeocoder(Fixed(RuntimeError("down")), fallback).search("r") == [other]
    assert "geocode.upstream_failed" in caplog.text
    # One source answering "nothing" is a real answer; every source failing is not.
    assert await FallbackGeocoder(Fixed(RuntimeError("down")), Fixed([])).search("r") == []
    with pytest.raises(GeocodeUnavailable):
        await FallbackGeocoder(Fixed(RuntimeError("a")), Fixed(RuntimeError("b"))).search("r")


# --- cache + pacing --------------------------------------------------------------------------------


async def test_cache_hits_by_normalised_query_and_does_not_cache_empty() -> None:
    inner = Fixed([REGONDA])
    geo = CachedGeocoder(inner, min_interval_s=0)
    assert await geo.search("Regonda") == [REGONDA]
    assert await geo.search("  regonda ") == [REGONDA]
    assert inner.calls == ["Regonda"]

    empty = Fixed([])
    geo = CachedGeocoder(empty, min_interval_s=0)
    await geo.search("x y")
    await geo.search("X  Y")
    assert len(empty.calls) == 2  # nothing found is retried, not remembered


async def test_cache_expires_and_evicts_least_recently_used() -> None:
    inner = Fixed([REGONDA])
    geo = CachedGeocoder(inner, ttl_s=0, min_interval_s=0)
    await geo.search("a")
    await geo.search("a")
    assert len(inner.calls) == 2

    inner = Fixed([REGONDA])
    geo = CachedGeocoder(inner, max_entries=2, min_interval_s=0)
    for q in ("a", "b", "a", "c", "a", "b"):  # 'b' was evicted when 'c' arrived; 'a' stayed hot
        await geo.search(q)
    assert inner.calls == ["a", "b", "c", "b"]


async def test_upstream_calls_are_paced_even_after_a_failure() -> None:
    inner = Fixed(RuntimeError("down"))
    geo = CachedGeocoder(inner, min_interval_s=0.2)
    with pytest.raises(RuntimeError):
        await geo.search("a")
    started = time.monotonic()
    with pytest.raises(RuntimeError):
        await geo.search("b")
    assert time.monotonic() - started >= 0.18


async def test_a_queue_that_is_too_long_is_refused_instead_of_waiting(caplog: pytest.LogCaptureFixture) -> None:
    geo = CachedGeocoder(Fixed([REGONDA], delay=0.3), min_interval_s=0, max_wait_s=0.05)
    first, second = await asyncio.gather(geo.search("a"), geo.search("b"), return_exceptions=True)
    assert first == [REGONDA]
    assert isinstance(second, GeocodeUnavailable)
    assert "geocode.busy" in caplog.text


# --- API -------------------------------------------------------------------------------------------


async def _get(geocoder: Fixed, params: dict[str, str]) -> httpx.Response:
    app = create_app(FakeProvider(None), geocoder)  # type: ignore[arg-type]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.get("/v1/geocode", params=params, headers={"X-Request-Id": "req-1"})


async def test_api_returns_places_cached_for_a_day() -> None:
    resp = await _get(Fixed([REGONDA]), {"q": "  Regonda "})
    assert resp.status_code == 200
    body = resp.json()
    GeocodeResults.model_validate(body)  # the documented schema is the real shape
    assert body == {"results": [{
        "id": 42, "name": "Regonda", "lat": 18.2378, "lon": 79.775, "admin2": "Bhupalpally",
        "admin1": "Telangana", "name_te": "రేగొండ",
    }]}
    assert resp.headers["Cache-Control"].startswith("public, max-age=86400")
    assert resp.headers["X-Request-Id"] == "req-1"
    assert resp.headers["Access-Control-Allow-Origin"] == "*"


async def test_api_empty_result_is_not_cacheable() -> None:
    inner = Fixed([])
    resp = await _get(inner, {"q": "Atlantis"})
    assert (resp.status_code, resp.json()) == (200, {"results": []})
    assert resp.headers["Cache-Control"] == "no-store"
    assert inner.calls == ["Atlantis"]


@pytest.mark.parametrize(
    ("failure", "outcome"), [(GeocodeUnavailable("all down"), "unavailable"), (ZeroDivisionError(), "error")]
)
async def test_api_says_unavailable_not_empty_when_no_source_answered(
    failure: Exception, outcome: str, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("INFO")
    resp = await _get(Fixed(failure), {"q": "Regonda"})
    assert resp.status_code == 503
    assert ErrorBody.model_validate(resp.json()).code == "upstream_unavailable"
    assert resp.headers["Cache-Control"] == "no-store"
    line = next(r for r in caplog.records if r.getMessage() == "geocode.request")
    assert line.fields["outcome"] == outcome  # type: ignore[attr-defined]


@pytest.mark.parametrize("params", [{}, {"q": ""}, {"q": " a "}, {"q": "x" * 61}])
async def test_api_rejects_bad_queries_without_calling_upstream(params: dict[str, str]) -> None:
    inner = Fixed([REGONDA])
    resp = await _get(inner, params)
    assert resp.status_code == 400
    ErrorBody.model_validate(resp.json())
    assert resp.json()["code"] == "bad_request"
    assert inner.calls == []


async def test_api_logs_outcome_but_not_the_query(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO")
    await _get(Fixed([REGONDA]), {"q": "Regonda"})
    lines = [r for r in caplog.records if r.getMessage() == "geocode.request"]
    assert len(lines) == 1
    fields = json.dumps(vars(lines[0]), default=str)
    assert "Regonda" not in fields
    assert lines[0].fields["outcome"] == "ok"  # type: ignore[attr-defined]
    assert lines[0].fields["results"] == 1  # type: ignore[attr-defined]
