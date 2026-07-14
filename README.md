# 🌾 Rythu (రైతు)

**A Telugu-first, honest weather + crop-advisory + market app for small farmers in
Bhupalpally, Telangana.** We sell you nothing — the advice is neutral, explainable, and framed
truthfully (no fake precision, no over-promising).

> Status: **weather vertical slice** is built end-to-end (live data → farmer-safe advice → a
> mobile screen). Crops → market → onboarding → alerts come next. See [`docs/`](docs/).

## What works today

- **Honest weather** from [Open-Meteo](https://open-meteo.com) (free, no key): rain *chance*
  (never a fake "confidence"), a fixed "~11 km, can be wrong, watch the sky" line, source +
  last-updated stamp, and the grid-cell snap disclosed.
- **Farmer-safe "farming reads"** — spray / irrigate / sow / harvest / drainage advice, each
  conservative, probability-framed, with a "Why?" caveat and a cited agronomy source. Every
  rule was adversarially reviewed for farmer-safety (see [`docs/weather-slice-spec.md`](docs/weather-slice-spec.md)).
- **Crops:** chilli (mirchi), cotton, paddy, red gram, maize. **Telugu ⇄ English** toggle.

## Architecture

```
apps/web        Next.js + TypeScript + Tailwind — the mobile screen
services/weather  Python, hexagonal — Open-Meteo → farming-read engine → typed JSON  (runs on AWS Lambda)
infra           AWS CDK (Python) — API Gateway + Lambda + DynamoDB cache
docs            problem statement, market research, verified weather spec, prototype
```

## Run it locally (two terminals)

**1. Backend** (Python 3.12, needs [uv](https://docs.astral.sh/uv/)):

```bash
cd services/weather
uv sync --extra dev
uv run python -m rythu_weather.app.local_server 8001      # http://127.0.0.1:8001/weather
```

**2. Frontend** (Node 18+):

```bash
cd apps/web
npm install
npm run dev                                                # http://localhost:3000
```

Open `http://localhost:3000`. To use it from a **phone on the same Wi-Fi**, run the frontend
with `npx next dev -H 0.0.0.0` and open `http://<your-computer-ip>:3000`.

Quality gate (backend): `cd services/weather && uv run ruff check . && uv run mypy && uv run pytest`

## Guardrails (please keep these)

- **Truthful weather** — probability, not certainty; show source + resolution + last-updated;
  never call it "hyperlocal" or "Apple-grade".
- **Farmer-safe advice** — conservative, cited, with caveats. New crop/pest rules must be
  agronomically verified before shipping (thresholds marked `TODO-VET` need district-agri-office sign-off).
- **We sell nothing** — no input-sales funnel, ever. Free for farmers, forever.
