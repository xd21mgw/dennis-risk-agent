# Security Preflight Shadow Mode Design Run v1

## 本轮目标

在 capability security preflight dry-run 通过后，设计 shadow mode 接入方案。

本轮只做设计文档和 schema，不接真实内部平台、不调用真实 API、不读取认证态、不实现真实审批系统、不实现真实审计落库、不更新 release / dist。

## 新增文件

- `computer_use_poc/security_preflight_shadow_mode_design.md`
- `computer_use_poc/run_logs/security_preflight_shadow_mode_design_run_v1.md`

## 修改文件

- `computer_use_poc/smoke_tests.md`

## Shadow Mode 设计摘要

三种运行模式：

- `dry_run`：只跑本地测试样例，不接真实工具。
- `shadow_mode`：对真实或模拟 `tool_call_request` 旁路判断并记录结果，不阻断真实执行。
- `enforce_mode`：preflight 结果决定是否允许工具调用。

shadow mode 运行逻辑：

1. Agent 生成 `tool_call_request`。
2. evaluator 读取 `security_preflight_policy.yaml`。
3. evaluator 输出 `preflight_result`。
4. shadow mode 记录 `allow` / `deny` / `require_approval` / `redact` 判断。
5. shadow mode 暂不阻断真实执行。
6. 如果 `deny` / `require_approval` 但真实链路仍执行，记录 `shadow_risk_event`。
7. 如果正常只读请求被误判，记录 `false_positive_candidate`。

## Enforce Mode 切换条件

进入 enforce mode 前至少需要：

- prompt injection 文本回归通过。
- security preflight dry-run case 通过。
- shadow mode 覆盖足够 case。
- 没有高风险漏拦。
- false positive 可接受。
- `require_approval` 默认阻断策略明确。
- audit_event 不包含 raw sensitive data。
- unknown capability deny 已验证。
- evaluator 异常 fail closed 已验证。
- redaction 失败不输出敏感字段已验证。

## 已知限制

- 当前没有真实审批系统。
- 当前没有真实审计落库。
- 当前没有接内部 Agent runtime。
- 当前没有阻断真实平台工具调用。
- 当前没有 release / dist 同步。

## 后续 TODO

- 在内部 Agent 执行层加入 shadow mode hook。
- 将 preflight_result 与真实工具调用结果做旁路比对。
- 定期汇总 `shadow_risk_event`、`false_positive_candidate`、`redaction_gap_candidate`。
- 完善 policy 字段集、scope 分类和 capability 覆盖。
- 在审批系统和审计落库完成后，再评估 enforce mode。
