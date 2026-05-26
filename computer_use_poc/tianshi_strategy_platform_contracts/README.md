# Tianshi Strategy Platform Contracts

## Package Scope

This C package defines the Dennis Risk Agent contract layer for Tianshi / strategy platform query capabilities. It is a runtime scheduling and observation contract, not a new platform executor.

The package covers:

- `fastQueryHbase` strategy hit overview.
- `eventList API-read` request-level / event-level detail lookup.
- Routing and tool selection between the two query types.
- Observation schemas and regression boundaries for safe consumption.

Related but separate strategy-governance POC:

- `computer_use_poc/strategy_governance/tianshi_policy_attribution_api_read_poc_v1.md` now records a full P0 E2E single-event policy attribution path: event detail, feature snapshot, policy version, policy tree node resolution, condition-level attribution, and node binding attribution.
- `computer_use_poc/strategy_governance/tianshi_strategy_governance_readonly_capability_v1.md` records the broader readonly governance capability: strategy detail, policy tree asset, single-event policy attribution, and policy release records.
- The validated policy tree API for that POC is `GET /v2/rest/pro/policyTree/queryProPolicyTree`.
- The POC is still a readonly evidence capability and does not imply final cheating classification or automatic enforcement.

## Relationship to Existing Validations

- v2.5.5 validated `fastQueryHbase` as `readonly_strategy_hit_check`, used to summarize whether a `sourceId` hit production risk-control or anti-cheating strategy records in a bounded time window.
- v2.5.9 validated `eventList API-read` as the request-level complement to `fastQueryHbase`, used for small-window event details such as event type, realtime feedback, error code, IP, device signal summary, and side effect operations.
- v2.5.7 / v2.5.8 / v2.5.8.1 use Tianshi as one evidence source inside multi-source E2E analysis, together with login logs and account profile sources.
- Strategy attribution follow-up validation fixed two important pitfalls: use `featureGroup=""` and exact event `_occurTime` for feature snapshots; resolve `policyTreeNodeCode` through `queryProPolicyTree`, never by guessing from `serial` or `policyCode`.

## Not Included

This C package does not itself execute general strategy governance. The strategy-governance docs define readonly evidence contracts and boundaries.

Out of scope:

- Runtime execution of broad strategy governance flows without explicit authorization.
- Automatic strategy semantic interpretation beyond readonly evidence summaries.
- Hit path reconstruction.
- Strategy version, experiment, or grey-release explanation beyond the verified single-event context.
- Automatic strategy semantic explanation or final policy judgement.

Those belong to strategy-governance follow-up work and future runtime integration, not the base C package wrapper.

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
