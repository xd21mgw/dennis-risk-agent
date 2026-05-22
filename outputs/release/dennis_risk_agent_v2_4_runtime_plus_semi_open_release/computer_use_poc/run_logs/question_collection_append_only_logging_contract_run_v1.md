# Question Collection Append-only Logging Contract Run v1

## 1. Target

Add a local append-only logging contract for semi-open runtime question collection.

## 2. Added Files

- `computer_use_poc/question_collection/runtime_append_only_logging_contract_v1.md`
- `computer_use_poc/question_collection/runtime_question_record_sample_v1.jsonl`
- `computer_use_poc/question_collection/runtime_logging_smoke_test_v1.md`
- `computer_use_poc/question_collection/runtime_question_record_collector_stub_v1.py`

## 3. Modified Files

- `computer_use_poc/question_collection/README.md`
- `computer_use_poc/question_collection/question_learning_policy_v1.md`
- `computer_use_poc/README.md`
- `computer_use_poc/smoke_tests.md`
- `outputs/intermediate/dennis_risk_agent_semi_open_release_manifest_patch_plan_v1.md`
- `outputs/intermediate/dennis_risk_agent_semi_open_release_readiness_review_v1.md`

## 4. Contract Summary

- Template CSV is read-only sample material.
- Real runtime records must be appended to `runtime_logs/question_collection/question_records_YYYYMMDD.jsonl`.
- Runtime logging is append-only.
- Runtime must not overwrite `question_learning_candidate_queue_v1.csv`.
- Each JSONL line follows the three-layer question record model: `agent_observed`, `agent_suggested`, `reviewer_final`.
- `reviewer_final.reviewer_decision` defaults to `pending`.
- Runtime must not write `accepted` decisions.
- Sensitive fields are filtered before writing.

## 5. Boundaries

This run:

- Did not access real platform.
- Did not call DataAgent.
- Did not integrate with real runtime.
- Did not update release/dist.
- Did not modify core Skill.
- Did not read or print cookie/token/session/header/auth state.

## 6. Current State

Current repository still has no real runtime write integration. The added stub is local-only and intended for append-only behavior validation.

## 7. Follow-up TODO

- Wire real semi-open runtime to this contract.
- Ensure runtime logs are excluded from release packages by default.
- Add offline reviewed queue generation after human review.
- Run package scanner before any release package includes question_collection.
