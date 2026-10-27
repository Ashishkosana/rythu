"""VAPID signing by Key Vault (implements ``app.webpush.VapidSigner``).

The VAPID private key is a non-exportable P-256 key created by the Bicep template; the app's identity
may only read its public half and ask Key Vault to sign (role "Key Vault Crypto User" on that vault).
The key version is resolved once per process, so the public key browsers subscribed with and the
signatures always belong to the same version.
"""

from __future__ import annotations

import hashlib

from azure.core.credentials_async import AsyncTokenCredential
from azure.keyvault.keys import KeyVaultKey, KeyVaultKeyIdentifier
from azure.keyvault.keys.aio import KeyClient
from azure.keyvault.keys.crypto import SignatureAlgorithm
from azure.keyvault.keys.crypto.aio import CryptographyClient


class KeyVaultVapidSigner:
    def __init__(self, key_id: str, credential: AsyncTokenCredential) -> None:
        self._id = KeyVaultKeyIdentifier(key_id)
        self._credential = credential
        self._key: KeyVaultKey | None = None

    async def _resolve(self) -> KeyVaultKey:
        if self._key is None:
            async with KeyClient(self._id.vault_url, self._credential) as client:
                self._key = await client.get_key(self._id.name, self._id.version)
        return self._key

    async def public_key(self) -> bytes:
        jwk = (await self._resolve()).key
        # The SDK sets JWK fields dynamically (typed stubs do not list x/y).
        x, y = getattr(jwk, "x", None), getattr(jwk, "y", None)
        if not x or not y:
            raise ValueError("the VAPID key is not an EC key")
        # JWK coordinates may drop leading zero bytes; the uncompressed point needs 32 each.
        return b"\x04" + bytes(x).rjust(32, b"\0") + bytes(y).rjust(32, b"\0")

    async def sign(self, data: bytes) -> bytes:
        key = await self._resolve()
        async with CryptographyClient(key, self._credential) as client:
            result = await client.sign(SignatureAlgorithm.es256, hashlib.sha256(data).digest())
        return bytes(result.signature)  # P-256 / ES256: raw r‖s, 64 bytes — exactly what JWS wants
