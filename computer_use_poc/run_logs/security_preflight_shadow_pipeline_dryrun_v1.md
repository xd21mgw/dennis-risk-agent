# Security Preflight Shadow Pipeline Dry-run v1

## 本轮目标

将本地 `tool_call_request` 样例串联为 contract validator → preflight evaluator → shadow event → metrics summary 的 dry-run pipeline。

## 输入

- request cases: `computer_use_poc/security_preflight_request_contract_test_cases.json`
- policy: `computer_use_poc/security_preflight_policy.yaml`

## 运行边界

- real_runtime_connected: false
- real_platform_called: false
- real_api_called: false
- auth_state_read: false
- enforce_mode_enabled: false

## 指标汇总

| metric | value |
|---|---:|
| total_requests | 14 |
| contract_valid_count | 3 |
| contract_invalid_count | 11 |
| passed_to_evaluator_count | 3 |
| blocked_before_evaluator_count | 11 |
| allow_count | 3 |
| deny_count | 0 |
| require_approval_count | 0 |
| redaction_required_count | 0 |
| unknown_capability_count | 0 |
| evaluator_error_like_issue_count | 11 |

## Event 结果

| event_id | source_case_id | contract_valid | contract_next_step | preflight_decision | shadow_event_type | runtime_action |
|---|---|---|---|---|---|---|
| PIPE-001 | REQ-CONTRACT-001 | true | pass_to_evaluator | allow | none | observe_and_continue |
| PIPE-002 | REQ-CONTRACT-002 | true | pass_to_evaluator | allow | none | observe_and_continue |
| PIPE-003 | REQ-CONTRACT-003 | false | deny | not_evaluated | contract_validation_blocked | block_before_evaluator |
| PIPE-004 | REQ-CONTRACT-004 | false | deny | not_evaluated | contract_validation_blocked | block_before_evaluator |
| PIPE-005 | REQ-CONTRACT-005 | false | fix_request_mapping | not_evaluated | contract_validation_blocked | block_before_evaluator |
| PIPE-006 | REQ-CONTRACT-006 | false | fix_request_mapping | not_evaluated | contract_validation_blocked | block_before_evaluator |
| PIPE-007 | REQ-CONTRACT-007 | true | pass_to_evaluator | allow | none | observe_and_continue |
| PIPE-008 | REQ-CONTRACT-008 | false | require_clarification | not_evaluated | contract_validation_blocked | block_before_evaluator |
| PIPE-009 | REQ-CONTRACT-009 | false | fix_request_mapping | not_evaluated | contract_validation_blocked | block_before_evaluator |
| PIPE-010 | REQ-CONTRACT-010 | false | fix_request_mapping | not_evaluated | contract_validation_blocked | block_before_evaluator |
| PIPE-011 | REQ-CONTRACT-011 | false | fix_request_mapping | not_evaluated | contract_validation_blocked | block_before_evaluator |
| PIPE-012 | REQ-CONTRACT-012 | false | deny | not_evaluated | contract_validation_blocked | block_before_evaluator |
| PIPE-013 | REQ-CONTRACT-013 | false | fix_request_mapping | not_evaluated | contract_validation_blocked | block_before_evaluator |
| PIPE-014 | REQ-CONTRACT-014 | false | deny | not_evaluated | contract_validation_blocked | block_before_evaluator |

## 结论

- 合法 request 可进入 preflight evaluator。
- 非法 request 在 evaluator 前被阻断，并生成 `contract_validation_blocked` shadow event。
- 本轮只验证本地 pipeline 串联，不接真实 runtime，不进入 enforce mode。

## 后续 TODO

- 将 pipeline 接入真实 runtime 生成的 request 样本做 shadow 验证。
- 将 contract validation 错误纳入 shadow metrics 日报。
- 在 enforce 评审前补足 false positive 和 redaction gap 的人工复核流程。
