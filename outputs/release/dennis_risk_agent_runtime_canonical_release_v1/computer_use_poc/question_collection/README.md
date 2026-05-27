# Question Collection / Learning Candidate Queue

## 1. Module Positioning

This module collects real user questions from semi-open Dennis Agent usage. It is a demand radar, capability-gap detector, learning candidate queue, and human review entry.

It is not an automatic brain evolution module.

Current location:

- `computer_use_poc/question_collection/`

This location is temporary. It is not a normal POC folder in product meaning; it is the candidate module for a future runtime learning loop. In later releases it should be packaged under:

- `outputs/release/<release_name>/question_collection/`

Long term, migrate to one of:

- `runtime/question_collection/`
- `learning/question_collection/`

## 2. Closed-loop Flow

```text
用户提问
→ Dennis Agent 正常回答
→ 生成 question_record
→ 记录 `agent_observed` 运行时信号
→ 生成 `agent_suggested` 候选标签：scene / capability / gap_type / learning_value / recommended_action
→ 高价值问题进入 candidate queue
→ 人工审核
→ Codex 按审核结论写入 Skill / FAQ / golden case / bad case / regression
→ 跑回归
→ 进入下一版 release
```

`agent_suggested` 不是最终判断；最终质量评估、最终 gap、最终 learning value 和最终沉淀动作只能由 `reviewer_final` 决定。

## 2-A. Runtime Append-only Logging

Runtime must not write real user questions into `question_learning_candidate_queue_v1.csv`.

That CSV is a read-only template and demo queue.

Correct runtime target:

```text
runtime_logs/question_collection/question_records_YYYYMMDD.jsonl
```

Runtime logging rules:

- Append-only.
- One `question_record` JSON object per line.
- Use `agent_observed` / `agent_suggested` / `reviewer_final`.
- Default `reviewer_final.reviewer_decision=pending`.
- Never generate `accepted` decisions in live runtime.
- Never overwrite template CSV in source tree or release package.
- Never record cookie / token / session / header / auth state / phone plaintext.

Contract files:

- `runtime_append_only_logging_contract_v1.md`
- `runtime_question_record_sample_v1.jsonl`
- `runtime_logging_smoke_test_v1.md`
- `runtime_question_record_collector_stub_v1.py`
- `pilot_observation_writer.py`

Core rule:

- Agent can automatically keep records.
- Agent cannot automatically change the brain.

## 2-B. Semi-open User Feedback Loop

Current pilot feedback flow:

```text
用户后续消息
→ 识别 feedback_type
→ 关联最近 observation record
→ 追加 feedback block 到 semi_open_pilot_logs/YYYY-MM-DD.md
→ 高价值反馈追加 runtime_logs/question_collection/question_learning_candidate_queue_v1.csv
→ reviewer_final 继续保持 pending
```

`pilot_observation_writer.py` supports two local input types:

- `observation_record`: appends a normal observation block and includes `user_feedback`.
- `feedback_record`: appends a linked feedback block.

High-value feedback types enter the runtime candidate queue:

- `too_generic`
- `off_target`
- `wrong_intent`
- `needs_data`
- `timeout_bad_experience`
- `worth_learning`
- `unsafe_or_overexposed`

`useful` feedback is recorded in the pilot log but does not enter the candidate queue by default.

The runtime candidate queue path is:

```text
$DENNIS_AGENT_HOME/runtime_logs/question_collection/question_learning_candidate_queue_v1.csv
```

If `DENNIS_AGENT_HOME` is not set, the writer resolves the `dennis-risk-agent` repo root from `pilot_observation_writer.py` and writes to:

```text
<dennis-risk-agent-repo-root>/runtime_logs/question_collection/question_learning_candidate_queue_v1.csv
```

The source-tree `computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv` remains a demo template and must not be overwritten by runtime. Release package copies of `question_collection/question_learning_candidate_queue_v1.csv` are also templates and must not receive runtime writes.

Runtime path resolution is stable and does not depend on arbitrary CWD. Observation logs and candidate queue use the same resolution order:

1. `--log-dir <path>` wins for observation logs; `--candidate-queue <path>` is allowed only for explicit local testing and must not point to the source-tree or release template CSV.
2. If `DENNIS_AGENT_HOME` is set, writer uses:
   `DENNIS_AGENT_HOME/semi_open_pilot_logs/YYYY-MM-DD.md` and
   `DENNIS_AGENT_HOME/runtime_logs/question_collection/question_learning_candidate_queue_v1.csv`.
3. Otherwise, writer resolves the `dennis-risk-agent` repo root from `pilot_observation_writer.py` and writes under that root.
4. Only if repo-root detection fails, writer falls back to current CWD and reports `path_resolution=fallback_cwd`.

Recommended live configuration:

```bash
export DENNIS_AGENT_HOME=/path/to/dennis-risk-agent
```

The writer also supports:

```bash
python3 computer_use_poc/question_collection/pilot_observation_writer.py \
  --candidate-queue /absolute/path/runtime_logs/question_collection/question_learning_candidate_queue_v1.csv
```

Writer output always includes `candidate_queue_path` and `path_resolution`.
It also includes `log_path_resolution` and `candidate_queue_path_resolution`.
If a caller attempts to write the runtime queue into `computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv` or a release package template CSV, the writer fails closed before appending.

Observation log format is markdown-only for this writer. Each record is a markdown block containing one JSON metadata block. The metadata block must include:

- `record_id`
- `record_type`
- `timestamp`
- `source_channel`
- `user_prompt`
- `routing_mode`
- `execution_mode`
- `final_status`
- `final_answer_summary`
- `issue_tags`
- `direct_tool_bypass`
- `bypass_reason`
- `risk_review_required`
- `feedback_type`
- `candidate_appended`
- `candidate_queue_path`
- `path_resolution`
- `subagent_session_id`
- `main_session_id`

Runtime candidate queue schema uses the 13-column header_field:

```text
candidate_id,timestamp,source_channel,linked_log_id,user_prompt,agent_answer_summary,feedback_type,feedback_text,issue_tags,suggested_fix_area,priority,review_status,notes
```

If the runtime CSV is missing, writer creates parent directories and writes the header. If an existing runtime CSV has an incompatible header, writer preserves it as a timestamped `schema_mismatch_backup` file and starts a new file with the 13-column header. It does not copy demo rows into runtime output.

## 3. Boundaries

- Does not access real internal platforms.
- Does not call DataAgent.
- Does not automatically modify core Skill.
- Does not automatically modify release packages.
- Does not store cookie / token / session / header.
- UID / DID / IP may be used as internal risk entity fields, but sharing scope determines whether they must be converted to `safe_ref`.
- Phone number, cookie, token, session, header, auth state file content and credential material must not be recorded.

## 4. Main Files

- `question_record_schema_v1.md`: question_record schema.
- `question_learning_policy_v1.md`: candidate queue decision policy.
- `question_learning_candidate_queue_v1.csv`: queue template and examples using the 13-column runtime schema; not a runtime write target.
- `user_feedback_capture_v1.md`: lightweight feedback options.
- `case_learning_note_template_v1.md`: candidate learning note template.
- `question_collection_text_regression_cases_v1.yaml`: text regression cases.
- `question_collection_text_regression_run_v1.md`: dry-run regression log.
- `runtime_append_only_logging_contract_v1.md`: runtime append-only logging contract.
- `runtime_question_record_sample_v1.jsonl`: JSONL sample records.
- `runtime_logging_smoke_test_v1.md`: append-only logging smoke tests.
- `runtime_question_record_collector_stub_v1.py`: local-only append stub.
- `pilot_observation_writer.py`: local-only pilot observation / feedback writer with candidate queue append.
