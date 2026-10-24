# 0003 — Client data layer: TanStack Query + IndexedDB persistence

- **Status:** accepted (2026-10-24)

## Context
Target: first useful screen < 3 s on 3G with offline fallback, and "updated N min ago" must be true at the
moment it is read (today the service worker can serve SSR HTML with a frozen stamp). Moving to a static
export means data fetching moves to the client.

## Options
1. **TanStack Query + IndexedDB persister** — stale-while-revalidate, retries, optimistic updates, persisted cache.
2. **SWR** — smaller, but weaker offline persistence story.
3. **Hand-rolled fetch + cache** — no dependency, but we would own retry/dedup/persistence bugs.

## Decision
Option 1. A typed API client (generated types, ADR-independent) sits under per-resource hooks
(`useWeather`, `useProfile`); presentational components receive props only. Data age is computed on-device
from `upstream_fetched_at`.

## Consequences
- ➕ Instant render from cache; honest age; consistent loading/error/offline states.
- ➖ ~13 KB gz dependency; two clocks (device vs server) to reason about — clamp negative ages.
- ➖ Cache invalidation is now a client concern (keys include lat/lon cell, crop, water).
