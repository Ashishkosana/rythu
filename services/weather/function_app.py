"""Azure Functions entry point (Python v2 programming model): hosts the FastAPI app on Flex Consumption.

The whole HTTP API — /v1/weather, /healthz, the legacy /weather — is the same ASGI app the dev server
and tests use (``rythu_weather.api.app``); this file only adapts it to the Functions host. Logs go to
the host (and from there to Application Insights) as JSON lines.

A timer trigger pre-warms the forecast cache for every cell farmers use (``app/prewarm.py``).
Push alerts (``app/alert_jobs.py``): a timer three times a day queues the alerts due, and a queue
trigger sends each one — the queue gives retries and a poison queue (``alerts-poison``) for free.

Packaged for deployment by ``scripts/package_functions.sh``.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import azure.functions as func
import httpx

from rythu_weather.api.app import create_app
from rythu_weather.app.alert_jobs import deliver, evaluate
from rythu_weather.app.composition import build_accounts, build_assistant, build_push, build_services
from rythu_weather.app.prewarm import prewarm
from rythu_weather.app.settings import get_settings
from rythu_weather.observability import configure_logging

configure_logging(get_settings().log_level, to_host=True)
services = build_services()
accounts = build_accounts()
push = build_push()
assistant = build_assistant()  # None unless switched on and keyed

# ANONYMOUS: the API is public by design (no farmer data behind it yet); per-user routes in S13 bring
# their own token check in the app, not a shared Functions key baked into a phone app.
app = func.AsgiFunctionApp(
    app=create_app(services.provider, accounts=accounts, push=push, assistant=assistant),
    http_auth_level=func.AuthLevel.ANONYMOUS,
)

ALERT_QUEUE = "alerts"


# Every 20 minutes (NCRONTAB: second minute hour day month weekday). With a 15-minute refresh threshold
# a farmer's forecast is at most ~20 minutes old, inside the 30-minute freshness target.
@app.timer_trigger(arg_name="timer", schedule="0 */20 * * * *", run_on_startup=False, use_monitor=True)
async def prewarm_cells(timer: func.TimerRequest) -> None:
    parts = services.prewarm
    if parts is None:  # no shared store configured (e.g. local dev without Azurite)
        return
    await prewarm(
        parts.registry, parts.store, parts.upstream, now=datetime.now(ZoneInfo("Asia/Kolkata")),
        max_cells=parts.max_cells,
    )


# 06:45, 12:45 and 17:45 IST (the timer runs in UTC): before field work, midday, and in the evening for
# tomorrow's tasks. Never at night.
@app.timer_trigger(arg_name="timer", schedule="0 15 1,7,12 * * *", run_on_startup=False, use_monitor=True)
@app.queue_output(arg_name="out", queue_name=ALERT_QUEUE, connection="AzureWebJobsStorage")
async def evaluate_alerts(timer: func.TimerRequest, out: func.Out[list[str]]) -> None:
    if accounts is None or push is None:
        return
    messages = await evaluate(accounts.users, services.provider, datetime.now(UTC))
    if messages:
        out.set([json.dumps(m, ensure_ascii=False) for m in messages])


@app.queue_trigger(arg_name="msg", queue_name=ALERT_QUEUE, connection="AzureWebJobsStorage")
async def send_alert(msg: func.QueueMessage) -> None:
    if accounts is None or push is None:
        raise RuntimeError("push alerts are switched off; leaving the message for a retry")
    async with httpx.AsyncClient() as client:
        await deliver(json.loads(msg.get_body()), accounts.users, push.signer, subject=push.subject,
                      now=datetime.now(UTC), client=client)
