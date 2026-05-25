# Multi Evidence Orchestration Contracts

## Package Scope

This B package defines the Dennis Risk Agent multi-source evidence orchestration contract for E2E risk assessment. It turns scattered v2.5.7 / v2.5.8 / v2.5.8.1 multi-source notes into a stable planner, output template, and regression layer.

## Relationship to A/C/D/E/F Packages

- A package: batch risk clustering / L1 shallow feature drilldown. B package consumes batch outputs only when the user asks for E2E assessment; it does not replace batch clustering.
- C package: Tianshi / strategy platform contracts. B package calls C package for `fastQueryHbase` strategy overview and `eventList API-read` request-level detail.
- D package: strategy tree / strategy configuration understanding. Not included in B v1.
- E package: frontend activity / behavior chain. Reserved as optional future evidence source; not default in B v1.
- F package: device / account association and device risk. Reserved as optional future evidence source; not default in B v1.

## Evidence Sources Covered in B v1

Default minimum three-source plan:

- `tianshi_strategy_hit_check`: Tianshi `fastQueryHbase` strategy hit overview.
- `unified_login_log_check`: login / token / verification chain.
- `archives_center_profile_check`: account profile / historical risk / current account status.

Conditional source:

- `tianshi_eventlist_api_read`: only when the user needs specific request fields, eventType details, realtime feedback, error code, IP, device signal, or side effect operations.

## Not Included

- No real platform query.
- No DataAgent execution.
- No release package update.
- No core Skill modification.
- No automatic enforcement or disposition.
- No strategy tree parsing.
- No new frontend activity or device SDK hand.
- No final risk classification from a single source.

## TODO

- Add live wrapper hooks only after explicit runtime authorization.
- Add D package strategy tree planner when the strategy configuration package exists.
- Add E/F evidence sources as optional, gated sources after their contracts are complete.
