# Runtime Logging Smoke Test v1

## 1. Purpose

Validate that question_collection runtime logging uses append-only JSONL records and never overwrites template CSV assets.

This smoke test is documentation-only unless explicitly run with the local stub. It does not access real platforms or DataAgent.

## 2. Test Cases

| test_id | input | expected_behavior | pass_criteria |
|---|---|---|---|
| QLOG-001 | Runtime receives a valid question_record | append JSON object to `runtime_logs/question_collection/question_records_YYYYMMDD.jsonl` | Existing file contents remain; one new line appended. |
| QLOG-002 | Runtime receives multiple question_records | append each as one JSONL line | Earlier records remain parseable and unchanged. |
| QLOG-003 | Template CSV exists | do not write template CSV | `question_learning_candidate_queue_v1.csv` remains unchanged. |
| QLOG-004 | Record lacks `reviewer_final.reviewer_decision` | default to `pending` | Written record has `reviewer_decision=pending`. |
| QLOG-005 | Record has `reviewer_decision=accepted` | reject write | Runtime must not auto-accept learning. |
| QLOG-006 | Record includes credential-like keys | redact or reject sensitive fields | No cookie/token/session/header/auth-state/phone/mobile/id_card plaintext appears in log. |
| QLOG-007 | Logging directory missing | create `runtime_logs/question_collection/` | Directory is created without touching release or template files. |
| QLOG-008 | Logging write fails | do not block main answer | Return `logging_failed`; do not print sensitive raw content. |
| QLOG-009 | Dry run requested | do not write file | Print sanitized record only. |
| QLOG-010 | JSONL line parse check | parse each line independently | Every line is valid JSON object. |

## 3. Non-goals

- No real Agent runtime integration.
- No real platform access.
- No DataAgent call.
- No release/dist update.
- No Skill / Prompt / runtime summary modification.

## 4. Required Runtime Boundary

```text
template_csv: read_only_sample
runtime_log_target: runtime_logs/question_collection/question_records_YYYYMMDD.jsonl
write_mode: append_only
reviewer_decision_default: pending
auto_accepted: prohibited
```
