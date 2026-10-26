"""The Azure Functions entry point: wiring, routing, request pass-through and log forwarding."""

from __future__ import annotations

import importlib.util
import json
import logging
from pathlib import Path

import azure.functions as func
import pytest

from builders import days_from, forecast, hours_from
from rythu_weather.adapters.fake import FakeProvider
from rythu_weather.api.app import create_app
from rythu_weather.app.handler import handle_request
from rythu_weather.observability import ROOT_LOGGER, configure_logging, log_event
from test_api import _FC

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def restore_logging():
    logger = logging.getLogger(ROOT_LOGGER)
    handlers, propagate, level = list(logger.handlers), logger.propagate, logger.level
    yield
    logger.handlers[:] = handlers
    logger.propagate = propagate
    logger.setLevel(level)


def _load_function_app():
    spec = importlib.util.spec_from_file_location("function_app", ROOT / "function_app.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _triggers(app, kind):
    return [b for fn in app.get_functions() for b in fn.get_bindings() if b.type == kind]


def test_entry_point_registers_one_anonymous_catch_all_http_function(restore_logging):
    app = _load_function_app().app
    [trigger] = _triggers(app, "httpTrigger")
    assert trigger.route == "/{*route}"
    assert trigger.auth_level == func.AuthLevel.ANONYMOUS


def test_prewarm_timer_runs_every_20_minutes(restore_logging):
    """20 min + a 15 min refresh threshold keeps a served forecast inside the 30 min freshness target."""
    [timer] = _triggers(_load_function_app().app, "timerTrigger")
    assert timer.schedule == "0 */20 * * * *"
    assert timer.run_on_startup is False  # never a burst of upstream calls on every cold start


def test_host_json_keeps_api_paths_unprefixed():
    """Functions prefixes routes with /api by default, which would turn /v1/weather into /api/v1/weather."""
    host = json.loads((ROOT / "host.json").read_text())
    assert host["extensions"]["http"]["routePrefix"] == ""
    assert host["version"] == "2.0"


async def _via_functions(provider, url: str, headers: dict[str, str] | None = None) -> func.HttpResponse:
    req = func.HttpRequest(method="GET", url=url, headers=headers or {}, body=b"")
    return await func.AsgiMiddleware(create_app(provider)).handle_async(req)


async def test_requests_pass_through_the_functions_adapter_unchanged():
    provider = FakeProvider(_FC)
    resp = await _via_functions(provider, "http://localhost/v1/weather?crop=chilli", {"X-Request-Id": "fn-1"})
    lam = await handle_request({"queryStringParameters": {"crop": "chilli"}, "headers": {"x-request-id": "fn-1"}},
                               provider)
    assert resp.status_code == 200
    assert json.loads(resp.get_body()) == json.loads(lam["body"])
    assert resp.headers["X-Request-Id"] == "fn-1"
    assert resp.headers["Cache-Control"] == lam["headers"]["Cache-Control"]


async def test_health_and_coverage_errors_through_the_functions_adapter():
    provider = FakeProvider(forecast(_FC.generated_at, hourly=hours_from(_FC.generated_at, 2),
                                     daily=days_from(_FC.generated_at.date(), 1)))
    health = await _via_functions(provider, "http://localhost/healthz")
    assert health.status_code == 200 and json.loads(health.get_body()) == {"status": "ok"}
    outside = await _via_functions(provider, "http://localhost/v1/weather?lat=13.08&lon=80.27")
    assert outside.status_code == 400
    assert json.loads(outside.get_body())["code"] == "outside_coverage"


def test_host_mode_forwards_json_lines_to_the_root_logger(restore_logging, caplog):
    """On Azure Functions the worker listens on the root logger; our fields must survive the trip."""
    configure_logging("INFO", to_host=True)
    caplog.set_level(logging.INFO)  # caplog's handler sits on the root logger, like the worker's
    log_event(logging.getLogger(ROOT_LOGGER + ".app.weather_request"), logging.INFO, "weather.request",
              outcome="ok", cell="18.4,79.9")
    [record] = [r for r in caplog.records if "weather.request" in r.getMessage()]
    doc = json.loads(record.getMessage())
    assert doc["event"] == "weather.request" and doc["outcome"] == "ok" and doc["cell"] == "18.4,79.9"
    assert record.name == ROOT_LOGGER + ".app.weather_request"  # category preserved for filtering


def test_host_mode_keeps_exceptions(restore_logging, caplog):
    configure_logging("INFO", to_host=True)
    caplog.set_level(logging.INFO)
    try:
        raise ZeroDivisionError("bug in a rule")
    except ZeroDivisionError:
        logging.getLogger(ROOT_LOGGER + ".x").exception("weather.unhandled_error")
    [record] = [r for r in caplog.records if "weather.unhandled_error" in r.getMessage()]
    assert "ZeroDivisionError: bug in a rule" in json.loads(record.getMessage())["exc"]
    assert record.exc_info is not None and record.exc_info[0] is ZeroDivisionError
