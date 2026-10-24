# 0004 — Anonymous device credentials before accounts

- **Status:** accepted (2026-10-24)

## Context
Profile sync, alerts and the crop calendar need a stable user identity and an authorization boundary. The
first users are family members; asking a low-literacy farmer for an email/password is friction and collects
PII we do not need. The existing Cognito pool is provisioned but no request is ever verified.

## Options
1. **Anonymous device credentials** — server issues a random user id + secret on first launch, exchanged for short-lived signed tokens.
2. **Microsoft Entra External ID** — email/Google sign-in, free tier; useful later to link devices.
3. **Phone OTP** — most farmer-friendly, but SMS cost and Indian DLT registration overhead.

## Decision
Option 1 now; add option 2 later as an *upgrade* that links an existing device identity. Remove Cognito.
Every `/v1/me/*` route derives `userId` from the verified token only, with a test that user A cannot read or
write user B (IDOR).

## Consequences
- ➕ Zero sign-up friction; minimal personal data (DPDP Act friendly).
- ➖ Losing the phone loses the identity until account linking exists; mitigated by small, re-enterable profile data.
- ➖ We own token issuance — keep it boring: HMAC-signed, short expiry, secret in Key Vault.
