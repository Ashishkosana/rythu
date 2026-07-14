from __future__ import annotations

from builders import at
from rythu_weather.domain.reliability import format_relative_age, format_source_stamp


def test_relative_age_buckets():
    now = at(2026, 7, 15, 12, 0)
    assert format_relative_age(now, at(2026, 7, 15, 11, 59, 30)) == "just now"  # 30s < 2min
    assert format_relative_age(now, at(2026, 7, 15, 11, 59)) == "just now"  # 60s < 2min
    assert format_relative_age(now, at(2026, 7, 15, 11, 1)) == "59 min ago"
    assert format_relative_age(now, at(2026, 7, 15, 0, 30)) == "11 hr ago"
    # >24h falls back to a date label
    assert format_relative_age(now, at(2026, 7, 12, 9, 0)) == "12 Jul"


def test_relative_age_clamps_future_skew():
    now = at(2026, 7, 15, 12, 0)
    assert format_relative_age(now, at(2026, 7, 15, 12, 5)) == "just now"


def test_source_stamp_always_shows_resolution():
    now = at(2026, 7, 15, 12, 8)
    stamp = format_source_stamp(now, at(2026, 7, 15, 12, 0))
    assert stamp == "Source: Open-Meteo (~11 km) · updated 8 min ago"


def test_source_stamp_offline_prefix():
    now = at(2026, 7, 15, 12, 0)
    stamp = format_source_stamp(now, at(2026, 7, 14, 12, 0), is_offline_cache=True)
    assert stamp.startswith("Offline — showing saved forecast · ")
    assert "(~11 km)" in stamp
