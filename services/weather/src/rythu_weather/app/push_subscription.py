"""A browser's push subscription, as the store keeps it. Dependency-free on purpose: the user store
(and so the AWS Lambda path) must not import the crypto that sending needs (app/webpush.py)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Subscription:
    endpoint: str
    p256dh: str  # the browser's P-256 public key, base64url
    auth: str  # the browser's 16-byte auth secret, base64url
