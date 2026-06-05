# Semi-open User Feedback Loop Patch v1

## 1. Goal

Implement a local minimum feedback loop for Dennis Risk Agent semi-open pilot usage.

Problem before this patch:

- `semi_open_pilot_logs/YYYY-MM-DD.md` recorded agent observation, but did not define a `user_feedback` field.
- `question_learning_candidate_queue_v1.csv` was only a demo template.
- `user_feedback_capture_v1.md` described feedback labels, but no local writer connected follow-up feedback to observation logs or candidate queue.

This patch adds local schema, writer, queue append logic, feedback inference rules, smoke tests, and run log only.

## 2. Boundaries

- real_platform_called: false
- DataAgent_called: false
- auth-state category_modified: false
- gateway_config_modified: false
- real_query_executed: false
- git_committed: false
- core_skill_modified: false
- release_dist_updated: false

## 3. Schema Additions

Observation records now include:

```yaml
user_feedback:
  feedback_type:
  feedback_text:
  inferred_from_message:
  confidence:
  linked_previous_record_id:
  should_enter_candidate_queue:
```

Feedback records include:

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

## 4. Local Writer

New local writer:

```text
computer_use_poc/question_collection/pilot_observation_writer.py
```

Supported record types:

- `observation_record`
- `feedback_record`

Write targets:

- observation / feedback markdown blocks:
  - `semi_open_pilot_logs/YYYY-MM-DD.md`
- high-value runtime candidate queue:
  - `runtime_logs/question_collection/question_learning_candidate_queue_v1.csv`

The source-tree template remains read-only:

```text
computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv
```

## 5. Feedback Inference

| user wording | inferred type | candidate queue |
|---|---|---|
| 有用 / 可以 / 这个对 / 这个结论准 | `useful` | no |
| 太泛了 / 都是方法论 / 没啥信息 | `too_generic` | yes |
| 不是这个意思 / 你理解错了 / 意图不对 | `wrong_intent` | yes |
| 答偏 | `off_target` | yes |
| 你没查数据 / 能不能实际查一下 / 查一下吧 | `needs_data` | yes |
| 等太久 / 卡住了 / 怎么还没结果 | `timeout_bad_experience` | yes |
| 这个值得沉淀 / 记录下 / 后面修 | `worth_learning` | yes |
| 你不该输出这个 / 这个太敏感 | `unsafe_or_overexposed` | yes |

Follow-up continuation:

- Short replies such as `查一下吧` / `继续` / `看下` / `可以` / `试一下` should be marked as `needs_data` with `followup_query` when linked to a prior risk-query context.
- Main agent should not directly exec from this short reply. It should route to dennis-risk-agent or the correct execution / plan mode.

## 6. Candidate Queue Priority

- `P0`: safety leakage, write action, sensitive output, severe overreach.
- `P1`: wrong intent, should-have-queried-but-did-not, wrong judgment, timeout blocking core task.
- `P2`: too generic, too long, poor format, missing evidence plan.
- `P3`: wording polish, template compression.

## 7. Smoke Test Result

Command:

```bash
python3 computer_use_poc/question_collection/pilot_observation_writer.py --self-test
```

Result:

```text
status: pass
too_generic_candidate: true
wrong_intent_candidate: true
needs_data_candidate: true
worth_learning_candidate: true
useful_not_candidate: true
sensitive_redacted: true
```

Compile check:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/dennis_pycache python3 -m py_compile computer_use_poc/question_collection/pilot_observation_writer.py
```

Result: pass.

## 8. Still Needed for Runtime

- Main agent / runtime must call `pilot_observation_writer.py` or equivalent logic after each user follow-up feedback message.
- Runtime must pass the previous observation id as `linked_previous_record_id`.
- Runtime must not write `review_status=accepted` or `reviewer_decision=accepted`.
- Runtime must not modify Skill, Prompt, runtime summary, release package, or regression automatically.
