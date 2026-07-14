"""Tiny stdlib HTTP server that exposes the weather handler for local / LAN development.

This is a DEV convenience, not the production path (that's AWS Lambda via ``handler.handler``).
It reuses ``handle_request`` verbatim, so it exercises the real engine.

    uv run python -m rythu_weather.app.local_server 8001
"""

from __future__ import annotations

import asyncio
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from rythu_weather.app.handler import build_provider, handle_request


class _WeatherRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") not in ("", "/weather"):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error":"not found"}')
            return
        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        event: dict[str, Any] = {"queryStringParameters": query}
        resp = asyncio.run(handle_request(event, build_provider()))
        body = str(resp["body"]).encode("utf-8")
        self.send_response(int(resp["statusCode"]))
        for key, value in dict(resp["headers"]).items():
            self.send_header(str(key), str(value))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        pass  # keep the console quiet


def main(host: str = "127.0.0.1", port: int = 8001) -> None:
    print(f"Rythu weather dev server → http://{host}:{port}/weather?crop=cotton&water=rainfed")
    ThreadingHTTPServer((host, port), _WeatherRequestHandler).serve_forever()


if __name__ == "__main__":
    main(port=int(sys.argv[1]) if len(sys.argv) > 1 else 8001)
