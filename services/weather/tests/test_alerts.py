"""Push alerts: the rules (pure), the evaluator (timer) and the sender (queue)."""

from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import http_ece
import httpx
import pytest
import respx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from builders import days_from, forecast, hours_from
from rythu_weather.adapters.fake import FailingProvider, FakeProvider
from rythu_weather.app.accounts import InMemoryUserStore, new_credentials
from rythu_weather.app.alert_jobs import deliver, evaluate
from rythu_weather.app.alerts import MAX_PER_RUN, due_alerts
from rythu_weather.app.push_subscription import Subscription
from rythu_weather.app.webpush import LocalVapidSigner, PushRetryable, b64url

IST = ZoneInfo("Asia/Kolkata")
MORNING = datetime(2026, 10, 27, 6, 15, tzinfo=IST)
EVENING = datetime(2026, 10, 27, 17, 45, tzinfo=IST)
PROFILE = {"village": {"name": "రేగొండ", "lat": 18.2378, "lon": 79.775}, "crop": "chilli", "water": "rainfed",
           "lang": "te", "fields": []}


def contract(probs: list[int | None], reads: list[dict] | None = None, degraded: bool = False) -> dict:
    c = {"hourly_rain": [{"precipitation_probability": p} for p in probs], "farming_read": reads or []}
    return {**c, "degraded": True} if degraded else c


def read(id_: str, severity: str, triggered: bool = True) -> dict:
    return {"id": id_, "severity": severity, "triggered": triggered, "headline_en": f"{id_} en",
            "headline_te": f"{id_} తెలుగు", "detail_en": "detail", "detail_te": "వివరం"}


# --- rules -----------------------------------------------------------------------------------------


def test_rain_alert_at_70_percent_in_the_next_12_hours_in_the_farmers_language() -> None:
    [a] = due_alerts(PROFILE, contract([10, 40, 72] + [0] * 20), MORNING)
    assert (a.key, a.topic, a.url) == ("rain.2026-10-27.am", "rain", "/")
    assert a.title == "వర్షం రావచ్చు — 72%" and "రేగొండ" in a.body
    [en] = due_alerts({**PROFILE, "lang": "en"}, contract([72]), EVENING)
    assert en.key == "rain.2026-10-27.pm" and en.title == "Rain likely — 72%"
    assert due_alerts(PROFILE, contract([69] * 12 + [95]), MORNING) == []  # 95 % is beyond 12 hours
    assert due_alerts(PROFILE, contract([None, None]), MORNING) == []  # unknown is not "no rain", nor rain


def test_only_act_now_advice_becomes_an_alert() -> None:
    alerts = due_alerts(PROFILE, contract([0], [read("spray_rain", "act"), read("scout", "caution"),
                                                read("harvest", "act", triggered=False)]), MORNING)
    assert [a.key for a in alerts] == ["read.spray_rain.2026-10-27"]
    assert alerts[0].title == "spray_rain తెలుగు" and alerts[0].priority == 0


def test_no_forecast_means_no_weather_alerts_but_field_tasks_still_come() -> None:
    field = {"id": "f1a2b3", "name": "తూర్పు", "crop": "cotton", "reference_date": "2026-09-28"}  # day 30 tomorrow
    profile = {**PROFILE, "fields": [field]}
    for c in (None, contract([99], [read("x", "act")], degraded=True)):
        [a] = due_alerts(profile, c, MORNING)
        assert a.key == "task.f1a2b3.cotton.split1.2026-10-28"
        assert a.title.startswith("తూర్పు: ") and a.body.startswith("రేపు: ") and a.url == "/field/"


def test_tasks_starting_today_say_today_and_bad_fields_are_skipped() -> None:
    fields = [{"id": "aaaaaa", "name": "A", "crop": "maize", "reference_date": "2026-09-22"},  # day 35… none
              {"id": "bbbbbb", "name": "B", "crop": "maize", "reference_date": "2026-10-02"},  # day 25 today
              {"id": "cccccc", "name": "C", "crop": "banana", "reference_date": "2026-10-02"},
              {"id": "dddddd", "crop": "maize"}]
    alerts = due_alerts({**PROFILE, "lang": "en", "fields": fields}, None, MORNING)
    assert [a.key for a in alerts] == ["task.bbbbbb.maize.split2.2026-10-27"]
    assert alerts[0].body.startswith("Today: ")


def test_most_urgent_first_and_never_more_than_three() -> None:
    reads = [read(f"r{i}", "act") for i in range(4)]
    alerts = due_alerts(PROFILE, contract([90], reads), MORNING)
    assert len(alerts) == MAX_PER_RUN == 3
    assert all(a.priority == 0 for a in alerts)


# --- evaluate (timer) ------------------------------------------------------------------------------

SUB = Subscription("https://fcm.googleapis.com/fcm/send/abc", "p", "a")


async def _farmer(users: InMemoryUserStore, profile: dict, subscribed: bool = True) -> str:
    uid = new_credentials().user_id
    await users.create_user(uid, "ab" * 32, MORNING)
    await users.put_profile(uid, profile, if_match=None, create_only=True)
    if subscribed:
        await users.put_push_subscription(uid, SUB, MORNING)
    return uid


def _rainy_provider() -> FakeProvider:
    now = MORNING.replace(minute=0)
    return FakeProvider(forecast(now - timedelta(minutes=10), hourly=hours_from(now, 48, pp=80, precip=2.0, code=61),
                                 daily=days_from(now.date(), 7, pp_max=85, precip_sum=20.0, code=61)))


async def test_evaluate_queues_due_alerts_for_subscribed_farmers_only_once() -> None:
    users = InMemoryUserStore()
    alice = await _farmer(users, PROFILE)
    await _farmer(users, PROFILE, subscribed=False)  # no phone to tell
    messages = await evaluate(users, _rainy_provider(), MORNING)
    assert {m["user_id"] for m in messages} == {alice}
    assert "rain.2026-10-27.am" in {m["key"] for m in messages}

    await users.claim_alert(alice, "rain.2026-10-27.am", MORNING)  # it went out
    again = await evaluate(users, _rainy_provider(), MORNING + timedelta(hours=1))
    assert "rain.2026-10-27.am" not in {m["key"] for m in again}


async def test_evaluate_survives_an_outage_and_a_broken_farmer() -> None:
    users = InMemoryUserStore()
    field = {"id": "f1a2b3", "name": "E", "crop": "cotton", "reference_date": "2026-09-28"}
    good = await _farmer(users, {**PROFILE, "fields": [field]})
    await _farmer(users, {**PROFILE, "village": {"lat": "not a number", "lon": 1, "name": "x"}})
    messages = await evaluate(users, FailingProvider(), MORNING)  # weather down for everyone
    assert [(m["user_id"], m["key"]) for m in messages] == [(good, "task.f1a2b3.cotton.split1.2026-10-28")]


# --- deliver (queue) -------------------------------------------------------------------------------


def _browser_sub(endpoint: str) -> tuple[Subscription, ec.EllipticCurvePrivateKey, bytes]:
    key = ec.generate_private_key(ec.SECP256R1())
    pub = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    auth = os.urandom(16)
    return Subscription(endpoint, b64url(pub), b64url(auth)), key, auth


MESSAGE = {"user_id": "u" * 32, "key": "rain.2026-10-27.am", "title": "వర్షం", "body": "75%", "url": "/",
           "topic": "rain", "priority": 1}
NOW = datetime(2026, 10, 27, 1, 0, tzinfo=UTC)


@respx.mock
async def test_deliver_sends_an_encrypted_alert_to_every_phone_and_drops_dead_ones() -> None:
    users = InMemoryUserStore()
    live, key, auth = _browser_sub("https://fcm.googleapis.com/fcm/send/live")
    dead, _, _ = _browser_sub("https://fcm.googleapis.com/fcm/send/dead")
    for s in (live, dead):
        await users.put_push_subscription(MESSAGE["user_id"], s, NOW)
    ok = respx.post(live.endpoint).mock(return_value=httpx.Response(201))
    respx.post(dead.endpoint).mock(return_value=httpx.Response(410))
    async with httpx.AsyncClient() as client:
        outcome = await deliver(MESSAGE, users, LocalVapidSigner(), subject="https://x.example", now=NOW, client=client)
        assert outcome == "sent"
        body = http_ece.decrypt(ok.calls.last.request.content, private_key=key, auth_secret=auth, version="aes128gcm")
        assert json.loads(body) == {"title": "వర్షం", "body": "75%", "url": "/", "tag": "rain"}
        assert await users.push_subscriptions(MESSAGE["user_id"]) == [live]  # the 410 one is gone

        # The same message again (queue redelivery): the phone does not buzz twice.
        assert await deliver(MESSAGE, users, LocalVapidSigner(), subject="https://x.example", now=NOW,
                             client=client) == "duplicate"
        assert ok.call_count == 1


@respx.mock
async def test_deliver_retries_only_when_nothing_got_through() -> None:
    users = InMemoryUserStore()
    a, _, _ = _browser_sub("https://fcm.googleapis.com/fcm/send/a")
    await users.put_push_subscription(MESSAGE["user_id"], a, NOW)
    route = respx.post(a.endpoint).mock(return_value=httpx.Response(503))
    async with httpx.AsyncClient() as client:
        with pytest.raises(PushRetryable):
            await deliver(MESSAGE, users, LocalVapidSigner(), subject="https://x.example", now=NOW, client=client)
        assert not await users.has_alert(MESSAGE["user_id"], MESSAGE["key"])  # released for the retry
        route.mock(return_value=httpx.Response(201))
        assert await deliver(MESSAGE, users, LocalVapidSigner(), subject="https://x.example", now=NOW,
                             client=client) == "sent"

        b, _, _ = _browser_sub("https://fcm.googleapis.com/fcm/send/b")
        await users.put_push_subscription(MESSAGE["user_id"], b, NOW)
        respx.post(b.endpoint).mock(return_value=httpx.Response(503))
        second = {**MESSAGE, "key": "rain.2026-10-27.pm"}
        assert await deliver(second, users, LocalVapidSigner(), subject="https://x.example", now=NOW,
                             client=client) == "sent"  # one phone got it: no retry, so no duplicate on it


def test_alert_dates_are_local_dates() -> None:
    # 00:30 IST on the 28th is still the 27th in UTC: keys and "today" follow the farmer's clock.
    late = datetime(2026, 10, 28, 0, 30, tzinfo=IST)
    [a] = due_alerts(PROFILE, contract([80]), late)
    assert a.key == f"rain.{date(2026, 10, 28).isoformat()}.am"
