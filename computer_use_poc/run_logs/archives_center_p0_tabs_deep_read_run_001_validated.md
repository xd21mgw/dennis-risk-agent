# 档案中心 P0 Tabs 深读 Run 001

## 1. 测试目标

验证档案中心 `userId` direct URL 用户详情页的 P0 Tab 只读深读能力。

P0 Tab 范围：

- 用户信息
- 用户分析
- 审核日志
- 视频作品集

## 2. 前置条件

```yaml
platform: archives_center
entry_mode: userId_direct_url
query_object: user_id
query_value_policy: redacted
saved_state_available: true
```

本次实跑发现：

```yaml
state_reuse_status: EXPIRED_RELOGIN_REQUIRED
reauth_result: SUCCESS
new_state_saved: true
auth_secret_recorded: false
```

说明：

- 首次加载时 saved state 已过期，回到档案中心独立登录页。
- 重新登录后进入档案中心成功，并保存新 state。
- run log 不记录密码、token、cookie、session、KIM code 或认证 header。

## 3. 页面与安全状态

```yaml
spa_render_status: FULLY_RENDERED
readonly_safety_check: PASSED
write_buttons_clicked: false
export_clicked: false
operator_account_recorded: false
sensitive_values_recorded: false
```

只读动作：

- 点击 P0 Tab 切换。
- 等待页面加载。
- 读取模块名、字段名、表头、按钮语义。

未执行动作：

- 未点击封禁。
- 未点击解封。
- 未点击打标。
- 未点击保存。
- 未点击提交。
- 未点击审批。
- 未点击导出。
- 未点击批量操作。

## 4. tabs_validated

```yaml
tabs_validated:
  - user_info_tab
  - user_analysis_tab
  - audit_log_tab
  - video_portfolio_tab
```

## 5. user_info_tab observation

```yaml
user_info_tab:
  tab_status: fully_loaded
  sections_observed:
    - 基本信息
    - 相关链接
    - 最近登录
    - 最近启动
    - 注册信息
    - 账户信息
    - 用户实时负向
    - 用户设置
    - 同设备登录用户入口
    - 同设备注册用户入口
    - 头像查重入口
    - 背景查重入口
  write_action_buttons_present: true
  write_action_buttons_clicked: false
  sensitive_fields_policy: redacted
  operator_account_policy: operator_identity_redacted
```

解释边界：

- 用户信息 Tab 已验证为高价值 P0 入口。
- 写操作按钮风险存在，但本次未点击。
- `user_header` 仅用于 `user_id_match`，不输出目标用户敏感明文。

## 6. user_analysis_tab observation

```yaml
user_analysis_tab:
  tab_status: fully_loaded
  filters_observed:
    - time_range
    - operation_type_filter
  sub_tabs_observed:
    - APP端核心操作日志
  list_or_table_present: true
  fields_observed:
    - operation_type
    - timestamp
    - operation_url
    - operation_result
    - app_version
  sensitive_fields_policy:
    user_ip_desc: redacted
    device_id: redacted
    phone: masked_redacted
    location: redacted
```

time_range 口径：

- 本次确认页面存在时间范围控件。
- observation 必须记录页面实际 start/end。
- “默认近 1 年”是 Agent 查询策略，不等于页面天然默认值。

## 7. audit_log_tab observation

```yaml
audit_log_tab:
  tab_status: loaded_empty_or_no_rows
  filters_present: true
  list_or_table_present: true
  fields_observed:
    - audit_time
    - auditor
    - page
    - operation
    - remark
  sensitive_fields_policy: summary_or_redacted
```

解释边界：

- 审核日志 Tab 已加载。
- 当前无数据行时应标记 `loaded_empty_or_no_rows`。
- 不得解释为无风险、无审核或无行为。

## 8. video_portfolio_tab observation

```yaml
video_portfolio_tab:
  tab_status: fully_loaded
  list_or_table_present: true
  pagination_present: true
  entries_observed:
    - detail_entry
    - similarity_check_entry
    - view_more_entry
  entry_validation_status:
    detail_entry: pending
    similarity_check_entry: pending
    view_more_entry: pending
  sensitive_fields_policy:
    photo_id: redacted_or_policy_controlled
    title: redacted
```

解释边界：

- 视频作品集 Tab 已加载。
- 详情、查重、查看更多入口仅记录为 pending。
- 未点击二级入口，不写 validated。

## 9. identity_context

```yaml
identity_context:
  target_object:
    source: user_header
    object_type: target_user
    user_id_match: true
    value_policy: target_object_allowed_for_match_only
  operator_account:
    source: nav_menu
    object_type: operator_account
    value_policy: operator_identity_redacted
```

## 10. 当前结论

```yaml
conclusion: archives_center_user_profile_p0_tabs_deep_read_validated
status: validated
readonly_safety_check: PASSED
```

档案中心 user profile P0 Tab 深读 observation 已验证通过。

该结论不代表：

- 二级链接已验证。
- 详情页已验证。
- 查重页已验证。
- 多入口已验证。
- 多平台已验证。
- 自动研判已完成。
