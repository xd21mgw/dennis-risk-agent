# User Login Log Readonly POC v2.4.8 Run 010

```yaml
test_stage: v2.4.8
test_type: archives_audit_label_log_access
validation_status: archives_audit_label_log_access_partially_validated

archives_audit_label_log_access_test:
  user_id: "4700398885"

  audit_log:
    accessible: true
    result_present: true
    empty_state_text: N/A
    visible_columns:
      - 业务领域
      - 操作来源
      - 操作时间
      - 操作结果 (punishCode)
      - 风控标签 (markCode)
      - 详情
      - 操作详情
    pagination_present: unknown
    limitations:
      - 新版/旧版切换按钮可见，当前为新版
      - 审核日期范围：2025-11-20 ~ 2026-05-19
      - 操作来源筛选框可见
      - 表格数据可见，包括内容安全、主站-用户简介、机审通过等
      - 未滚动到表格底部确认分页
      - 未点击详情

  label_log:
    accessible: true
    result_present: unknown
    empty_state_text: unknown
    visible_columns:
      - 业务领域
      - 操作来源
      - 操作时间
      - 操作结果 (punishCode)
      - 风控标签 (markCode)
    pagination_present: unknown
    limitations:
      - 打标日期范围：2025-11-20 ~ 2026-05-19
      - 打标类型：营销号打标—server
      - 操作来源筛选框可见
      - 表头可见，但未确认数据行
      - 未确认 empty state
      - 未确认分页

  guardrail:
    no_result_not_equal_no_risk: true
    readonly_only: true

validated_scope:
  - audit_log_tab_accessible
  - audit_log_result_present
  - audit_log_visible_columns
  - label_log_tab_accessible
  - label_log_visible_columns
  - readonly_safety_passed

pending_scope:
  - audit_log_pagination_behavior
  - audit_log_detail_view
  - label_log_result_presence
  - label_log_empty_state_or_data_rows
  - label_log_pagination_behavior
  - old_version_new_version_switch_behavior
```

## Guardrail

- 权限系统升级通知弹窗可能遮挡 Tab 点击，点击 Tab 前应先关闭弹窗。
- Tab 点击后必须确认 `current_url` 仍在档案中心 direct URL 下。
- Tab selected 状态和页面实际内容都要确认，不能只看 click 成功。
- 打标日志表头可见不等于有数据。
- 审核日志有结果不等于登录风险定性完成。
- 审核 / 打标日志只作为补充 source，不替代登录链路证据。
