# Security Preflight Request Contract Validator Run v1

## 本轮目标

校验本地 `tool_call_request` 样例的字段完整性和安全字段质量，用于后续接 runtime 前降低 `evaluator_error_like_issue`。

## 新增文件

- `computer_use_poc/security_preflight_request_contract_validator.py`
- `computer_use_poc/security_preflight_request_contract_test_cases.json`
- `computer_use_poc/run_logs/security_preflight_request_contract_validator_run_v1.md`

## Case 覆盖范围

- 完整合法 user_profile_read
- 完整合法 login_log_read
- 缺 capability_name
- unknown capability
- requested_scope 缺失 / 非法
- requested_fields 缺失
- input_entities 缺失
- input_entity_count 不一致
- bool 字段类型错误
- prohibited field 请求
- 敏感实体未标记 is_sensitive
- 底层平台名被当 capability_name

## Validator 结果摘要

- total_cases: 14
- passed_cases: 14
- failed_cases: 0

| case_id | valid | next_step | warnings | errors | result |
|---|---|---|---|---|---|
| REQ-CONTRACT-001 | true | pass_to_evaluator | none | none | pass |
| REQ-CONTRACT-002 | true | pass_to_evaluator | none | none | pass |
| REQ-CONTRACT-003 | false | deny | none | capability_name_missing | pass |
| REQ-CONTRACT-004 | false | deny | none | unknown_capability | pass |
| REQ-CONTRACT-005 | false | fix_request_mapping | none | requested_scope_missing | pass |
| REQ-CONTRACT-006 | false | fix_request_mapping | none | requested_scope_invalid | pass |
| REQ-CONTRACT-007 | true | pass_to_evaluator | requested_fields_missing_safe_summary_only | none | pass |
| REQ-CONTRACT-008 | false | require_clarification | none | input_entities_missing, input_entities_type_error | pass |
| REQ-CONTRACT-009 | false | fix_request_mapping | none | entity_count_mismatch | pass |
| REQ-CONTRACT-010 | false | fix_request_mapping | none | direct_tool_requested_by_user_type_error | pass |
| REQ-CONTRACT-011 | false | fix_request_mapping | none | attempts_to_override_policy_type_error | pass |
| REQ-CONTRACT-012 | false | deny | none | prohibited_field_requested | pass |
| REQ-CONTRACT-013 | false | fix_request_mapping | none | sensitive_entity_not_marked | pass |
| REQ-CONTRACT-014 | false | deny | none | unknown_capability, raw_platform_name_used_as_capability, prohibited_field_requested | pass |

## recommended_next_step 分布

- deny: 4
- fix_request_mapping: 6
- pass_to_evaluator: 3
- require_clarification: 1

## 主要 warning 类型

- requested_fields_missing_safe_summary_only: 1

## 主要 error 类型

- attempts_to_override_policy_type_error: 1
- capability_name_missing: 1
- direct_tool_requested_by_user_type_error: 1
- entity_count_mismatch: 1
- input_entities_missing: 1
- input_entities_type_error: 1
- prohibited_field_requested: 2
- raw_platform_name_used_as_capability: 1
- requested_scope_invalid: 1
- requested_scope_missing: 1
- sensitive_entity_not_marked: 1
- unknown_capability: 2

## 已知限制

- 本轮只校验本地样例，不接真实 runtime。
- 本轮不调用 preflight evaluator。
- 本轮不读取认证态、不调用真实 API、不接真实平台。
- validator 只做输入质量检查，不代替 security preflight evaluator。

## 后续 TODO

- 接 runtime 前，用真实 Agent 生成的 request 样本跑 validator。
- 将 validator 与 evaluator 串联，形成 shadow hook 接入前输入质量闸门。
- 将字段缺失和类型错误纳入 shadow metrics。
