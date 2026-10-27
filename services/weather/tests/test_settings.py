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


def test_token_signing_key_is_secret_and_validated():
    s = Settings.from_env({"RYTHU_TOKEN_SIGNING_KEY": "s" * 40})
    assert s.token_signing_key == b"s" * 40
    assert "sss" not in repr(s)
    assert Settings.from_env({}).token_signing_key is None
    with pytest.raises(ValueError, match="at least 32"):
        Settings.from_env({"RYTHU_TOKEN_SIGNING_KEY": "short"})


def test_an_unresolved_key_vault_reference_is_never_used_as_a_key():
    ref = "@Microsoft.KeyVault(SecretUri=https://kv.vault.azure.net/secrets/token-signing-key)"
    s = Settings.from_env({"RYTHU_TOKEN_SIGNING_KEY": ref})
    assert s.token_signing_key is None
    assert s.token_signing_key_problem is not None and "Key Vault Secrets User" in s.token_signing_key_problem


def test_users_table_and_registration_limit():
    s = Settings.from_env({"RYTHU_AZURE_USERS_TABLE": "people", "RYTHU_DEVICE_REGISTRATIONS_PER_HOUR": "5"})
    assert (s.azure_users_table, s.device_registrations_per_hour) == ("people", 5)
    assert Settings.from_env({}).azure_users_table == "users"
    with pytest.raises(ValueError):
        Settings.from_env({"RYTHU_AZURE_USERS_TABLE": "no-dashes"})
    with pytest.raises(ValueError):
        Settings.from_env({"RYTHU_DEVICE_REGISTRATIONS_PER_HOUR": "0"})


def test_accounts_switch_off_in_azure_without_a_key_but_weather_is_unaffected(caplog):
    from rythu_weather.app.composition import build_accounts

    ref = "@Microsoft.KeyVault(SecretUri=https://kv.vault.azure.net/secrets/token-signing-key)"
    endpoint = "https://x.table.core.windows.net"
    s = Settings.from_env({"RYTHU_AZURE_TABLES_ENDPOINT": endpoint, "RYTHU_TOKEN_SIGNING_KEY": ref})
    assert build_accounts(s) is None
    [record] = [r for r in caplog.records if r.getMessage() == "accounts.disabled"]
    assert "Key Vault Secrets User" in record.fields["reason"]  # type: ignore[attr-defined]
    local = build_accounts(Settings.from_env({}))  # local dev: a throwaway key, in-memory users
    assert local is not None


def test_vapid_key_id_must_be_a_key_vault_key():
    ok = "https://kv-rythu-dev-abc.vault.azure.net/keys/vapid"
    assert Settings.from_env({"RYTHU_VAPID_KEY_ID": ok}).vapid_key_id == ok
    assert Settings.from_env({}).vapid_key_id is None
    for bad in ("http://kv.vault.azure.net/keys/vapid", "https://evil.example/keys/vapid", "https://kv.vault.azure.net/secrets/x"):
        with pytest.raises(ValueError, match="Key Vault key URL"):
            Settings.from_env({"RYTHU_VAPID_KEY_ID": bad})


def test_vapid_subject_is_a_contact_url():
    assert Settings.from_env({}).vapid_subject.startswith("https://")
    mail = "mailto:pilot@example.com"
    assert Settings.from_env({"RYTHU_VAPID_SUBJECT": mail}).vapid_subject == mail
    with pytest.raises(ValueError, match="RFC 8292"):
        Settings.from_env({"RYTHU_VAPID_SUBJECT": "pilot@example.com"})


def test_push_is_off_in_azure_without_a_key_and_ephemeral_locally():
    from rythu_weather.app.composition import build_push

    assert build_push(Settings.from_env({"RYTHU_AZURE_TABLES_ENDPOINT": "https://x.table.core.windows.net"})) is None
    assert build_push(Settings.from_env({})) is not None


def test_ask_rythu_is_off_unless_switched_on_and_keyed(caplog):
    from rythu_weather.app.composition import build_assistant

    s = Settings.from_env({})
    assert (s.assistant_enabled, s.assistant_model, s.assistant_effort) == (False, "claude-opus-5-5", "low")
    assert (s.assistant_per_device_per_day, s.assistant_daily_cap) == (10, 200)
    assert build_assistant(s) is None  # the default is off
    keyed = {"RYTHU_ANTHROPIC_API_KEY": "sk-ant-api-secretvalue"}
    assert build_assistant(Settings.from_env(keyed)) is None  # a key alone does not switch it on
    on = Settings.from_env({**keyed, "RYTHU_ASSISTANT_ENABLED": "true"})
    assert "secretvalue" not in repr(on)
    bot = build_assistant(on)
    assert bot is not None and bot.per_device_per_day == 10 and len(bot.corpus) > 50
    ref = "@Microsoft.KeyVault(SecretUri=https://kv.vault.azure.net/secrets/anthropic-api-key)"
    unresolved = Settings.from_env({"RYTHU_ANTHROPIC_API_KEY": ref, "RYTHU_ASSISTANT_ENABLED": "true"})
    assert unresolved.anthropic_api_key is None and "Key Vault" in (unresolved.anthropic_api_key_problem or "")
    assert build_assistant(unresolved) is None
    assert "assistant.disabled" in caplog.text


@pytest.mark.parametrize("env,match", [
    ({"RYTHU_ASSISTANT_ENABLED": "yes"}, "true or false"),
    ({"RYTHU_ASSISTANT_MODEL": "gpt-x"}, "Claude model id"),
    ({"RYTHU_ASSISTANT_EFFORT": "max"}, "RYTHU_ASSISTANT_EFFORT"),
    ({"RYTHU_ASSISTANT_PER_DEVICE_PER_DAY": "0"}, "RYTHU_ASSISTANT_PER_DEVICE_PER_DAY"),
    ({"RYTHU_ASSISTANT_DAILY_CAP": "100000"}, "RYTHU_ASSISTANT_DAILY_CAP"),
])
def test_ask_rythu_settings_fail_fast(env, match):
    with pytest.raises(ValueError, match=match):
        Settings.from_env(env)
