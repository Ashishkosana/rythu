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

import asyncio
import contextlib
import gzip
import json
import random
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from azure.core import MatchConditions
from azure.core.credentials_async import AsyncTokenCredential
from azure.core.exceptions import (
    HttpResponseError,
    ResourceExistsError,
    ResourceModifiedError,
    ResourceNotFoundError,
)
from azure.data.tables import UpdateMode
from azure.data.tables.aio import TableClient

from rythu_weather.adapters.budget import BudgetContention
from rythu_weather.adapters.cache import MAX_STALE
from rythu_weather.app.accounts import PreconditionFailed, alert_row, push_row
from rythu_weather.app.push_subscription import Subscription

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
class TableAuth:
    """How to reach the storage account: a connection string (local Azurite) OR endpoint + credential."""

    # repr=False: the connection string carries the account key.
    connection_string: str | None = field(default=None, repr=False)
    endpoint: str | None = None
    # Shared for the process lifetime so its token cache is reused.
    credential: AsyncTokenCredential | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        by_key = self.connection_string is not None
        by_identity = self.endpoint is not None and self.credential is not None
        if by_key == by_identity:
            raise ValueError("Azure Table access needs a connection_string OR endpoint + credential")

    def client(self, table_name: str) -> TableClient:
        if self.connection_string is not None:
            return TableClient.from_connection_string(self.connection_string, table_name=table_name, **_FAIL_FAST)
        assert self.endpoint is not None and self.credential is not None  # guaranteed by __post_init__
        return TableClient(self.endpoint, table_name=table_name, credential=self.credential, **_FAIL_FAST)


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
        return TableAuth(self.connection_string, self.endpoint, self.credential).client(self.table_name)

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


async def _create_table_quietly(client: TableClient) -> None:
    with contextlib.suppress(ResourceExistsError):
        await client.create_table()


@dataclass(frozen=True, slots=True)
class AzureTableCellRegistry:
    """``CellRegistry`` on Table Storage: one row per cell, PartitionKey ``cells``, RowKey = cell key."""

    auth: TableAuth
    table_name: str = "cells"

    async def touch(self, cell: str, seen_at: datetime) -> None:
        entity = {"PartitionKey": "cells", "RowKey": cell, "lastSeen": seen_at}
        async with self.auth.client(self.table_name) as client:
            try:
                await client.upsert_entity(entity, mode=UpdateMode.REPLACE)
            except ResourceNotFoundError:
                await _create_table_quietly(client)
                await client.upsert_entity(entity, mode=UpdateMode.REPLACE)

    async def active(self, since: datetime) -> list[str]:
        rows = await self._query("PartitionKey eq 'cells' and lastSeen ge @t", since)
        rows.sort(key=lambda r: r["lastSeen"], reverse=True)
        return [str(r["RowKey"]) for r in rows]

    async def prune(self, before: datetime) -> int:
        rows = await self._query("PartitionKey eq 'cells' and lastSeen lt @t", before)
        async with self.auth.client(self.table_name) as client:
            for r in rows:
                with contextlib.suppress(ResourceNotFoundError):
                    await client.delete_entity("cells", str(r["RowKey"]))
        return len(rows)

    async def _query(self, flt: str, t: datetime) -> list[dict[str, Any]]:
        async with self.auth.client(self.table_name) as client:
            try:
                return [dict(e) async for e in client.query_entities(flt, parameters={"t": t})]
            except ResourceNotFoundError:  # table not created yet → no cells
                return []


async def _backoff(attempt: int) -> None:
    # Jittered, growing pause so concurrent writers stop colliding in lockstep (≤ ~0.3 s in total).
    await asyncio.sleep(random.uniform(0.005, 0.02) * attempt)


@dataclass(frozen=True, slots=True)
class AzureTableUpstreamBudget:
    """``UpstreamBudget`` on Table Storage: one counter row per hour, updated with ETag optimistic
    concurrency, so instances on different machines share one budget without a lock service."""

    auth: TableAuth
    table_name: str = "budget"
    max_attempts: int = 6

    async def try_acquire(self, window: str, limit: int) -> bool:
        async with self.auth.client(self.table_name) as client:
            for attempt in range(1, self.max_attempts + 1):
                try:
                    row = await client.get_entity("budget", window)
                except ResourceNotFoundError:
                    try:
                        await client.create_entity({"PartitionKey": "budget", "RowKey": window, "count": 1})
                        return True
                    except ResourceExistsError:
                        await _backoff(attempt)  # another instance opened the window first
                        continue
                    except ResourceNotFoundError:
                        await _create_table_quietly(client)  # very first use of the table
                        continue
                spent = int(row["count"])
                if spent >= limit:
                    return False
                row["count"] = spent + 1
                try:
                    await client.update_entity(
                        row, mode=UpdateMode.REPLACE, etag=row.metadata["etag"],
                        match_condition=MatchConditions.IfNotModified,
                    )
                    return True
                except ResourceModifiedError:
                    await _backoff(attempt)  # someone spent in between — re-read and try again
                    continue
        raise BudgetContention(f"gave up after {self.max_attempts} conflicting updates on {window}")


@dataclass(frozen=True, slots=True)
class AzureTableUserStore:
    """``UserStore`` on Table Storage — one partition per user (ADR 0002):

        PartitionKey = user id    RowKey = "device"          secretHash, createdAt
                                  RowKey = "profile"         data (JSON), conditional writes on the row's ETag
                                  RowKey = "push_<sha256>"   one browser push subscription
                                  RowKey = "alert_<key>"     an alert already sent (idempotency), pruned

    Everything about a user is one partition, so deleting a user is one query. (Table keys may not
    contain '#', '/', '\\' or '?', hence the underscores.)
    """

    auth: TableAuth
    table_name: str = "users"

    async def create_user(self, user_id: str, secret_hash: str, now: datetime) -> None:
        entity = {"PartitionKey": user_id, "RowKey": "device", "secretHash": secret_hash, "createdAt": now}
        async with self.auth.client(self.table_name) as client:
            try:
                await client.create_entity(entity)
            except ResourceNotFoundError:
                await _create_table_quietly(client)
                await client.create_entity(entity)

    async def secret_hash(self, user_id: str) -> str | None:
        async with self.auth.client(self.table_name) as client:
            try:
                entity = await client.get_entity(user_id, "device")
            except ResourceNotFoundError:
                return None
        return str(entity["secretHash"])

    async def get_profile(self, user_id: str) -> tuple[dict[str, Any], str] | None:
        async with self.auth.client(self.table_name) as client:
            try:
                entity = await client.get_entity(user_id, "profile")
            except ResourceNotFoundError:
                return None
        return json.loads(entity["data"]), str(entity.metadata["etag"])

    async def put_profile(
        self, user_id: str, profile: dict[str, Any], *, if_match: str | None, create_only: bool
    ) -> str:
        entity = {
            "PartitionKey": user_id,
            "RowKey": "profile",
            "data": json.dumps(profile, ensure_ascii=False, separators=(",", ":")),
        }
        async with self.auth.client(self.table_name) as client:
            if create_only:
                try:
                    meta = await client.create_entity(entity)
                except ResourceExistsError as exc:
                    raise PreconditionFailed from exc
                except ResourceNotFoundError:
                    await _create_table_quietly(client)
                    meta = await client.create_entity(entity)
                return str(meta["etag"])
            if if_match is None:
                raise PreconditionFailed
            try:
                meta = await client.update_entity(
                    entity, mode=UpdateMode.REPLACE, etag=if_match, match_condition=MatchConditions.IfNotModified
                )
            except (ResourceModifiedError, ResourceNotFoundError) as exc:
                raise PreconditionFailed from exc
            except HttpResponseError as exc:
                if exc.status_code == 400:  # an ETag that was never ours (garbage in If-Match)
                    raise PreconditionFailed from exc
                raise
        return str(meta["etag"])

    async def delete_user(self, user_id: str) -> int:
        async with self.auth.client(self.table_name) as client:
            try:
                rows = client.query_entities("PartitionKey eq @u", parameters={"u": user_id}, select=["RowKey"])
                keys = [str(e["RowKey"]) async for e in rows]
            except ResourceNotFoundError:
                return 0
            for row_key in keys:
                with contextlib.suppress(ResourceNotFoundError):
                    await client.delete_entity(user_id, row_key)
        return len(keys)

    async def profiles(self) -> AsyncIterator[tuple[str, dict[str, Any]]]:
        async with self.auth.client(self.table_name) as client:
            try:
                async for e in client.query_entities("RowKey eq 'profile'", select=["PartitionKey", "data"]):
                    yield str(e["PartitionKey"]), json.loads(e["data"])
            except ResourceNotFoundError:
                return

    async def _rows_with_prefix(self, client: TableClient, user_id: str, prefix: str) -> list[dict[str, Any]]:
        # RowKey range [prefix, prefix + '\x7f'): every key starting with the prefix.
        flt = "PartitionKey eq @u and RowKey ge @lo and RowKey lt @hi"
        try:
            return [dict(e) async for e in client.query_entities(
                flt, parameters={"u": user_id, "lo": prefix, "hi": prefix + "\x7f"})]
        except ResourceNotFoundError:
            return []

    async def push_subscriptions(self, user_id: str) -> list[Subscription]:
        async with self.auth.client(self.table_name) as client:
            rows = await self._rows_with_prefix(client, user_id, "push_")
        return [Subscription(str(r["endpoint"]), str(r["p256dh"]), str(r["auth"])) for r in rows]

    async def put_push_subscription(self, user_id: str, sub: Subscription, now: datetime) -> None:
        entity = {"PartitionKey": user_id, "RowKey": push_row(sub.endpoint), "endpoint": sub.endpoint,
                  "p256dh": sub.p256dh, "auth": sub.auth, "at": now}
        async with self.auth.client(self.table_name) as client:
            await client.upsert_entity(entity, mode=UpdateMode.REPLACE)

    async def delete_push_subscription(self, user_id: str, endpoint: str) -> None:
        async with self.auth.client(self.table_name) as client:
            with contextlib.suppress(ResourceNotFoundError):
                await client.delete_entity(user_id, push_row(endpoint))

    async def claim_alert(self, user_id: str, key: str, now: datetime) -> bool:
        async with self.auth.client(self.table_name) as client:
            try:
                await client.create_entity({"PartitionKey": user_id, "RowKey": alert_row(key), "at": now})
            except ResourceExistsError:
                return False
        return True

    async def has_alert(self, user_id: str, key: str) -> bool:
        async with self.auth.client(self.table_name) as client:
            try:
                await client.get_entity(user_id, alert_row(key), select=["RowKey"])
            except ResourceNotFoundError:
                return False
        return True

    async def release_alert(self, user_id: str, key: str) -> None:
        async with self.auth.client(self.table_name) as client:
            with contextlib.suppress(ResourceNotFoundError):
                await client.delete_entity(user_id, alert_row(key))

    async def prune_alerts(self, user_id: str, before: datetime) -> int:
        async with self.auth.client(self.table_name) as client:
            rows = [r for r in await self._rows_with_prefix(client, user_id, "alert_") if r["at"] < before]
            for r in rows:
                with contextlib.suppress(ResourceNotFoundError):
                    await client.delete_entity(user_id, str(r["RowKey"]))
        return len(rows)
