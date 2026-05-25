# Tianshi Platform Capability Contract v1

## Platform Positioning

Tianshi / strategy platform is treated as a production risk-control and anti-cheating strategy event query platform. It can provide evidence about strategy hits, risk decisions, event records, and request-level context.

## Dennis Agent Integration Positioning

Dennis Agent currently treats Tianshi as a `readonly evidence source`.

Tianshi evidence can support:

- Strategy hit overview.
- Request-level or event-level detail lookup.
- Cross-source evidence cards when combined with login logs, account profile, device evidence, frontend behavior, or offline aggregation plans.

Tianshi evidence must not be consumed as a standalone final risk conclusion.

## Current Capability List

### fastQueryHbase

Purpose: strategy hit overview for a `sourceId` in a bounded time window.

Typical output:

- Whether any record exists.
- Whether production policy was hit.
- Risk decision distribution.
- Event type / risk type distribution.
- Sample hit summaries.

### eventList API-read

Purpose: request-level / event-level detail lookup for a specific event type and small time window.

Typical output:

- Event list count and records total.
- Realtime operation, error code, side effect operations.
- IP / city / openId presence.
- Device signal summary and raw field summary.

## Excluded Capabilities

The C package does not include:

- Strategy tree parsing.
- Strategy node or condition expression understanding.
- Strategy version, grey-release, or experiment explanation.
- Automatic strategy semantic explanation.
- Final risk classification or automatic disposition.

## Unified Boundaries

- Readonly only.
- No platform write operation.
- No automatic user punishment, verification, block, allowlist, or rollback.
- No final cheating / ATO / crawler / fraud determination from Tianshi alone.
- No replacement for DataAgent / Hive when the user needs batch aggregation, trends, denominators, or cross-day statistics.
- No persistence of cookie, token, session, authorization, or full platform request headers.
- `auth blocker`, `permission blocker`, `no_data`, and `sampling` are different states and must not be collapsed.
