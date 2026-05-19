# Archives Center Focused Login Risk Event Scan Run 001

## 1. 测试目标

验证档案中心 `focused_login_risk` 模式下，用户分析 Tab 的 `risk_event_scan` 是否能在只读、安全、脱敏边界内生成登录风险相关派生摘要。

本轮目标不是自动风险定性，也不是 full validated。重点验证：

- 是否能读取用户分析 Tab 当前时间范围内的日志结构。
- 是否能生成操作类型、成功失败、关键事件序列、一致性判断等派生摘要。
- 是否遵守敏感字段执行态可读、沉淀态脱敏策略。
- 是否识别 selector 噪声和覆盖限制。

## 2. 执行摘要

```yaml
execution_mode: focused_login_risk
scan_type: risk_event_scan
actual_duration: 156s
state_reuse_status: SUCCESS
spa_render_status: FULLY_RENDERED
readonly_safety_check: PASSED
```

## 3. 敏感字段策略

```yaml
sensitive_runtime_evidence_policy:
  raw_value_access: runtime_allowed_for_risk_judgment
  raw_value_persistence: false
  raw_value_display: false
  derived_feature_output: true
```

执行态可读字段包括 IP、设备、手机号、open_id、APP 版本、地理位置等，用于生成派生判断。

沉淀态不输出 IP、设备 ID、手机号、open_id、token、请求参数、cookie、session、KIM code、操作者身份等明文。

## 4. 用户分析 Tab 结果

```yaml
user_analysis_tab:
  table_structure: ks-table__row
  extraction_method: js_eval + ks-table__row selector
  fallback_used: true
  risk_event_scan:
    status: partial_validated_with_selector_noise
  operation_type_counts: recorded_without_raw_values
  success_failure_counts: recorded_without_raw_values
  earliest_event_time: recorded_without_raw_values
  latest_event_time: recorded_without_raw_values
  login_method_sequence: derived_summary_only
  ip_consistency: derived_summary_only
  geo_consistency: derived_summary_only
  device_consistency: derived_summary_only
  app_version_consistency: derived_summary_only
  third_party_login_visible: recorded_without_raw_values
  phone_or_binding_event_visible: recorded_without_raw_values
  key_event_sequence: derived_summary_only
  suspicious_event_markers: derived_summary_only
  pagination_required: recorded
  coverage_limitations: recorded
```

## 5. 重要发现

1. 用户分析 Tab 表格使用 `ks-table__row`，不是标准 `ant-table`。
2. 用户信息 Tab 与用户分析 Tab 的表格行会在同一页面 DOM 中共存。
3. 当前 `risk_event_scan` 已能生成有效派生摘要。
4. 当前 selector 存在噪声：用户信息 Tab 的表格行可能混入用户分析日志行。
5. 后续需要按 active tab container 或 row feature 做过滤。

## 6. 当前结论

```yaml
current_status: partial_validated_with_selector_noise
full_validated: false
reason: risk_event_scan can produce derived summaries, but selector noise is not fully removed.
```

本轮可以证明 `focused_login_risk` 的 `risk_event_scan` 已具备派生摘要能力，但不能写成 full validated。

## 7. 下一步

优先做 selector noise 修正实跑：

1. 优先定位 active user_analysis tab container。
2. 增加 row feature filter。
3. 排除用户信息 Tab 中的平台操作、直播功能、电商功能等非日志表格行。
4. 修正后再评估是否可标记 full validated。

