#!/usr/bin/env bash
# Stage the Azure Functions deployment package: exactly what the Functions host needs, nothing else.
#
#   dist/functions/
#     function_app.py   host.json   requirements.txt   rythu_weather/
#
# requirements.txt is exported from uv.lock (pinned, no dev tools), and Flex Consumption installs it
# with a remote build on Azure (Linux wheels built there, not on this machine).
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$HERE/dist/functions"

rm -rf "$OUT"
mkdir -p "$OUT"
cp "$HERE/function_app.py" "$HERE/host.json" "$OUT/"
cp -r "$HERE/src/rythu_weather" "$OUT/"
uv export --project "$HERE" --frozen --no-emit-project --no-hashes --extra functions --no-header \
  --output-file "$OUT/requirements.txt" >/dev/null
find "$OUT" -type d -name "__pycache__" -prune -exec rm -rf {} +

echo "Functions package staged at $OUT"
