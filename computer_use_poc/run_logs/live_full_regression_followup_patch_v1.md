# Live Full Regression Follow-up Patch v1

## Scope

This patch records the lightweight local fixes after the full semi-open self-test returned `PARTIAL`.

The patch only updates local rules, templates, schema notes, writer guardrails, regression cases, and smoke tests.

## Boundaries

- Real platform access: no.
- DataAgent call: no.
- Auth / gateway change: no.
- Real query execution: no.
- Release package rebuild: no.
- Live workspace overlay: no.
- Git commit / push: no.

## Issues Addressed

### 1. ATO single-case execution timeout fallback

Finding:

- `user_id=290534602` ATO single-case path correctly routed through dennis-risk-agent.
- The internal route attempted readonly Weapon observation and then timed out.
- The issue is not the route; explicit single-user ATO should remain `single_entity_execution_mode`.
- The issue is missing partial evidence fallback after platform timeout / auth blocked / parse error.

Patch:

- ATO single case with explicit `user_id` stays in `single_entity_execution_mode`.
- Readonly login log / Weapon / archives / strategy-hit observation remains allowed.
- Any source timeout / auth blocked / parse error must return a partial evidence card.
- Required fallback fields:
  - `completed_sources`
  - `blocked_sources`
  - `timeout_sources`
  - `parse_error_sources`
  - `missing_evidence`
  - `source_quality`
  - `next_action`
- `no_data`, `timeout`, `blocked`, and `auth_failed` are not counter evidence.
- If all sources fail, output query plan + missing evidence instead of bare timeout.
- Conclusion status must use:
  - `data_supports_ato_suspicion`
  - `insufficient_support`
  - `data_against_ato_suspicion`

Regression added:

- `SINGLE-ATO-EXECUTION-PARTIAL-FALLBACK-001`

### 2. routing_metadata standard YAML schema

Finding:

- Several paths returned useful metadata but used JSON or custom names instead of the standard schema.
- Route / capability names must remain registered names from routing and capability registry docs.

Patch:

- `routing_metadata` must be a YAML block, not JSON.
- Standard fields now include:
  - `route`
  - `capability`
  - `sub_capability`
  - `intent_type`
  - `execution_mode`
  - `evidence_mode`
  - `query_plan_only`
  - `platform_called`
  - `platform_call_summary`
  - `dataagent_called`
  - `direct_tool_bypass`
  - `sensitive_output`
  - `redaction_applied`
  - `boundary_flags`
  - `source_quality`
  - `missing_required_fields`
  - `partial_reason`
  - `final_status`
- `execution_mode` standard enum:
  - `plan_mode`
  - `execution_mode`
  - `single_entity_execution_mode`
  - `batch_clustering_mode`
  - `expert_mode`
  - `denied`
- `evidence_mode` standard enum:
  - `evidence_card`
  - `expert_reasoning`
  - `batch_pattern_summary`
  - `strategy_recommendation`
  - `partial_evidence`

### 3. Candidate queue canonical path

Finding:

- Runtime logs and question collection paths were observed in multiple locations.
- The template CSV must remain a static template, not a runtime write target.

Patch:

- Canonical runtime candidate queue:
  - `$DENNIS_AGENT_HOME/runtime_logs/question_collection/question_learning_candidate_queue_v1.csv`
- If `DENNIS_AGENT_HOME` is absent, writer resolves the `dennis-risk-agent` repo root from `pilot_observation_writer.py` and writes:
  - `<repo-root>/runtime_logs/question_collection/question_learning_candidate_queue_v1.csv`
- Only if repo-root detection fails may it fall back to CWD.
- Writer output includes:
  - `candidate_queue_path`
  - `path_resolution`
  - `log_path_resolution`
  - `candidate_queue_path_resolution`
- Explicit `--candidate-queue` remains available for local tests, but fails closed if it points to:
  - `computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv`
  - `outputs/release/<release_name>/question_collection/question_learning_candidate_queue_v1.csv`

## Modified Assets

- `AGENTS.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/runtime_integration_validation_checklist_v1.md`
- `computer_use_poc/question_collection/pilot_observation_writer.py`
- `computer_use_poc/question_collection/README.md`
- `computer_use_poc/question_collection/runtime_append_only_logging_contract_v1.md`
- `computer_use_poc/question_collection/question_record_schema_v1.md`
- `computer_use_poc/README.md`
- `computer_use_poc/smoke_tests.md`

## Validation Plan

- `python3 -m py_compile computer_use_poc/question_collection/pilot_observation_writer.py`
- YAML parse for `computer_use_poc/runtime_validation_cases_v1.yaml`
- Writer self-test with `DENNIS_AGENT_HOME` pointing to a temp directory.
- Writer fail-closed check for source-tree template candidate queue target.
- `git diff --check`

## Remaining Work

- Runtime overlay / packaging can be done after diff review.
- Cloud runtime should rerun the affected paths after overlay:
  - ATO single case partial fallback.
  - metadata YAML schema across all key paths.
  - feedback candidate queue canonical path.
