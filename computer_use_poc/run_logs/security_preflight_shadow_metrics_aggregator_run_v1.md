# Security Preflight Shadow Metrics Aggregator Run v1

## 本轮目标

读取 `security_preflight_shadow_event_samples.json`，本地聚合 shadow mode 模拟指标，验证后续 runtime shadow event 的可观测性。

## 输入 / 输出

- input: `computer_use_poc/security_preflight_shadow_event_samples.json`
- output: `computer_use_poc/run_logs/security_preflight_shadow_metrics_aggregator_run_v1.md`
- real_runtime_connected: false
- real_platform_called: false
- auth-state category_read: false
- enforce_mode_enabled: false

## 核心指标

| metric | value |
|---|---:|
| total_tool_requests | 15 |
| allow_count | 6 |
| deny_count | 6 |
| require_approval_count | 3 |
| redaction_required_count | 2 |
| shadow_risk_event_count | 8 |
| false_positive_candidate_count | 0 |
| redaction_gap_candidate_count | 1 |
| unknown_capability_count | 1 |
| evaluator_error_count | 1 |
| evaluator_error_like_issue_count | 0 |

## Capability 维度聚合

| capability | total | allow | deny | require_approval | redaction_required | event_types |
|---|---:|---:|---:|---:|---:|---|
| api_direct_read | 1 | 0 | 1 | 0 | 0 | shadow_risk_event:1 |
| browser_dom_read | 1 | 0 | 1 | 0 | 0 | shadow_risk_event:1 |
| device_to_user_resolution | 3 | 1 | 0 | 2 | 0 | none:1, shadow_risk_event:2 |
| login_log_read | 5 | 3 | 1 | 1 | 2 | evaluator_error_event:1, none:2, redaction_gap_candidate:1, shadow_risk_event:1 |
| system_or_logic_modification | 2 | 0 | 2 | 0 | 0 | shadow_risk_event:2 |
| unknown_internal_tool | 1 | 0 | 1 | 0 | 0 | unknown_capability_event:1 |
| user_profile_read | 1 | 1 | 0 | 0 | 0 | none:1 |
| user_to_device_resolution | 1 | 1 | 0 | 0 | 0 | none:1 |

## Enforce Readiness 初步判断

| check | value |
|---|---|
| high_risk_shadow_risk_event_count_is_zero | false |
| unknown_capability_count_is_zero_or_explained | false |
| evaluator_error_count_is_zero | false |
| redaction_gap_candidate_count_is_zero | false |
| require_approval_default_blocking_policy_is_clear | true |
| preliminary_enforce_ready | false |

## 字段 / 格式问题

- none

## 结论

- shadow event samples 可聚合为核心指标和 capability 维度指标。
- 当前模拟样例包含 shadow risk、unknown capability、evaluator error 和 redaction gap，因此不满足 enforce readiness。
- 本轮只验证本地样例可观测性，不进入 enforce mode。
