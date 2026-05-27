# Dennis Risk Agent Live Overlay 20260527 Full Patch Manifest

## Purpose

Focused live overlay patch package. This is not a full release and does not include historical release directories, outputs/dist, auth state, or unrelated run logs.

## Included Capabilities

- SSO runner real executor and live dependency patch.
- Release / overlay readiness gate and runtime preflight.
- DataAgent / Hive registry preflight and per-call authorization boundary.
- General evidence reasoning contract and runtime summary updates.
- Platform capability four-status taxonomy and low-cost source priority.
- Track-analysis API direct contract, capability registration, routing, and event-day activity alignment.

## Included Files

- `TOOLS.md`
- `AGENTS.md`
- `computer_use_poc/sso_session_runner.py`
- `computer_use_poc/runtime_preflight_check.py`
- `computer_use_poc/release_overlay_readiness_checklist.md`
- `computer_use_poc/user_login_log_api_readonly_internal_agent_playbook_v2_4_10.md`
- `computer_use_poc/run_logs/sso_session_runner_real_executor_patch_v1.md`
- `computer_use_poc/run_logs/sso_session_runner_live_dependency_patch_v1.md`
- `computer_use_poc/README.md`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/run_logs/release_overlay_readiness_gate_v1.md`
- `computer_use_poc/approval_policy.md`
- `computer_use_poc/run_logs/dataagent_hive_registry_preflight_patch_v1.md`
- `computer_use_poc/run_logs/dataagent_per_call_authorization_guard_v1.md`
- `computer_use_poc/batch_risk_clustering/account_security_hive_source_registry_v1.md`
- `computer_use_poc/general_evidence_reasoning_contract_v1.md`
- `computer_use_poc/run_logs/general_evidence_reasoning_contract_patch_v1.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/account_security_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/protocol_attack_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/group_control_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/anti_crawler_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/activity_anti_cheating_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/traffic_diversion_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/traffic_anti_cheating_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/cracked_app_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/real_user_crowdsourcing_runtime_summary_v1.md`
- `computer_use_poc/run_logs/platform_capability_status_and_cost_priority_v1.md`
- `computer_use_poc/track_analysis_api_direct_contract_current.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/run_logs/track_analysis_api_direct_contract_current.md`
- `computer_use_poc/run_logs/platform_capability_status_track_analysis_registration_and_alignment_v1.md`

## Missing Files

None.

## Explicitly Excluded

- `outputs/release/dennis_risk_agent_tianshi_runtime_patch_v1_safe/`
- `computer_use_poc/run_logs/archives_center_v2_6_1_text_dryrun_regression.md`
- `.DS_Store`
- `outputs/dist/` old packages
- cookie / token / session / header / auth state
- real sensitive data

## Overlay Validation Steps

1. Run `python3 computer_use_poc/runtime_preflight_check.py`.
2. Validate runner: `python3 computer_use_poc/sso_session_runner.py --platform login_log --action query_user_login_log --user-id 62950989 --timeout 30 --format json`.
3. KIM/Web retest: `不走缓存，用户是不是有问题？user_id=62950989`.
4. Verify realtime API auto-trigger and DataAgent/Hive per-call authorization.
5. Verify track-analysis capability registration and event-day activity alignment.
6. Verify evidence_card / source_quality / routing_metadata hard gate.
