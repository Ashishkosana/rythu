from __future__ import annotations

import io
import json
import logging

import pytest

from rythu_weather.observability import (
    ROOT_LOGGER,
    JsonFormatter,
    configure_logging,
    current_request_id,
    log_event,
    request_context,
    resolve_request_id,
)


def _record(msg: str = "cache.result", **extra) -> logging.LogRecord:
    rec = logging.LogRecord(ROOT_LOGGER + ".x", logging.INFO, __file__, 1, msg, None, None)
    for k, v in extra.items():
        setattr(rec, k, v)
    return rec


def test_formatter_emits_one_json_line_with_fields_and_request_id():
    with request_context("req-123"):
        line = JsonFormatter().format(_record(fields={"result": "hit", "age_s": 12}))
    assert "\n" not in line
    doc = json.loads(line)
    assert doc["event"] == "cache.result"
    assert doc["level"] == "INFO"
    assert doc["logger"] == "rythu_weather.x"
    assert doc["request_id"] == "req-123"
    assert doc["result"] == "hit" and doc["age_s"] == 12
    assert doc["ts"].endswith("+00:00")


def test_fields_cannot_spoof_fixed_keys():
    doc = json.loads(JsonFormatter().format(_record(fields={"level": "DEBUG", "event": "fake"})))
    assert doc["level"] == "INFO"
    assert doc["event"] == "cache.result"


def test_exception_traceback_is_included():
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        import sys

        rec = _record(exc_info=sys.exc_info())
    doc = json.loads(JsonFormatter().format(rec))
    assert "RuntimeError: boom" in doc["exc"]


def test_non_json_values_are_stringified_and_telugu_kept_readable():
    doc_line = JsonFormatter().format(_record(fields={"obj": object(), "te": "వర్షం"}))
    assert "వర్షం" in doc_line  # ensure_ascii=False — readable in the log viewer
    assert json.loads(doc_line)["obj"].startswith("<object")


def test_request_context_is_scoped():
    assert current_request_id() is None
    with request_context("abc"):
        assert current_request_id() == "abc"
    assert current_request_id() is None


@pytest.mark.parametrize("candidate", ["abc-123", "a.b_c", "x" * 128])
def test_safe_caller_request_ids_are_kept(candidate):
    assert resolve_request_id(candidate) == candidate


@pytest.mark.parametrize("candidate", [None, "", "has space", "line\nbreak", "x" * 129, '"quoted"'])
def test_unsafe_or_missing_request_ids_are_replaced(candidate):
    rid = resolve_request_id(candidate)
    assert rid != candidate
    assert len(rid) == 32 and rid.isalnum()


@pytest.fixture
def clean_root_logger():
    """configure_logging mutates the shared logger tree — restore it so other tests' caplog works."""
    logger = logging.getLogger(ROOT_LOGGER)
    handlers, propagate, level = list(logger.handlers), logger.propagate, logger.level
    yield logger
    logger.handlers[:] = handlers
    logger.propagate = propagate
    logger.setLevel(level)  # setLevel (not attribute assignment) also clears the level cache


def test_configure_logging_is_idempotent_and_writes_json(clean_root_logger, monkeypatch):
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    configure_logging("INFO")
    configure_logging("INFO")  # warm invocation: must not add a second handler
    assert len(clean_root_logger.handlers) == 1
    assert clean_root_logger.propagate is False

    log_event(logging.getLogger(ROOT_LOGGER + ".adapters.cache"), logging.INFO, "cache.result", result="miss")
    doc = json.loads(out.getvalue().strip())
    assert doc["event"] == "cache.result" and doc["result"] == "miss"


def test_configure_logging_respects_level(clean_root_logger, monkeypatch):
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    configure_logging("WARNING")
    logging.getLogger(ROOT_LOGGER + ".x").info("quiet")
    assert out.getvalue() == ""
