"""Ask Rythu (S17): the corpus, the prompt, and what the server trusts in a model's reply.

Offline — no model is called. The live eval (``scripts/eval_assistant.py``) needs a key and money.
"""

from __future__ import annotations

import json
import re

import anthropic
import httpx2
import pytest

from rythu_weather.adapters.claude import FALLBACK_BETA, ClaudeAnswerModel
from rythu_weather.app.assistant import (
    MAX_ANSWER_CHARS,
    WEATHER_CONTEXT_ID,
    Assistant,
    AssistantUnavailable,
    ModelReply,
    answer_schema,
    cost_usd,
    interpret,
    load_corpus,
    system_prompt,
    user_message,
)
from rythu_weather.domain.models import Crop

CORPUS = load_corpus()
BY_ID = {i.id: i for i in CORPUS}


def reply(payload: object, stop: str = "end_turn", model: str = "claude-opus-5-5") -> ModelReply:
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return ModelReply(text=text, stop_reason=stop, model=model)


# --- corpus and prompt ------------------------------------------------------------------------------


def test_the_corpus_is_the_apps_own_checked_content() -> None:
    ids = [i.id for i in CORPUS]
    assert len(ids) == len(set(ids))
    for expected in ("fertilizer.paddy", "fertilizer.bag_prices", "pest.chilli_thrips", "crop.red_gram",
                     "scheme.pm_kisan", "help.kisan_call_centre", "help.cyber_fraud", "calendar.cotton.split2"):
        assert expected in BY_ID
    assert all(i.source.startswith("https://") for i in CORPUS)  # every item says where it came from
    assert "266.5" in BY_ID["fertilizer.bag_prices"].text


def test_the_cached_prefix_is_byte_stable() -> None:
    # Any byte that changes between requests (a date, a shuffled id) would void the prompt cache.
    a, b = system_prompt(load_corpus()), system_prompt(load_corpus())
    assert a == b
    assert not re.search(r"20\d\d-\d\d-\d\d", a.split("<rythu_content>")[0])  # no dates in the instructions
    assert answer_schema(load_corpus()) == answer_schema(CORPUS)


def test_the_schema_only_allows_corpus_ids() -> None:
    schema = answer_schema(CORPUS)
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]["source_ids"]["items"]["enum"]) == {*BY_ID, WEATHER_CONTEXT_ID}


def test_the_question_and_todays_reads_go_after_the_cache_breakpoint() -> None:
    reads = [{"severity": "act", "headline_en": "Don't spray today", "detail_en": "Rain within 6 h.",
              "headline_te": "ఈరోజు పిచికారీ వద్దు", "detail_te": "6 గంటల్లో వర్షం."}]
    msg = user_message("పిచికారీ చేయొచ్చా?", "te", crop=Crop.COTTON, reads=reads)
    assert "Telugu" in msg and "cotton" in msg
    assert "[act] Don't spray today Rain within 6 h. / ఈరోజు పిచికారీ వద్దు" in msg
    assert msg.endswith("<question>\nపిచికారీ చేయొచ్చా?\n</question>")
    assert "not available" in user_message("x?", "en", crop=None, reads=None)
    assert "nothing needs action" in user_message("x?", "en", crop=None, reads=[])


# --- what the server trusts -------------------------------------------------------------------------


def test_a_grounded_answer_keeps_its_sources_in_order() -> None:
    a = interpret(reply({"covered": True, "answer": "Urea: 266.50 rupees a bag.",
                         "source_ids": ["fertilizer.bag_prices", "help.kisan_call_centre", "fertilizer.bag_prices"]}),
                  BY_ID, "en", had_reads=False)
    assert a.covered and [s.id for s in a.sources] == ["fertilizer.bag_prices", "help.kisan_call_centre"]


def test_an_answer_citing_nothing_real_is_not_covered() -> None:
    for ids in ([], ["made.up"], [WEATHER_CONTEXT_ID]):  # the weather id without reads cites nothing
        a = interpret(reply({"covered": True, "answer": "Sure!", "source_ids": ids}), BY_ID, "en", had_reads=False)
        assert not a.covered and a.sources == ()
    w = interpret(reply({"covered": True, "answer": "Don't spray today.", "source_ids": [WEATHER_CONTEXT_ID]}),
                  BY_ID, "en", had_reads=True)
    assert w.covered and w.cites_weather


@pytest.mark.parametrize("bad", [
    reply({}, stop="refusal"), reply({"covered": True, "answer": "half", "source_ids": []}, stop="max_tokens"),
    ModelReply(None, "end_turn", "claude-opus-5-5"), reply("not json"), reply([1, 2]),
    reply({"covered": True, "answer": "  ", "source_ids": ["fertilizer.paddy"]}),
    reply({"covered": True, "answer": "x", "source_ids": "fertilizer.paddy"}),
])
def test_anything_odd_becomes_the_honest_fallback(bad: ModelReply) -> None:
    a = interpret(bad, BY_ID, "te", had_reads=False)
    assert not a.covered and "1800-180-1551" in a.answer and "కిసాన్ కాల్ సెంటర్" in a.answer


def test_a_rambling_answer_is_cut_short() -> None:
    a = interpret(reply({"covered": True, "answer": "word " * 600, "source_ids": ["crop.paddy"]}), BY_ID, "en",
                  had_reads=False)
    assert len(a.answer) <= MAX_ANSWER_CHARS + 2 and a.answer.endswith("…")


def test_cost_comes_from_the_published_prices_or_not_at_all() -> None:
    r = ModelReply("{}", "end_turn", "claude-opus-5-5", input_tokens=200, cache_read_tokens=20_000,
                   cache_write_tokens=0, output_tokens=500)
    assert cost_usd(r) == pytest.approx((200 * 4 + 20_000 * 0.20 + 500 * 20) / 1e6)
    assert cost_usd(ModelReply("{}", "end_turn", "claude-unknown-9")) is None


async def test_the_assistant_asks_once_with_the_built_prompt() -> None:
    seen: list[tuple[str, str]] = []

    class Model:
        async def complete(self, system, user, schema):  # type: ignore[no-untyped-def]
            seen.append((system, user))
            return reply({"covered": True, "answer": "ok", "source_ids": ["crop.maize"]})

    bot = Assistant(Model(), CORPUS, per_device_per_day=3, daily_cap=10)
    a = await bot.ask("When to sow maize?", "en", crop=Crop.MAIZE)
    assert a.covered and seen[0][0] == bot.system and "When to sow maize?" in seen[0][1]


# --- the Claude adapter, against a mock transport (no network) --------------------------------------


def _claude(handler, model: str = "claude-opus-5-5") -> ClaudeAnswerModel:  # type: ignore[no-untyped-def]
    client = anthropic.AsyncAnthropic(
        api_key="test-key", max_retries=0,
        http_client=anthropic.DefaultAsyncHttpxClient(transport=httpx2.MockTransport(handler)),
    )
    return ClaudeAnswerModel("test-key", model, "low", client=client)


MESSAGE = {
    "id": "msg_1", "type": "message", "role": "assistant", "model": "claude-opus-5-5",
    "content": [{"type": "thinking", "thinking": "", "signature": "s"},
                {"type": "text", "text": '{"covered": true, "answer": "ok", "source_ids": ["crop.paddy"]}'}],
    "stop_reason": "end_turn", "stop_sequence": None,
    "usage": {"input_tokens": 180, "output_tokens": 240, "cache_read_input_tokens": 21000,
              "cache_creation_input_tokens": 0},
}


async def test_the_request_caches_the_corpus_and_asks_for_json() -> None:
    sent: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        sent.append(request)
        return httpx2.Response(200, json=MESSAGE)

    schema = answer_schema(CORPUS)
    r = await _claude(handler).complete("SYSTEM", "USER", schema)
    body = json.loads(sent[0].content)
    assert sent[0].url.path == "/v1/messages"
    assert body["system"] == [{"type": "text", "text": "SYSTEM", "cache_control": {"type": "ephemeral"}}]
    assert body["messages"] == [{"role": "user", "content": "USER"}]
    assert body["output_config"] == {"effort": "low", "format": {"type": "json_schema", "schema": schema}}
    assert body["fallbacks"] == "default" and FALLBACK_BETA in sent[0].headers["anthropic-beta"]
    assert not {"temperature", "top_p", "top_k"} & body.keys()
    assert sent[0].headers["authorization"] == "Bearer test-key"  # SDK 2.x: bearer, API version 2026-10-21
    assert sent[0].headers["anthropic-version"] == "2026-10-21"
    assert (r.text, r.stop_reason, r.cache_read_tokens, r.output_tokens) == (
        '{"covered": true, "answer": "ok", "source_ids": ["crop.paddy"]}', "end_turn", 21000, 240)


async def test_models_without_server_side_fallbacks_are_not_sent_the_parameter() -> None:
    sent: list[dict[str, object]] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        sent.append(json.loads(request.content))
        return httpx2.Response(200, json={**MESSAGE, "model": "claude-haiku-5-5"})

    await _claude(handler, "claude-haiku-5-5").complete("S", "U", {})
    assert "fallbacks" not in sent[0]


@pytest.mark.parametrize("status", [429, 500, 529, 400, 401])
async def test_api_failures_become_assistant_unavailable(status: int) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(status, json={"type": "error", "error": {"type": "x", "message": "no"}})

    with pytest.raises(AssistantUnavailable):
        await _claude(handler).complete("S", "U", {})
