"""Azure Functions entry point (Python v2 programming model): hosts the FastAPI app on Flex Consumption.

The whole HTTP API — /v1/weather, /healthz, the legacy /weather — is the same ASGI app the dev server
and tests use (``rythu_weather.api.app``); this file only adapts it to the Functions host. Logs go to
the host (and from there to Application Insights) as JSON lines.

A timer trigger pre-warms the forecast cache for every cell farmers use (``app/prewarm.py``).

Packaged for deployment by ``scripts/package_functions.sh``.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import azure.functions as func

from rythu_weather.api.app import create_app
from rythu_weather.app.composition import build_services
from rythu_weather.app.prewarm import prewarm
from rythu_weather.app.settings import get_settings
from rythu_weather.observability import configure_logging

configure_logging(get_settings().log_level, to_host=True)
services = build_services()

# ANONYMOUS: the API is public by design (no farmer data behind it yet); per-user routes in S13 bring
# their own token check in the app, not a shared Functions key baked into a phone app.
app = func.AsgiFunctionApp(app=create_app(services.provider), http_auth_level=func.AuthLevel.ANONYMOUS)


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
