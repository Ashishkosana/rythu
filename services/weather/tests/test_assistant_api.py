"""POST /v1/assistant/ask: who may ask, how often, and what the farmer gets back (S17)."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from builders import days_from, forecast, hours_from
from rythu_weather.adapters.budget import InMemoryUpstreamBudget
from rythu_weather.adapters.fake import FakeProvider
from rythu_weather.api.app import create_app
from rythu_weather.app.accounts import InMemoryUserStore, TokenSigner
from rythu_weather.app.assistant import Assistant, AssistantUnavailable, ModelReply, load_corpus
from rythu_weather.app.composition import Accounts

NOW = datetime(2026, 10, 27, 4, 0, tzinfo=UTC)  # 09:30 IST
RAINY = forecast(NOW - timedelta(minutes=10), hourly=hours_from(NOW, 48, pp=85, precip=3.0, code=63, wind=12.0),
                 daily=days_from(NOW.date(), 7, pp_max=90, precip_sum=30.0, code=63))


class FakeModel:
    def __init__(self, answer: dict[str, object] | None = None, fail: bool = False) -> None:
        self.answer = answer or {"covered": True, "answer": "యూరియా బస్తా ₹266.50.",
                                 "source_ids": ["fertilizer.bag_prices"]}
        self.fail = fail
        self.users: list[str] = []

    async def complete(self, system: str, user: str, schema: dict[str, object]) -> ModelReply:
        self.users.append(user)
        if self.fail:
            raise AssistantUnavailable
        return ModelReply(json.dumps(self.answer, ensure_ascii=False), "end_turn", "claude-opus-5-5",
                          input_tokens=150, cache_read_tokens=20_000, output_tokens=300)


class Clock:
    now = NOW

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def accounts() -> Accounts:
    return Accounts(InMemoryUserStore(), TokenSigner(b"k" * 32), InMemoryUpstreamBudget(), registrations_per_hour=50)


def _app(accounts: Accounts, model: FakeModel | None, *, per_device: int = 3, cap: int = 100, clock=None):  # type: ignore[no-untyped-def]
    bot = Assistant(model, load_corpus(), per_device_per_day=per_device, daily_cap=cap) if model else None
    return create_app(FakeProvider(RAINY), object(), accounts, clock or Clock(), None, bot)  # type: ignore[arg-type]


async def _client(app):  # type: ignore[no-untyped-def]
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def _device(c: httpx.AsyncClient) -> dict[str, str]:
    creds = (await c.post("/v1/devices")).json()
    token = (await c.post("/v1/sessions", json=creds)).json()["token"]
    return {"Authorization": f"Bearer {token}"}


ASK = {"question": "యూరియా బస్తా ధర ఎంత?", "lang": "te"}


async def test_needs_a_device_token(accounts) -> None:
    async with await _client(_app(accounts, FakeModel())) as c:
        r = await c.post("/v1/assistant/ask", json=ASK)
    assert r.status_code == 401 and r.json()["code"] == "unauthorized"


async def test_switched_off_says_so(accounts) -> None:
    async with await _client(_app(accounts, None)) as c:
        r = await c.post("/v1/assistant/ask", json=ASK, headers=await _device(c))
    assert r.status_code == 503 and r.json()["code"] == "assistant_off"


async def test_an_answer_with_its_sources_and_the_helpline(accounts) -> None:
    model = FakeModel()
    async with await _client(_app(accounts, model)) as c:
        r = await c.post("/v1/assistant/ask", json=ASK, headers=await _device(c))
    assert r.status_code == 200 and r.headers["Cache-Control"] == "no-store"
    body = r.json()
    assert body["covered"] is True and body["answer"] == "యూరియా బస్తా ₹266.50."
    assert [s["id"] for s in body["sources"]] == ["fertilizer.bag_prices"]
    assert body["sources"][0]["url"].startswith("https://")
    assert body["remaining_today"] == 2
    assert body["helpline"] == {"display": "1800-180-1551", "tel": "tel:18001801551"}
    assert "not available" in model.users[0]  # no village sent → no weather context claimed


async def test_todays_reads_for_the_village_reach_the_model(accounts) -> None:
    model = FakeModel({"covered": True, "answer": "Don't spray today.", "source_ids": ["context.weather"]})
    ask = {"question": "Can I spray my cotton today?", "lang": "en", "lat": 18.33, "lon": 79.88, "crop": "cotton"}
    async with await _client(_app(accounts, model)) as c:
        r = await c.post("/v1/assistant/ask", json=ask, headers=await _device(c))
    assert r.json()["used_todays_weather"] is True and r.json()["covered"] is True
    assert "Today's Rythu weather reads for the farmer's village" in model.users[0]
    assert re.search(r"^- \[(act|caution|info)\] ", model.users[0], re.M)  # at least one read went along


async def test_a_phone_gets_its_daily_questions_and_no_more(accounts) -> None:
    clock = Clock()
    async with await _client(_app(accounts, FakeModel(), per_device=2, clock=clock)) as c:
        me, other = await _device(c), await _device(c)
        assert [(await c.post("/v1/assistant/ask", json=ASK, headers=me)).status_code for _ in range(3)] == [
            200, 200, 429]
        r = await c.post("/v1/assistant/ask", json=ASK, headers=me)
        assert r.json()["code"] == "rate_limited" and 0 < int(r.headers["Retry-After"]) <= 24 * 3600
        assert (await c.post("/v1/assistant/ask", json=ASK, headers=other)).status_code == 200
        clock.now = NOW + timedelta(days=1)  # tokens last an hour: a new session for the new day
        assert (await c.post("/v1/assistant/ask", json=ASK, headers=await _device(c))).status_code == 200


async def test_the_daily_cap_holds_for_everyone_together(accounts) -> None:
    async with await _client(_app(accounts, FakeModel(), per_device=5, cap=2)) as c:
        codes = [(await c.post("/v1/assistant/ask", json=ASK, headers=await _device(c))).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


async def test_a_failed_answer_costs_no_question(accounts) -> None:
    async with await _client(_app(accounts, FakeModel(fail=True), per_device=1)) as c:
        me = await _device(c)
        r = await c.post("/v1/assistant/ask", json=ASK, headers=me)
        assert r.status_code == 503 and r.json()["code"] == "unavailable"
        assert (await accounts.users.assistant_usage(me_id(accounts), "2026-10-27"))[0] == 0


def me_id(accounts: Accounts) -> str:
    ids = [uid for uid in accounts.users._rows if uid != "assistant"]  # type: ignore[attr-defined]
    assert len(ids) == 1
    return ids[0]


async def test_not_covered_comes_back_honest(accounts) -> None:
    model = FakeModel({"covered": False, "answer": "Rythuలో దీనిపై సమాచారం లేదు.", "source_ids": []})
    async with await _client(_app(accounts, model)) as c:
        body = (await c.post("/v1/assistant/ask", json={"question": "బంగారం ధర ఎంత?"}, headers=await _device(c))).json()
    assert body["covered"] is False and body["sources"] == [] and body["helpline"]["tel"] == "tel:18001801551"


@pytest.mark.parametrize("bad", [{"question": "x" * 301}, {"question": "hi"}, {"question": "ok?", "lang": "hi"},
                                 {"question": "ok?", "extra": 1}])
async def test_bad_requests_are_refused_before_any_model_call(accounts, bad) -> None:
    model = FakeModel()
    async with await _client(_app(accounts, model)) as c:
        r = await c.post("/v1/assistant/ask", json=bad, headers=await _device(c))
    assert r.status_code == 400 and model.users == []
