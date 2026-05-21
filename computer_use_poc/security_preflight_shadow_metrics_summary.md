# Security Preflight Shadow Metrics Summary

## 1. 指标定义

Shadow 阶段指标用于观察 preflight policy 在真实或模拟 tool-call 请求上的表现。指标只用于评估接入质量，不代表已进入 enforce mode。

| 指标 | 含义 | 用途 |
|---|---|---|
| `total_tool_requests` | shadow hook 观察到的 tool_call_request 总数 | 分母指标 |
| `allow_count` | preflight decision 为 allow 的数量 | 观察正常只读请求比例 |
| `deny_count` | preflight decision 为 deny 的数量 | 观察高风险请求、越权请求和敏感输出请求 |
| `require_approval_count` | preflight decision 为 require_approval 的数量 | 观察批量、扩散、直接指定工具等需要审批的请求 |
| `redaction_required_count` | preflight 标记需要脱敏的数量 | 观察敏感字段请求和输出脱敏压力 |
| `shadow_risk_event_count` | preflight 判 deny / require_approval 但真实链路仍执行的数量 | 评估 shadow 阶段的潜在风险 |
| `false_positive_candidate_count` | 正常只读请求被 preflight 判 deny / require_approval 的数量 | 评估误拦候选 |
| `redaction_gap_candidate_count` | preflight 要求脱敏但真实输出仍含敏感字段的数量 | 评估输出脱敏缺口 |
| `unknown_capability_count` | 真实链路调用 policy 未登记 capability 的数量 | 发现未纳管能力 |
| `evaluator_error_count` | evaluator 异常或 policy 不可读的数量 | 评估 preflight 运行稳定性 |

## 2. 派生指标

| 指标 | 计算方式 | 解释 |
|---|---|---|
| `shadow_risk_event_rate` | `shadow_risk_event_count / total_tool_requests` | shadow 阶段被标记为风险但仍继续执行的比例 |
| `false_positive_rate` | `false_positive_candidate_count / total_tool_requests` | 误拦候选比例 |
| `redaction_gap_rate` | `redaction_gap_candidate_count / redaction_required_count` | 脱敏要求未被输出层满足的比例 |
| `unknown_capability_rate` | `unknown_capability_count / total_tool_requests` | 未登记能力调用比例 |
| `evaluator_error_rate` | `evaluator_error_count / total_tool_requests` | evaluator 稳定性风险比例 |

## 3. 进入 enforce mode 的判断条件

进入 enforce mode 前至少满足：

- 高风险漏拦为 0。
- unknown capability 均可解释，并已补 registry / policy 或移除调用路径。
- evaluator error 可控，且 fail closed 策略已验证。
- false positive 可接受，且有人工复核与 policy 修正规则。
- redaction gap 已修复，输出层可稳定执行脱敏。
- `require_approval` 默认阻断策略明确，不能当作 allow。
- audit_event 不包含 cookie / token / session / storageState / raw response。
- shadow mode 覆盖正常只读、批量扩散、直接指定底层工具、任意 URL / JS、prompt exfiltration、系统逻辑修改和敏感字段请求。

## 4. 模拟汇总表

基于 `security_preflight_shadow_event_samples.json` 的 15 条模拟事件，预期聚合如下：

| 指标 | 模拟值 | 说明 |
|---|---:|---|
| `total_tool_requests` | 15 | 15 条 shadow event |
| `allow_count` | 6 | 4 条正常 allow + 2 条 redaction allow |
| `deny_count` | 6 | 任意 URL / JS、凭证明文、系统修改、unknown capability |
| `require_approval_count` | 3 | 扩散、直接指定工具、evaluator error |
| `redaction_required_count` | 2 | 手机号 / IP 脱敏场景 |
| `shadow_risk_event_count` | 8 | deny / require_approval 且 shadow 下仍继续的风险事件 |
| `false_positive_candidate_count` | 0 | 当前样例未设置误拦候选 |
| `redaction_gap_candidate_count` | 1 | 输出前脱敏缺口样例 |
| `unknown_capability_count` | 1 | 未登记 capability |
| `evaluator_error_count` | 1 | evaluator 异常样例 |

说明：

- 模拟值只验证字段和指标是否足够，不代表真实流量分布。
- shadow mode 不阻断真实执行；这些指标用于进入 enforce mode 前的风险评审。
- 如果后续真实 shadow 数据中出现高风险漏拦或大量 redaction gap，不应进入 enforce mode。
