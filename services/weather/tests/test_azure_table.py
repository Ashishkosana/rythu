"""Azure-specific behaviour of the Table Storage cache store (the shared contract is elsewhere)."""

from __future__ import annotations

import gzip
import json
import random
import string
import subprocess
import sys
from datetime import timedelta

import pytest

from builders import at
from rythu_weather.adapters.azure_table import MAX_PAYLOAD_BYTES, ROW_KEY, AzureTableCacheStore
from rythu_weather.adapters.cache import MAX_STALE
from rythu_weather.app.composition import build_cache_store
from rythu_weather.app.settings import Settings
from test_cache_store_contract import AZURITE, azure_store_or_skip

SECRET = "AccountKey=SuperSecretKey=="
_EP = "https://a.table.core.windows.net"


def test_connection_string_never_appears_in_repr():
    store = AzureTableCacheStore(f"DefaultEndpointsProtocol=https;AccountName=x;{SECRET}")
    settings = Settings(azure_tables_connection_string=f"AccountName=x;{SECRET}")
    assert "SuperSecretKey" not in repr(store)
    assert "SuperSecretKey" not in repr(settings)


def test_settings_select_the_azure_backend_and_reject_ambiguity():
    s = Settings.from_env({"RYTHU_AZURE_TABLES_CONNECTION_STRING": AZURITE, "RYTHU_AZURE_FORECAST_TABLE": "fc2"})
    store = build_cache_store(s)
    assert isinstance(store, AzureTableCacheStore) and store.table_name == "fc2"
    assert build_cache_store(Settings()) is None
    with pytest.raises(ValueError, match="at most one cache backend"):
        Settings.from_env({"RYTHU_CACHE_TABLE": "dyn", "RYTHU_AZURE_TABLES_CONNECTION_STRING": AZURITE})
    with pytest.raises(ValueError, match="RYTHU_AZURE_FORECAST_TABLE"):
        Settings.from_env({"RYTHU_AZURE_TABLES_CONNECTION_STRING": AZURITE, "RYTHU_AZURE_FORECAST_TABLE": "bad-name"})


def test_client_fails_fast(monkeypatch):
    captured = {}

    def fake_from_connection_string(conn, **kw):
        captured.update(kw)
        return object()

    monkeypatch.setattr(
        "rythu_weather.adapters.azure_table.TableClient.from_connection_string", fake_from_connection_string
    )
    AzureTableCacheStore(AZURITE, "forecast")._client()
    assert captured["table_name"] == "forecast"
    assert captured["connection_timeout"] <= 1 and captured["read_timeout"] <= 1
    assert captured["retry_total"] == 0  # a cache miss is cheaper than a retry


async def test_an_oversize_payload_is_refused_before_any_network_call():
    rng = random.Random(0)
    noise = "".join(rng.choices(string.ascii_letters + string.digits, k=MAX_PAYLOAD_BYTES * 2))  # incompressible
    store = AzureTableCacheStore("AccountName=unreachable;AccountKey=eA==;TableEndpoint=http://192.0.2.1:1/x;")
    with pytest.raises(ValueError, match="over"):
        await store.put("18.4,79.9", {"blob": noise})


async def test_entity_layout_on_the_wire():
    """PartitionKey = cell, RowKey = v1, gzip'd payload, expiresAt = write time + 6 h."""
    now = at(2026, 7, 15, 12)
    store = azure_store_or_skip()
    store = AzureTableCacheStore(store.connection_string, store.table_name, clock=lambda: now)
    await store.put("18.4,79.9", {"hello": "వర్షం"})

    from azure.data.tables.aio import TableClient

    async with TableClient.from_connection_string(AZURITE, table_name=store.table_name) as client:
        entity = await client.get_entity("18.4,79.9", ROW_KEY)
    assert json.loads(gzip.decompress(entity["payload"])) == {"hello": "వర్షం"}
    assert entity["expiresAt"] == now + MAX_STALE
    assert timedelta(hours=6) == MAX_STALE


def test_lambda_path_never_loads_the_azure_sdk():
    """build_lambda.sh bundles only httpx: the AWS handler must not import azure/aiohttp."""
    code = (
        "import sys, rythu_weather.app.handler; "
        "print([m for m in ('azure', 'aiohttp', 'fastapi', 'pydantic') if m in sys.modules])"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "[]"


async def test_managed_identity_mode_needs_no_secret():
    s = Settings.from_env({"RYTHU_AZURE_TABLES_ENDPOINT": "https://rythudev.table.core.windows.net"})
    store = build_cache_store(s)
    try:
        assert isinstance(store, AzureTableCacheStore)
        assert store.connection_string is None
        assert store.endpoint == "https://rythudev.table.core.windows.net"
        assert type(store.credential).__name__ == "DefaultAzureCredential"
    finally:
        await store.credential.close()


def test_store_requires_exactly_one_auth_mode():
    with pytest.raises(ValueError, match="OR"):
        AzureTableCacheStore()
    with pytest.raises(ValueError, match="OR"):
        AzureTableCacheStore(AZURITE, endpoint="https://x.table.core.windows.net", credential=object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "env",
    [
        {"RYTHU_AZURE_TABLES_ENDPOINT": _EP, "RYTHU_AZURE_TABLES_CONNECTION_STRING": AZURITE},
        {"RYTHU_AZURE_TABLES_ENDPOINT": _EP, "RYTHU_CACHE_TABLE": "dyn"},
    ],
)
def test_only_one_cache_backend_may_be_configured(env):
    with pytest.raises(ValueError, match="at most one cache backend"):
        Settings.from_env(env)


def test_endpoint_must_be_https():
    with pytest.raises(ValueError, match="https"):
        Settings.from_env({"RYTHU_AZURE_TABLES_ENDPOINT": "http://a.table.core.windows.net"})
