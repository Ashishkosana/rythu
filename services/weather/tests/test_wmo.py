from __future__ import annotations

from rythu_weather.domain.models import WMOCategory
from rythu_weather.domain.wmo import THUNDERSTORM_CODES, WMO_TABLE, lookup


def test_all_expected_codes_present():
    expected = {0, 1, 2, 3, 45, 48, 51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99}
    assert set(WMO_TABLE) == expected


def test_every_condition_has_valid_category_and_note():
    for cond in WMO_TABLE.values():
        assert isinstance(cond.category, WMOCategory)
        assert cond.emoji
        assert cond.farm_note


def test_thunderstorm_codes_map_to_thunderstorm_category():
    for code in THUNDERSTORM_CODES:
        assert WMO_TABLE[code].category is WMOCategory.THUNDERSTORM


def test_lookup_handles_unknown_and_none():
    assert lookup(None).en_short == "Unknown"
    assert lookup(12345).en_short == "Unknown"
    assert lookup(95).category is WMOCategory.THUNDERSTORM
