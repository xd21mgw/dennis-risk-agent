# Tool Call Audit Schema

## 1. 目标

所有内部平台手脚和 capability 调用都必须留下可审计记录，用于复盘、问责、权限排查和安全评估。

审计日志不存放敏感原文。`raw_result_reference` 只能是内部安全引用，不能包含 cookie、token、session、storageState、手机号、精确 IP、完整设备指纹、完整 header、完整 JSON 或内部密钥。

## 2. 标准字段

```yaml
tool_call_audit:
  audit_id:
  timestamp:
  operator:
  agent_version:
  release_name:
  user_input_summary:
  normalized_intent:
  scene:
  capability_name:
  capability_level:
  input_entities:
    - entity_type:
      entity_value_policy:
      entity_reference:
  input_entity_count:
  requested_time_range:
  approved_scope:
  actual_scope:
  sensitive_fields_requested:
  sensitive_fields_returned:
  redaction_applied:
  approval_required:
  approval_status:
  denial_reason:
  tool_status:
  result_count:
  output_summary:
  prompt_injection_suspected:
  policy_flags:
  fallback_used:
  raw_result_reference:
  manual_review_required:
```

## 3. 字段说明

- `audit_id`: 审计记录唯一 ID。
- `timestamp`: 工具调用时间。
- `operator`: 操作者或 agent session 标识，不记录敏感认证信息。
- `agent_version`: Agent 版本。
- `release_name`: 当前加载 release 或能力包名称。
- `user_input_summary`: 用户请求摘要，不包含敏感原文。
- `normalized_intent`: 归一化意图。
- `scene`: 场景，如 ATO、设备风险、策略命中解释。
- `capability_name`: 已登记 capability 名称。
- `capability_level`: 安全分级。
- `input_entities`: 输入实体引用化记录。
- `input_entity_count`: 输入实体数量。
- `requested_time_range`: 用户请求时间范围。
- `approved_scope`: 审批或默认允许范围。
- `actual_scope`: 实际执行范围。
- `sensitive_fields_requested`: 用户是否要求敏感字段。
- `sensitive_fields_returned`: 实际是否返回敏感字段；通常应为 `false` 或 `redacted_only`。
- `redaction_applied`: 是否应用脱敏。
- `approval_required`: 是否需要审批。
- `approval_status`: `not_required / approved / denied / pending`。
- `denial_reason`: 拒绝原因。
- `tool_status`: `success / failed / blocked / partial / skipped`。
- `result_count`: 返回结果数量。
- `output_summary`: 输出摘要。
- `prompt_injection_suspected`: 是否疑似提示词攻击。
- `policy_flags`: 命中的安全策略标记。
- `fallback_used`: 是否使用 fallback。
- `raw_result_reference`: 内部安全引用，不含敏感原文。
- `manual_review_required`: 是否需要人工复核。

## 4. YAML 示例

```yaml
tool_call_audit:
  audit_id: audit_20260520_000001
  timestamp: "2026-05-20T15:30:00+08:00"
  operator: internal_agent_session_ref
  agent_version: dennis_risk_agent_v2_6
  release_name: dennis_risk_agent_v2_6_full_experience_first_release
  user_input_summary: "用户请求查看单个账号是否存在盗号风险"
  normalized_intent: ato_risk_assessment
  scene: account_security_ato
  capability_name: login_log_read
  capability_level: readonly_sensitive
  input_entities:
    - entity_type: user_id
      entity_value_policy: referenced
      entity_reference: user_ref_001
  input_entity_count: 1
  requested_time_range: "recent_7d"
  approved_scope: "single_user_recent_window"
  actual_scope: "single_user_recent_window"
  sensitive_fields_requested: false
  sensitive_fields_returned: redacted_only
  redaction_applied: true
  approval_required: false
  approval_status: not_required
  denial_reason: null
  tool_status: success
  result_count: 12
  output_summary: "返回登录方式分布、成功失败计数、设备一致性摘要"
  prompt_injection_suspected: false
  policy_flags:
    - readonly_first
    - sensitive_field_redaction_applied
  fallback_used: false
  raw_result_reference: secure_internal_ref://audit/audit_20260520_000001
  manual_review_required: false
```

## 5. 使用要求

- 每次工具调用必须生成 audit schema。
- blocked / denied / fallback 也要审计。
- 审计记录不能成为敏感数据泄露通道。
- 审计摘要应能回答：谁在什么版本下、因为什么业务问题、调用了哪个能力、范围多大、是否审批、输出是否脱敏、是否命中安全策略。
