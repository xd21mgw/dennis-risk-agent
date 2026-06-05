# Security Preflight Shadow Hook Plan

## 1. 目标

将 preflight evaluator 从纯 dry-run 推进到 shadow hook。

目标：

- 在 Agent 生成 `tool_call_request` 后、真实 tool 执行前，旁路调用 evaluator。
- shadow mode 只记录判断结果，不阻断真实执行。
- 观察误拦、漏拦、脱敏缺口和 `require_approval` 风险。
- 为后续 enforce mode 评审提供真实运行样本。

非目标：

- 不进入 enforce mode。
- 不接真实内部平台。
- 不调用真实 API。
- 不读取认证态。
- 不实现真实审批系统。
- 不实现真实审计落库。
- 不更新 release / dist。

## 2. 推荐接入点

理想接入点有三处：

1. `tool_call_request` 构造完成后。
   - 此时 capability、实体、字段、范围、时间窗口已经结构化。
   - evaluator 可以稳定读取同一份 request。

2. tool 实际执行前。
   - shadow mode 只旁路判断并记录。
   - 当前阶段不阻断真实执行。
   - 后续 enforce mode 可在此处切换为阻断点。

3. response 输出前。
   - 对 evaluator 标记的 `redaction_required` 做输出前复核。
   - 如果真实输出仍包含敏感字段，记录 `redaction_gap_candidate`。

## 3. 核心流程

文字流程：

用户输入
→ 主 Agent 识别意图
→ 选择 capability
→ 构造 `tool_call_request`
→ shadow preflight evaluator
→ 记录 `shadow_preflight_result`
→ 原工具链路继续执行
→ 输出前敏感字段检查
→ 写入 shadow run log / audit_event

关键要求：

- 模型只能提交 `tool_call_request`，不能自己决定跳过 preflight。
- shadow hook 不改变本轮工具执行结果。
- shadow hook 的风险事件必须可回放、可聚合。
- 输出前检查不应记录敏感原文，只记录字段类型和脱敏状态。

## 4. shadow_preflight_result 字段

```yaml
shadow_preflight_result:
  request_id:
  capability_name:
  decision: allow / deny / require_approval
  policy_flags:
  denial_reasons:
  approval_reasons:
  redaction_required:
  fields_to_redact:
  shadow_risk_event:
  false_positive_candidate:
  redaction_gap_candidate:
  recommended_runtime_action:
```

字段说明：

- `request_id`：与 `tool_call_request.request_id` 对齐。
- `capability_name`：本次拟调用能力。
- `decision`：evaluator 判断。
- `policy_flags`：命中的策略标记。
- `denial_reasons`：拒绝原因。
- `approval_reasons`：审批原因。
- `redaction_required`：是否需要输出脱敏。
- `fields_to_redact`：需要脱敏的字段名。
- `shadow_risk_event`：preflight 判高风险但真实链路仍继续。
- `false_positive_candidate`：疑似误拦候选。
- `redaction_gap_candidate`：输出脱敏缺口候选。
- `recommended_runtime_action`：shadow 下仅记录，enforce 下才可阻断。

## 5. 风险事件定义

### shadow_risk_event

preflight 判定为 `deny` 或 `require_approval`，但真实链路仍执行。

典型场景：

- 用户直接指定底层工具。
- 任意 URL / API 请求。
- 批量扩散请求。
- 写动作或系统逻辑修改请求。
- 请求 raw output / full JSON。

### false_positive_candidate

正常只读请求被 preflight 判为 `deny` 或 `require_approval`。

典型场景：

- capability scope 过窄。
- 字段命名误触发 denied field。
- entity_count 统计口径错误。
- 场景需要补充 allowlist。

### redaction_gap_candidate

preflight 要求脱敏，但真实输出仍含敏感字段。

典型场景：

- 输出包含 cookie / token / session / browser_storage_state_marker。
- 输出包含手机号、精确 IP、完整 device fingerprint。
- 输出包含完整 requestParam / extraParam / source response summary。

### unknown_capability_event

真实链路调用了 policy 未登记 capability。

处理口径：

- shadow mode 记录事件。
- enforce mode 下应 deny。
- 需要补 registry / policy，或移除未登记调用路径。

### evaluator_error_event

evaluator 异常或 policy 不可读。

处理口径：

- shadow mode 记录异常并进入人工复核。
- enforce mode 下必须 fail closed：deny 或 require_approval。

## 6. Shadow 阶段观察指标

建议按天 / 周聚合：

- `total_tool_requests`
- `allow_count`
- `deny_count`
- `require_approval_count`
- `redaction_required_count`
- `shadow_risk_event_count`
- `false_positive_candidate_count`
- `redaction_gap_candidate_count`
- `unknown_capability_count`
- `evaluator_error_count`

衍生指标：

- `shadow_risk_event_rate = shadow_risk_event_count / total_tool_requests`
- `false_positive_rate = false_positive_candidate_count / total_tool_requests`
- `redaction_gap_rate = redaction_gap_candidate_count / redaction_required_count`
- `unknown_capability_rate = unknown_capability_count / total_tool_requests`

## 7. 不进入 enforce 的边界

本轮和 shadow 阶段不阻断真实执行。

边界：

- 不把 shadow mode 自动切换为 enforce mode。
- 不因单个 shadow case 直接修改生产行为。
- 不把 `require_approval` 当作 allow。
- 不把 shadow 记录当作真实审批。
- enforce mode 需要单独评审、单独变更、单独灰度。

## 8. 与 readonly runtime config 的关系

shadow hook 是 Agent 内部安全判断。

readonly runtime config 是平台侧工具隔离。

两者互补，不互相替代：

- shadow hook 判断“这次 capability 请求是否符合策略”。
- readonly runtime config 限制“工具运行环境是否允许写、改、执行危险动作”。
- 即使 shadow hook 漏判，平台侧仍应限制 write / edit / exec / gateway / subagents 等危险工具。
- 即使 runtime config 是只读，Agent 仍需要 shadow hook 观察 prompt injection、越权工具选择、敏感字段输出和批量扩散风险。

## 9. 后续接入建议

建议顺序：

1. 在内部 Agent tool-call 生成点添加 shadow hook。
2. 只记录 preflight_result，不阻断。
3. 输出前增加敏感字段检查。
4. 聚合 shadow 指标。
5. 评审误拦 / 漏拦 / 脱敏缺口。
6. 再设计 enforce mode 灰度，不自动开启。
