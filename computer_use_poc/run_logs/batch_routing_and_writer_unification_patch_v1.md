# Batch Routing And Writer Unification Patch v1

## Live validation findings

Semi-open live validation result was PARTIAL:

- evidence type separation: PASS
- strategy recommendation plan mode: PASS
- context contamination guard: PASS
- main agent direct exec: PASS
- batch clustering: FAIL
- observation writer: PARTIAL

## Batch routing issue

The 10-user batch clustering case still attempted per-user platform lookup and timed out. Existing batch risk clustering templates were present, but the live routing guard was not hard enough before execution-mode selection.

## Batch routing fix

- Added a hard batch routing guard to `multi_entry_runtime_guard_v1.md`.
- Reinforced `scene_to_capability_routing.md`, `answer_experience_templates.md`, `capability_registry.md`, and batch clustering runtime docs.
- 10+ detected entities now force `batch_clustering_mode` / plan mode by default.
- 10-49 entities use `batch_clustering_mode`.
- 50+ entities use aggregation / DataAgent-Hive query plan.
- Per-entity online execution for 10+ requires explicit user wording and scope/cost confirmation.
- Strategy recommendation, expansion, grey release, false-positive control, and monitoring remain plan mode even with ids attached.

## Writer issue

Live validation found two writer inconsistencies:

- observation and candidate outputs could split across workspace root and `dennis-risk-agent` subdirectory depending on CWD;
- observation records had inconsistent expectations between markdown and JSON-lines style logs.

## Writer fix

- Observation log and candidate queue now share stable path resolution:
  1. explicit `--log-dir` / `--candidate-queue`
  2. `DENNIS_AGENT_HOME`
  3. repo root from script path
  4. CWD fallback only if repo-root detection fails
- Observation writer output is markdown block only, with a JSON metadata block.
- Metadata includes `direct_tool_bypass`, `bypass_reason`, `risk_review_required`, `feedback_type`, `candidate_appended`, `candidate_queue_path`, `path_resolution`, `subagent_session_id`, and `main_session_id`.
- Sensitive content remains redacted.

## Modified files

- `AGENTS.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/runtime_integration_validation_checklist_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_threshold_policy_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_response_template_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_runtime_prompt_examples_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_runtime_validation_cases_v1.yaml`
- `computer_use_poc/question_collection/pilot_observation_writer.py`
- `computer_use_poc/question_collection/README.md`
- `computer_use_poc/question_collection/runtime_append_only_logging_contract_v1.md`
- `computer_use_poc/question_collection/question_record_schema_v1.md`
- `computer_use_poc/smoke_tests.md`

## Local validation summary

- Python compile for `pilot_observation_writer.py`: pass after rerun with permission to write Python cache.
- YAML parse for `runtime_validation_cases_v1.yaml` and `batch_risk_runtime_validation_cases_v1.yaml`: pass.
- Writer self-test with `DENNIS_AGENT_HOME` from repo root: pass.
- Writer self-test with `DENNIS_AGENT_HOME` from workspace parent CWD: pass; same log and candidate queue paths.
- Writer self-test with explicit `--log-dir` and `--candidate-queue`: pass.
- Keyword grep for `BATCH-ROUTING-GUARD-010`, `BATCH-ROUTING-GUARD-050`, and writer metadata fields: pass.
- Sensitive scan over `/tmp` test outputs: no raw credential value or phone-like string found; expected `main_session_id` / `subagent_session_id` field names are present for audit metadata.
- `git diff --check`: pass.

## Still needs internal Agent live validation

- KIM/webchat must replay the 10-user batch case and verify no platform API call is attempted.
- 50+ entity prompt must route to aggregation / DataAgent-Hive query plan without online lookup.
- Live Agent should set `DENNIS_AGENT_HOME` and verify observation markdown plus candidate queue land under that home.
- Confirm live writer records include `main_session_id` and `subagent_session_id` when the caller can provide them.

## Boundaries

- Did not access real platform.
- Did not call DataAgent.
- Did not modify auth or gateway.
- Did not execute real business query.
- Did not repackage release.
- Did not upload cloud artifacts.
- Did not commit git.
- Did not modify live workspace.
