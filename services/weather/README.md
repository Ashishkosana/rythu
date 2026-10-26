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

# The HTTP API (FastAPI) on http://127.0.0.1:8001 — /v1/weather, /v1/geocode, /healthz, docs at /docs:
uv run python -m rythu_weather.app.local_server 8001

# Quality gate:
uv run ruff check . && uv run mypy && uv run pytest
uv run pytest -m live       # the one network test (hits Open-Meteo)

# Table Storage tests run against Azurite (skipped if it isn't running; CI requires it):
npx azurite@3.37.0 azurite-table --inMemoryPersistence --tableHost 127.0.0.1 --tablePort 10002
```

## Layers

```
api/          FastAPI transport — /v1/weather, /v1/geocode, /healthz, OpenAPI; Pydantic schemas = the contract
function_app.py  Azure Functions entry point: the same FastAPI app on Flex Consumption (logs → host → App Insights)
app/          handler.py (Lambda transport) · weather_request.py (shared parse → validate → answer → log)
              geocode_request.py (village search: validate → search → shape → log)
              service.py (use case) · serialize.py (THE wire shape) · composition.py (wiring) · settings.py
domain/       pure rules, windows, models — no I/O, no clock, no logging (enforced by test_domain_purity)
adapters/     Open-Meteo HTTP, read-through cache (DynamoDB · Azure Table Storage), geocoding, fakes
```

Both transports are thin adapters over `app.weather_request.answer_weather`, so they cannot drift;
`tests/test_api.py` checks they return identical status, headers and JSON. The Lambda path never
imports FastAPI/Pydantic (also tested), so its bundle is still just `httpx`.
`tests/test_contract_schema.py` (the golden test) proves `api/schemas.py` matches the serializer exactly.

## Deploying to Azure Functions

`./scripts/package_functions.sh` stages `dist/functions/` (`function_app.py`, `host.json`,
`rythu_weather/`, and a `requirements.txt` exported from `uv.lock` without dev tools). Flex Consumption
installs the requirements with a remote build on Azure. `tests/test_function_app.py` drives real requests
through the Functions ASGI adapter. Infrastructure and the deploy workflow: see `infra/azure/`.

## Keeping it fast and inside the free quota (S7)

On Azure the request path is `RegisteringProvider → CachedProvider → BudgetedProvider → Open-Meteo`:
each request notes its ~11 km cell (throttled to one write per cell per hour), cache hits return in
milliseconds, and cache misses spend from a **shared hourly budget** (Table Storage counter with ETag
optimistic concurrency; a burst is refused, a storage error fails open). A timer
(`function_app.py`, every 20 min) **pre-warms** every cell used in the last 14 days, so farmers almost
never wait on Open-Meteo. Defaults keep the worst case at 7,200 calls/day, under 80 % of Open-Meteo's
free tier (a test enforces the arithmetic).

## Village search (S9)

`GET /v1/geocode?q=Regonda` → `{"results": [{id, name, name_te, admin2, admin1, lat, lon}]}`, only places
inside coverage. OpenStreetMap Nominatim first (best coverage of small villages, and `name_te` = the
Telugu name when OSM has one), Open-Meteo's geocoder as fallback. Nominatim's
[usage policy](https://operations.osmfoundation.org/policies/nominatim/) shapes the design: an
identifying User-Agent, **at most one upstream call per second** (per process), results cached for a
day, and **no autocomplete** — the app searches when the farmer taps the search button.
A 200 with an empty list means a source really found nothing; when no source could be asked (all
failed, or too many searches queued) the answer is **503 `upstream_unavailable`**, so the app says
"try again" instead of "no such village". The query is never logged, only its length and outcome.
Served by the FastAPI app (local + Azure) only: the AWS Lambda keeps just `/weather` — its front end
is offline and AWS retires in S10, so the web app needs a FastAPI backend for search.

## Configuration & logs

All settings are environment variables, parsed and validated once at startup in
`app/settings.py` (a bad value fails the cold start, naming the variable):

| Variable | Default | Meaning |
| --- | --- | --- |
| `RYTHU_CACHE_TABLE` | unset | DynamoDB forecast-cache table (AWS) |
| `RYTHU_AZURE_TABLES_ENDPOINT` | unset | Azure Table Storage forecast cache via the app's **managed identity** — no secret (how Azure runs) |
| `RYTHU_AZURE_TABLES_CONNECTION_STRING` | unset | same cache via a connection string — for local Azurite. **Secret**: never logged or in `repr` |
| `RYTHU_AZURE_FORECAST_TABLE` | `forecast` | table name for the Azure cache |
| `RYTHU_OPEN_METEO_TIMEOUT_S` | `4` | total deadline for one Open-Meteo fetch, (0, 60] |
| `RYTHU_LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `RYTHU_UPSTREAM_BUDGET_PER_HOUR` | `120` | on-demand Open-Meteo calls per hour across all instances (1–400) |
| `RYTHU_PREWARM_MAX_CELLS` | `60` | most cells the 20-minute pre-warm refreshes (0–100) |

At most one cache backend may be set (more = startup error); none = no cache.

Logs are one JSON object per line on stdout (`rythu_weather/observability.py`). Every request
gets a correlation id — the caller's `X-Request-Id` if it is safe, else API Gateway's request id,
else a new one — stamped on every line and returned as the `X-Request-Id` response header.
Events: `weather.request` (one summary per request: status, outcome, latency, ~11 km cell),
`weather.degraded`, `weather.unhandled_error` (with traceback), `upstream.open_meteo`,
`cache.result` (`hit` / `miss` / `refreshed` / `stale_served` / `miss_upstream_failed`), and
`cache.read_failed` / `cache.write_failed` / `cache.item_malformed`. Raw coordinates are never logged.

## Status

v0 slice complete: domain + rules + live Open-Meteo adapter, verified end-to-end.
**Next:** AWS Lambda handler + API Gateway + CDK (nightly cache), then the Next.js screen +
Telugu voice output. Numbers marked `TODO-VET` in `rules.py` need district-agri-office sign-off
before pilot.
