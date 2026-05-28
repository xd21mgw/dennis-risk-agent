# Failure Triage Card Template v1

Use this template when a Dennis Risk Agent case fails, times out, routes incorrectly, or produces weak output. The goal is to classify the failure layer instead of guessing from the final symptom.

```yaml
Failure Triage Card:
  case_id:
  entrance: KIM | Web | manual_spawn
  executor_agent: main | dennis-risk-agent
  main_direct_tool_bypass: true | false

  config_runtime:
    runner_exists:
    safeBin_callable:
    real_platform_request_executed:
    auth_permission_status:
    overlay_files_present:
    tools_agents_loaded_correctly:

  intent_routing:
    expected_routing_mode:
    actual_routing_mode:
    expected_execution_mode:
    actual_execution_mode:
    plan_mode_misfire:
    execution_misfire:

  source_orchestration:
    expected_sources:
    actual_sources:
    completed_sources:
    no_data_sources:
    blocked_sources:
    timeout_sources:
    skipped_sources:
    checkpoint_present:
    partial_evidence_output:

  evidence_reasoning:
    no_data_misused:
    strategy_hit_misused:
    strong_medium_weak_separated:
    source_window_boundary_explained:
    conclusion_recomputed_after_new_evidence:

  output_contract:
    evidence_card_present:
    source_quality_present:
    routing_metadata_present:
    missing_evidence_present:
    caveats_present:
    next_action_present:

  final_attribution:
    primary_failure_layer: config/runtime | intent/routing | source_orchestration | evidence_reasoning | output_contract | no_issue
    secondary_failure_layer:
    confidence:
    fix_owner: Codex | Internal Agent | Main Agent | No Fix
    next_fix:
    suggested_regression_case:
```

Rules:

- If plan-only is good but execution fails, first check `config/runtime`, `runner/safeBin/auth`, and `source_orchestration`.
- If execution succeeds but the conclusion is wrong, first check `evidence_reasoning` and `output_contract`.
- If platform was not called, `reason_not_executed` must be explicit in routing metadata.
- `no_data`, `blocked`, `timeout`, and `auth_failed` are never low-risk proof.
- Strategy hit is a signal and cross-validation direction, not a final judgement.
