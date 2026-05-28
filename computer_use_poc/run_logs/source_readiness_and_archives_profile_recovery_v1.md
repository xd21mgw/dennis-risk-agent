# Source Readiness Matrix and Archives Profile Recovery v1

## Purpose

This patch restores Archives Center user analysis as a P0 source in Dennis Risk Agent planning and adds a source readiness matrix so source priority is not confused with current runner availability.

## Files Changed

- `computer_use_poc/source_readiness_matrix_v1.yaml`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/source_orchestration_plan_v1.yaml`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## Readiness Summary

- `user_login_unified_log`: `runner_ready`, `health_check_verified`, `playbook_ready`.
- `weapon_graphData`: `runner_ready`, `health_check_verified`, `playbook_ready`.
- `weapon_riskData`: `runner_ready`, `health_check_verified`, `playbook_ready`, conditional on `device_id`.
- `archives_profile_readonly`: `playbook_ready`, `not_connected`; remains P0 by evidence value.
- `archives_publish_device_trace`: future source, not connected in this patch.
- `tianshi_strategy_hit_inventory` and `rcp_event_detail`: `playbook_ready_not_runner_ready`.
- `track_analysis_activity_profile`: `endpoint_verified_not_runner_ready`.
- `dataagent_hive`: `requires_authorization`, `playbook_ready`.

## Archives Profile Boundary

- Readonly only.
- Supports `user_id` input.
- Intended output: user profile, account status, ban/downrank summary, registration device summary, login device summary.
- If homeInfo is available, output `archives_profile_source_status=completed`.
- Auth failure must be marked `archives_auth_gap`.
- Do not output cookie/token/session/header.
- Do not perform auth repair in business case.
- Without publish_device_id, do not judge publish-device anomaly.

## Not Done

- Did not implement full publish-device trace.
- Did not implement Tianshi / RCP runner.
- Did not implement track-analysis runner.
- Did not access real platforms.
- Did not call DataAgent / Hive.
- Did not modify live config, gateway, safeBins, or tools.
- Did not repackage.
