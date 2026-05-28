# ATO Source Priority / Access Method Correction v1

## Purpose

This patch fixes the plan-only diagnostic and source-plan interpretation for ATO / account-security cases.

The key correction is:

> Evidence value decides `source_priority`; execution path decides `access_method`. API direct first is a low-cost collection preference, not the P0 / P1 / P2 decision rule.

## Files Updated

- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/source_orchestration_plan_v1.yaml`
- `computer_use_poc/plan_only_diagnostic_rubric_v1.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## Corrected Rules

- `source_priority` and `access_method` must be expressed separately.
- ATO Archives Center user analysis is a P0 account-baseline source, not P1.
- Non-API sources are not automatically downgraded. A P0 source can use `browser_cookie_activation` / `same_origin_fetch` when that is the controlled access method.
- Browser is not a general default replacement and must not be used by main agent as direct fallback.
- Abnormal publish / non-owner publish / traffic-diversion content makes publish list, publish time, publish device, and publish source chain P0-conditional evidence.
- User-explicit strategy-hit questions make Tianshi strategy hit a P0-explicit target source.
- Weapon graphData is P0; Weapon riskData is P0-conditional / P1 depending on whether a raw device reference exists.
- Missing device reference must be represented as `missing_device_reference`, not fake riskData coverage.
- DataAgent / Hive remains per-call authorization only; P0 / P1 source gaps do not grant automatic Hive execution.
- Stop condition cannot skip explicit target sources, Archives user analysis in ATO, or publish chain in abnormal-publish cases.

## Time Window Inference

ATO time_window_inference is now a P0 pre-step. When event time is missing, do not use the latest 7 days as the only window.

Candidate anchors:

- `user_report_time`
- `archive_user_analysis_time`
- `audit_log_time`
- `publish_time`
- `publish_device_time`
- `strategy_hit_time`
- `login_event_time`
- `device_first_seen_time`
- `frontend_activity_time`

Audit reason guides investigation direction and time window selection, but does not prove ATO. Abnormal publish makes publish time and publish device primary anchors; the agent should look backward to login / scan / OAuth / device switch / token-session / strategy hit and forward to audit / punishment / complaint.

## Regression Cases Added

- `ATO-ARCHIVE-CENTER-P0-001`
- `ATO-PUBLISH-CHAIN-P0-001`
- `ATO-POLICY-HIT-EXPLICIT-SOURCE-001`
- `WEAPON-RISKDATA-CONDITIONAL-001`
- `SOURCE-PRIORITY-ACCESS-METHOD-SEPARATION-001`
- `DATAAGENT-HIVE-PER-CALL-AUTHORIZATION-001`
- `ATO-TIME-WINDOW-INFERENCE-001`
- `ATO-PUBLISH-TIME-ANCHOR-001`

## Boundaries

- Did not access real platforms.
- Did not call DataAgent / Hive.
- Did not modify auth / gateway / safeBins / TOOLS configuration.
- Did not repackage.
- Did not submit git.
