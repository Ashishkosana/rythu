"""Write the API's OpenAPI document — the source the web app's TypeScript types are generated from.

    uv run python -m rythu_weather.api.openapi_export            # rewrites services/weather/openapi.json
    uv run python -m rythu_weather.api.openapi_export -          # prints to stdout

The committed ``openapi.json`` is the contract between backend and frontend: ``tests/test_openapi_file.py``
fails if it is stale, and the web CI fails if ``apps/web/lib/api.gen.ts`` was not regenerated from it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from rythu_weather.adapters.fake import FailingProvider
from rythu_weather.api.app import create_app

DEFAULT_PATH = Path(__file__).resolve().parents[3] / "openapi.json"


def openapi_document() -> dict[str, Any]:
    # The schema doesn't depend on the provider; a fake keeps this free of settings and network.
    return create_app(FailingProvider()).openapi()


def render() -> str:
    """Stable text: same input → byte-identical output, so a diff means the contract changed."""
    return json.dumps(openapi_document(), indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> None:
    text = render()
    if argv[:1] == ["-"]:
        sys.stdout.write(text)
        return
    target = Path(argv[0]) if argv else DEFAULT_PATH
    target.write_text(text, encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main(sys.argv[1:])
