# 0002 — Azure Table Storage as the primary store

- **Status:** accepted (2026-10-24)

## Context
Every access pattern is a key lookup or a short sorted range: forecast by grid cell, everything-for-a-user,
latest prices for commodity+district. No joins, no ad-hoc queries. The student subscription restricts regions
(community reports include Cosmos DB being limited to US regions), and the budget is ≈ $0.

## Options
1. **Azure Table Storage** — pennies, lives in the storage account Functions already needs, any allowed region.
2. **Cosmos DB free tier** — native TTL and secondary indexes; region availability on student subscriptions is uncertain.
3. **Azure SQL serverless / Postgres Flexible** — relational, but auto-pause resume (tens of seconds) or ≈ $12+/month.

## Decision
Option 1, with partition/row keys designed per access pattern (see the table in `../README.md`). Expiry is
enforced in code (`expiresAt`) plus a cleanup job; optimistic concurrency via ETags.

## Consequences
- ➕ Near-zero cost; no extra region risk; emulated locally and in CI by Azurite.
- ➖ No secondary indexes, no native TTL, transactions only within one partition.
- ➖ 64 KiB per property: the forecast payload is stored gzip-compressed as binary (7-day ≈ 37 KiB as a
  UTF-16 string, 16-day ≈ 84 KiB — over the limit; compressed ≈ 1–2 KiB). Measured in S5.
- Revisit (Postgres) when cross-user queries are needed — e.g. an extension-officer dashboard or analytics.

References: Kleppmann, *Designing Data-Intensive Applications* ch. 2–3 (model by access pattern); DeCandia et al., *Dynamo* and Chang et al., *Bigtable* (partition + sort-key design).
