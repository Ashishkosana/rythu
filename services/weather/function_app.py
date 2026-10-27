"""Azure Functions entry point (Python v2 programming model): hosts the FastAPI app on Flex Consumption.

The whole HTTP API — /v1/weather, /healthz, the legacy /weather — is the same ASGI app the dev server
and tests use (``rythu_weather.api.app``); this file only adapts it to the Functions host. Logs go to
the host (and from there to Application Insights) as JSON lines.

Packaged for deployment by ``scripts/package_functions.sh``.
"""

from __future__ import annotations

import azure.functions as func

from rythu_weather.api.app import create_app
from rythu_weather.app.settings import get_settings
from rythu_weather.observability import configure_logging

configure_logging(get_settings().log_level, to_host=True)

# ANONYMOUS: the API is public by design (no farmer data behind it yet); per-user routes in S13 bring
# their own token check in the app, not a shared Functions key baked into a phone app.
app = func.AsgiFunctionApp(app=create_app(), http_auth_level=func.AuthLevel.ANONYMOUS)
