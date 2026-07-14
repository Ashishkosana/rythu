# Rythu — Weather service

Turns **Open-Meteo** forecast data into an **honest** weather picture plus **farmer-safe
"farming read" advisories** for Bhupalpally, Telangana. Python, hexagonal, deploys to AWS
Lambda. This is the first vertical slice of [Rythu](../../docs/problem-statement.md).

## Why it's built this way

- **Honest by construction.** The free Open-Meteo endpoint is a single ~11 km global model
  run with *no* uncertainty field, so we show **no fabricated confidence score** — we lead
  with the real rain *chance*, a fixed "this can be wrong / ~11 km / watch the sky" line, and
  a source + last-updated stamp. We disclose the grid-cell snap (your pin vs the cell the
  model answered for). Never "hyperlocal".
- **Advice that can't quietly hurt a farmer.** Every farming rule was researched against
  agri-extension sources and then adversarially reviewed for farmer-safety (see
  [`docs/weather-slice-spec.md`](../../docs/weather-slice-spec.md)). Rules are conservative,
  probability-framed, carry a mandatory caveat, and cite a source. The pink-bollworm spray
  rule was *deferred* because it isn't safe without crop-stage data.
- **Hexagonal + pure domain.** `domain/` has no network, no clock, no env — the current time
  is an input (`FarmerContext.now`), so every "next 6 h / this morning" rule is deterministic
  and unit-tested. A CI test parses the domain AST to keep it that way.

```
src/rythu_weather/
  domain/      # pure: models · wmo table · windows/null helpers · reliability · rules · engine
  adapters/    # open_meteo (live HTTP) · fake (tests)          <- implement the WeatherProvider port
  app/         # serialize (typed contract) · service (orchestration) · demo (live CLI)
```

Data flow: `adapter.fetch()` -> domain `Forecast` -> `engine.evaluate_reads()` -> `serialize`
-> typed JSON. The client never sees a raw Open-Meteo field.

## Run it

```bash
uv sync --extra dev

# Live end-to-end against the real API (no key needed):
uv run python -m rythu_weather.app.demo --crop cotton --water rainfed

# Quality gate:
uv run ruff check . && uv run mypy && uv run pytest
uv run pytest -m live       # the one network test (hits Open-Meteo)
```

## Status

v0 slice complete: domain + rules + live Open-Meteo adapter, verified end-to-end.
**Next:** AWS Lambda handler + API Gateway + CDK (nightly cache), then the Next.js screen +
Telugu voice output. Numbers marked `TODO-VET` in `rules.py` need district-agri-office sign-off
before pilot.
