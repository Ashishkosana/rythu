# Rythu infra (AWS CDK, Python)

The weather slice's cloud backend:

```
API Gateway (HTTP API)  ──GET /weather──▶  Lambda (rythu_weather.app.handler)  ──▶  DynamoDB (forecast cache, TTL)
```

- **DynamoDB** — read-through forecast cache (`pk` = grid-rounded lat/lon, `ttl` auto-expiry),
  pay-per-request (free-tier friendly). Cuts Open-Meteo calls and powers the offline-cache path.
- **Lambda** (Python 3.12) — runs the hexagonal weather service; `RYTHU_CACHE_TABLE` wires the cache.
- **HTTP API** — `GET /weather?lat=&lon=&crop=&water=`.

Region: `ap-south-1` (Mumbai, closest to Telangana).

## Use

```bash
uv venv --python 3.12 && uv pip install "aws-cdk-lib>=2.170,<3" "constructs>=10.3,<11"
cdk synth                       # author/verify — no AWS account needed
cdk deploy                      # needs AWS creds (personal account)
```

**Deploy note:** the Lambda asset is the pure service source; the `httpx` dependency is **not
bundled yet**. Before `cdk deploy`, add it via a Lambda layer or switch `WeatherFn` to a
bundling construct (`aws-lambda-python-alpha` `PythonFunction`, or `uv pip install --target`).
See the `DEPLOY NOTE` in `rythu_infra/weather_stack.py`. `cdk synth` works without it.
