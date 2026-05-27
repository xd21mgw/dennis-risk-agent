# Platform Capability Status + Track-analysis Registration and Alignment v1

## Goal

Unify three related changes:

- Four-level platform capability status and low-cost-first routing.
- Formal registration of `track_analysis_activity_profile_api_direct`.
- Track-analysis event-day activity alignment for login / scan / device switch / strategy-hit dates.

## Capability Status

The runtime must not use a binary API direct / non-API-direct split. Platform sources use:

- `api_direct_confirmed`
- `same_origin_api_confirmed`
- `partial_api_direct`
- `pending_api_direct_confirmation`

## Track-analysis Capability

Registered capability:

- capability: `track_analysis_activity_profile_api_direct`
- type: `platform_source`
- status: `api_direct_confirmed`
- cost: low
- execution_mode: `realtime_readonly_api`
- user_confirmation_required: false
- dataagent_required: false

Supported input:

- `user_id`
- `device_id`
- `appName=KUAISHOU|NEBULA`

Supported actions:

- `getLastestDateTime`
- `getDeviceIds`
- `getUseDuration`
- `profile`

Observation fields:

- `profile_card`
- `device_ids`
- `latest_datetime`
- `uid_did_relation_latest_datetime`
- `daily_duration_rows`
- `total_duration`
- `peak_duration`
- `first_active_date`
- `register_time`
- `fan_distribution`
- `active_days_bucket`

## Routing

Route to `track_analysis_activity_profile_api_direct` for:

- user / device recent-30-day activity.
- long-inactive-then-sudden-activation.
- whether an abnormal device was active on a given day.
- protocol login vs traditional ATO supporting evidence.
- group-control / device abnormal activity supporting evidence.
- account profile / low-activity account risk.
- anti-crawler / traffic anomaly questions involving userId/deviceId activity mismatch.

## Event-day Alignment

`getUseDuration` must support day-level alignment against:

- login success date.
- scan-login date.
- device-switch date.
- abnormal-device-login date.
- strategy-hit date.

If backend login / scan / abnormal-device login / strategy hit exists on a day but track-analysis userId/deviceId duration is `0` or no frontend activity, mark `front_backend_activity_mismatch`.

This is a medium/high-value lead for protocol login, token/session use, or non-real-client behavior, but it is not standalone final judgement.

## Account-security Integration

When login logs, Hive, Weapon, or Archives Center find abnormal mobile device, non-historical device, new-device login, post-scan new device, device-risk tag, or strategy hit, Dennis should trigger track-analysis as low-cost realtime supporting evidence before browser or DataAgent/Hive.

## Modified Files

- `computer_use_poc/capability_registry.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/track_analysis_api_direct_contract_current.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/account_security_runtime_summary_v1.md`

## Regression Added

- `TRACK-ANALYSIS-CAPABILITY-REGISTERED-001`
- `TRACK-ANALYSIS-ROUTED-FOR-ACTIVITY-QUESTION-001`
- `TRACK-ANALYSIS-LOW-COST-BEFORE-DATAAGENT-001`
- `TRACK-ANALYSIS-NO-DOM-BY-DEFAULT-001`
- `TRACK-ANALYSIS-EVIDENCE-BOUNDARY-001`
- `TRACK-ANALYSIS-EVENT-DAY-ACTIVITY-ALIGNMENT-001`
- `LOGIN-DAY-NO-FRONTEND-ACTIVITY-SIGNAL-001`

## Not Done

- Did not access real platforms.
- Did not call DataAgent.
- Did not modify gateway / safeBins / tools.
- Did not repackage release.
- Did not add a runner.
- Did not modify `sso_session_runner.py`.
