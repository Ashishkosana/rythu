# 0001 — Modular monolith on Azure Functions

- **Status:** accepted (2026-10-24)

## Context
One developer, 1–20 users, ≈ $0/month on an Azure for Students subscription. New features (alerts, mandi
ingest, calendar, assistant) need HTTP endpoints *and* scheduled/queued work.

## Options
1. **FastAPI mounted in Azure Functions (`AsgiFunctionApp`) + timer/queue triggers in the same Function App** — one bill, built-in triggers, monthly free grant (Flex Consumption: 250k executions + 100k GB-s per subscription, per the Azure pricing page at time of writing).
2. **FastAPI on Azure Container Apps + Container Apps Jobs** — no cold-start quirks specific to Functions, more ops surface.
3. **App Service B1** — always warm, ≈ $13/month.
4. **Microservices per context** — independent deploys nobody needs yet.

## Decision
Option 1. Bounded contexts (weather/advisory, market, profile/field/calendar, notify, assistant) are Python
packages with an import-boundary test, each keeping the hexagonal domain/ports/adapters split.

## Consequences
- ➕ One deployable, one pipeline; triggers and HTTP share the service layer.
- ➕ Plain ASGI → portable to option 2 without code changes.
- ➖ Python cold starts (1–3 s); mitigated by offline-first client rendering cached data first.
- ➖ Module boundaries enforced by convention + lint, not by the network.
- Revisit when a second team or a component with very different scaling/latency needs appears.

References: Newman, *Building Microservices* (when not to split); Martin, *Clean Architecture* (dependency rule); Evans, *Domain-Driven Design* (bounded contexts).
