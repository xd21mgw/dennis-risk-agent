# User Feedback Capture v1

## 1. Purpose

User feedback helps Dennis Agent identify whether an answer was useful, too generic, off-target, missing evidence, or worth turning into reusable learning material.

Feedback is written into `question_record.user_feedback`. It can raise `learning_value` or push a question into the candidate queue, but it cannot directly modify Skill, Prompt, routing, runtime summary, release package, or regression assets.

In semi-open runtime, later user messages can also be captured as `feedback_record` blocks linked to the previous observation id. The runtime must append these blocks; it must not rewrite historical observation text in place.

## 2. Minimal Feedback Options

| value | label | meaning | suggested record impact |
|---|---|---|---|
| 1 | useful | The answer is usable as-is. | Keep `learning_value` unchanged unless the case is reusable. |
| 2 | too_generic | The answer is too generic or lacks Dennis-style judgment. | Consider `gap_type=template_gap` or `knowledge_gap`; raise to candidate queue if repeated. |
| 3 | off_target | The answer misunderstood the scene, entity, or risk type. | Set `gap_type=routing_gap` or `user_context_gap`; usually `need_human_review`. |
| 4 | needs_data | The answer needs data verification. | Generate evidence plan or DataAgent query plan; do not directly query by default. |
| 5 | worth_learning | The question is reusable and should be reviewed. | Set `learning_value=high` or `medium`; `reviewer_decision=pending`. |
| 6 | need_user_profile | User profile evidence is missing. | Recommend `internal_platform_routing_plan` or evidence plan for user profile. |
| 7 | need_device_profile | Device profile evidence is missing. | Recommend device risk / device relation evidence planning. |
| 8 | need_login_log | Login log evidence is missing. | Recommend login log read only when within reliable window, otherwise offline Hive plan. |
| 9 | need_strategy_hit | Strategy hit evidence is missing. | Recommend strategy hit evidence plan. |
| 10 | need_dataagent_hive | Offline aggregation or long-window analysis is needed. | Generate DataAgent / Hive query plan; do not call DataAgent automatically. |

## 2-A. Free-text Feedback Inference Rules

| user wording | inferred feedback_type | candidate queue |
|---|---|---|
| 有用 / 可以 / 这个对 / 这个结论准 | `useful` | no by default |
| 太泛了 / 都是方法论 / 没啥信息 | `too_generic` | yes |
| 不是这个意思 / 你理解错了 / 意图不对 | `wrong_intent` | yes |
| 答偏 | `off_target` | yes |
| 你没查数据 / 能不能实际查一下 / 查一下吧 | `needs_data` | yes |
| 等太久 / 卡住了 / 怎么还没结果 | `timeout_bad_experience` | yes |
| 这个值得沉淀 / 记录下 / 后面修 | `worth_learning` | yes |
| 你不该输出这个 / 这个太敏感 | `unsafe_or_overexposed` | yes |

Follow-up continuation rule:

- If the previous turn is a risk-query context and the user only replies `查一下吧` / `继续` / `看下` / `可以` / `试一下`, record `needs_data` with issue tag `followup_query`.
- The main agent should not directly execute from that short reply. It should route the follow-up to `dennis-risk-agent` or the correct execution / plan mode.

## 3. Recording Rules

Recommended shape:

```yaml
user_feedback:
  selected_options:
    - 2
    - 5
  free_text_sanitized: "回答偏泛，希望补成 ATO 证据卡模板"
  captured_at: "2026-05-22T10:00:00+08:00"
```

Security rules:

- Do not store cookie, token, session, browserState, header, password, auth code, or credential secret.
- Phone number and personal identity data must be removed or converted to safe reference.
- UID / DID / IP can appear as internal risk entities only when necessary and should be safe-refed for wider sharing.
- Feedback text should be sanitized before it enters candidate queue or case learning note.

## 4. Candidate Queue Impact

If feedback includes `too_generic` or `off_target`, Dennis Agent should consider:

- `agent_observed.user_negative_feedback=true`
- `agent_observed.user_correction_detected=true` when the user corrects scene, evidence, routing, or boundary
- `agent_observed.answer_uncertainty_high=true` when the answer needed self-correction or had thin evidence
- `gap_type=template_gap`, `routing_gap`, `knowledge_gap`, or `user_context_gap`
- `learning_value=medium` or `high`
- `recommended_action=need_human_review`, `add_bad_case`, `update_routing`, or `update_evidence_template`

These are candidate signals. Final quality assessment and final action must be written under `reviewer_final`.

Runtime candidate queue append target:

```text
runtime_logs/question_collection/question_learning_candidate_queue_v1.csv
```

Do not append real runtime feedback into the source-tree template:

```text
computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv
```

Runtime candidate queue fields:

- `candidate_id`
- `timestamp`
- `source_channel`
- `linked_log_id`
- `user_prompt`
- `agent_answer_summary`
- `feedback_type`
- `feedback_text`
- `issue_tags`
- `suggested_fix_area`
- `priority`
- `review_status`
- `notes`

Priority rules:

- `P0`: safety leakage, write action, sensitive output, severe overreach.
- `P1`: wrong intent, should-have-queried-but-did-not, wrong judgment, timeout blocking core task.
- `P2`: too generic, too long, poor format, missing evidence plan.
- `P3`: wording polish, template compression.

If feedback includes `needs_data` or `need_dataagent_hive`, Dennis Agent should:

- Generate an evidence plan or DataAgent / Hive query plan.
- Not call real platform or DataAgent automatically.
- Mark missing source, window gap, permission gap, or offline requirement explicitly.

## 5. Non-Automatic Learning Boundary

Feedback can create learning candidates. It cannot directly:

- Modify core Skill or Prompt.
- Update routing in runtime.
- Add golden case / bad case without review.
- Change release package.
- Trigger real platform access.
- Trigger DataAgent / Hive execution.

The default reviewer state is `reviewer_decision=pending`.
