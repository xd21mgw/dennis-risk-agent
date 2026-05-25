# Feedback Writer Candidate Queue Path Patch v1

## Goal

Fix the feedback writer runtime candidate queue path instability and CSV schema mismatch found during live overlay validation.

## Problem

`pilot_observation_writer.py` previously used a relative candidate queue path:

```text
runtime_logs/question_collection/question_learning_candidate_queue_v1.csv
```

That made output depend on the process CWD. Calling the writer from the workspace parent and from the repo root could create two different runtime queues, making review and debugging unreliable.

## Fix

- Added `--candidate-queue <path>` for explicit queue output.
- Added stable default resolution:
  1. explicit argument
  2. `DENNIS_AGENT_HOME/runtime_logs/question_collection/question_learning_candidate_queue_v1.csv`
  3. repo root resolved from the script path
  4. CWD fallback only when repo-root detection fails
- Writer output now includes:
  - `candidate_queue_path`
  - `path_resolution`
- Candidate queue parent directories are created automatically.
- Missing runtime CSV gets the 13-column header.
- Existing runtime CSV with incompatible header is preserved as `schema_mismatch_backup` and replaced with a new 13-column runtime CSV.
- Source-tree template CSV was upgraded to the 13-column demo schema and remains template-only.

## Runtime queue schema

```text
candidate_id,timestamp,source_channel,linked_log_id,user_prompt,agent_answer_summary,feedback_type,feedback_text,issue_tags,suggested_fix_area,priority,review_status,notes
```

## Tests

Local validation results:

- `python3 -m py_compile computer_use_poc/question_collection/pilot_observation_writer.py`: pass after rerun with permission to write Python cache.
- Repo-root self-test: pass, `path_resolution=script_repo_root`.
- Parent-CWD self-test: pass, same candidate queue path under repo root, `path_resolution=script_repo_root`.
- Explicit `--candidate-queue /tmp/dennis_feedback_queue_test/question_learning_candidate_queue_v1.csv`: pass, `path_resolution=explicit_arg`.
- `DENNIS_AGENT_HOME=/tmp/dennis_agent_home_test`: pass, `path_resolution=dennis_agent_home`.
- Sensitive keyword scan over `/tmp/dennis_feedback_queue_test`: pass, no raw credential or phone-like strings found.
- `git diff --check`: pass.

## Runtime configuration recommendation

Internal Agent should set:

```bash
DENNIS_AGENT_HOME=/path/to/dennis-risk-agent
```

This is recommended but not strictly required, because the writer can resolve the repo root from its own script path.

## Boundaries

- Did not access real platforms.
- Did not call DataAgent.
- Did not modify auth or gateway.
- Did not execute real business queries.
- Did not repackage release.
- Did not commit git.
- Did not write real user feedback into the template CSV.
