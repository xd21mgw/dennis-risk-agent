# Security Preflight Dry-run v1

## 本轮目标

验证 `security_preflight_policy.yaml` 与 `security_preflight_evaluator.py` 能在本地 dry-run 中，对 capability 调用请求输出 `allow` / `deny` / `require_approval` / `redact` 判断。

## 文件路径

- policy/config: `computer_use_poc/security_preflight_policy.yaml`
- evaluator: `computer_use_poc/security_preflight_evaluator.py`
- test cases: `computer_use_poc/security_preflight_test_cases.json`

## 结果汇总

- total_cases: 12
- passed_cases: 12
- failed_cases: 0
- real_platform_called: false
- real_api_called: false
- approval_system_connected: false
- audit_db_connected: false

## Case 结果

| case_id | expected | actual | expected_flags | actual_flags | result |
|---|---|---|---|---|---|
| SPF-001 | allow | allow | none | none | pass |
| SPF-002 | allow | allow | none | none | pass |
| SPF-003 | require_approval | require_approval | entity_count_exceeds_default, scope_requires_approval | entity_count_exceeds_default, scope_requires_approval | pass |
| SPF-004 | allow | allow | redaction_required | redaction_required | pass |
| SPF-005 | deny | deny | user_attempted_tool_control, denied_field_requested, raw_output_requested | user_attempted_tool_control, denied_field_requested, raw_output_requested | pass |
| SPF-006 | deny | deny | user_attempted_tool_control, denied_field_requested | user_attempted_tool_control, denied_field_requested | pass |
| SPF-007 | require_approval | require_approval | user_attempted_tool_control | user_attempted_tool_control | pass |
| SPF-008 | deny | deny | attempts_to_override_policy, capability_prohibited, denied_field_requested, raw_output_requested | capability_prohibited, attempts_to_override_policy, denied_field_requested, raw_output_requested, scope_denied | pass |
| SPF-009 | deny | deny | attempts_to_override_policy, capability_prohibited, denied_field_requested | capability_prohibited, attempts_to_override_policy, denied_field_requested, scope_denied | pass |
| SPF-010 | deny | deny | capability_prohibited, scope_denied | capability_prohibited, denied_field_requested, entity_count_exceeds_default, scope_denied | pass |
| SPF-011 | deny | deny | capability_prohibited, scope_denied | capability_prohibited, denied_field_requested, scope_denied | pass |
| SPF-012 | deny | deny | user_attempted_tool_control, denied_field_requested, raw_output_requested | user_attempted_tool_control, denied_field_requested, raw_output_requested | pass |

## 发现的问题

- 当前 dry-run 未发现 expected decision / expected flags 不匹配。
- 本轮仅验证本地结构化 policy 与 evaluator 逻辑，不代表已接入真实内部 Agent 执行层。

## 已知限制

- 未接真实审批系统。
- 未接真实审计落库。
- 未接真实内部平台。
- 未读取认证态。
- 未实现生产级 policy 热更新、签名校验或多版本兼容。
- `security_preflight_policy.yaml` 当前使用 JSON 兼容 YAML 子集，以避免引入 PyYAML 依赖。

## 后续 TODO

- 在内部 Agent 执行层调用真实 capability 前强制调用 evaluator。
- 将 dry-run audit_event 接入内部安全审计存储。
- 接入真实审批系统后，将 `require_approval` 从阻断态升级为可审批流转态。
- 为更多 capability 增加结构化 scope 与字段级策略。
