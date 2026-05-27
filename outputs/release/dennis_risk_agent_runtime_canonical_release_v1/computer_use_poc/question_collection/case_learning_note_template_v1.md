# Case Learning Note Template v1

## 1. Positioning

`case_learning_note` is a candidate learning artifact derived from a high-value user question or multi-turn conversation. It is not a direct Skill update and must not change Dennis Agent brain, routing, runtime summary, or release package before human review.

`reviewer_decision=accepted` is required before Codex can turn the note into FAQ, golden case, bad case, routing update, evidence template update, or regression case.

## 2. Template

```yaml
case_learning_note_id:
source_question_id:
case_title:
original_question_sanitized:
conversation_summary:
risk_scene:
entities:
  - entity_type:
    entity_ref:
    sensitivity:
user_provided_context:
dennis_agent_answer_summary:
key_evidence:
  raw_evidence:
    - evidence_summary:
      evidence_source:
      source_quality:
  manual_input:
    - statement:
      boundary:
  model_inference:
    - hypothesis:
      boundary:
missing_evidence:
agent_gap:
recommended_skill_update:
recommended_routing_update:
recommended_evidence_template_update:
recommended_regression_case:
safety_notes:
reviewer_decision: pending
codex_followup_prompt:
```

## 3. Evidence Boundary

- `raw_evidence` must come from a traceable source such as internal platform API, browser DOM read, screenshot/manual read, DataAgent/Hive result, or historical document.
- `manual_input` is useful context, but it cannot independently support a strong conclusion.
- `model_inference` is a hypothesis, not raw evidence.
- Login log over-window `no_data` cannot be used as counter evidence.
- Blocked or partial source must be visible and should downgrade conclusion confidence.
- Device relation is candidate relationship evidence, not direct cheating or ATO conclusion.
- `raw_reference` must be safe internal reference only; do not include cookie, token, session, header, phone number plaintext, or credential secret.

## 4. Example: ATO User Claims No Operation

```yaml
case_learning_note_id: cln_ato_claim_no_operation_001
source_question_id: q_demo_ato_001
case_title: "用户称未发作品但账号出现异常发布"
original_question_sanitized: "用户称没有发过作品，但账号出现异常发布，是否可能是盗号？"
conversation_summary: "用户提供异常发布描述，但缺少发布审计、登录完整窗口和 token 使用链路。"
risk_scene: ato
entities:
  - entity_type: user_id
    entity_ref: safe_ref_user_001
    sensitivity: risk_entity
user_provided_context:
  - "用户称未操作。"
  - "存在异常发布。"
dennis_agent_answer_summary: "应按 ATO 候选路径处理，但不能仅凭用户描述定性。"
key_evidence:
  raw_evidence: []
  manual_input:
    - statement: "用户描述存在非本人发布。"
      boundary: "manual_input only; cannot support strong conclusion alone"
  model_inference:
    - hypothesis: "可能存在 token/OAuth/登录态复用或新设备接管。"
      boundary: "hypothesis only"
missing_evidence:
  - publish_audit_log
  - token_usage_trace
  - login_log_with_reliable_window_check
  - oauth_authorization_record
agent_gap: "需要稳定的 ATO 单例 evidence card 和 source metadata。"
recommended_skill_update: "none_before_review"
recommended_routing_update: "ATO 历史 case 超窗时生成 offline Hive query plan。"
recommended_evidence_template_update: "补充 publish/token/OAuth/source_quality 字段。"
recommended_regression_case: "ATO manual_input cannot support strong conclusion"
safety_notes:
  - "Do not store credentials."
  - "Do not treat over-window login no_data as counter evidence."
reviewer_decision: pending
codex_followup_prompt: "如审核接受，将该 case 转为 ATO bad/golden candidate 并补充 smoke test。"
```

## 5. Example: Protocol Attack Short Question

```yaml
case_learning_note_id: cln_protocol_short_question_001
source_question_id: q_demo_protocol_001
case_title: "后端请求很多但用户前端无操作的协议攻击短问"
original_question_sanitized: "后端请求很多但用户前端没有操作，是不是协议攻击？"
conversation_summary: "用户问的是风险类型判断，需要区分协议攻击、自动化脚本、前端埋点缺失、正常后台任务。"
risk_scene: protocol_attack
entities:
  - entity_type: request_pattern
    entity_ref: safe_ref_request_pattern_001
    sensitivity: non_personal_pattern
user_provided_context:
  - "后端请求多。"
  - "前端操作少或无。"
dennis_agent_answer_summary: "更像协议/自动化候选，但需要 UA、token、设备、前端埋点、请求节奏和来源一致性补证。"
key_evidence:
  raw_evidence: []
  manual_input:
    - statement: "用户提供后端/前端不一致现象。"
      boundary: "manual_input only"
  model_inference:
    - hypothesis: "协议攻击或自动化脚本候选。"
      boundary: "not raw evidence"
missing_evidence:
  - request_headers_redacted
  - ua_app_version_distribution
  - frontend_activity_trace
  - token_source_consistency
  - rate_and_sequence_pattern
agent_gap: "短问需要输出最小区分标识，而不是直接定性协议攻击。"
recommended_skill_update: "none_before_review"
recommended_routing_update: "risk_short_question -> protocol_attack evidence planning"
recommended_evidence_template_update: "补充前后端一致性 evidence card。"
recommended_regression_case: "backend_requests_without_frontend_action_not_auto_protocol_attack"
safety_notes:
  - "Do not output raw headers or tokens."
reviewer_decision: pending
codex_followup_prompt: "如审核接受，将该短问加入 FAQ 或 golden short-answer case。"
```
