# 档案中心 Focused Login Risk Run 001

## 1. 测试目标

验证 v2.4.5.1 `focused_login_risk` mode 是否可以在只读边界下，完成档案中心用户信息 Tab + 用户分析 Tab 的结构化提取。

本次验证重点：

- 快速进入用户详情页。
- 读取用户信息 Tab。
- 读取用户分析 Tab。
- 记录实际 time_range。
- 完成 table_schema_probe。
- 不把前 3 条样例当作完整登录日志研判。

## 2. 执行摘要

```yaml
execution_mode: focused_login_risk
target_duration: 3-5min
actual_duration: 103s
extraction_strategy:
  - state_load
  - open
  - semantic_wait
  - partial_eval
  - find_click
  - scoped_snapshot
tabs_requested:
  - user_info_tab
  - user_analysis_tab
tabs_observed:
  - user_info_tab
  - user_analysis_tab
state_reuse_status: SUCCESS
redirect_detected: false
login_required: false
spa_render_status: FULLY_RENDERED
readonly_safety_check: PASSED
```

## 3. time_range_policy

```yaml
time_range_policy:
  actual_start: redacted_or_relative
  actual_end: redacted_or_relative
  source: auto_populated
  adjusted_by_agent: false
```

说明：

- 本次记录页面自动填充的实际时间范围。
- 未主动调整为近 1 年。
- 只能表述为“当前页面时间范围下的观察”。

## 4. list_sample_policy

```yaml
list_sample_policy:
  max_rows_observed: 3
  values_policy: redacted
  purpose: infer_table_schema_only
```

边界：

- 前 3 条只用于字段结构识别。
- 不用于完整登录日志研判。
- 不输出手机号、IP、设备 ID、open_id、sig、token、请求参数等明文。

## 5. user_info_tab

```yaml
user_info_tab:
  tab_status: fully_loaded
  sections_extracted: true
  device_relation_entries_extracted: true
  write_action_button_semantics_grouped: true
  operator_account_policy: operator_identity_redacted
  sensitive_values_policy: redacted
```

## 6. user_analysis_tab

```yaml
user_analysis_tab:
  tab_status: fully_loaded
  operation_type_filter_visible: true
  sub_tabs_visible: true
  list_or_table_present: true
  table_schema_probe:
    status: validated
    max_rows_observed: 3
    values_policy: redacted
    purpose: infer_table_schema_only
  risk_event_scan:
    status: pending
    reason: full risk_event_scan aggregation not completed in this run
  selector_profile:
    table_structure: non_standard
    extraction_method: mixed
    fallback_used: true
  selector_issue: non_standard_table_structure
```

重要发现：

- 用户分析 Tab 的表格不是标准 ant-table 结构。
- 初始 eval 选择器未命中。
- 后续通过语义点击 + scoped snapshot 确认数据完整。
- 下一步需要为 `user_analysis_tab` 增加专属 selector / fallback extraction。

## 7. readonly_safety_check

```yaml
readonly_safety_check:
  status: PASSED
  no_write_action_clicked: true
  no_submit_clicked: true
  no_approval_clicked: true
  no_export_clicked: true
  no_batch_download_clicked: true
  sensitive_values_recorded: false
  operator_account_recorded: false
```

## 8. 当前结论

```yaml
conclusion: focused_login_risk_structure_extraction_validated
full_risk_event_scan: pending
```

本次只能结论为：

- `focused_login_risk` 结构提取已验证。
- 用户分析 Tab 字段结构探测已验证。
- full risk_event_scan 聚合摘要仍待验证。

不得结论为：

- 完整登录风险研判已完成。
- ATO / 协议上号风险已完成判断。
- 前 3 条样例覆盖完整日志。
- 自动研判已完成。
