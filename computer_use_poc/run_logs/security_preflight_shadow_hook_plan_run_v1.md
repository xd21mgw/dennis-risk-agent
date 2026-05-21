# Security Preflight Shadow Hook Plan Run v1

## 本轮目标

设计 preflight shadow hook 接入方案，说明后续如何把 `security_preflight_evaluator.py` 接到内部 Agent tool-call 生成点，以旁路方式记录 preflight 判断结果。

本轮不进入 enforce mode，不接真实内部平台，不调用真实 API，不读取认证态，不更新 release / dist，不提交 git。

## 新增文件

- `computer_use_poc/security_preflight_shadow_hook_plan.md`
- `computer_use_poc/run_logs/security_preflight_shadow_hook_plan_run_v1.md`

## 修改文件

- `computer_use_poc/smoke_tests.md`

## 设计摘要

推荐接入点：

- `tool_call_request` 构造完成后。
- tool 实际执行前。
- response 输出前做 redaction check。

核心流程：

用户输入
→ 主 Agent 识别意图
→ 选择 capability
→ 构造 `tool_call_request`
→ shadow preflight evaluator
→ 记录 `shadow_preflight_result`
→ 原工具链路继续执行
→ 输出前敏感字段检查
→ 写入 shadow run log / audit_event

风险事件：

- `shadow_risk_event`：preflight 判 `deny` / `require_approval`，但真实链路仍执行。
- `false_positive_candidate`：正常只读请求被误判为 `deny` / `require_approval`。
- `redaction_gap_candidate`：preflight 要求脱敏，但真实输出仍含敏感字段。
- `unknown_capability_event`：真实链路调用了 policy 未登记 capability。
- `evaluator_error_event`：evaluator 异常或 policy 不可读。

观察指标：

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

## 不做事项

- 不进入 enforce mode。
- 不阻断真实执行。
- 不接真实审批系统。
- 不接真实审计落库。
- 不接真实内部平台。
- 不调用真实 API。
- 不读取认证态。
- 不更新 release / dist。

## 后续 TODO

- 在内部 Agent tool-call 生成点添加 shadow hook。
- 将 `shadow_preflight_result` 写入安全审计或 shadow run log。
- 输出前增加脱敏缺口检测。
- 聚合 shadow mode 指标。
- 基于误拦 / 漏拦结果修正 policy。
- 单独评审 enforce mode，不自动开启。
