from __future__ import annotations

import pytest

from rythu_weather.app.settings import Settings


def test_defaults_when_env_is_empty():
    s = Settings.from_env({})
    assert s == Settings(cache_table=None, open_meteo_timeout_s=4.0, log_level="INFO")


def test_reads_and_normalises_values():
    s = Settings.from_env(
        {"RYTHU_CACHE_TABLE": "rythu-cache", "RYTHU_OPEN_METEO_TIMEOUT_S": "2.5", "RYTHU_LOG_LEVEL": " debug "}
    )
    assert s.cache_table == "rythu-cache"
    assert s.open_meteo_timeout_s == 2.5
    assert s.log_level == "DEBUG"


def test_blank_values_fall_back_to_defaults():
    s = Settings.from_env({"RYTHU_CACHE_TABLE": "", "RYTHU_OPEN_METEO_TIMEOUT_S": "  "})
    assert s.cache_table is None
    assert s.open_meteo_timeout_s == 4.0


@pytest.mark.parametrize("raw", ["abc", "0", "-1", "61", "nan"])
def test_invalid_timeout_fails_fast_naming_the_variable(raw):
    with pytest.raises(ValueError, match="RYTHU_OPEN_METEO_TIMEOUT_S"):
        Settings.from_env({"RYTHU_OPEN_METEO_TIMEOUT_S": raw})


def test_invalid_log_level_fails_fast():
    with pytest.raises(ValueError, match="RYTHU_LOG_LEVEL"):
        Settings.from_env({"RYTHU_LOG_LEVEL": "LOUD"})
