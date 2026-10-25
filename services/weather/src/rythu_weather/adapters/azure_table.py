"""Azure Table Storage backend for the forecast cache (implements the ``CacheStore`` port).

One entity per ~11 km cell (see ADR 0002 and ``adapters.cache``):

    PartitionKey = cache key, e.g. "18.4,79.9"    RowKey = "v1"
    payload      = gzip(JSON of serde.forecast_to_cache)   (Edm.Binary)
    expiresAt    = write time + MAX_STALE                    (for a future cleanup job)

Why gzip: Table Storage caps a property at 64 KiB. A 7-day forecast is ~37 KiB as a UTF-16 string —
it fits, but a 16-day one (~84 KiB) would not, and caching would silently stop. Compressed it is
~1–2 KiB. Expiry is NOT trusted to the store: ``CachedProvider`` refuses copies older than
``MAX_STALE`` itself, exactly as with DynamoDB.

Auth: in Azure, ``endpoint`` + a token ``credential`` (the Function App's managed identity, granted
"Storage Table Data Contributor" by the Bicep template) — no secret exists. Locally, a
``connection_string`` (Azurite's public dev account).

The Azure SDK is imported only by this module, and ``app.composition`` imports this module lazily, so
the AWS Lambda path never loads it.
"""

from __future__ import annotations

import contextlib
import gzip
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from azure.core.credentials_async import AsyncTokenCredential
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.data.tables import UpdateMode
from azure.data.tables.aio import TableClient

from rythu_weather.adapters.cache import MAX_STALE

# Bump to orphan every entry at once if the payload format ever changes incompatibly.
ROW_KEY = "v1"
# Edm.Binary limit is 64 KiB per property; keep a margin.
MAX_PAYLOAD_BYTES = 60 * 1024


def _ist_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Kolkata"))


# The cache is an optimisation, so a slow store must fall through rather than eat the request — and
# for a cache a retry buys nothing: a failed read is cheaper to answer from upstream (~0.5–1 s) than to
# retry (up to 1 s more), and a failed write only means the next request misses. Measured with a hung
# endpoint: 1 retry → 4.1 s, no retry → ~2 s (get + put).
_FAIL_FAST: dict[str, Any] = {"connection_timeout": 1, "read_timeout": 1, "retry_total": 0}


@dataclass(frozen=True, slots=True)
class AzureTableCacheStore:
    # repr=False: the connection string carries the account key.
    connection_string: str | None = field(default=None, repr=False)
    table_name: str = "forecast"
    expire_after: timedelta = MAX_STALE
    clock: Callable[[], datetime] = _ist_now
    endpoint: str | None = None
    # Shared for the process lifetime so its token cache is reused (a fresh credential per call would
    # fetch a new token on every request).
    credential: AsyncTokenCredential | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        by_key = self.connection_string is not None
        by_identity = self.endpoint is not None and self.credential is not None
        if by_key == by_identity:
            raise ValueError("AzureTableCacheStore needs a connection_string OR endpoint + credential")

    def _client(self) -> TableClient:
        if self.connection_string is not None:
            return TableClient.from_connection_string(self.connection_string, table_name=self.table_name, **_FAIL_FAST)
        assert self.endpoint is not None and self.credential is not None  # guaranteed by __post_init__
        return TableClient(self.endpoint, table_name=self.table_name, credential=self.credential, **_FAIL_FAST)

    async def get(self, key: str) -> dict[str, Any] | None:
        async with self._client() as client:
            try:
                entity = await client.get_entity(partition_key=key, row_key=ROW_KEY)
            except ResourceNotFoundError:  # no such entity — or the table doesn't exist yet
                return None
        payload = entity.get("payload")
        if not isinstance(payload, bytes):
            return None
        value = json.loads(gzip.decompress(payload))
        return value if isinstance(value, dict) else None

    async def put(self, key: str, value: dict[str, Any]) -> None:
        payload = gzip.compress(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        if len(payload) > MAX_PAYLOAD_BYTES:
            # Checked before any network call; CachedProvider logs it as cache.write_failed.
            raise ValueError(f"forecast cache payload is {len(payload)} bytes, over {MAX_PAYLOAD_BYTES}")
        entity = {
            "PartitionKey": key,
            "RowKey": ROW_KEY,
            "payload": payload,
            "expiresAt": self.clock() + self.expire_after,
        }
        async with self._client() as client:
            try:
                await client.upsert_entity(entity, mode=UpdateMode.REPLACE)
            except ResourceNotFoundError:
                # First write into a fresh account (local Azurite, or a new environment).
                with contextlib.suppress(ResourceExistsError):
                    await client.create_table()
                await client.upsert_entity(entity, mode=UpdateMode.REPLACE)
