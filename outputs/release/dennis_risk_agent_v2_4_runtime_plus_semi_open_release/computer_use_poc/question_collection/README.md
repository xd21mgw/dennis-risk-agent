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

Core rule:

- Agent can automatically keep records.
- Agent cannot automatically change the brain.

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
- `question_learning_candidate_queue_v1.csv`: queue template and examples.
- `user_feedback_capture_v1.md`: lightweight feedback options.
- `case_learning_note_template_v1.md`: candidate learning note template.
- `question_collection_text_regression_cases_v1.yaml`: text regression cases.
- `question_collection_text_regression_run_v1.md`: dry-run regression log.
- `runtime_append_only_logging_contract_v1.md`: runtime append-only logging contract.
- `runtime_question_record_sample_v1.jsonl`: JSONL sample records.
- `runtime_logging_smoke_test_v1.md`: append-only logging smoke tests.
- `runtime_question_record_collector_stub_v1.py`: local-only append stub.
