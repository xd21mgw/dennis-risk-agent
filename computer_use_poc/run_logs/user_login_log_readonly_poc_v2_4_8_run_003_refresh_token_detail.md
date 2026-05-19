# User Login Unified Log Readonly POC v2.4.8 Run 003

## 1. 测试目标

验证用户中心智能工作台 / 账号问题排查 / 统一日志查询页面中“快手APP刷新token成功”记录的详情弹窗是否可通过只读方式打开，并确认 JSON key 可安全提取。

本轮只验证 refreshToken 详情弹窗的只读字段名观察，不代表统一登录日志 fully validated。

## 2. 执行结果

```yaml
test_stage: v2.4.8
platform: user_center_workbench_unified_log_search
validation_status: refresh_token_detail_modal_validated
validated_scope:
  - refresh_token_row_found
  - refresh_token_detail_modal_openable
  - modal_dialog_display_type
  - readonly_json_key_extraction
  - ip_user_agent_app_version_did_fields_observed
  - token_session_ticket_authorization_fields_absent
  - copy_button_present_but_not_clicked
  - readonly_safety_passed
pending_scope:
  - nested_json_field_completeness
  - copy_button_behavior
  - no_result_behavior
  - pagination_behavior
  - permission_blocked_behavior
  - multi_source_joint_validation
```

## 3. 查询与结果表

```yaml
query:
  query_object: user_id
  query_value_policy: redacted_in_long_term_docs
  time_range_manual_selected: false
  log_source_default_checked: true
result_table:
  result_present: true
  refresh_token_row_found: true
  selected_row_tag: 快手APP刷新token成功
  selected_row_method: /rest/n/token/infra/refreshToken
```

## 4. Detail Modal Observation

```yaml
detail_modal:
  detail_openable: true
  display_type: modal_dialog
  json_panel_visible: true
  json_key_extraction: readonly_keys_only
  json_values_extracted: false
  copy_button_present: true
  copy_button_clicked: false
  visible_json_keys:
    - serverIp
    - actionType
    - appType
    - userId
    - result
    - userIp
    - userAgent
    - did
    - dateTime
    - uri
    - reason
    - appVer
    - extra
```

## 5. Field Presence

```yaml
field_presence:
  has_request_id_or_trace_id: false
  has_ip_or_region: true
  has_user_agent: true
  has_app_version: true
  has_device_type: true
  has_token_session_ticket_present_redacted: false
  has_oauth_or_scan: false
  has_login_method: true
  has_risk_label_or_decision: false
  has_fail_reason: false
  has_login_source: false
sensitive_fields:
  token: absent
  session: absent
  ticket: absent
  authorization: absent
  refresh_token: absent
  access_token: absent
```

说明：

- 本样本未观察到 token / session / ticket / authorization / refresh_token / access_token 字段。
- 如果后续样本观察到这些字段，只能记录 `present_redacted`，不得输出 raw value。
- 无 request_id / trace_id 或无 risk decision 字段不代表页面无价值，只能记录为 missing / not_observed。

## 6. 页面稳定性

```yaml
page_stability_issue:
  - modal 打开后 JSON 内容显示有延迟，首次 snapshot 只显示 "{"
  - 等待 5 秒后 JSON key 正常显示
recommended_wait_policy:
  json_panel_initial_incomplete: wait_5_seconds_then_read_keys
```

## 7. 只读安全

```yaml
readonly_safety_check:
  full_json_copied: false
  sensitive_raw_value_output: false
  write_action_performed: false
  passed: true
```

已遵守：

- 未点击复制按钮。
- 未复制完整 JSON。
- 未读取或输出 JSON value 明文。
- 未输出 IP、DID、deviceId、token、session、ticket、authorization、refresh_token、access_token 明文。
- 未点击导出、批量下载、处置类按钮。

Clarification note:

- 本 run log 中“未输出 IP、DID、deviceId 明文”是当时的保守沉淀口径，不代表这些字段不能作为风控证据保留。
- v2.4.8 后续统一字段策略已修正为：userId / accountId / principal、did / deviceId / deviceType / deviceModel、userIp / serverIp / userIpv6 / region、userAgent / appVer / appType / sysVer、actionType / uri / method / result / reason、timestamp / dateTime / token/session 生命周期时间等字段应保留。
- 只隐藏 token、accessToken、refreshToken、session、sessionId、ticket、authorization、cookie 等认证凭证明文 raw value。

## 8. 未完成项

- 未验证 JSON 完整内容是否包含更多嵌套字段。
- 未点击复制按钮验证复制功能；后续也不应点击，除非有独立只读安全审批。
- 未验证无结果 / 分页 / 权限阻断行为。
- 未完成多源联合 observation validation。

## 9. 当前结论

用户登录统一日志 refreshToken 详情弹窗已验证可只读打开，并可安全提取 JSON key。当前仅代表 refreshToken detail modal 的 readonly JSON key extraction validated，不代表统一登录日志全能力 fully validated。
