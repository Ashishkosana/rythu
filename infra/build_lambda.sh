#!/usr/bin/env bash
# Stage the Lambda deployment asset: the pure service package + its (pure-Python) deps.
# No Docker needed — httpx and its deps ship as portable wheels.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
BUILD="$HERE/build/lambda"
SRC="$HERE/../services/weather/src/rythu_weather"

rm -rf "$BUILD"
mkdir -p "$BUILD"
cp -r "$SRC" "$BUILD/"
python3 -m pip install "httpx>=0.27" -t "$BUILD" --quiet --disable-pip-version-check
# trim bytecode / dist-info noise to keep the asset small
find "$BUILD" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$BUILD" -type d -name "*.dist-info" -prune -exec rm -rf {} +

echo "Lambda asset staged at $BUILD"
