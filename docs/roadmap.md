# Rythu — Status & Roadmap

_An honest self-review: what's built, what's missing, and what to do next. Grounded in the verified research in this folder (`farmer-needs-research.md`, `schemes-research.md`, `agronomy-data.md`)._

## Built & live (PWA on AWS Amplify + Python/AWS serverless backend)

- **Weather** — honest hyperlocal forecast (Open-Meteo, rain-probability framing), farming-read advisory rules, dynamic-sky UI. GPS + village search (OpenStreetMap) + verified pilot mandals.
- **Crops** — guide for the 5 pilot crops; **fertilizer calculator** from verified PJTSAU/ICAR doses (overdose-safe math, cited); **pest guide** (IPM-first, active-ingredient-not-brand); **expert bridge** (tap-to-call Kisan Call Centre).
- **Schemes** — 19 verified central + Telangana schemes with honest status badges + eligibility/honesty notes.
- **Accessibility** — Telugu-first, tap-to-hear voice, first-run welcome, remembers village/language, offline support (service worker).
- **Auth** — AWS Cognito email login (guest-first / optional).
- **Engineering** — Next.js/TS PWA + Python (hexagonal) on Lambda + API Gateway + DynamoDB (TTL cache), all IaC in AWS CDK; ~50 automated tests.

## The biggest gap: real farmers

Rythu is **pre-pilot — zero real users.** The make-or-break is **distribution** (AEO / Rythu Vedika demos) and **field validation** — not more features. Everything below is theory until one real farmer uses it.

## Gaps — Tier 1 (farmer value)

1. **No mandi prices** — the #1 unmet farmer need. Blocked only on a free data.gov.in API key.
2. **Farming advice is English-only** — the most valuable content is unreadable to a low-literacy Telugu farmer. Needs a backend change (`headline_te`).
3. **No personalized crop calendar** — nothing tells a farmer "what to do on MY crop this week" keyed to plot + sowing date (My-Field). Research: sev-5.
4. **Voice is one-way** — farmers can hear (TTS) but can't ask by voice.
5. **Login syncs nothing yet** — auth ships, but doesn't persist village/fields (a `custom:place` slot is reserved for this).

## Gaps — Tier 2 (production-readiness)

6. **No observability** — no CloudWatch alarms, error tracking, or analytics. Flying blind on failures + usage.
7. **No CI test gate** — a broken push deploys live; tests don't gate the Amplify build.
8. **Region split** — frontend (us-east-1) ↔ backend (ap-south-1) adds ~250 ms/request. Co-locate to Mumbai.
9. **No custom domain + email deliverability** — ugly `amplifyapp.com` URL; Cognito default email sender (move to SES before scale).
10. **No end-to-end tests** — good unit coverage, but screen flows are verified manually.

## Gaps — Tier 3 (data accuracy & trust)

11. **Most agronomy is unverified** — only paddy is high-confidence; the rest is flagged "confirm with AEO." Needs local PJTSAU/AEO sign-off before launch.
12. **No farmer feedback loop** — Telugu wording, icons, and flows are untested on a real Bhupalpally user.

## Top 3 to do next

1. **Mandi prices** — biggest farmer value, nearly unblocked (needs the data.gov.in key).
2. **Telugu farming advice** — the content farmers need most, currently unreadable to them (backend `*_te` fields).
3. **Make login useful** — sync saved village / My-Field to the Cognito `custom:place` attribute.

In parallel, the thing no code fixes: **get it in front of one real farmer and watch.**
