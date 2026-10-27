"""Anonymous device accounts (ADR 0004): credentials, short-lived tokens, and the user-store port.

A phone registers once and gets a random ``user_id`` plus a 256-bit ``device_secret``; the server keeps
only the secret's SHA-256 (the secret is random, not a password, so a slow KDF buys nothing). The phone
trades the secret for a one-hour token — ``v1.<user_id>.<expiry>.<HMAC-SHA256>`` — so most requests
carry a credential that expires, and checking one needs no database read.

``user_id`` on every ``/v1/me`` route comes ONLY from a verified token, never from the request
(tests/test_accounts_api.py proves user A cannot read, write or delete user B).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from rythu_weather.app.push_subscription import Subscription

TOKEN_TTL = timedelta(hours=1)
MAX_PUSH_SUBSCRIPTIONS = 3  # per user: a phone or two, not a fan-out list
_USER_ID = re.compile(r"[0-9a-f]{32}")


class Unauthorized(Exception):
    """Missing, malformed, forged or expired credentials. Deliberately says nothing more."""


class PreconditionFailed(Exception):
    """The caller's version (ETag) is not the stored one — someone else wrote first, or nothing exists."""


@dataclass(frozen=True, slots=True)
class DeviceCredentials:
    user_id: str
    device_secret: str


def new_credentials() -> DeviceCredentials:
    return DeviceCredentials(user_id=secrets.token_hex(16), device_secret=secrets.token_urlsafe(32))


def secret_digest(device_secret: str) -> str:
    return hashlib.sha256(device_secret.encode("utf-8")).hexdigest()


def push_row(endpoint: str) -> str:
    """Row key for a push subscription. (Table keys may not contain '#', '/', '\\' or '?'.)"""
    return "push_" + hashlib.sha256(endpoint.encode("utf-8")).hexdigest()[:40]


def alert_row(key: str) -> str:
    return "alert_" + key


ASSISTANT_PARTITION = "assistant"  # everyone's daily question count; never a user id (32 hex characters)


def ask_row(day: str) -> str:
    return "ask_" + day


def is_user_id(value: str) -> bool:
    return _USER_ID.fullmatch(value) is not None


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


@dataclass(frozen=True, slots=True)
class TokenSigner:
    # repr=False: the signing key is the one secret the service holds.
    key: bytes = field(repr=False)
    ttl: timedelta = TOKEN_TTL

    def __post_init__(self) -> None:
        if len(self.key) < 32:
            raise ValueError("token signing key must be at least 32 bytes")

    def _sign(self, payload: str) -> str:
        return _b64(hmac.new(self.key, payload.encode("ascii"), hashlib.sha256).digest())

    def issue(self, user_id: str, now: datetime) -> tuple[str, datetime]:
        if not is_user_id(user_id):
            raise ValueError("not a user id")
        expires = now + self.ttl
        payload = f"v1.{user_id}.{int(expires.timestamp())}"
        return f"{payload}.{self._sign(payload)}", expires

    def verify(self, token: str, now: datetime) -> str:
        """The token's user id — or ``Unauthorized``. Constant-time on the signature."""
        parts = token.split(".")
        if len(parts) != 4 or parts[0] != "v1" or not is_user_id(parts[1]) or not parts[2].isdigit():
            raise Unauthorized
        payload = ".".join(parts[:3])
        if not hmac.compare_digest(self._sign(payload), parts[3]):
            raise Unauthorized
        if int(parts[2]) <= now.timestamp():
            raise Unauthorized
        return parts[1]


class UserStore(Protocol):
    """Per-user records, one partition per user (ADR 0002). Profile writes are conditional (ETags)."""

    async def create_user(self, user_id: str, secret_hash: str, now: datetime) -> None: ...

    async def secret_hash(self, user_id: str) -> str | None: ...

    async def get_profile(self, user_id: str) -> tuple[dict[str, Any], str] | None:
        """(profile, etag), or None."""
        ...

    async def put_profile(
        self, user_id: str, profile: dict[str, Any], *, if_match: str | None, create_only: bool
    ) -> str:
        """Store the profile and return its new ETag. ``create_only``: fail if one exists;
        else ``if_match`` must be the stored ETag. ``PreconditionFailed`` otherwise."""
        ...

    async def delete_user(self, user_id: str) -> int:
        """Remove everything stored for the user; returns how many records went."""
        ...

    def profiles(self) -> AsyncIterator[tuple[str, dict[str, Any]]]:
        """Every (user id, profile) — for the alert evaluator. A full scan: fine for a pilot; an index
        partition replaces it when users number in the thousands."""
        ...

    async def push_subscriptions(self, user_id: str) -> list[Subscription]: ...

    async def put_push_subscription(self, user_id: str, sub: Subscription, now: datetime) -> None: ...

    async def delete_push_subscription(self, user_id: str, endpoint: str) -> None: ...

    async def claim_alert(self, user_id: str, key: str, now: datetime) -> bool:
        """Record that this alert is being sent; False if it already was (idempotency)."""
        ...

    async def has_alert(self, user_id: str, key: str) -> bool: ...

    async def release_alert(self, user_id: str, key: str) -> None:
        """Forget a claim whose sending failed, so a retry may send it."""
        ...

    async def prune_alerts(self, user_id: str, before: datetime) -> int: ...

    async def assistant_usage(self, user_id: str, day: str) -> tuple[int, int]:
        """Questions answered on ``day`` (IST date): (this user, everyone)."""
        ...

    async def record_assistant_use(self, user_id: str, day: str) -> None:
        """Count one answered question for the user and for everyone. Best effort under contention:
        a lost count lets one extra question through, never blocks one."""
        ...


class InMemoryUserStore:
    """Dev/test store with the same semantics as the Table Storage one (see the contract tests)."""

    def __init__(self) -> None:
        self._rows: dict[str, dict[str, tuple[dict[str, Any], str]]] = {}
        self._version = 0

    def _etag(self) -> str:
        self._version += 1
        return f'W/"{self._version}"'

    async def create_user(self, user_id: str, secret_hash: str, now: datetime) -> None:
        self._rows.setdefault(user_id, {})["device"] = ({"secretHash": secret_hash, "createdAt": now}, self._etag())

    async def secret_hash(self, user_id: str) -> str | None:
        row = self._rows.get(user_id, {}).get("device")
        return str(row[0]["secretHash"]) if row else None

    async def get_profile(self, user_id: str) -> tuple[dict[str, Any], str] | None:
        row = self._rows.get(user_id, {}).get("profile")
        return (dict(row[0]), row[1]) if row else None

    async def put_profile(
        self, user_id: str, profile: dict[str, Any], *, if_match: str | None, create_only: bool
    ) -> str:
        rows = self._rows.setdefault(user_id, {})
        current = rows.get("profile")
        if create_only and current is not None:
            raise PreconditionFailed
        if not create_only and (current is None or current[1] != if_match):
            raise PreconditionFailed
        etag = self._etag()
        rows["profile"] = (dict(profile), etag)
        return etag

    async def delete_user(self, user_id: str) -> int:
        return len(self._rows.pop(user_id, {}))

    async def profiles(self) -> AsyncIterator[tuple[str, dict[str, Any]]]:
        for user_id, rows in list(self._rows.items()):
            if "profile" in rows:
                yield user_id, dict(rows["profile"][0])

    async def push_subscriptions(self, user_id: str) -> list[Subscription]:
        rows = self._rows.get(user_id, {})
        return [Subscription(**v[0]["sub"]) for k, v in sorted(rows.items()) if k.startswith("push_")]

    async def put_push_subscription(self, user_id: str, sub: Subscription, now: datetime) -> None:
        sub_dict = {"endpoint": sub.endpoint, "p256dh": sub.p256dh, "auth": sub.auth}
        self._rows.setdefault(user_id, {})[push_row(sub.endpoint)] = ({"sub": sub_dict, "at": now}, self._etag())

    async def delete_push_subscription(self, user_id: str, endpoint: str) -> None:
        self._rows.get(user_id, {}).pop(push_row(endpoint), None)

    async def claim_alert(self, user_id: str, key: str, now: datetime) -> bool:
        rows = self._rows.setdefault(user_id, {})
        if alert_row(key) in rows:
            return False
        rows[alert_row(key)] = ({"at": now}, self._etag())
        return True

    async def has_alert(self, user_id: str, key: str) -> bool:
        return alert_row(key) in self._rows.get(user_id, {})

    async def release_alert(self, user_id: str, key: str) -> None:
        self._rows.get(user_id, {}).pop(alert_row(key), None)

    async def prune_alerts(self, user_id: str, before: datetime) -> int:
        rows = self._rows.get(user_id, {})
        old = [k for k, v in rows.items() if k.startswith("alert_") and v[0]["at"] < before]
        for k in old:
            del rows[k]
        return len(old)

    def _count(self, partition: str, row: str) -> int:
        return int(self._rows.get(partition, {}).get(row, ({"n": 0}, ""))[0]["n"])

    async def assistant_usage(self, user_id: str, day: str) -> tuple[int, int]:
        return self._count(user_id, ask_row(day)), self._count(ASSISTANT_PARTITION, day)

    async def record_assistant_use(self, user_id: str, day: str) -> None:
        for partition, row in ((user_id, ask_row(day)), (ASSISTANT_PARTITION, day)):
            self._rows.setdefault(partition, {})[row] = ({"n": self._count(partition, row) + 1}, self._etag())


def utc_now() -> datetime:
    return datetime.now(UTC)
