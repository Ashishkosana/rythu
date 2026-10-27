"""Ask Rythu's model: Claude through the Anthropic SDK (S17).

Imported lazily by ``app.composition`` — the old Lambda path never loads the SDK.

* The system prompt (instructions + corpus) is cached: it is identical for every question until the
  next deploy, and it is most of the input.
* Structured output: the reply is JSON matching ``app.assistant.answer_schema``.
* ``fallbacks: "default"``: if the model's safety classifier declines, the API re-runs the request on
  the model Anthropic recommends for that case instead of returning a refusal (only on the models
  that accept the parameter).
* One retry, a 25 s deadline: a farmer is waiting, and the app offers the Kisan Call Centre instead.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

import anthropic
from anthropic.types.beta import BetaOutputConfigParam, BetaTextBlockParam

from rythu_weather.app.assistant import AssistantUnavailable, ModelReply
from rythu_weather.observability import log_event

_log = logging.getLogger(__name__)

TIMEOUT_S = 25.0
MAX_TOKENS = 4096  # a short answer plus the model's reasoning; caps the cost of one question
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MODELS_WITH_FALLBACKS = frozenset({"claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5", "claude-fable-5-1"})

Effort = Literal["low", "medium", "high"]


class ClaudeAnswerModel:
    def __init__(self, api_key: str, model: str, effort: Effort, *,
                 client: anthropic.AsyncAnthropic | None = None) -> None:
        self.model = model
        self.effort = effort
        self._client = client or anthropic.AsyncAnthropic(api_key=api_key, timeout=TIMEOUT_S, max_retries=1)

    async def complete(self, system: str, user: str, schema: dict[str, Any]) -> ModelReply:
        fallbacks = self.model in MODELS_WITH_FALLBACKS
        cached_prefix: BetaTextBlockParam = {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
        output: BetaOutputConfigParam = {"effort": self.effort, "format": {"type": "json_schema", "schema": schema}}
        try:
            msg = await self._client.beta.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=[cached_prefix],
                messages=[{"role": "user", "content": user}],
                output_config=output,
                betas=[FALLBACK_BETA] if fallbacks else anthropic.omit,
                fallbacks="default" if fallbacks else anthropic.omit,
            )
        except anthropic.APIConnectionError as exc:  # network, including timeouts — after the SDK's one retry
            log_event(_log, logging.WARNING, "assistant.model_unavailable", error=type(exc).__name__)
            raise AssistantUnavailable from exc
        except anthropic.APIStatusError as exc:
            if exc.status_code == 429 or exc.status_code >= 500:  # rate limit, overloaded (529), server error
                log_event(_log, logging.WARNING, "assistant.model_unavailable", status=exc.status_code)
            else:  # 400/401/403/404: our request or configuration is wrong — loud in the logs
                log_event(_log, logging.ERROR, "assistant.model_rejected", status=exc.status_code,
                          request_id=getattr(exc, "request_id", None), error=str(exc)[:300])
            raise AssistantUnavailable from exc
        texts = [b.text for b in msg.content if b.type == "text"]
        usage = msg.usage
        return ModelReply(
            text=texts[-1] if texts else None,  # after a server-side fallback the last text is the answer
            stop_reason=str(msg.stop_reason),
            model=msg.model,
            input_tokens=usage.input_tokens,
            cache_read_tokens=usage.cache_read_input_tokens or 0,
            cache_write_tokens=usage.cache_creation_input_tokens or 0,
            output_tokens=usage.output_tokens,
        )
