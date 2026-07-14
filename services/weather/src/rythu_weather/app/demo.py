"""Runnable local demo: hit the LIVE Open-Meteo API for Bhupalpally and print the contract.

    uv run python -m rythu_weather.app.demo --crop cotton --water rainfed

This is the vertical-slice verification without a frontend: real data → adapter → pure rule
engine → the honest JSON a React screen will consume.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from rythu_weather.adapters.open_meteo import OpenMeteoHttpProvider
from rythu_weather.app.service import BHUPALPALLY, get_weather
from rythu_weather.domain.models import Crop, FarmerContext, GeoPoint, ProviderError, WaterSource


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Rythu weather slice — live Open-Meteo demo")
    p.add_argument("--crop", choices=[c.value for c in Crop], default=Crop.COTTON.value)
    p.add_argument("--water", choices=[w.value for w in WaterSource], default=WaterSource.RAINFED.value)
    p.add_argument("--lat", type=float, default=BHUPALPALLY.lat)
    p.add_argument("--lon", type=float, default=BHUPALPALLY.lon)
    return p.parse_args()


async def _run(args: argparse.Namespace) -> int:
    ctx = FarmerContext(
        now=datetime.now(ZoneInfo("Asia/Kolkata")),
        water_source=WaterSource(args.water),
        crop=Crop(args.crop),
    )
    provider = OpenMeteoHttpProvider()
    try:
        contract = await get_weather(provider, GeoPoint(args.lat, args.lon), ctx)
    except ProviderError as exc:
        print(f"Fetch failed: {exc}")
        return 1
    print(json.dumps(contract, indent=2, ensure_ascii=False))
    reads = contract["farming_read"]
    print(f"\n— {len(reads)} farming read(s) fired for crop={args.crop}, water={args.water} —")
    for r in reads:
        print(f"  [{r['severity']}] {r['id']}: {r['headline_en']}")
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_run(_parse_args())))


if __name__ == "__main__":
    main()
