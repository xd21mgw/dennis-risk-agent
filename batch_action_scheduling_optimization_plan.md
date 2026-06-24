# Batch Action Scheduling Optimization Plan

## Scope

This plan optimizes browser-backed batch action scheduling for autonomous feature discovery. It does not reduce source coverage as a goal. It changes how actions are layered, waited on, timed, cached, and appended so slow or unstable sources do not block the first discovery report.

Boundaries:

- No platform access in this planning step.
- No Hive/DataAgent.
- No code changes in this planning step.
- No release/dist/full_runtime refresh.
- Timeout, auth_failed, missing_device_id, parser_boundary, and business_field_gap must be recorded as source gaps, never as no-risk evidence.
- Once a raw bundle is collected, P0 foundation, candidate replay, discovery provenance, and oracle eval should reuse the local bundle.

## Primary Timing Clarification

`primary` is not a single interface. It is the first-round foundational source group. In the current timing report, `D2 primary=186s` means the foundational source group accumulated about 186 seconds of browser-backed wait time. It cannot be interpreted as one specific interface being slow.

Current primary group usually includes:

| Source/action | Purpose |
|---|---|
| `archives_user_profile` | Current profile/account state. |
| `weapon_inventory` graph/inventory path | Device/risk-device entry evidence. |
| `archives_user_analysis` | Account/user operation history and behavior facts when available. |
| `archives_photo_search` | Content/photo entry facts and followup anchors. |

Current gap:

- Primary currently lacks action-level timing in the summary.
- Primary should not be cut to reduce latency.
- Primary should be split internally into timing and scheduling sublayers:
  - `fast_core`
  - `risk_core`
  - `unstable`

Recommended new timing fields:

- `source_group`
- `source_action`
- `chunk_id`
- `user_count`
- `status_count`
- `wait_ms`
- `start_time`
- `end_time`
- `timeout_count`
- `auth_failed_count`
- `parser_boundary_count`
- `data_gap_count`

## Source Layers

### blocking_core

Sources needed to produce a credible first discovery report or a meaningful source-gap statement. The first report waits for these sources to reach a terminal state, or until their per-source budget is exhausted.

Terminal states:

- `completed`
- `no_data`
- `auth_failed`
- `timeout`
- `parser_gap`
- `business_field_gap`
- `missing_required_fields`

### nonblocking_broad

Broad discovery sources that should still be requested to preserve feature discovery coverage, but should not block the first report if they are slow. Returned facts are included if available before first-report cutoff; otherwise they become `pending_tail`.

### slow_tail

Known slow or unstable sources. These are still useful for coverage and later evidence, but they should not determine when the first report is emitted. They should run under a tail budget and circuit breaker.

### conditional_followup

Sources that require an anchor from earlier sources, such as `device_id`, `event_id`, `photo_id`, or Track readiness. If the anchor is missing, the action should not be forced; it should be recorded as `source_gap` with a concrete missing reason.

## Source/action Layering

| Source/action | Suggested layer | First-report behavior | Notes |
|---|---|---|---|
| `login_logs_search` | `blocking_core` / `fast_core` | Wait until terminal state or core budget. | Event chain, client runtime, URI, IP/network, token/credential actions. |
| `archives_user_profile` | `blocking_core` / `fast_core` | Wait until terminal state or core budget. | Current profile/account state. |
| `archives_user_analysis` | `nonblocking_broad` / `unstable` | Include if completed before cutoff; otherwise `source_gap`. | Valuable operation history, but auth_failed/parser gaps must not block. |
| `archives_review_logs` | `blocking_core` for profile/content/enforcement waves; otherwise `nonblocking_broad` | Wait for profile-lure/enforcement waves; broad otherwise. | Historical profile/content submissions and enforcement facts. |
| `archives_negative_report` | `blocking_core` for enforcement waves; otherwise `nonblocking_broad` | Wait for enforcement waves; broad otherwise. | Negative ops and enforcement chain. |
| `archives_private_message_search` | `nonblocking_broad` | Include if completed before cutoff; otherwise `pending_tail`. | Important for social/contact diversion, but should not block unrelated device waves. |
| `archives_photo_search` | `nonblocking_broad` / `primary` | Include if completed before cutoff; anchors followup. | Content entry source; detail followup is conditional. |
| `archives_comment_search` | `nonblocking_broad` | Include if completed before cutoff; otherwise `pending_tail`. | Social/content funnel evidence. |
| `weapon_inventory` graphData | `blocking_core` for device waves; otherwise `nonblocking_broad` / `risk_core` | Wait for device/fresh-device waves; broad otherwise. | Must preserve raw device_id references for riskData. |
| `weapon_inventory` riskData | `conditional_followup` | Do not block first report unless device wave and device_id exists. | Requires raw device_id. If missing, mark `missing_device_id`, not no-risk. |
| `rcp_fast_query_hbase` | `conditional_followup` | Do not block generic first report. | Event/policy anchor source, not primary feature source. |
| `rcp_event_detail` | `slow_tail` / `conditional_followup` | Never block first report. | High timeout risk; append later if completed. |
| `rcp_event_feature_list` | `slow_tail` / `conditional_followup` | Never block first report. | Useful feature source when stable; timeout must be `source_gap`. |
| `track_analysis_check_data_ready` | `nonblocking_broad` / readiness gate | Include readiness if fast; do not treat as behavior evidence. | `NEED_DATA_SYNC` / `HIVE_UNFINISHED` becomes `track_business_field_gap`. |
| Track duration / behavior source | `slow_tail` / `conditional_followup` | Only run after readiness supports it; never block first report. | Cannot infer duration/active days/lineage from readiness-only responses. |
| one-degree / detail followup | `slow_tail` / `conditional_followup` | Never block first report. | Useful for extended social graph, but high fanout risk. |

## First Report Contract

The first report is the first usable autonomous discovery output from completed core facts plus any broad facts that have already arrived.

### Wait for

- `login_logs_search`
- `archives_user_profile`
- Scenario-critical core sources:
  - profile/content/enforcement waves: `archives_review_logs`, `archives_negative_report`
  - device/fresh-device waves: `weapon_inventory` graphData
- Any source already completed before first-report cutoff.

### Do not wait for

- `rcp_event_detail`
- `rcp_event_feature_list`
- Track duration / behavior source
- one-degree/detail followup
- `weapon_inventory` riskData when raw device_id is absent
- source/action groups that have hit circuit breaker

### Required output fields

- `first_report_id`
- `raw_bundle_id`
- `first_report_ready_time`
- `first_report_elapsed_ms`
- `waited_sources`
- `completed_sources`
- `pending_tail_sources`
- `source_gap_sources`
- `parser_gap_sources`
- `business_field_gap_sources`
- `candidate_proposals`
- `coverage_boundary`

### Pending tail / source gap handling

- `pending_tail`: source still running or intentionally allowed to append later.
- `source_gap`: source reached terminal failure or cannot execute due to missing anchor.
- `business_field_gap`: transport completed but business fields are not available, such as Track readiness returning `NEED_DATA_SYNC` / `HIVE_UNFINISHED`.
- `missing_required_fields`: followup cannot run, such as riskData missing raw `device_id`.

## Late Append Contract

Late append adds evidence from tail sources after the first report. It must not overwrite the first report silently.

Required fields:

- `late_append_id`
- `parent_first_report_id`
- `raw_bundle_id`
- `source_completion_delta`
- `new_evidence`
- `candidate_delta`
- `conclusion_delta`
- `append_type`
- `still_missing_sources`

Append types:

- `evidence_strengthened`: late evidence supports an existing candidate.
- `evidence_countered`: late evidence weakens or contradicts an existing candidate.
- `new_candidate_discovered`: late evidence adds a new discovery-only candidate.
- `no_change`: source completed but did not materially change the report.
- `still_gap`: source still failed, timed out, or lacked business fields.

Rules:

- Preserve the original first-report conclusion and timestamp.
- If late evidence changes the interpretation, emit a revised conclusion delta instead of rewriting history.
- Replay/provenance must distinguish first-report evidence from late-append evidence.

## Timeout Circuit Breaker

### Per source/action breaker

Open a circuit for one wave when either condition is met:

- Two consecutive chunks for the same source/action exceed timeout budget.
- Timeout ratio for a source/action exceeds 50% within the wave.

Circuit-open result:

- Stop scheduling more chunks for that source/action in the current wave.
- Mark remaining users as `source_gap` with `gap_reason=circuit_open_timeout`.
- Continue other source layers.

### Suggested max waits

| Layer | Suggested max wait |
---|---:|
| `fast_core` | 8-12s per chunk |
| `risk_core` | 15-25s per chunk |
| `nonblocking_broad` | 15-30s per chunk, not first-report blocking |
| `slow_tail` | 30-60s tail budget per wave, not first-report blocking |
| `conditional_followup` | Only if anchor exists; otherwise immediate gap |

### Special cases

- `auth_failed`: after repeated auth failure in the same source/action, stop retrying and mark `auth_session_issue`.
- `missing_device_id`: do not attempt riskData; mark `not_executed_missing_device_id`.
- `NEED_DATA_SYNC` / `HIVE_UNFINISHED`: stop Track behavior expansion and mark `track_business_field_gap`.
- `parser_boundary`: do not treat transport completion as business evidence.

## Raw Bundle Cache / Replay Contract

Browser-backed harness should only collect raw source observations and source status/timing. It should not be responsible for repeated local analysis.

Recommended flow:

1. Browser-backed batch writes immutable raw bundle.
2. Raw bundle includes source status, timing, chunk metadata, and safe raw references.
3. P0 foundation reads the raw bundle locally.
4. Candidate replay reads P0 artifacts locally.
5. Discovery provenance reads replay outputs locally.
6. Oracle/final eval reads local replay/provenance outputs.

Required identifiers:

- `raw_bundle_id`
- `raw_bundle_path`
- `source_artifact_hash`
- `source_plan_id`
- `batch_run_id`
- `first_report_id`
- `late_append_id`

Expected benefit:

- Live/browser-backed time is paid once.
- Re-running P0/replay/eval should be cache replay, not source reacquisition.

## Metrics

Top-level metrics:

- `total_elapsed_ms`
- `first_report_elapsed_ms`
- `tail_elapsed_ms`
- `source_elapsed_ms`
- `browser_wait_ms`
- `cache_replay_elapsed_ms`

Source metrics:

- `source_group`
- `source_action`
- `layer`
- `chunk_id`
- `user_count`
- `status_count`
- `completed_count`
- `timeout_count`
- `auth_failed_count`
- `missing_required_fields_count`
- `parser_gap_count`
- `business_field_gap_count`
- `source_gap_count`
- `wait_ms`

Report metrics:

- `first_report_ready_time`
- `pending_tail_count`
- `late_append_count`
- `late_append_strengthened_count`
- `late_append_countered_count`
- `late_append_still_gap_count`

Cache metrics:

- `raw_bundle_cache_hit`
- `p0_foundation_elapsed_ms`
- `candidate_replay_elapsed_ms`
- `oracle_eval_elapsed_ms`

## Optimization Direction

Do not optimize by reducing source coverage. Optimize by:

1. Splitting primary into `fast_core`, `risk_core`, and `unstable`.
2. Keeping broad source acquisition, but not letting slow tails block the first report.
3. Adding action-level timing for every primary source/action.
4. Applying circuit breakers to repeated timeout/auth/missing-anchor cases.
5. Reusing raw bundles for local P0/replay/eval.

Expected impact:

- Full all-source wave: reduce first-report latency by roughly 30%-50% without dropping source coverage.
- Targeted supplement runs: keep around 30-90 seconds when only confirming specific gaps.
- Local replay/eval: should be seconds to low-minute range after raw bundle cache is available.
