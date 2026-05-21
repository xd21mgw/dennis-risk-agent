# Security Preflight Tool Call Request Contract Run v1

## 本轮目标

沉淀 `tool_call_request` 字段契约，为后续接入内部 Agent runtime 做准备，减少字段缺失、字段命名不一致、scope 表达不一致导致的 `evaluator_error_like_issue`。

本轮不进入 enforce mode，不接真实 runtime，不接真实内部平台，不调用真实 API，不读取认证态，不更新 release / dist，不提交 git。

## 新增文件

- `computer_use_poc/security_preflight_tool_call_request_contract.md`
- `computer_use_poc/run_logs/security_preflight_tool_call_request_contract_run_v1.md`

## 修改文件

- `computer_use_poc/smoke_tests.md`

## 字段契约摘要

标准 `tool_call_request` 字段包括：

- `request_id`
- `operator`
- `user_input_summary`
- `normalized_intent`
- `scene`
- `capability_name`
- `input_entities`
- `input_entity_count`
- `requested_fields`
- `requested_scope`
- `requested_time_range`
- `direct_tool_requested_by_user`
- `attempts_to_override_policy`
- `requested_raw_output`
- `source_agent`
- `runtime_mode`

核心原则：

- 模型只能提交 request，不能自己决定 `allow` / `deny`。
- `capability_name` 必须来自 `security_preflight_policy.yaml`。
- `requested_scope` 必须使用标准枚举。
- 敏感实体和敏感字段必须显式标注。
- 缺字段不能静默 allow。

## Capability 映射摘要

已给出 request 示例的 capability：

- `user_profile_read`
- `login_log_read`
- `user_to_device_resolution`
- `device_to_user_resolution`
- `device_risk_read`
- `strategy_hit_read`
- `frontend_activity_read`
- `api_direct_read`
- `browser_dom_read`

## 缺失字段处理策略

- 缺 `request_id`：生成临时 id，并记录 `field_missing_warning`。
- 缺 `capability_name`：deny。
- 缺 `requested_scope`：`unknown` => require_approval 或 deny。
- 缺 `requested_fields`：只允许 safe summary。
- 缺 `input_entities`：根据场景 require clarification 或 deny。
- 字段类型错误：fail closed。

## 未做事项

- 未修改 evaluator 运行逻辑。
- 未接 runtime。
- 未接真实内部平台。
- 未调用真实 API。
- 未读取认证态。
- 未进入 enforce mode。
- 未更新 release / dist。

## 后续 TODO

- 在 runtime tool-call 构造层按本 contract 输出 request。
- 为缺字段 / 类型错误补本地 validator 或 evaluator 扩展。
- 将 `evaluator_error_like_issue` 纳入 shadow metrics 日报。
- 接入 runtime 前用真实 request 样本做字段完整性 dry-run。
