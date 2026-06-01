# run_logs Index

Status: `historical_only`. Files in this directory are run history, patch logs,
validation summaries, and replay evidence. They are not runtime mainline rules.

Do not move or delete existing run logs in this indexing round.

## Theme Groups

| theme | representative files | runtime role |
|---|---|---|
| browser-backed / passthrough | `browser_backed_service_adapter_dry_run_v1.md`, `browser_backed_service_executable_adapter_dry_run_v1.md`, `browser_backed_passthrough_dual_run_track_login_v1.md`, `browser_backed_passthrough_four_source_dual_run_v1.md`, `dennis_passthrough_default_path_migration_v1.md`, `dennis_passthrough_default_path_controlled_smoke_v1.md`, `dennis_passthrough_cleanup_dependency_scan_v1.md` | historical_only / regression_source |
| ATO / account security | `ato_suspicious_anchor_discovery_badcase_2892617234_patch_v1.md`, `ato_login_log_window_false_negative_badcase_v2_6.md`, `ato_single_case_source_checkpoint_patch_v1.md`, `ato_source_priority_access_method_correction_v1.md`, `batch_ato_cluster_lens_alignment_v1.md`, `ato_huawei_quicklogin_*` | historical_only / regression_source |
| Archives / platform access | `archives_center_*`, `archives_user_analysis_api_direct_post_run_001_validated.md`, `source_readiness_and_archives_profile_recovery_v1.md` | historical_only |
| Tianshi / RCP / policy attribution | `tianshi_*`, `rcp_eventlist_har_body_contract_patch_v0_1.md` | historical_only / regression_source |
| DataAgent / Hive | `dataagent_*`, `account_security_hive_*`, `dataagent_hive_registry_preflight_patch_v1.md` | historical_only; execution still requires explicit authorization |
| release / preflight / asset scanner | `release_overlay_readiness_gate_v1.md`, `semi_open_release_package_run_v1.md`, `package_asset_scanner_baseline_run_v1.md`, `asset_extraction_*`, `security_preflight_*` | historical_only / release support evidence |
| raw reference / redaction | `raw_reference_redaction_layering_contract_v1.md`, `full_runtime_redaction_case_smoke_v1.md`, `bc_field_semantic_001_badcase_regression_run_v1.md` | historical_only / regression_source |
| runtime preview / overlay / consolidation | `runtime_config_apply_canonical_baseline_patch_v1.md`, `full_runtime_cleanup_and_consolidation_v1.md`, `runtime_preview_no_dependency_chasing_patch_v1.md`, `safe_delta_overlay_packaging_v1.md`, `platform_access_execution_overlay_packaging_*` | historical_only |
| batch risk clustering | `batch_risk_clustering_*`, `batch_l1_drilldown_layer_patch_v1.md`, `batch_risk_golden_answers_v1.md`, `abnormal_correlation_matrix_deepening_v1.md` | historical_only / regression_source |
| safety / guardrails / routing | `source_execution_guard_patch_v1.md`, `no_live_auth_repair_in_business_case_guard_v1.md`, `routing_metadata_*`, `context_boundary_guard_generalization_patch_v1.md`, `agent_safety_*` | historical_only / guardrail evidence |

## Usage Boundary

- Use run logs to understand why a rule or regression was added.
- Do not treat a run log as current runtime behavior if it conflicts with
  active files in `AGENTS.md`, `TOOLS.md`, `computer_use_poc/*.md`, validation
  cases, or runtime summaries.
- If a run log is used to justify a new rule, port the rule into the active
  runtime, orchestration, capability, answer, or validation file first.

## Future Migration Check

Before moving run logs:

- Check whether any docs or validation cases reference the exact file name.
- Keep old logs marked `historical_only`.
- Mark logs that feed regressions as `regression_source`.
- Do not move logs together with runtime source files in the same commit.
