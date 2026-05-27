# Runtime Canonical Baseline v1

## Purpose

This file defines the canonical semi-open Dennis Risk Agent runtime baseline. It is the reference for future overlay generation and runtime validation.

## Runtime Layers

| layer | role | hard boundary |
|---|---|---|
| main agent | entry routing, intent classification, spawn, user-facing logging | must not directly query risk platforms |
| dennis-risk-agent | risk analysis, source orchestration, evidence card generation | must run under dedicated readonly runtime config |
| source wrapper | controlled readonly data access for P0 sources such as unified login log, Weapon, and Tianshi | wrapper-first; no ad hoc curl/cookie |
| browser fallback | fallback only when wrapper is unavailable or same-origin is required | must mark access method and source quality |
| browser UI observation | P1/P2 supplemental evidence only | must not block completed P0/P1 evidence output |
| observation writer | canonical semi-open pilot log writer | append-only, redacted, no raw secrets |
| candidate queue | canonical user feedback / learning candidate sink | append-only; template CSV is not runtime target |

## Source Access Priority

1. `readonly_wrapper_api`
2. `browser_same_origin_fetch` fallback
3. `browser_ui_observation` for P1/P2 supplemental evidence only

Every source output must record `access_method`. Browser fallback success must not be described as wrapper-first success.

## ATO Runtime Baseline

Single ATO user query:

- `single_entity_execution_mode`
- readonly platform execution is allowed
- per-source checkpoint required
- partial evidence card required on timeout / auth failure / blocked / parse error

2-9 user ATO complaint batch:

- `small_batch_execution_with_checkpoint`
- P0 source per user, unified login log first
- P1 source only for anomalous users
- P2 browser source excluded by default
- per-user/source checkpoint required

10-49 entity clustering:

- `batch_clustering_mode`
- no default one-by-one online platform execution

50+ entity population:

- aggregation / DataAgent-Hive query plan only

Required ATO boundary flags:

- `no_data_not_risk_exclusion`
- `timeout_not_counter_evidence`
- `blocked_source_not_counter_evidence`
- `login_log_window_incomplete`
- `app_login_only_source_gap`
- `user_claim_not_standalone_evidence`

## Canonical Output Baseline

ATO partial evidence card must include:

- `case_id` or `batch_id`
- `user_id` or `user_count`
- `final_status`
- `conclusion_state`
- `completed_sources`
- `no_data_sources`
- `blocked_sources`
- `auth_failed_sources`
- `timeout_sources`
- `parse_error_sources`
- `missing_evidence`
- `source_quality`
- evidence sections: strong / medium / weak / counter
- `caveats`
- `next_action`
- YAML `routing_metadata`

## Observation and Feedback Baseline

- Observation skeleton is written at execution start.
- Source checkpoint is appended after each source completes or fails.
- Timeout / partial results still write final observation.
- Direct tool bypass, if it ever occurs, must be recorded with `bypass_reason` and `risk_review_required=true`.
- Runtime feedback candidate queue writes only under the canonical runtime logs path, not the template CSV.

## Overlay Hygiene

- Do not keep stacking unlimited patch overlays.
- A clean overlay must be generated from this canonical baseline.
- Old overlays must not overwrite newer runtime files.
- `runtime_config_apply_checklist_v1.md` must pass before claiming a live runtime is protected.

Recommended live order:

1. Apply dedicated dennis-risk-agent readonly runtime config.
2. Validate `safeBins`, `tools.deny`, `workspaceOnly`, and `loopDetection`.
3. Overlay ATO checkpoint / small-batch / auth-bridge rules.
4. Run single ATO and small-batch regressions.

## Non-goals

- This baseline does not modify live `openclaw.json`.
- This baseline does not grant platform access.
- This baseline does not call DataAgent.
- This baseline does not replace runtime config enforcement.
