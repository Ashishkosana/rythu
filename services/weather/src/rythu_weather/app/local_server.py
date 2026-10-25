"""Local / LAN development server: the FastAPI app under uvicorn.

This is a DEV convenience, not a production path (today that is AWS Lambda via ``handler.handler``;
after S6 it is the same FastAPI app on Azure Functions). It serves the real app, so it exercises
the real engine, the ``/v1`` contract and the interactive docs:

    uv run python -m rythu_weather.app.local_server 8001
    # http://127.0.0.1:8001/v1/weather?crop=cotton   (and the legacy /weather the web app calls)
    # http://127.0.0.1:8001/docs                     (try the API in the browser)
"""

from __future__ import annotations

import sys

import uvicorn

from rythu_weather.api.app import create_app
from rythu_weather.app.settings import get_settings
from rythu_weather.observability import configure_logging


def main(host: str = "127.0.0.1", port: int = 8001) -> None:
    configure_logging(get_settings().log_level)
    print(f"Rythu API dev server → http://{host}:{port}/v1/weather?crop=cotton · docs: http://{host}:{port}/docs")
    # Access lines are replaced by the structured weather.request log.
    uvicorn.run(create_app(), host=host, port=port, access_log=False, log_level="warning")


if __name__ == "__main__":
    main(port=int(sys.argv[1]) if len(sys.argv) > 1 else 8001)
