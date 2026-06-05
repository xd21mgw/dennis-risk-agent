# Runtime Append-only Logging Contract v1

## 1. Positioning

This contract defines how semi-open runtime should record real user questions for `question_collection`.

It is an accounting and candidate-learning log contract. It is not an automatic learning system and does not modify Dennis Agent brain.

## 2. Current State

`computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv` is a static template and demo queue.

It is not a runtime write target.

Runtime must never overwrite this template CSV.

## 3. Correct Runtime Target

Runtime user question records must be written to:

```text
runtime_logs/question_collection/question_records_YYYYMMDD.jsonl
```

Semi-open pilot observation / feedback markdown logs may be appended to:

```text
semi_open_pilot_logs/YYYY-MM-DD.md
```

High-value feedback candidates may be appended to:

```text
$DENNIS_AGENT_HOME/runtime_logs/question_collection/question_learning_candidate_queue_v1.csv
```

If `DENNIS_AGENT_HOME` is absent, the local writer must resolve the `dennis-risk-agent` repo root from `pilot_observation_writer.py` and append to:

```text
<dennis-risk-agent-repo-root>/runtime_logs/question_collection/question_learning_candidate_queue_v1.csv
```

This runtime CSV is separate from the source-tree template CSV.

Observation log and candidate queue path resolution must be stable:

1. `pilot_observation_writer.py --log-dir <path>` and `--candidate-queue <path>` use explicit paths for local tests only; `--candidate-queue` must not point to the source-tree template CSV or release package template CSV.
2. `DENNIS_AGENT_HOME` uses `DENNIS_AGENT_HOME/semi_open_pilot_logs/YYYY-MM-DD.md` and `DENNIS_AGENT_HOME/runtime_logs/question_collection/question_learning_candidate_queue_v1.csv`.
3. If the env var is absent, the writer resolves the repo root from the script path.
4. Only if repo-root detection fails, the writer may use CWD and must report `path_resolution=fallback_cwd`.

Writer output must include `candidate_queue_path`, `path_resolution`, `log_path_resolution`, and `candidate_queue_path_resolution` for debugging.

The writer uses one observation log format: markdown block with one JSON metadata block. It must not create a parallel JSON-lines observation log. Required metadata fields:

```text
record_id,record_type,timestamp,source_channel,user_prompt,routing_mode,execution_mode,final_status,final_answer_summary,issue_tags,direct_tool_bypass,bypass_reason,risk_review_required,feedback_type,candidate_appended,candidate_queue_path,path_resolution,subagent_session_id,main_session_id
```

Runtime candidate queue CSV uses this 13-column schema:

```text
candidate_id,timestamp,source_channel,linked_log_id,user_prompt,agent_answer_summary,feedback_type,feedback_text,issue_tags,suggested_fix_area,priority,review_status,notes
```

If `runtime_logs/question_collection/` does not exist, the writer creates it. If the runtime CSV does not exist, it writes only the header. It must not copy demo rows from the template CSV. If an existing runtime CSV has an incompatible header, the writer preserves it as a timestamped schema mismatch backup and creates a new file with the 13-column header.

Rules:

- One JSON object per line.
- Each line is independently parseable.
- Filename rotates daily by local runtime date.
- Writing mode is append-only.
- Existing records must not be truncated or overwritten.

## 4. Forbidden Runtime Write Targets

Runtime must not write real user questions to:

```text
computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv
outputs/release/<release_name>/question_collection/question_learning_candidate_queue_v1.csv
```

The release copy of the CSV remains a template. It is not a live learning queue.

`pilot_observation_writer.py` must fail closed before appending if an explicit candidate queue path resolves to either forbidden template target.

## 5. Required Record Shape

Each JSONL record must follow `question_record_schema_v1.md` and include the three-layer model:

```yaml
agent_observed:
agent_suggested:
reviewer_final:
```

Minimum reviewer rule:

```yaml
reviewer_final:
  reviewer_decision: pending
```

Runtime must not generate `reviewer_decision=accepted`.

## 6. Sensitive Filtering

Before writing, runtime must filter sensitive content.

Forbidden to record:

- cookie
- token secret / accessToken / refreshToken
- session / sessionId
- header containing credentials
- auth state
- browser_storage_state_marker
- phone / mobile number plaintext
- ID card / identity number
- credential file content

UID / DID / IP can be retained as internal risk-control entity fields or converted to `safe_ref`, depending on audience and sharing scope.

## 7. No Brain Modification

Runtime logging must not modify:

- Skill
- Prompt
- runtime summary
- routing
- release package
- regression suite
- template CSV

Runtime only writes `question_record` candidates.

For follow-up user feedback, runtime can write a linked `feedback_record`:

```yaml
feedback_record:
  timestamp:
  source_channel:
  feedback_message:
  linked_previous_record_id:
  inferred_feedback_type:
  confidence:
  should_enter_candidate_queue:
  sanitized_feedback_text:
```

High-value feedback enters the runtime candidate queue only with `review_status=pending`.

Final learning deposition requires human review and a separate Codex task after `reviewer_decision=accepted`.

## 8. Error Handling

If logging fails:

- Do not block the main user answer.
- Return or record `logging_failed` as a status.
- Do not retry by printing sensitive raw content.
- Do not fall back to writing the template CSV.

If the log directory does not exist, runtime may create:

```text
runtime_logs/question_collection/
```

## 9. Offline Review Queue

Reviewed queues may be generated later by offline scripts, for example:

```text
reviewed_question_learning_queue_v1.csv
```

That reviewed queue is not generated by live runtime and must not mark records as accepted without human review.

## 10. Release Boundary

Semi-open release should include this contract and a sample JSONL, but should not include real runtime question logs by default.
