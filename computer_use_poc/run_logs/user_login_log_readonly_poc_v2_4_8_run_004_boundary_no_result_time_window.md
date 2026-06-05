# User Login Unified Log Readonly POC v2.4.8 Run 004

## 1. 测试目标

验证用户登录统一日志页面的无结果行为和时间窗口边界行为，避免 Dennis / browser computer use 将“暂无数据”误解释为历史无记录或用户无风险。

## 2. 执行结果

```yaml
test_stage: v2.4.8
platform: user_center_workbench_unified_log_search
validation_target: no_result_and_time_window_behavior
validation_status: boundary_behavior_partially_validated
validated_scope:
  - no_result_empty_state_observed
  - query_condition_retained_after_empty_result
  - no_error_on_empty_result
  - readonly_safety_passed
  - frontend_time_picker_allows_over_7_days
  - over_7_days_query_returns_empty_without_limit_prompt
risk_discovered:
  - page_does_not_explicitly_warn_realtime_window_limit
  - over_7_days_empty_result_may_be_misread_as_historical_no_record
  - frontend_selectable_range_is_wider_than_reliable_data_window
pending_scope:
  - backend_actual_retention_window
  - whether_over_7_days_result_is_backend_truncated_or_true_empty
  - pagination_behavior
  - permission_blocked_behavior
```

## 3. No Result Behavior

```yaml
no_result_behavior:
  query_condition:
    user_id_policy: synthetic_nonexistent_test_id
    log_sources: all_checked
    time_range: page_default_not_manually_changed
  result_status: query_success_empty_result
  empty_state_text: 暂无数据
  error_message: none
  loading_issue: none
  query_condition_retained: true
  correct_interpretation: 当前查询条件下最近 7 天实时页面无结果
  forbidden_interpretation:
    - 用户无风险
    - 用户无登录记录
    - 全量无记录
```

说明：

- 测试输入使用 synthetic nonexistent user_id，不记录具体测试 ID 明文。
- 页面查询成功，表格显示“暂无数据”，无错误提示。
- “暂无数据”只能解释为当前查询条件下的实时页面无结果。

## 4. Time Window Behavior

```yaml
time_window_behavior:
  manual_time_change_attempted: true
  over_7_days_selectable: true
  platform_limit_text: none
  query_result: empty_result
  empty_state_text: 暂无数据
  error_message: none
  auto_truncate_observed: false
  reliable_window_assumption: default_recent_7_days_only
  correct_interpretation: 超出实时页面可靠窗口，需要转 DataAgent / Hive 或离线日志能力
  required_fallback:
    - DataAgent / Hive
    - 离线日志能力
  forbidden_interpretation:
    - 超过 7 天无记录
    - 历史无登录
    - 全量无风险
```

关键发现：

- 时间控件前端允许选择超过最近 7 天的历史时间。
- 超过 7 天查询可以执行，但返回“暂无数据”，页面无明确限制提示。
- 当前 POC 只能将默认最近 7 天作为实时页面可靠查询窗口。
- 超窗“暂无数据”不能解释为历史无记录或全量无风险。

## 5. 只读安全

```yaml
readonly_safety_check:
  export_clicked: false
  safe_json_summary_copied: false
  write_action_performed: false
  credential_raw_value_output: false
  passed: true
```

## 6. 当前结论

用户登录统一日志的无结果行为已部分验证：页面会稳定显示“暂无数据”，查询条件保留且无错误提示。时间窗口边界存在误判风险：前端可选择超过最近 7 天，但该范围不是当前 POC 的可靠实时查询窗口，超窗空结果必须降级解释并建议 DataAgent / Hive 或离线日志补证。
