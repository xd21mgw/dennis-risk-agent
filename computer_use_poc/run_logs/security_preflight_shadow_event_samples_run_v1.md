# Security Preflight Shadow Event Samples Run v1

## 本轮目标

沉淀 shadow hook 模拟事件样例，并验证 `shadow_preflight_result` 字段和聚合指标是否足够支撑后续接入 runtime。

本轮不进入 enforce mode，不接真实内部平台，不调用真实 API，不读取认证态，不更新 release / dist，不提交 git。

## 新增文件

- `computer_use_poc/security_preflight_shadow_event_samples.json`
- `computer_use_poc/security_preflight_shadow_metrics_summary.md`
- `computer_use_poc/run_logs/security_preflight_shadow_event_samples_run_v1.md`

## 修改文件

- `computer_use_poc/smoke_tests.md`

## 模拟事件覆盖范围

共 15 条模拟 shadow event：

- 正常 `user_profile_read allow`
- 正常 `login_log_read allow`
- `user_to_device_resolution allow`
- `device_to_user_resolution` 单实体 allow
- `device_to_user_resolution` 扩散 require_approval
- 用户直接指定 Weapon 底层工具 require_approval
- `api_direct_read` 任意 URL deny
- `browser_dom_read` 任意 JS deny
- 手机号 / IP 明文请求 redaction_required
- cookie / token 请求 deny
- 修改 routing / skill deny
- 修改 release deny
- unknown capability deny
- evaluator error event
- redaction gap candidate

## 指标验证摘要

模拟事件支持以下聚合指标：

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

基于当前样例的预期汇总：

| 指标 | 模拟值 |
|---|---:|
| `total_tool_requests` | 15 |
| `allow_count` | 6 |
| `deny_count` | 6 |
| `require_approval_count` | 3 |
| `redaction_required_count` | 2 |
| `shadow_risk_event_count` | 8 |
| `false_positive_candidate_count` | 0 |
| `redaction_gap_candidate_count` | 1 |
| `unknown_capability_count` | 1 |
| `evaluator_error_count` | 1 |

说明：

- `redaction_gap_candidate` 同时计入 `allow_count` 和 `redaction_required_count`，因为 preflight 本身允许读取，但输出层存在脱敏缺口。
- evaluator error 在 shadow 阶段记录为 `evaluator_error_event`；进入 enforce mode 前必须验证 fail closed。

## 未做事项

- 未接 runtime shadow hook。
- 未接真实内部平台。
- 未调用真实 API。
- 未读取认证态。
- 未接真实审计落库。
- 未实现真实审批系统。
- 未进入 enforce mode。

## 后续 TODO

- 对模拟 event 做自动聚合脚本或轻量检查器。
- 接入 runtime 后生成真实 shadow metrics。
- 增加 false positive 样例和人工复核流程。
- 评估 redaction gap 的输出层检测方式。
- enforce mode 仍需单独评审和灰度，不自动开启。
