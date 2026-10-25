"""Golden test: the Pydantic schemas describe EXACTLY what the serializer emits.

Every real response shape (each crop × water source, wet and dry, unknown values, offline cache,
degraded) must validate against ``WeatherContract`` and round-trip unchanged. The models forbid
unknown fields, so a field added to ``app.serialize`` but not to ``api.schemas`` fails here — and
with it the OpenAPI document and (from S4) the generated TypeScript types.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest
from pydantic import ValidationError

from builders import at, day, days_from, forecast, hour, hours_from
from rythu_weather.adapters.fake import FakeProvider
from rythu_weather.api.schemas import ErrorBody, WeatherContract
from rythu_weather.app.degraded import degraded_contract
from rythu_weather.app.service import BHUPALPALLY, get_weather
from rythu_weather.domain.models import Crop, FarmerContext, WaterSource

NOW = at(2026, 10, 14, 7)  # chilli season, spray morning


def _wet():
    return forecast(
        NOW,
        hourly=hours_from(NOW, 72, pp=80, precip=2.0, rh=92, wind=20.0, code=95, temp=26.0),
        daily=days_from(NOW.date(), 7, pp_max=90, precip_sum=60.0, tmax=37.0, code=95),
    )


def _dry():
    return forecast(
        NOW,
        hourly=hours_from(NOW, 72, rh=40, temp=33.0),
        daily=days_from(NOW.date(), 7, tmax=36.0, tmin=22.0),
    )


def _unknowns():
    return forecast(
        NOW,
        hourly=[hour(NOW + timedelta(hours=i), pp=None, precip=None, temp=None, rh=None, code=None, wind=None)
                for i in range(24)],
        daily=[day(NOW.date(), pp_max=None, precip_sum=None, tmax=None, tmin=None, code=None, wind_max=None)],
    )


async def _contracts():
    out = []
    for fc in (_wet(), _dry(), _unknowns()):
        for crop in (None, *Crop):
            for water in WaterSource:
                ctx = FarmerContext(now=NOW, water_source=water, crop=crop)
                out.append(await get_weather(FakeProvider(fc), BHUPALPALLY, ctx))
    offline = replace(_wet(), reliability=replace(_wet().reliability, is_offline_cache=True))
    out.append(await get_weather(FakeProvider(offline), BHUPALPALLY, FarmerContext(NOW, WaterSource.RAINFED)))
    out.append(degraded_contract(BHUPALPALLY, FarmerContext(NOW, WaterSource.TANK, Crop.PADDY)))
    return out


async def test_every_real_response_round_trips_through_the_schema_unchanged():
    contracts = await _contracts()
    reads = sum(len(c["farming_read"]) for c in contracts)
    assert reads > 50  # the fixtures really exercise the advice cards, Telugu text included
    for c in contracts:
        model = WeatherContract.model_validate(c)
        assert model.model_dump(mode="json", exclude_unset=True) == c


async def test_an_undeclared_field_fails_the_schema():
    c = (await _contracts())[0]
    with pytest.raises(ValidationError, match="extra"):
        WeatherContract.model_validate({**c, "confidence": 0.9})  # e.g. someone re-adds a confidence score


async def test_a_missing_field_fails_the_schema():
    c = dict((await _contracts())[0])
    del c["reliability"]
    with pytest.raises(ValidationError):
        WeatherContract.model_validate(c)


def test_confidence_rating_can_never_be_true():
    c = degraded_contract(BHUPALPALLY, FarmerContext(NOW, WaterSource.RAINFED))
    c["reliability"]["show_confidence_rating"] = True
    with pytest.raises(ValidationError):
        WeatherContract.model_validate(c)


@pytest.mark.parametrize(
    "body",
    [{"error": "unknown crop 'banana'", "code": "bad_request"},
     {"error": "Rythu currently covers Telangana only", "code": "outside_coverage"}],
)
def test_error_bodies_match_the_schema(body):
    assert ErrorBody.model_validate(body).model_dump() == body
