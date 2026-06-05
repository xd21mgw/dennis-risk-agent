# User Login Unified Log Readonly POC v2.4.8 Run 001

## 1. 测试目标

验证用户中心智能工作台 / 账号问题排查 / 统一日志查询页面的只读可访问性、认证态复用、基础表单查询、默认日志来源 checkbox、结果表可见性和只读安全边界。

## 2. 执行结果

```yaml
test_stage: v2.4.8
platform: user_center_workbench_unified_log_search
validation_status: partially_validated
validated_scope:
  - page_accessibility
  - auth-state category_reuse
  - basic_form_query
  - default_log_source_checkbox
  - result_table_visibility
  - readonly_safety_without_detail_modal
pending_scope:
  - explicit_time_range_value_visibility
  - detail_modal_readonly_observation
  - oauth_qr_field_visibility
  - token_session_redaction_in_detail
  - pagination_behavior
  - no_result_behavior
  - permission_blocked_behavior
```

## 3. 查询条件

```yaml
query_conditions:
  query_object: user_id
  query_value_policy: redacted_in_long_term_docs
  did: empty
  keyword: empty
  log_source_checkboxes: all_4_checked_by_default
  time_selection: page_default_used
```

## 4. 时间范围观察

```yaml
time_range_observation:
  explicit_time_value_visible: false
  start_button_text: choose_start_time
  end_button_text: choose_end_time
  source: auto_populated_or_backend_default
  default_recent_7_days: observed_by_query_result
  returned_data_time_span: derived_feature_only
```

说明：

- 页面按钮没有显式展示具体 start_time / end_time。
- 未手动选择时间，也能查出近 7 天内数据。
- 不能写成“UI 明确展示最近 7 天”。
- 超过最近 7 天仍需转 DataAgent / Hive 或离线日志能力。

## 5. 结果表观察

```yaml
result_table_observation:
  page_status: loaded_with_results
  total_records_current_page: 10
  table_headers:
    - 时间
    - 标签
    - User ID
    - DID
    - Method
    - 日志来源
    - 日志内容
  pagination:
    current_page: 1
    page_size: 20
    prev: disabled
    next: disabled
```

## 6. 派生特征

```yaml
derived_features:
  operation_type_distribution:
    refresh_token_success: 6
    app_switch_account_success: 4
  log_source_distribution:
    account_middle_platform_login_logs: 6
    growth_login_logs: 4
  device_consistency: same_android_device
  time_span: about_16_hours
  key_observations:
    - all_records_from_same_android_device
    - no_login_failure_observed
    - refresh_token_and_switch_account_alternate
    - app_switch_account_success_observed_4_times
    - no_observed_geo_or_device_drift_in_result_table
```

## 7. 只读安全

```yaml
readonly_safety_check: PASSED
sensitive_fields_policy:
  did: redacted
  token field  never_collect
  session field  never_collect
  detail_json: not_opened
  copy_button_clicked: false
```

已遵守：

- 未点击详情弹窗。
- 未复制完整 JSON。
- 未输出 DID 明文。
- 未采集 token / session。
- 未点击导出、批量下载、处置类按钮。

Clarification note:

- 本 run log 里的 `did: redacted` 是当时的保守沉淀口径，不应扩展解释为“DID / deviceId 不能参与风控判断”。
- v2.4.8 后续统一字段策略已修正为：userId、DID / deviceId、IP、UA、appVer、sysVer、登录时间、token/session 生命周期时间等均属于风控分析字段，应保留用于证据解释。
- 仅 token、accessToken、refreshToken、session、sessionId、ticket、authorization、cookie 等认证凭证明文需要隐藏 raw value。

## 8. 限制

- 详情弹窗尚未验证。
- OAuth / 扫码字段可见性尚未验证。
- token / session detail redaction 尚未验证。
- 分页行为尚未验证。
- 无结果行为尚未验证。
- 权限阻断行为尚未验证。
- 当前仅为页面可访问性与基础查询 partially validated。

## 9. 推荐下一步

1. 进入 detail modal readonly observation 实跑。
2. 验证 token/session 字段只记录可见性、不输出明文。
3. 验证超过最近 7 天的 time_range 行为。
4. 验证无结果 / 权限阻断 / 分页行为。
