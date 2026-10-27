"""Web Push: encryption a browser can open, VAPID a push service accepts, and the SSRF guard."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime

import http_ece
import httpx
import pytest
import respx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

from rythu_weather.app.webpush import (
    LocalVapidSigner,
    PushRetryable,
    Subscription,
    SubscriptionGone,
    b64url,
    b64url_decode,
    encrypt,
    endpoint_allowed,
    send,
    vapid_authorization,
)

NOW = datetime(2026, 10, 27, 6, 0, tzinfo=UTC)
ENDPOINT = "https://fcm.googleapis.com/fcm/send/abc123"


def _browser():
    """What a browser does when it subscribes: a P-256 key pair and a 16-byte auth secret."""
    key = ec.generate_private_key(ec.SECP256R1())
    pub = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    auth = os.urandom(16)
    return key, Subscription(ENDPOINT, b64url(pub), b64url(auth)), auth


@pytest.mark.parametrize(
    ("endpoint", "ok"),
    [
        ("https://fcm.googleapis.com/fcm/send/x", True),
        ("https://updates.push.services.mozilla.com/wpush/v2/x", True),
        ("https://web.push.apple.com/x", True),
        ("https://db5p.notify.windows.com/w/?token=x", True),
        ("http://fcm.googleapis.com/fcm/send/x", False),  # not https
        ("https://fcm.googleapis.com:8443/x", False),  # odd port
        ("https://evil.example/fcm.googleapis.com", False),
        ("https://fcm.googleapis.com.evil.example/x", False),
        ("https://169.254.169.254/metadata", False),  # the cloud metadata service
        ("https://localhost/x", False),
    ],
)
def test_only_real_push_services_are_reachable(endpoint: str, ok: bool) -> None:
    assert endpoint_allowed(endpoint) is ok


def test_the_browser_can_decrypt_what_we_send() -> None:
    key, sub, auth = _browser()
    payload = json.dumps({"title": "వర్షం రావచ్చు", "body": "75%"}, ensure_ascii=False).encode()
    sealed = encrypt(payload, sub.p256dh, sub.auth)
    assert payload not in sealed
    assert http_ece.decrypt(sealed, private_key=key, auth_secret=auth, version="aes128gcm") == payload
    assert encrypt(payload, sub.p256dh, sub.auth) != sealed  # fresh key + salt every time


async def test_vapid_jwt_is_valid_es256_for_the_push_service() -> None:
    signer = LocalVapidSigner()
    header = await vapid_authorization(ENDPOINT, signer, "https://github.com/Ashishkosana/rythu", NOW)
    assert header.startswith("vapid t=")
    token, k = header.removeprefix("vapid t=").split(", k=")
    head, claims, sig = token.split(".")
    assert json.loads(b64url_decode(head)) == {"typ": "JWT", "alg": "ES256"}
    body = json.loads(b64url_decode(claims))
    assert body["aud"] == "https://fcm.googleapis.com"  # the push service's origin, not the full URL
    assert body["exp"] - NOW.timestamp() == 12 * 3600
    assert body["sub"].startswith("https://")
    raw = b64url_decode(sig)
    assert len(raw) == 64  # JWS r‖s, not DER
    public = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), b64url_decode(k))
    der = encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big"))
    public.verify(der, f"{head}.{claims}".encode(), ec.ECDSA(hashes.SHA256()))  # raises if forged
    assert b64url_decode(k) == await signer.public_key()


@respx.mock
async def test_send_posts_an_encrypted_message_with_vapid() -> None:
    _, sub, _ = _browser()
    route = respx.post(ENDPOINT).mock(return_value=httpx.Response(201))
    async with httpx.AsyncClient() as client:
        await send(sub, b'{"title":"t"}', LocalVapidSigner(), subject="https://x.example", now=NOW,
                   client=client, topic="rain")
    req = route.calls.last.request
    assert req.headers["Content-Encoding"] == "aes128gcm"
    assert req.headers["TTL"] == "43200"
    assert req.headers["Topic"] == "rain"
    assert req.headers["Authorization"].startswith("vapid t=")
    assert b'"title"' not in req.content


@respx.mock
@pytest.mark.parametrize(
    ("status", "error"), [(404, SubscriptionGone), (410, SubscriptionGone), (429, PushRetryable),
                          (503, PushRetryable), (413, ValueError)],
)
async def test_send_classifies_push_service_answers(status: int, error: type[Exception]) -> None:
    _, sub, _ = _browser()
    respx.post(ENDPOINT).mock(return_value=httpx.Response(status))
    async with httpx.AsyncClient() as client:
        with pytest.raises(error):
            await send(sub, b"{}", LocalVapidSigner(), subject="https://x.example", now=NOW, client=client)


@respx.mock
async def test_send_never_contacts_a_disallowed_endpoint_and_network_errors_retry() -> None:
    _, sub, _ = _browser()
    async with httpx.AsyncClient() as client:
        with pytest.raises(SubscriptionGone):
            await send(Subscription("https://evil.example/x", sub.p256dh, sub.auth), b"{}", LocalVapidSigner(),
                       subject="https://x.example", now=NOW, client=client)
        respx.post(ENDPOINT).mock(side_effect=httpx.ConnectError("down"))
        with pytest.raises(PushRetryable):
            await send(sub, b"{}", LocalVapidSigner(), subject="https://x.example", now=NOW, client=client)
    assert all("evil" not in str(c.request.url) for c in respx.calls)


async def test_key_vault_signer_signs_the_sha256_and_publishes_the_same_key(monkeypatch) -> None:
    """Key Vault stand-in backed by a local key: proves the adapter hashes, passes ES256, keeps r‖s,
    and builds the uncompressed point (padding short JWK coordinates)."""
    import hashlib
    from types import SimpleNamespace

    import rythu_weather.adapters.keyvault_vapid as kv

    local = ec.generate_private_key(ec.SECP256R1())
    nums = local.public_key().public_numbers()
    jwk = SimpleNamespace(x=nums.x.to_bytes(32, "big").lstrip(b"\0"), y=nums.y.to_bytes(32, "big"))
    seen: dict[str, object] = {}

    class FakeKeyClient:
        def __init__(self, vault_url, credential): seen["vault"] = vault_url
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return None
        async def get_key(self, name, version=None):
            seen["get_key"] = seen.get("get_key", 0) + 1  # type: ignore[operator]
            return SimpleNamespace(id=f"https://kv.vault.azure.net/keys/{name}/v1", key=jwk)

    class FakeCrypto:
        def __init__(self, key, credential): seen["sign_key"] = key.id
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return None
        async def sign(self, algorithm, digest):
            seen["alg"], seen["digest"] = algorithm, digest
            from cryptography.hazmat.primitives.asymmetric.utils import Prehashed, decode_dss_signature
            r, s = decode_dss_signature(local.sign(digest, ec.ECDSA(Prehashed(hashes.SHA256()))))
            return SimpleNamespace(signature=r.to_bytes(32, "big") + s.to_bytes(32, "big"))

    monkeypatch.setattr(kv, "KeyClient", FakeKeyClient)
    monkeypatch.setattr(kv, "CryptographyClient", FakeCrypto)
    signer = kv.KeyVaultVapidSigner("https://kv.vault.azure.net/keys/vapid", credential=object())  # type: ignore[arg-type]

    header = await vapid_authorization(ENDPOINT, signer, "https://x.example", NOW)
    token, k = header.removeprefix("vapid t=").split(", k=")
    head, claims, sig = token.split(".")
    raw = b64url_decode(sig)
    public = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), b64url_decode(k))
    der = encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big"))
    public.verify(der, f"{head}.{claims}".encode(), ec.ECDSA(hashes.SHA256()))
    assert seen["digest"] == hashlib.sha256(f"{head}.{claims}".encode()).digest()
    assert str(seen["alg"]).endswith("es256") and seen["vault"] == "https://kv.vault.azure.net"
    assert seen["sign_key"] == "https://kv.vault.azure.net/keys/vapid/v1"  # the version we published
    assert seen["get_key"] == 1  # resolved once
