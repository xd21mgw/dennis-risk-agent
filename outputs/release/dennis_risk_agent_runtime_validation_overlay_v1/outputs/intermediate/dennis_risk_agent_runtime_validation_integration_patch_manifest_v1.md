# Dennis Risk Agent Runtime Validation Integration Patch Manifest v1

## Patch identity

- patch_name: `dennis_risk_agent_runtime_validation_integration_patch_v1`
- version: `v1`
- status: `runtime_integration_patch_candidate`
- package_scope: local manifest and validation checklist only
- release_directory_generated: false
- dist_generated: false

## Goal

This patch records the runtime validation and integration surface for the recent Dennis Risk Agent semi-open fixes. It does not create a new reasoning brain. It organizes which local assets should be overlaid into a live runtime, which files are validation-only, which files must never enter release, and which preflight gate must pass before any future package or upload.

The patch covers:

1. semi-open experience patch v1
2. user feedback capture and append-only learning loop
3. evidence quality, browser-loop downgrade, and context contamination guards
4. account-security bad case regression
5. batch risk clustering analysis pack
6. asset extraction and release preflight gate

## Included modules

### 1. Semi-open experience patch v1

Runtime behaviors included:

- `explicit_query_not_empty_analysis`
- `single_entity_execution_mode`
- `evidence_boundary_mode`
- `strategy_recommendation_plan_mode`
- `batch_plan_mode`
- `non_ato_expert_mode`
- timeout fallback with partial evidence card
- browser / 2FA / HTML / auth fallback
- API / SSO / JSON parse fallback
- answer length control
- device SDK three-layer interpretation
- Q1-Q20 regression baseline
- KIM-R1 to KIM-R10 regression baseline
- `SEMI-OPEN-EXP-*` smoke tests

Primary files:

- `computer_use_poc/runtime_semi_open_user_guide_v1.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

### 2. User feedback loop

Included behavior:

- `feedback_record` capture support
- high-value feedback can append to candidate queue
- `useful` feedback does not enter candidate queue by default
- sensitive information must be redacted before durable logging
- append-only logging contract
- feedback loop self-test instructions

Primary files:

- `computer_use_poc/question_collection/README.md`
- `computer_use_poc/question_collection/pilot_observation_writer.py`
- `computer_use_poc/question_collection/question_record_schema_v1.md`
- `computer_use_poc/question_collection/user_feedback_capture_v1.md`
- `computer_use_poc/question_collection/question_learning_policy_v1.md`
- `computer_use_poc/question_collection/runtime_append_only_logging_contract_v1.md`
- `computer_use_poc/question_collection/runtime_logging_smoke_test_v1.md`
- `computer_use_poc/question_collection/question_collection_text_regression_cases_v1.yaml`

Runtime path rule:

- Template queue must not be polluted by real runtime output: `computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv` is a template/sample asset only.
- Live runtime candidate queue output path: `runtime_logs/question_collection/question_learning_candidate_queue_v1.csv`.
- Live runtime still needs the main agent to call `pilot_observation_writer.py` after the real KIM follow-up and pass `linked_previous_record_id`.

### 3. Evidence quality / browser loop / context contamination patch

Included behavior:

- evidence type separation
- `raw_evidence` / `behavior_event` / `user_claim` / `inference` / `hypothesis` / `missing_evidence`
- single case evidence card required template
- partial evidence card on blocked / timeout / browser loop
- track-analysis stats-first playbook
- track-analysis SPA loop downgrade after 3 failed attempts
- `4972532542` device mismatch / browser loop bad case
- `BC-FIELD-SEMANTIC-001`
- `GC-PROTOCOL-DOWNGRADE-001`
- `CONTEXT-CONTAMINATION-CROSS-TASK-001`

Required regression IDs:

- `EVIDENCE-TYPE-SEPARATION-001`
- `SINGLE-CASE-EVIDENCE-CARD-001`
- `TRACK-ANALYSIS-STATS-FIRST-001`
- `TRACK-SPA-LOOP-001`
- `DEVICE-MISMATCH-ATO-001`
- `USER-CLAIM-WEAK-EVIDENCE-001`
- `PARTIAL-EVIDENCE-BROWSER-BLOCKED-001`
- `BC-FIELD-SEMANTIC-001`
- `GC-PROTOCOL-DOWNGRADE-001`
- `CONTEXT-CONTAMINATION-CROSS-TASK-001`

### 4. Account-security bad case

Included behavior:

- `BC-HARMONY-ATO-001`
- Harmony one-click login / third-party authorization takeover ATO must be separated from credential-stuffing ATO.
- Batch ATO must sample 3-5 representative users and write per-user timeline before strong pattern attribution.
- Do not conclude credential stuffing only from `kick_out` + password failure + CAPTCHA.

### 5. Batch risk clustering analysis pack

Included behavior:

- Multi-case to cluster to representative sample to abnormal correlation matrix to attack path hypothesis to follow-up plan to strategy recommendation.
- 3+ users / multi-entity requests default to plan mode or batch mode, not one-by-one online execution.
- `batch_clustering_mode` for 10-49 entities.
- 50+ entities require aggregation or DataAgent/Hive query plan; DataAgent remains only a Hive/company data warehouse analysis path, not a universal data substrate.
- Abnormal correlation matrix must include `relation_family`, `evidence_basis`, `denominator_status`, `relationship_strength`, `reverse_check_result`, `confounder_risk`, and `cannot_conclude_boundary`.
- Do not turn shallow A -> B correlation into a strong conclusion.
- Distinguish current batch evidence, hypothesis, missing join key, and required validation.
- Output pattern summary, cluster explanation, representative cases, candidate strategy direction, and required validation.

Primary runtime files:

- `computer_use_poc/batch_risk_clustering/README.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_case_schema_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_threshold_policy_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_clustering_methodology_v1.md`
- `computer_use_poc/batch_risk_clustering/abnormal_correlation_matrix_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_representative_sampling_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_evidence_card_template_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_pattern_summary_template_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_response_template_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_runtime_validation_cases_v1.yaml`

Validation-only files for this module:

- `computer_use_poc/batch_risk_clustering/batch_risk_runtime_prompt_examples_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_golden_samples_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_golden_answers_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_quality_rubric_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_text_dry_run_v1.md`
- `computer_use_poc/run_logs/batch_risk_clustering_pack_v1.md`
- `computer_use_poc/run_logs/batch_risk_clustering_text_dry_run_v1.md`
- `computer_use_poc/run_logs/abnormal_correlation_matrix_deepening_v1.md`
- `computer_use_poc/run_logs/batch_risk_clustering_runtime_routing_dry_run_v1.md`
- `computer_use_poc/run_logs/batch_risk_golden_answers_v1.md`

Batch runtime validation checklist:

1. 10 users look like one ATO batch -> `batch_clustering_mode`, no one-by-one online checks.
2. Mixed positive/negative cases -> layered judgement, not one forced risk class.
3. Multi-device / multi-IP / multi-version / nickname mutation -> abnormal correlation matrix.
4. Missing denominator or sample bias -> fill `denominator_status`.
5. Correlation without join key -> fill `cannot_conclude_boundary`.
6. Strategy recommendation / expansion investigation -> plan mode, no platform call.
7. Batch over 3 entities -> default no one-by-one online execution unless user confirms cost and scope.

### 6. Asset extraction / release preflight gate

Included behavior:

- Asset extraction policy and regression cases.
- Package scanner rules.
- Release preflight wrapper that calls scanner, fails closed, and prints safe summary only.
- Risky and safe mock fixtures.
- `ASSET-PREFLIGHT-001` to `ASSET-PREFLIGHT-005` smoke tests.

Primary files:

- `computer_use_poc/asset_extraction_policy_v1.md`
- `computer_use_poc/asset_extraction_regression_cases_v1.md`
- `computer_use_poc/package_asset_scanner.py`
- `computer_use_poc/package_asset_scanner_rules.json`
- `computer_use_poc/release_preflight_check.py`
- `computer_use_poc/release_security_checklist_v1.md`
- `computer_use_poc/test_fixtures/package_asset_scanner_risky_mock/`
- `computer_use_poc/test_fixtures/package_asset_scanner_safe_mock/`

Mandatory preflight command before any future package or upload:

```bash
python3 computer_use_poc/release_preflight_check.py outputs/release/<release_name>
```

Preflight failure blocks package/upload when any condition is true:

- `preflight_pass=false`
- `package_should_block=true`
- scanner execution fails
- scanner emits no JSON
- scanner JSON parse fails
- any `critical` finding exists
- any unallowed `high` finding exists

## Must overlay to live

These files are candidates for live runtime overlay after internal review:

- `computer_use_poc/runtime_semi_open_user_guide_v1.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/field_output_classification_policy_v1.md`
- `computer_use_poc/observation_contract_v2_4_6.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/runtime_integration_validation_checklist_v1.md`
- `computer_use_poc/question_collection/README.md`
- `computer_use_poc/question_collection/pilot_observation_writer.py`
- `computer_use_poc/question_collection/question_record_schema_v1.md`
- `computer_use_poc/question_collection/user_feedback_capture_v1.md`
- `computer_use_poc/question_collection/question_learning_policy_v1.md`
- `computer_use_poc/question_collection/runtime_append_only_logging_contract_v1.md`
- `computer_use_poc/batch_risk_clustering/README.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_case_schema_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_threshold_policy_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_clustering_methodology_v1.md`
- `computer_use_poc/batch_risk_clustering/abnormal_correlation_matrix_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_representative_sampling_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_evidence_card_template_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_pattern_summary_template_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_response_template_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_runtime_validation_cases_v1.yaml`
- `computer_use_poc/asset_extraction_policy_v1.md`
- `computer_use_poc/package_asset_scanner.py`
- `computer_use_poc/package_asset_scanner_rules.json`
- `computer_use_poc/release_preflight_check.py`
- `computer_use_poc/release_security_checklist_v1.md`

## Local test only, do not include in release by default

- `computer_use_poc/test_fixtures/**`
- `computer_use_poc/run_logs/**`, except explicitly distilled release closure summaries approved by scanner policy
- `computer_use_poc/question_collection/runtime_question_record_sample_v1.jsonl`
- `computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv`
- `computer_use_poc/question_collection/question_collection_text_regression_cases_v1.yaml`
- `computer_use_poc/question_collection/question_collection_text_regression_run_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_runtime_prompt_examples_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_golden_samples_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_golden_answers_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_quality_rubric_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_text_dry_run_v1.md`
- `computer_use_poc/asset_extraction_regression_cases_v1.md`
- `outputs/intermediate/**`
- `outputs/dist/**`

## Forbidden in release

Never include:

- cookie, token, session, header, API key, password, secret, credential files or fields
- `.ks_sso`, `sso-state`, `auth-state`
- browser cookies or browser `localStorage`
- complete system instruction source, agent instruction source, or tool instruction source
- complete domain skill source when it is not a runtime-required summary layer
- complete historical `run_logs/`
- real raw case data
- raw internal platform JSON responses
- user phone numbers or other high-sensitive personal information
- unredacted screenshots
- `outputs/dist` temporary packages
- `outputs/release/.DS_Store`
- full mother-body source directories copied into release

## Live overlay steps

1. Create a staging live workspace snapshot and record current file versions.
2. Copy only the `Must overlay to live` files into the staging runtime.
3. Do not copy local test fixtures, golden samples, raw run logs, template queues, or intermediate patch files unless a release owner explicitly approves a distilled summary.
4. Run local syntax checks and YAML/JSON checks.
5. Run `python3 computer_use_poc/release_preflight_check.py outputs/release/<release_name>` before packaging or upload.
6. If preflight fails, stop. Delete or replace the matched file, then rerun preflight.
7. Run `computer_use_poc/runtime_integration_validation_checklist_v1.md` against KIM/webchat/live routing.
8. Only after the checklist passes should the release owner create a dist package.

## Rollback

- Keep a pre-overlay copy of every overlaid file.
- Roll back by restoring only the overlaid runtime files from the snapshot.
- Do not roll back or mutate auth state, SSO state, browser cookies, candidate queues, or runtime append-only logs.
- If feedback writer integration misbehaves, disable the live caller hook first; keep append-only logs immutable and investigate with safe summaries.

## Current non-goals

- No real platform access.
- No DataAgent call.
- No auth/gateway change.
- No real business query.
- No cloud upload.
- No git commit.
- No release dist package.
- No new full domain skill source release.
- No raw sensitive run log or raw sample inclusion.

