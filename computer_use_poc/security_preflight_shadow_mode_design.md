# Security Preflight Shadow Mode Design

## 1. 目标

将 `security_preflight_evaluator.py` 从本地 dry-run 推进到 shadow mode。

目标：

- evaluator 对真实或模拟 `tool_call_request` 做结构化判断。
- shadow mode 只旁路记录，不阻断真实执行。
- 观察误拦、漏拦、policy 缺口和字段缺失。
- 为后续 enforce mode 做数据准备。

非目标：

- 不接真实内部平台。
- 不调用真实 API。
- 不读取认证态。
- 不实现真实审批系统。
- 不实现真实审计落库。
- 不更新 release / dist。

## 2. 三种模式定义

### dry_run

本地测试模式。

- 输入来源：`security_preflight_test_cases.json`。
- 执行动作：只跑本地样例。
- 工具调用：不调用真实工具。
- 输出：dry-run result 和 run log。
- 用途：验证 evaluator 与结构化 policy 的基础逻辑。

### shadow_mode

旁路观察模式。

- 输入来源：真实或模拟的 `tool_call_request`。
- 执行动作：evaluator 输出 `allow` / `deny` / `require_approval` / `redact` 判断。
- 工具调用：shadow mode 暂不阻断真实链路。
- 输出：preflight_result、audit_event、shadow_risk_event / false_positive_candidate。
- 用途：观察 policy 与真实请求之间的差距，评估误拦和漏拦。

### enforce_mode

强制拦截模式。

- 输入来源：真实 `tool_call_request`。
- 执行动作：preflight_result 决定是否允许工具调用。
- 工具调用：
  - `allow`：可继续。
  - `deny`：不得继续。
  - `require_approval`：没有真实审批通过前不得继续。
  - `redact`：可继续读取，但输出必须执行脱敏策略。
- 用途：正式运行时安全闸门。

## 3. tool_call_request schema

```yaml
tool_call_request:
  request_id:
  operator:
  user_input_summary:
  normalized_intent:
  scene:
  capability_name:
  input_entities:
    - type:
      value:
  requested_fields:
  requested_scope:
  requested_time_range:
  direct_tool_requested_by_user:
  attempts_to_override_policy:
  requested_raw_output:
  source_agent:
  runtime_mode: dry_run / shadow_mode / enforce_mode
```

字段说明：

- `request_id`：单次请求唯一 ID。
- `operator`：执行主体或内部 Agent 标识。
- `user_input_summary`：用户输入摘要，不记录敏感原文。
- `normalized_intent`：归一化意图。
- `scene`：场景，如 login_investigation / entity_resolution。
- `capability_name`：必须为 registry / policy 中登记的 capability。
- `input_entities`：结构化实体，不写入 cookie / token / browser_storage_state_marker。
- `requested_fields`：请求字段集合。
- `requested_scope`：single_entity / batch / expansion / write / system_modification 等。
- `requested_time_range`：查询时间窗口摘要。
- `direct_tool_requested_by_user`：用户是否直接指定底层工具。
- `attempts_to_override_policy`：是否存在绕过规则、管理员伪装等提示词注入。
- `requested_raw_output`：是否请求原始响应或完整 JSON。
- `source_agent`：生成该请求的 Agent。
- `runtime_mode`：当前运行模式。

## 4. preflight_result schema

```yaml
preflight_result:
  decision: allow / deny / require_approval
  tool_call_allowed:
  policy_flags:
  denial_reasons:
  approval_reasons:
  redaction_required:
  fields_to_redact:
  allowed_fields:
  audit_event:
  recommended_runtime_action:
```

`recommended_runtime_action` 规则：

- dry_run：
  - `allow`：record_only。
  - `deny`：record_denial。
  - `require_approval`：record_approval_needed。
- shadow_mode：
  - `allow`：observe_and_continue。
  - `deny`：record_shadow_risk_event_and_continue。
  - `require_approval`：record_shadow_risk_event_and_continue。
  - `redaction_required=true`：record_redaction_requirement。
- enforce_mode：
  - `allow`：continue_tool_call。
  - `deny`：block_tool_call。
  - `require_approval`：block_until_approval。
  - `redaction_required=true`：continue_with_output_redaction。

## 5. shadow mode 运行逻辑

1. Agent 根据用户问题生成 `tool_call_request`。
2. evaluator 读取 `security_preflight_policy.yaml`。
3. evaluator 输出 `preflight_result`。
4. shadow mode 只记录判断结果，不阻断真实执行。
5. 如果 evaluator 输出 `deny` / `require_approval`，但真实链路仍执行，记录为 `shadow_risk_event`。
6. 如果正常只读请求被 evaluator 判为 `deny` / `require_approval`，记录为 `false_positive_candidate`。
7. 如果真实执行输出包含敏感字段，而 evaluator 已标记 `redaction_required`，记录为 `redaction_gap_candidate`。
8. shadow mode 结果定期汇总，用于修正 policy、字段集合和 capability scope。

shadow mode 事件示例：

```yaml
shadow_risk_event:
  request_id:
  capability_name:
  preflight_decision:
  real_chain_continued:
  policy_flags:
  risk_type:
  review_needed:
```

```yaml
false_positive_candidate:
  request_id:
  capability_name:
  preflight_decision:
  expected_safe_reason:
  policy_flags:
  suggested_policy_fix:
```

## 6. enforce mode 切换条件

进入 enforce mode 前至少满足：

- prompt injection 文本回归通过。
- security preflight dry-run case 通过。
- shadow mode 覆盖足够 case，包含正常只读、敏感字段、批量扩散、越权工具、prompt 注入、写动作、系统逻辑修改。
- 未发现高风险漏拦。
- false positive 处于可接受范围，且有明确人工复核口径。
- `require_approval` 默认阻断策略明确。
- audit_event 不包含 cookie / token / session / raw result / browser_storage_state_marker 等敏感原文。
- unknown capability 默认 deny 已验证。
- evaluator 异常 fail closed 已验证。
- redaction 失败时不输出敏感字段的策略已验证。

## 7. require_approval 默认处理

在没有真实审批系统前：

- enforce mode 下 `require_approval` 默认不执行工具调用。
- Agent 可返回“需要审批 / 人工确认 / 缩小范围”的响应。
- `require_approval` 不能当作 `allow`。
- 审批通过前不得执行批量扩散、关联多跳、导出明细或敏感字段读取。

## 8. 审计边界

audit_event 只能记录摘要和引用：

- 可记录：request_id、capability、scope、policy_flags、approval_status、tool_status、result_count、output_summary。
- 不记录：cookie、token、session、browser_storage_state_marker、source response summary、完整 header、完整请求参数、完整工具返回。
- `source_result_reference` 只能是内部安全引用，不能包含敏感原文。
- audit_event 用于复盘、问责、权限排查和安全评估，不作为敏感数据二次存储。

## 9. 失败 / 降级策略

- evaluator 异常时默认 fail closed：`deny` 或 `require_approval`。
- policy 缺失时：unknown capability => `deny`。
- policy 文件不可读时：`deny` 或进入人工复核，不允许继续真实工具调用。
- redaction 失败时：不输出敏感字段。
- audit_event 生成失败时：不得进入 enforce allow。
- shadow mode 下 evaluator 异常需记录 `preflight_evaluator_error`，并进入人工复核队列。

## 10. 当前边界

- 当前只完成 dry-run evaluator 和 shadow mode 设计。
- 尚未接内部 Agent runtime。
- 尚未接真实审批。
- 尚未接审计落库。
- 尚未对真实平台请求做阻断。
- 不更新 release / dist。
