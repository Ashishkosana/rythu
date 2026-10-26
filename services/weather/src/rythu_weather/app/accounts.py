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
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

TOKEN_TTL = timedelta(hours=1)
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


def utc_now() -> datetime:
    return datetime.now(UTC)
