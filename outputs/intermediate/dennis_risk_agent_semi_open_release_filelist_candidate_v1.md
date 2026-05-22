# Dennis Risk Agent Semi-open Release Filelist Candidate v1

Status meanings:

- `include`: recommended for semi-open release.
- `exclude`: do not include.
- `review_needed`: include only after owner review / minimization / redaction.

## 1. Runtime Entry / README

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `README.md` | review_needed | Repo-level entry may include development context. | medium | no | yes | no | summary version preferred | low |
| `computer_use_poc/README.md` | include | Current capability and semi-open entry overview. | low | yes | yes | no | yes | low |
| `computer_use_poc/runtime_semi_open_user_guide_v1.md` | include | User-facing semi-open guide. | low | yes | yes | no | yes | low |
| `computer_use_poc/multi_entry_runtime_guard_v1.md` | include | KIM / APP / Web routing guard. | low | yes | yes | no | yes | low |

## 2. Global Routing / Capability Registry

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `computer_use_poc/scene_to_capability_routing.md` | include | Cross-scene routing and boundaries. | low | yes | yes | no | yes | low |
| `computer_use_poc/capability_registry.md` | include | Formal capability map by capability, not platform. | low | yes | yes | no | yes | low |
| `computer_use_poc/project_structure_index.md` | include | Helps users understand entry vs historical files. | low | no | yes | no | yes | low |

## 3. Response Contracts

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `computer_use_poc/answer_experience_templates.md` | include | Full-scenario response templates. | low | yes | yes | no | yes | low |
| `computer_use_poc/observation_contract_v2_4_6.md` | include | Observation and evidence source contract. | low | yes | review_needed | no | yes | low |
| `computer_use_poc/field_output_classification_policy_v1.md` | include | Field output policy for internal / semi-open / external scopes. | low | yes | yes | no | yes | low |

## 4. ATO Deep Runtime

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `skills/.../02_domain_skills/account_security_expert_skill.md` | review_needed | Full Skill source may be core asset. Prefer runtime summary or minimized copy. | high | maybe | no | yes | review | none |
| `skills/.../09_scenario_workflows/ato_account_takeover_workflows_v1.md` | review_needed | ATO workflow useful but may be too detailed. | medium | maybe | no | yes | review | none |
| `eval/.../19_ato_batch_case_management/` selected contracts | include | ATO batch input/output contracts, status, pilot checklist. | low/medium | no | yes | no | yes if redacted | none |
| `computer_use_poc/query_plans/ato_huawei_quicklogin_hive_expansion_questions_v1.md` | include | DataAgent/Hive query plan example, not execution. | low | no | yes | no | yes | none |

## 5. Anti-crawler Runtime Summary

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `skills/.../11_runtime_summaries/anti_crawler_runtime_summary_v1.md` | include | Formal anti-crawler cognition. | low | yes | yes | no | yes | high if excluded |
| `skills/.../02_domain_skills/anti_crawler_expert_skill.md` | review_needed | Full Skill source; prefer summary. | medium | no | no | yes | review | medium |

## 6. Protocol Attack Runtime Summary

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `skills/.../11_runtime_summaries/protocol_attack_runtime_summary_v1.md` | include | Formal protocol attack cognition. | low | yes | yes | no | yes | high if excluded |
| `skills/.../03_attack_skills/protocol_attack_expert_skill.md` | review_needed | Full Skill source; prefer summary. | medium | no | no | yes | review | medium |

## 7. Group Control / Device Risk Runtime Summary

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `skills/.../11_runtime_summaries/group_control_runtime_summary_v1.md` | include | Formal group control cognition. | low | yes | yes | no | yes | high if excluded |
| `computer_use_poc/device_sdk_api_answer_contract_v2_5_3.md` | include | Device risk answer contract. | low | yes | yes | no | yes | medium |
| `computer_use_poc/entity_resolution_user_device_contract_v2_6_0.md` | include | Entity relation boundary. | low | yes | yes | no | yes | medium |

## 8. Account Farm Runtime Summary

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `eval/.../20_black_market_account_matrix_batch/` selected templates | include | Account matrix / account farm batch sample. | medium | no | yes | no | include selected only | high if excluded |
| `computer_use_poc/run_logs/black_market_account_matrix_lightweight_closure_v1.md` | include | Paused branch boundary. | low | yes | yes | no | yes | low |

## 9. Activity Anti-cheating Runtime Summary

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `skills/.../11_runtime_summaries/activity_anti_cheating_runtime_summary_v1.md` | include | Formal activity anti-cheating cognition. | low | yes | yes | no | yes | high if excluded |

## 10. Traffic Anti-cheating Runtime Summary

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `skills/.../11_runtime_summaries/traffic_anti_cheating_runtime_summary_v1.md` | include | Formal traffic anti-cheating cognition. | low | yes | yes | no | yes | high if excluded |

## 11. Traffic Diversion Runtime Summary

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `skills/.../11_runtime_summaries/traffic_diversion_runtime_summary_v1.md` | include | Formal diversion / interception cognition. | low | yes | yes | no | yes | high if excluded |

## 12. Cracked App / Plugin Risk Runtime Summary

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `skills/.../11_runtime_summaries/cracked_app_runtime_summary_v1.md` | include | Cracked app cognition. | low | yes | yes | no | yes | high if excluded |
| `skills/.../03_attack_skills/plugin_reverse_analysis_skill.md` | review_needed | Plugin full Skill source; prefer minimized summary. | medium | no | no | yes | review | medium |

## 13. Evidence Card / Evidence Planning

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `computer_use_poc/plan_mode_capability_v1.md` | include | Plan mode and evidence card planning. | low | yes | yes | no | yes | low |
| `computer_use_poc/run_logs/single_case_evidence_source_text_regression_run_v1.md` | include selected summary | Evidence source regression. | low | no | yes | no | selected only | low |

## 14. Strategy Recommendation / Generalization

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `skills/.../01_core_skills/risk_governance_design_skill.md` | review_needed | Full Skill source; prefer runtime summary. | medium | maybe | no | yes | review | medium |
| `eval/.../batch_analysis_framework_v1.md` | include | Cross-scenario batch framework. | low | no | yes | no | yes | medium |

## 15. DataAgent Boundary

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `computer_use_poc/runtime_semi_open_test_checklist_v1.md` | include | Runtime boundary and DataAgent non-default. | low | yes | yes | no | yes | low |
| `outputs/release/*/dataagent_*` | review_needed | Existing DataAgent docs may imply broader execution. | medium | no | no | yes | review/minimize | low |

## 16. Safety / Asset Extraction Guard

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `computer_use_poc/asset_extraction_guard_policy.md` | include | Protects source/prompt/case assets. | low | yes | yes | no | yes | low |
| `computer_use_poc/release_package_asset_minimization_policy.md` | include | Package slimming guidance. | low | no | yes | no | yes | low |
| `computer_use_poc/package_asset_scanner.py` | include | Local package scanner. | low | no | internal | yes | yes | low |
| `computer_use_poc/asset_extraction_guard_regression_cases.md` | review_needed | Full regression corpus may be too much. | medium | no | no | yes | selected summary preferred | low |

## 17. question_collection

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `computer_use_poc/question_collection/README.md` | include | Module entry. | low | yes | yes | no | yes | high if excluded |
| `computer_use_poc/question_collection/question_record_schema_v1.md` | include | Three-layer record schema. | low | yes | yes | no | yes | high if excluded |
| `computer_use_poc/question_collection/question_learning_policy_v1.md` | include | Candidate queue and reviewer gate. | low | yes | yes | no | yes | high if excluded |
| `computer_use_poc/question_collection/user_feedback_capture_v1.md` | include | Feedback capture contract. | low | yes | yes | no | yes | medium |
| `computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv` | include | Safe sample queue. | low | no | yes | no | yes | medium |
| `computer_use_poc/question_collection/question_collection_text_regression_cases_v1.yaml` | review_needed | Regression corpus; include compact or selected version. | medium | no | no | yes | review | medium |

## 18. Semi-open Test Prompts

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `outputs/intermediate/dennis_risk_agent_semi_open_test_prompt_matrix_v1.md` | include | Full-scenario prompt matrix. | low | no | yes | no | yes | low |

## 19. Validation Cases

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `computer_use_poc/runtime_validation_cases_v1.yaml` | include | Semi-open runtime validation cases. | low | yes | internal | yes | yes | low |
| `computer_use_poc/smoke_tests.md` | include summary | Full smoke file is large; include or summarize depending package size. | low/medium | no | internal | yes | review | low |

## 20. User Guide / Manifest

| path | status | reason | sensitive risk | runtime required | user visible | internal only | semi-open fit | non-ATO gap risk |
|---|---|---|---|---|---|---|---|---|
| `computer_use_poc/runtime_semi_open_user_guide_v1.md` | include | User-facing guide. | low | yes | yes | no | yes | low |
| `outputs/intermediate/*manifest_patch_plan_v1.md` | include in build docs | Patch plan, not runtime. | low | no | internal | yes | yes | low |

## 21. Explicit Exclusions

See `outputs/intermediate/dennis_risk_agent_semi_open_release_exclusion_list_v1.md`.
