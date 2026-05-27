# Source Orchestration Validator Patch v1

## Goal

Add an executable local gate so single-user account security / ATO execution cannot stop after only `user_login_unified_log`.

This patch is intentionally minimal. It does not edit long playbooks, probe track-analysis endpoints, access real platforms, call DataAgent, change gateway / safeBins / tools, or repackage a release.

## Added Files

- `computer_use_poc/source_orchestration_plan_v1.yaml`
- `computer_use_poc/source_orchestration_check.py`

## Plan Summary

For `single_user_account_security` / ATO / login anomaly with one entity, required P0 sources are:

- `user_login_unified_log`
- `weapon_user_to_device_graph`
- `weapon_device_risk`

Conditional sources are:

- `archives_profile_if_auth_ready`
- `tianshi_if_event_or_source_id_available`
- `track_analysis_if_endpoint_verified`

Stop conditions:

- `allow_stop_after_login_log_only: false`
- `allow_final_conclusion_without_source_completion_matrix: false`
- `allow_low_risk_from_no_data_only: false`

## Validator Summary

`source_orchestration_check.py`:

- Outputs the required source plan for a task type / entity count.
- Validates a JSON `source_completion_matrix` when provided.
- Fails if only login log is present.
- Fails if Weapon graph/risk sources do not use `/apiv2/graphData` and `/apiv2/riskData`.
- Fails if track-analysis is marked completed without endpoint verification.

## Runtime Preflight

`runtime_preflight_check.py` now checks:

- `source_orchestration_plan_v1.yaml` exists and contains required P0 / stop condition markers.
- `source_orchestration_check.py` contains validator rules.
- The validator can run locally and select the single-user account security plan.

## Regression

- `SOURCE-PLAN-REQUIRED-001`
- `LOGIN-LOG-ONLY-CANNOT-CONCLUDE-001`
- `SOURCE-COMPLETION-MATRIX-REQUIRED-001`

## Boundaries

- No real platform access.
- No DataAgent call.
- No gateway / safeBins / tools change.
- No track-analysis endpoint handling.
- No release repackaging.
