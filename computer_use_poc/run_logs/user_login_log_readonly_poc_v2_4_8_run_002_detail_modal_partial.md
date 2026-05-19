# User Login Unified Log Readonly POC v2.4.8 Run 002

## 1. 测试目标

验证用户中心智能工作台 / 账号问题排查 / 统一日志查询页面的详情弹窗是否可通过只读方式打开，并确认 JSON 面板字段名可被安全提取。

本轮只验证 detail modal 的部分能力，不代表统一登录日志 detail observation fully validated。

## 2. 执行结果

```yaml
test_stage: v2.4.8
platform: user_center_workbench_unified_log_search
validation_status: detail_modal_partially_validated
validated_scope:
  - switch_user_success_detail_modal_openable
  - json_panel_visible
  - readonly_field_name_extraction
  - user_time_device_ip_fields_observed
  - sensitive_raw_value_output_avoided
pending_scope:
  - refresh_token_success_detail_modal_observation
  - request_id_trace_id_presence
  - token_session_ticket_redaction
  - oauth_qr_field_presence
  - risk_decision_field_presence
  - stable_selector_profile
  - execution_time_optimization
```

## 3. Selector Profile

```yaml
selector_profile:
  date_picker_probe_policy: do_not_probe_repeatedly
  time_range_policy:
    explicit_time_value_visible: false
    default_recent_7_days: observed_by_query_result
    source: auto_populated_or_backend_default
    agent_adjusted_time: false
  result_row_selection:
    method: js_scoped_row_click
    row_text_filter:
      - APP切换账号成功
      - 快手APP刷新token成功
    detail_click_policy: click_detail_within_target_row_only
    global_first_detail_button_click_allowed: false
  retry_policy:
    no_data_after_first_query: wait_3_to_5_seconds_then_retry_once
    max_query_retry: 1
  white_screen_policy:
    on_white_screen: record_page_white_screen_and_stop
```

## 4. Detail Modal Observation

```yaml
detail_modal:
  opened: true
  validated_record_type: APP切换账号成功
  pending_record_type: 快手APP刷新token成功
  display_type: json_panel
  json_key_extraction: readonly_keys_only
  json_values_extracted: false
  copy_button_clicked: false
  raw_json_copied: false
  fields_observed:
    - userId
    - timestamp
    - deviceId
    - userIp
    - userIpv6
    - serverIp
    - sysVer
  sensitive_fields_policy:
    userId: present_redacted
    deviceId: present_redacted
    userIp: present_redacted
    userIpv6: present_redacted
    serverIp: present_redacted
    token: never_collect
    session: never_collect
    ticket: never_collect
    params: key_presence_only_if_needed
```

## 5. Page Stability Notes

```yaml
page_stability:
  white_screen_observed: true
  no_data_after_requery_observed: true
  query_delay_observed: true
  handling:
    - do_not_loop_date_picker_probe
    - do_not_infinite_retry
    - retry_query_once_after_3_to_5_seconds_if_no_data
    - record_page_white_screen_if_page_blank
```

## 6. 只读安全

```yaml
readonly_safety_check: PASSED
unsafe_actions_avoided:
  - copy_full_json
  - export
  - batch_download
  - mutation_or_enforcement
  - raw_sensitive_value_output
```

已遵守：

- 未复制完整 JSON。
- 未输出 JSON value 明文。
- 未输出 DID、deviceId、IP、token、session、ticket 明文。
- 未点击导出、批量下载、处置类按钮。

Clarification note:

- 本 run log 中 `userId`、`deviceId`、`userIp`、`userIpv6`、`serverIp` 标为 `present_redacted` 是当时的保守沉淀口径。
- v2.4.8 后续统一字段策略已修正为：用户标识、设备字段、网络字段、客户端字段、行为字段和时间字段均是风控分析字段，应保留用于登录链路判断。
- 仅 token、accessToken、refreshToken、session、sessionId、ticket、authorization、cookie 等认证凭证明文需要隐藏 raw value。

## 7. 限制

- “快手APP刷新token成功”详情尚未完成观察。
- request_id / trace_id 是否存在尚未确认。
- token / session / ticket 字段在详情中的 redaction 尚未完成实跑。
- OAuth / QR 字段和风险决策字段尚未确认。
- selector profile 仍需继续稳定化，避免页面白屏、延迟和暂无数据导致重复探路。

## 8. 推荐下一步

1. 使用同一 selector shortcut 验证 `快手APP刷新token成功` 的详情弹窗。
2. 只提取 JSON key，不提取 value。
3. 验证 token / session / ticket 字段如出现时只记录 `present_redacted` 或 `never_collect`。
4. 固化稳定 selector profile 和超时 / 白屏 / 暂无数据降级策略。
