"""Structured logging + request correlation.

Every log line is one JSON object on stdout (CloudWatch today, Application Insights after the Azure
move), so it can be filtered by field instead of grepped. Each request gets a correlation id that
is attached to every line logged while handling it and returned to the caller as ``X-Request-Id``,
so a farmer-visible failure can be traced to the exact log lines.

Usage::

    log_event(_log, logging.INFO, "cache.result", result="hit", key=key)

Privacy: never log raw coordinates — log a coarse cell (see ``handler._cell``).
"""

from __future__ import annotations

import json
import logging
import re
import sys
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

ROOT_LOGGER = "rythu_weather"

_request_id: ContextVar[str | None] = ContextVar("rythu_request_id", default=None)
# Accept a caller-supplied id only if it is short and log-safe (no spaces/newlines → no log injection).
_SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,128}")


def resolve_request_id(candidate: str | None) -> str:
    """Use the caller's id when it is safe, else mint a new one."""
    if candidate and _SAFE_REQUEST_ID.fullmatch(candidate):
        return candidate
    return uuid.uuid4().hex


def current_request_id() -> str | None:
    return _request_id.get()


@contextmanager
def request_context(request_id: str) -> Iterator[None]:
    """Bind ``request_id`` to every log line emitted inside the block."""
    token = _request_id.set(request_id)
    try:
        yield
    finally:
        _request_id.reset(token)


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    """Log a named event with structured fields (rendered as top-level JSON keys)."""
    logger.log(level, event, extra={"fields": fields})


class JsonFormatter(logging.Formatter):
    """Render a record as a single JSON line: ts, level, logger, event, request_id, fields, exc."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        request_id = current_request_id()
        if request_id is not None:
            payload["request_id"] = request_id
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            # Fixed keys win, so a field can never spoof the level or the event name.
            payload = {**fields, **payload}
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


_HANDLER_MARK = "_rythu_json_handler"


def configure_logging(level: str = "INFO") -> None:
    """Send the service's logs to stdout as JSON. Idempotent (warm invocations call it again).

    Only the ``rythu_weather`` logger tree is configured, and it does not propagate to the root
    logger, so the host runtime's own handler (Lambda / Azure Functions) cannot double-log or
    re-format our lines.
    """
    logger = logging.getLogger(ROOT_LOGGER)
    logger.setLevel(level)
    if any(getattr(h, _HANDLER_MARK, False) for h in logger.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    setattr(handler, _HANDLER_MARK, True)
    logger.addHandler(handler)
    logger.propagate = False
