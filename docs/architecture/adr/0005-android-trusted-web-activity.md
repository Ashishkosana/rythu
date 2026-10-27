# 0005 — Android via Trusted Web Activity

- **Status:** accepted (2026-10-24)

## Context
The first real user installs apps from the Play Store. The product is already an installable PWA; there is
one developer. Web updates should reach the user without a Play review for every content change.

## Options
1. **Trusted Web Activity (Bubblewrap)** — thin Android wrapper around the PWA; needs a verified domain (`assetlinks.json`) and Chrome on the device; web notifications are delegated to the app.
2. **Capacitor** — bundles web assets in the APK, native plugins, offline from first install; every update is a Play release.
3. **Native rewrite (React Native/Expo or Kotlin)** — months before the first user benefits.

## Decision
Option 1. Publish to the internal testing track first so the father can install immediately; run the
12-tester / 14-day closed test (required for new personal Play accounts) in parallel before production.

## Consequences
- ➕ One codebase; instant updates; Play distribution also counters fake-APK scams ("install only from Play").
- ➖ Depends on Chrome being present and up to date; offline-first behaviour relies on the service worker.
- ➖ A one-time $25 Play Console fee. *(Amended 2026-10-27: a custom domain is not required — Asset Links
  verify per host, and the Static Web Apps host is ours. A custom domain is still worth it for a stable,
  readable host: changing the host later means an app update.)*
- Revisit Capacitor if a native capability is needed that the web platform cannot provide.
