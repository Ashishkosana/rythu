"""Pure geographic helpers."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from rythu_weather.domain.models import GeoPoint

_EARTH_RADIUS_KM = 6371.0088


def haversine_km(a: GeoPoint, b: GeoPoint) -> float:
    """Great-circle distance between two points, in km.

    Used to tell the farmer how far the model's grid cell is from their pin (the honest
    grid-snap disclosure).
    """
    lat1, lon1, lat2, lon2 = map(radians, (a.lat, a.lon, b.lat, b.lon))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * asin(sqrt(h))
