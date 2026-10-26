"""Where Rythu serves weather and advice: Telangana plus a border margin.

The rules, crop doses and schemes are Telangana-specific. Shared by the weather endpoint (refuse with
``outside_coverage``) and village search (only offer places we serve). Keep in sync with
``apps/web/lib/coverage.ts``.
"""

from __future__ import annotations

import math

COVERAGE_LAT = (15.7, 20.0)
COVERAGE_LON = (77.1, 81.5)


def in_coverage(lat: float, lon: float) -> bool:
    if not (math.isfinite(lat) and math.isfinite(lon)):
        return False
    return COVERAGE_LAT[0] <= lat <= COVERAGE_LAT[1] and COVERAGE_LON[0] <= lon <= COVERAGE_LON[1]
