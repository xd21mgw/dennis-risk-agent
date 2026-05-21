# User Login Log Reliable Window Contract v1

## 1. Contract Scope

- capability_name: `login_log_read`
- adapter: `user_login_log_online_api`
- reliable_window_days: 7
- contract_type: `tool_precheck_rule`
- real_platform_called: false
- dataagent_called: false

该 contract 固化统一登录日志在线 API 的可靠窗口口径，避免把超窗查询的 `no_data` / `0 result` 误解释为历史无登录或日志被清理。

## 2. Reliable Window Rule

`login_log_read` 在调用前必须执行 `reliable_window_precheck`。

判断规则：

- 当 `event_time` 或 `query_time_range` 落在近 7 天可靠窗口内：
  - `query_should_execute=true`
  - 在线统一登录日志可作为当前窗口内登录 evidence。
- 当 `event_time` 或 `query_time_range` 超过近 7 天可靠窗口：
  - `query_should_execute=false`
  - 返回 `skipped_due_to_over_window`
  - 标记 `login_log_window_incomplete`
  - 标记 `offline_hive_required`

## 3. Over-window Behavior

超窗时默认不调用在线统一登录日志做事实验证。

必须返回：

- status: `skipped_due_to_over_window`
- evidence_interpretation: `online_login_log_not_reliable_for_requested_historical_window`
- fallback_recommendation: `DataAgent / Hive 或人工离线日志补查`

不得输出：

- “历史无登录”
- “无异设备登录”
- “账号日志被清理”
- “在线 API no_data 支持无风险”
- “在线 API no_data 可作为 counter evidence”

## 4. no_data Interpretation

在线 API `no_data` 只能解释为：

- 当前可靠窗口内，当前查询条件下未见在线日志结果。

在线 API `no_data` 不能解释为：

- 历史无登录。
- 账号无风险。
- 无异设备登录。
- 日志被清理。
- ATO / 黑产矩阵的反证。

## 5. Long-period Login Analysis

需要长周期登录分析时，应转：

- DataAgent / Hive 数仓取数分析。
- 人工离线日志补查。
- 已授权的离线审计链路。

DataAgent 边界：

- DataAgent 只作为 Hive / 数仓取数分析能力。
- 不作为万能风控执行器。
- 不自动处置，不自动封禁。

## 6. Observation Fields

所有涉及 `login_log_read` 的 observation 建议包含：

```yaml
reliable_window_check:
  reliable_window_days: 7
  query_window_start:
  query_window_end:
  is_within_reliable_window:
  over_window:
  query_should_execute:
  skip_reason:
  evidence_interpretation:
  fallback_recommendation:
```

## 7. MCP / Tool Rule Patch

如果后续存在 MCP / tools 配置，应为 `user_login_log_read` 增加：

- precheck: `reliable_window_precheck`
- max_reliable_window_days: 7
- over_window_behavior: `skip_and_return_offline_hive_required`
- no_data_interpretation: `current_window_no_data_only`

该规则当前只沉淀为 tool contract，不接真实 runtime，不调用真实平台。
