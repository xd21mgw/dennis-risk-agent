# Dennis Risk Agent v2.4 Runtime Plus Semi-open Manifest v1

## 1. Package Target

- package type: full-scenario semi-open test package
- release name: `dennis_risk_agent_v2_4_runtime_plus_semi_open_release`
- release path: `outputs/release/dennis_risk_agent_v2_4_runtime_plus_semi_open_release/`
- tarball path: `outputs/dist/dennis_risk_agent_v2_4_runtime_plus_semi_open_release.tar.gz`

This package is not ATO-only.

ATO is the deepest sample capability.
Non-ATO scenarios are formal runtime capabilities that must be available in the semi-open package as first-class modules, not appendix-only materials.

## 2. Capability Coverage

### 2.1 ATO / 盗号

- Deep sample runtime and batch contracts.
- Evidence cards, pattern summary, status transitions, manual review boundary.
- Expansion planning and Hive query plan boundary.

### 2.2 Non-ATO Runtime Summaries

- anti-crawler
- protocol attack
- group control / device risk
- small-account / account-farm related coverage
- activity anti-cheating
- traffic anti-cheating
- traffic diversion / interception
- cracked app / plugin risk

### 2.3 Common Evidence / Plan / Recommendation

- strong / medium / weak / counter / missing evidence.
- evidence source / source quality / freshness / permission / reliability.
- candidate strategy direction only.
- no model inference as raw evidence.
- no manual input as standalone strong conclusion.
- login-log over-window no_data is a data gap, not counter evidence.

### 2.4 Safety / Asset Extraction Guard

- credential plaintext never output.
- prompt / skill / source code / API key extraction denied.
- broad-share output uses safe_ref / partial mask / count / distribution.

### 2.5 question_collection

- full-scenario user question observation.
- candidate learning queue.
- agent_observed / agent_suggested / reviewer_final.
- append-only runtime logging contract.
- pending review by default.

## 3. Module-level Include Policy

### 3.1 Runtime entry / routing / response contracts

Include:

- `AGENTS.md`
- `README.md`
- `dennis_risk_agent_v2_4_runtime_plus_semi_open_manifest_v1.md`
- `computer_use_poc/README.md`
- `computer_use_poc/project_structure_index.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/observation_contract_v2_4_6.md`
- `computer_use_poc/field_output_classification_policy_v1.md`
- `computer_use_poc/sensitive_field_redaction_policy.md`
- `computer_use_poc/approval_policy.md`

### 3.2 Security / preflight

Include:

- `computer_use_poc/security_preflight_coverage_matrix.md`
- `computer_use_poc/security_preflight_policy.yaml`
- `computer_use_poc/security_preflight_evaluator.py`
- `computer_use_poc/security_preflight_test_cases.json`
- `computer_use_poc/security_preflight_request_contract_validator.py`
- `computer_use_poc/security_preflight_request_contract_test_cases.json`
- `computer_use_poc/security_preflight_tool_call_request_contract.md`
- `computer_use_poc/tool_contracts/user_login_log_reliable_window_contract_v1.md`
- `computer_use_poc/asset_extraction_guard_policy.md`
- `computer_use_poc/asset_extraction_guard_coverage_matrix.md`
- `computer_use_poc/release_package_asset_minimization_policy.md`
- `computer_use_poc/readonly_semi_open_release_manifest_guidance.md`

### 3.3 question_collection

Include:

- `computer_use_poc/question_collection/README.md`
- `computer_use_poc/question_collection/question_record_schema_v1.md`
- `computer_use_poc/question_collection/question_learning_policy_v1.md`
- `computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv`
- `computer_use_poc/question_collection/user_feedback_capture_v1.md`
- `computer_use_poc/question_collection/case_learning_note_template_v1.md`
- `computer_use_poc/question_collection/runtime_append_only_logging_contract_v1.md`
- `computer_use_poc/question_collection/runtime_question_record_sample_v1.jsonl`
- `computer_use_poc/question_collection/runtime_logging_smoke_test_v1.md`
- `computer_use_poc/question_collection/runtime_question_record_collector_stub_v1.py`

### 3.4 Validation / user guide / prompt matrix

Include:

- `computer_use_poc/runtime_semi_open_user_guide_v1.md`
- `computer_use_poc/runtime_semi_open_test_checklist_v1.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/runtime_semi_open_test_prompt_matrix_v1.md`

### 3.5 Runtime summaries

Include:

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/general_runtime_summary_manifest_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/anti_crawler_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/protocol_attack_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/group_control_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/activity_anti_cheating_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/traffic_anti_cheating_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/traffic_diversion_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/cracked_app_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/real_user_crowdsourcing_runtime_summary_v1.md`

### 3.6 Entity resolution / platform hand docs

Include:

- `computer_use_poc/entity_resolution_user_device_layer_v2_6_0.md`
- `computer_use_poc/entity_resolution_user_device_contract_v2_6_0.md`
- `computer_use_poc/entity_resolution_user_device_routing_rules_v2_6_0.md`
- `computer_use_poc/entity_resolution_user_device_smoke_tests_v2_6_0.md`
- `computer_use_poc/device_sdk_api_answer_contract_v2_5_3.md`
- `computer_use_poc/device_sdk_api_direct_readonly_playbook_v2_5_2.md`
- `computer_use_poc/device_sdk_api_error_semantics_v2_5_2.md`
- `computer_use_poc/device_sdk_api_observation_contract_v2_5_2.md`
- `computer_use_poc/device_sdk_api_routing_rules_v2_5_3.md`
- `computer_use_poc/device_sdk_foundation_internal_agent_playbook_v2_5_0.md`
- `computer_use_poc/device_sdk_foundation_readonly_poc_v2_5_0.md`
- `computer_use_poc/frontend_activity_profile_readonly_poc_v2_5_2.md`
- `computer_use_poc/frontend_activity_profile_internal_agent_playbook_v2_5_2.md`
- `computer_use_poc/frontend_activity_profile_observation_schema_v2_5_2.md`
- `computer_use_poc/frontend_activity_profile_test_cases_v2_5_2.md`
- `computer_use_poc/frontend_activity_profile_url_templates_v2_5_2.md`
- `computer_use_poc/frontend_activity_profile_browser_poc_v2_5_3.md`
- `computer_use_poc/archives_center_api_inventory_v2_4_7_2.md`
- `computer_use_poc/archives_center_user_profile_deep_read_v2_4_5.md`
- `computer_use_poc/archives_center_user_lookup_flow.md`
- `computer_use_poc/archives_user_analysis_api_direct_post_v2_4_7_1.md`
- `computer_use_poc/user_login_log_readonly_poc_v2_4_8.md`
- `computer_use_poc/user_login_log_readonly_poc_v2_4_8_readiness_summary.md`
- `computer_use_poc/user_login_log_api_readonly_poc_v2_4_10.md`
- `computer_use_poc/user_login_log_internal_agent_playbook_v2_4_8.md`
- `computer_use_poc/user_login_log_api_readonly_internal_agent_playbook_v2_4_10.md`
- `computer_use_poc/tianshi_strategy_hit_readonly_poc_v2_5_5.md`
- `computer_use_poc/tianshi_strategy_hit_routing_v2_5_6.md`
- `computer_use_poc/tianshi_eventlist_api_read_poc_v2_5_9.md`

### 3.7 ATO batch management

Include:

- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_case_import_rules_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_case_registry_template_v1.csv`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_case_schema_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_dry_run_sample_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_evidence_card_template_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_execution_status_tracker_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_input_contract_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_output_contract_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_pattern_summary_template_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_real_case_manual_dry_run_guide_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_real_case_pilot_checklist_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_regression_selection_rules_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_result_summary_schema_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_sampling_strategy_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_status_transition_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_strategy_direction_template_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_user_interaction_examples_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_workflow_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_case_expansion_plan_v1.md`

### 3.8 Black market account matrix batch

Include:

- `eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/black_market_account_matrix_case_schema_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/black_market_account_matrix_dry_run_sample_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/black_market_account_matrix_evidence_card_template_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/black_market_account_matrix_pattern_summary_template_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/black_market_account_matrix_real_case_manual_dry_run_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/black_market_account_matrix_registry_template_v1.csv`
- `eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/black_market_account_matrix_strategy_direction_template_v1.md`
- `computer_use_poc/run_logs/black_market_account_matrix_lightweight_closure_v1.md`

### 3.9 Selected run logs

Include:

- `computer_use_poc/run_logs/semi_open_release_readiness_review_run_v1.md`
- `computer_use_poc/run_logs/multi_entry_candidate_readiness_closure_run_v1.md`
- `computer_use_poc/run_logs/question_collection_append_only_logging_contract_run_v1.md`
- `computer_use_poc/run_logs/ato_batch_real_case_pilot_run_v1.md`
- `computer_use_poc/run_logs/ato_pos001_browser_smoke_test_run_v1.md`
- `computer_use_poc/run_logs/ato_batch_evidence_source_text_regression_run_v1.md`
- `computer_use_poc/run_logs/ato_huawei_quicklogin_20_case_final_summary_v1.md`
- `computer_use_poc/run_logs/ato_huawei_quicklogin_20_case_closure_summary_v1.md`
- `computer_use_poc/run_logs/black_market_account_matrix_lightweight_closure_v1.md`

## 4. question_collection Mapping

`computer_use_poc/question_collection/` must map to:

```text
outputs/release/dennis_risk_agent_v2_4_runtime_plus_semi_open_release/question_collection/
```

This module is:

- full-scenario user question observation.
- learning candidate queue.
- human review entry.
- `agent_observed` / `agent_suggested` / `reviewer_final` three-layer record structure.
- append-only runtime logging contract.

Boundaries:

- not ATO-only.
- no auto brain update.
- no auto release update.
- no auto DataAgent call.
- no sensitive credential recording.
- template CSV is read-only and not a runtime target.

Runtime logging target:

```text
runtime_logs/question_collection/question_records_YYYYMMDD.jsonl
```

Runtime must never overwrite:

```text
computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv
```

Release package must include:

- `question_collection/runtime_append_only_logging_contract_v1.md`
- `question_collection/runtime_question_record_sample_v1.jsonl`
- `question_collection/runtime_logging_smoke_test_v1.md`
- `question_collection/runtime_question_record_collector_stub_v1.py`

## 5. Exclusion Policy

The following must not enter the release package:

- `auth_states/`
- `.ks_sso/`
- any cookie / token / session / header / auth state plaintext
- any raw observation original dump
- any unredacted platform screenshot
- any historical `outputs/dist` package
- any full historical `run_logs/`
- any unreviewed eval pilot file
- any full source / full prompt / full skill / full case library
- any file that would imply DataAgent is a universal data substrate

UID / DID / IP may exist as internal risk entity fields, but semi-open sharing must follow audience scope and prefer `safe_ref` / partial mask / count / distribution when appropriate.

## 6. Package Scanner Result

The local package asset scanner has been run on this release directory.

Result:

- status: `warning`
- fail: `0`
- warning: `63`
- pass: `6`
- total findings: `69`

Interpretation:

- no hard-excluded path was found.
- warnings are expected because this package intentionally includes selected POC / runtime summary / run log / prompt matrix assets.
- the scanner warnings must be reviewed as selected, redacted, or summarized assets rather than full historical corpora.

## 7. Known Non-blocking TODO

- Real runtime append-only question logging wiring still needs a later integration pass.
- APP / Web actual deployment verification should be done before wider rollout.
- Additional non-ATO runtime summaries can be added in later versions if usage feedback justifies it.
