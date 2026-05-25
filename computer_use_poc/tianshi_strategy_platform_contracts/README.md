# Tianshi Strategy Platform Contracts

## Package Scope

This C package defines the Dennis Risk Agent contract layer for Tianshi / strategy platform query capabilities. It is a runtime scheduling and observation contract, not a new platform executor.

The package covers:

- `fastQueryHbase` strategy hit overview.
- `eventList API-read` request-level / event-level detail lookup.
- Routing and tool selection between the two query types.
- Observation schemas and regression boundaries for safe consumption.

## Relationship to Existing Validations

- v2.5.5 validated `fastQueryHbase` as `readonly_strategy_hit_check`, used to summarize whether a `sourceId` hit production risk-control or anti-cheating strategy records in a bounded time window.
- v2.5.9 validated `eventList API-read` as the request-level complement to `fastQueryHbase`, used for small-window event details such as event type, realtime feedback, error code, IP, device signal summary, and side effect operations.
- v2.5.7 / v2.5.8 / v2.5.8.1 use Tianshi as one evidence source inside multi-source E2E analysis, together with login logs and account profile sources.

## Not Included

This C package does not cover strategy tree understanding.

Out of scope:

- Strategy tree parsing.
- Strategy nodes and condition expression interpretation.
- Hit path reconstruction.
- Strategy version, experiment, or grey-release explanation.
- Automatic strategy semantic explanation.

Those belong to the future D package: strategy tree / strategy configuration understanding.

## Boundaries

- Readonly evidence source only.
- No write operation.
- No automatic enforcement or disposition.
- No final cheating / ATO / fraud classification by Tianshi evidence alone.
- No replacement for DataAgent / Hive aggregation.
- No cookie, token, session, authorization, or full request header persistence.
- `auth blocker`, `no_data`, and `sampling` must be separated.

## TODO

- Connect this contract to future live wrappers only after explicit runtime authorization.
- Keep strategy tree interpretation in the future D package.
- Add more eventType mappings only after verified need; do not build a full eventType dictionary in this package.
