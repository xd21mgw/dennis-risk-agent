# Browser-Backed Fixed Actions v1 Integration Closure

## Scope

This document closes the Dennis mother-runtime integration layer for the
browser-backed fixed actions v1 batch. It records registration parity, routing,
orchestration, and output-boundary rules. It does not add actions, run live
smoke, access real platforms, change default runtime routing, call DataAgent, or
package runtime artifacts.

## Registration Consistency Table

Local inspection confirms the adjacent Node service registry/allowlist and the
Dennis Python client use the same fixed action names. The README and online
summary in `browser-backed-api-poc` also list these fixed actions and preserve
the same safety boundaries.

| action_name | platform | Node registry/allowlist | Python client endpoint | source status for routing | default_runtime_routing |
| --- | --- | --- | --- | --- | --- |
| `login_logs_search` | Login Logs | registered | `/actions/login_logs_search` | `live_smoke_verified` | false |
| `track_analysis_check_data_ready` | Track Analysis | registered | `/actions/track_analysis_check_data_ready` | `live_smoke_verified`; provenance/readiness only | false |
| `archives_user_profile` | Archives Center | registered | `/actions/archives_user_profile` | `live_smoke_verified` | false |
| `archives_user_analysis` | Archives Center | registered | `/actions/archives_user_analysis` | `live_smoke_verified`; large `pageSize` can become `partial_observation_available` | false |
| `archives_photo_search` | Archives Center | registered | `/actions/archives_photo_search` | `no_data`; path live; `no_data_not_risk_exclusion` | false |
| `archives_related_users` | Archives Center | registered | `/actions/archives_related_users` | `live_smoke_verified` | false |
| `rcp_event_detail` | RCP / Tianshi | registered | `/actions/rcp_event_detail` | `live_smoke_verified` | false |
| `rcp_event_feature_list` | RCP / Tianshi | registered | `/actions/rcp_event_feature_list` | `partial_observation_available` | false |
| `rcp_policy_tree_lookup` | RCP / Tianshi | registered | `/actions/rcp_policy_tree_lookup` | `live_smoke_verified`; strategy asset governance only | false |

Registry evidence is registration parity only. It does not make any action a
default runtime route. Every action must be selected by an explicit source plan.

## Routing Coverage

| scene | route/capability layer | explicit actions | boundary |
| --- | --- | --- | --- |
| ATO / login anomaly | `multi_evidence_orchestration_contracts` with account-security source plan | `login_logs_search` -> `archives_user_profile` -> `archives_user_analysis` -> `track_analysis_check_data_ready` | Login `no_data` or window gap does not exclude ATO. Track readiness is source-quality/provenance, not risk conclusion. |
| Abnormal publish / sexual diversion / content handoff | account-security with publish/content conditional source plan | `archives_photo_search` -> `archives_user_profile` -> `archives_user_analysis` | Photo `no_data` does not exclude abnormal publish or content handoff. |
| Account spread / same-device relation | relation clue source plan | `archives_related_users` -> `archives_user_profile` / `login_logs_search` / `track_analysis_check_data_ready` | Related users are spread clues, not gang conclusion. |
| RCP event attribution | `single_event_policy_attribution` support source plan | `rcp_event_detail` -> `rcp_event_feature_list` | Feature list partial supports feature-group summary only; do not claim complete feature evidence. |
| Policy asset governance / policy-tree explanation | `policy_tree_asset_lookup` | `rcp_policy_tree_lookup` | Policy-tree lookup explains strategy assets and tree/node context; it is not a single-case event-hit path. |

## Orchestration Output Contract

Every answer that uses these actions must output or internally produce:

- `source_plan`
- `actions`
- `source_quality_matrix`
- `missing_evidence`
- `evidence_strength`
- `final_answer_boundary`

Required boundary flags include:

- `no_data_not_risk_exclusion`
- `partial_observation_available`
- `large_response_limited`
- `auth_flow_not_completed_in_bound_context`
- `strategy_hit_not_final_judgement`
- `policy_tree_asset_not_event_hit_path`
- `related_users_not_gang_conclusion`
- `track_readiness_not_risk_conclusion`

## Source Quality Semantics

`no_data`, `auth_failed`, `blocked`, `timeout`, `parse_error`,
`partial_observation_available`, and `large_response_limited` are source-quality
states. They must not be rewritten as low risk, no risk, permission denial, or
platform absence without evidence.

Archives 302 or login redirection must be normalized as
`auth_flow_not_completed_in_bound_context`; do not describe it as generic
permission denied.

Risk entity identifiers are valid evidence handles in internal risk review and
source chaining: `user_id`, `device_id`, `ip`, `event_id`, `strategy_id`,
`photo_id`, `policyCode`, and `policyTreeCode`.

Credential secrets and strict PII remain forbidden in every mode:
`cookie`, `token`, `session`, `header`, `authorization`, `password`, full phone
number, ID card number, real name, and detailed address.

## Gaps Preserved

- No action is promoted to `default_runtime_routing=true`.
- `archives_photo_search=no_data` still requires publish/context supplement
  before abnormal publish can be excluded.
- `archives_user_analysis` large response must shrink time window/page size or
  paginate; partial observation can be used only with that boundary.
- `rcp_event_feature_list` partial observation can summarize feature groups but
  cannot claim complete feature values.
- `rcp_policy_tree_lookup` remains strategy-governance context and must not be
  mixed with event detail, feature list, or strategy-hit judgement.
