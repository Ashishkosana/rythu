"""Web Push, done by hand on the standards (no vendor SDK):

* RFC 8291 — the payload is encrypted for one browser (its P-256 key + auth secret), so the push
  service in between (Google FCM for Chrome / the Android app) cannot read it;
* RFC 8188 ``aes128gcm`` content coding;
* RFC 8292 VAPID — a short-lived ES256 JWT proves the message comes from Rythu. Its private key is a
  non-exportable EC key in Key Vault (adapters/keyvault_vapid.py): we ask Key Vault to sign; the key
  never exists in config, on disk, or in this process.

Security: the server POSTs to a URL the phone gave it, so endpoints are restricted to the browsers'
real push services (``ALLOWED_PUSH_HOSTS``) — otherwise "subscribe" would be a way to make Rythu send
requests anywhere (SSRF).
"""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timedelta
from typing import Protocol
from urllib.parse import urlsplit

import http_ece
import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from rythu_weather.app.push_subscription import Subscription

__all__ = ["Subscription"]  # re-exported for callers of send()

# Push services of the browsers Rythu runs in (Chrome / Android TWA first). Suffix match on the host.
ALLOWED_PUSH_HOSTS = (
    "fcm.googleapis.com",
    "android.googleapis.com",
    "updates.push.services.mozilla.com",
    "push.apple.com",
    "notify.windows.com",
)
JWT_TTL = timedelta(hours=12)  # RFC 8292: at most 24 h
MESSAGE_TTL_S = 12 * 60 * 60  # a weather alert is worthless after half a day
SEND_TIMEOUT_S = 5.0


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def b64url_decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def endpoint_allowed(endpoint: str) -> bool:
    parts = urlsplit(endpoint)
    host = (parts.hostname or "").lower()
    return (
        parts.scheme == "https"
        and parts.port in (None, 443)
        and any(host == h or host.endswith("." + h) for h in ALLOWED_PUSH_HOSTS)
    )


class VapidSigner(Protocol):
    async def public_key(self) -> bytes:
        """The application server key: 65-byte uncompressed P-256 point (what browsers subscribe with)."""
        ...

    async def sign(self, data: bytes) -> bytes:
        """ES256 over ``data``: the 64-byte r‖s that JWS expects."""
        ...


class LocalVapidSigner:
    """For local development and tests: a key in memory (a fresh one per process unless given)."""

    def __init__(self, private_key: ec.EllipticCurvePrivateKey | None = None) -> None:
        self._key = private_key or ec.generate_private_key(ec.SECP256R1())

    async def public_key(self) -> bytes:
        return self._key.public_key().public_bytes(
            serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
        )

    async def sign(self, data: bytes) -> bytes:
        r, s = decode_dss_signature(self._key.sign(data, ec.ECDSA(hashes.SHA256())))
        return r.to_bytes(32, "big") + s.to_bytes(32, "big")


async def vapid_authorization(endpoint: str, signer: VapidSigner, subject: str, now: datetime) -> str:
    """``Authorization: vapid t=<JWT>, k=<public key>`` for one push service (its origin is the audience)."""
    parts = urlsplit(endpoint)
    header = b64url(json.dumps({"typ": "JWT", "alg": "ES256"}, separators=(",", ":")).encode())
    claims = {"aud": f"{parts.scheme}://{parts.netloc}", "exp": int((now + JWT_TTL).timestamp()), "sub": subject}
    body = b64url(json.dumps(claims, separators=(",", ":")).encode())
    signing_input = f"{header}.{body}".encode("ascii")
    token = f"{header}.{body}.{b64url(await signer.sign(signing_input))}"
    return f"vapid t={token}, k={b64url(await signer.public_key())}"


def encrypt(payload: bytes, p256dh: str, auth: str) -> bytes:
    """RFC 8291: encrypt for one subscription, with a fresh sender key and salt per message."""
    return bytes(
        http_ece.encrypt(
            payload,
            salt=os.urandom(16),
            private_key=ec.generate_private_key(ec.SECP256R1()),
            dh=b64url_decode(p256dh),
            auth_secret=b64url_decode(auth),
            version="aes128gcm",
        )
    )


class SubscriptionGone(Exception):
    """404/410 from the push service: the browser unsubscribed or the app was removed. Delete it."""


class PushRetryable(Exception):
    """429 / 5xx / network: try again later (the queue retries the message)."""


async def send(
    sub: Subscription, payload: bytes, signer: VapidSigner, *, subject: str, now: datetime,
    client: httpx.AsyncClient, urgency: str = "high", topic: str | None = None,
) -> None:
    if not endpoint_allowed(sub.endpoint):
        raise SubscriptionGone("endpoint not on an allowed push service")
    headers = {
        "Authorization": await vapid_authorization(sub.endpoint, signer, subject, now),
        "Content-Encoding": "aes128gcm",
        "Content-Type": "application/octet-stream",
        "TTL": str(MESSAGE_TTL_S),
        "Urgency": urgency,
    }
    if topic:  # a newer message with the same topic replaces an undelivered older one
        headers["Topic"] = topic
    try:
        resp = await client.post(sub.endpoint, content=encrypt(payload, sub.p256dh, sub.auth), headers=headers,
                                 timeout=SEND_TIMEOUT_S)
    except httpx.HTTPError as exc:
        raise PushRetryable(repr(exc)) from exc
    if resp.status_code in (404, 410):
        raise SubscriptionGone(f"push service answered {resp.status_code}")
    if resp.status_code == 429 or resp.status_code >= 500:
        raise PushRetryable(f"push service answered {resp.status_code}")
    if resp.status_code >= 400:  # our request is wrong (e.g. payload too big): retrying will not help
        raise ValueError(f"push service refused the message: {resp.status_code} {resp.text[:200]}")
