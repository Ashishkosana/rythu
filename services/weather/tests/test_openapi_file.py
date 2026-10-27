"""The committed openapi.json must match the code — it is what the web app's types are generated from."""

from __future__ import annotations

from rythu_weather.api.openapi_export import DEFAULT_PATH, render


def test_committed_openapi_json_is_up_to_date():
    committed = DEFAULT_PATH.read_text(encoding="utf-8") if DEFAULT_PATH.exists() else ""
    assert committed == render(), (
        "services/weather/openapi.json is stale. Regenerate it and the web types:\n"
        "  cd services/weather && uv run python -m rythu_weather.api.openapi_export\n"
        "  cd apps/web && npm run gen:api"
    )


def test_render_is_deterministic():
    assert render() == render()
