# 档案中心 userId Not Found Run 001

## 1. 测试目标

验证非法 / 不存在 `userId` direct URL 的预期失败处理。

本次只验证：

- 已保存档案中心认证 state 仍可用。
- 非法 / 不存在 userId 能稳定返回空结果页。
- 该失败应识别为 `USER_NOT_FOUND`。
- 不应误判为登录失败、权限失败或系统崩溃。

## 2. 前置条件

```yaml
environment: internal_agent_runtime
saved_state_available: true
saved_state_scope: archives_center
state_file_policy: local_only_do_not_commit
auth_secret_recorded: false
```

## 3. 输入

```yaml
entry_mode: userId_direct_url
query_object: user_id
query_value: invalid_sample_user_id
query_value_policy: synthetic_invalid_sample_redacted
target_url_policy: redacted
state_loaded: true
```

说明：

- 不记录具体测试 userId 明文。
- 不记录 target URL 参数。

## 4. 执行结果

```yaml
state_reuse_status: SUCCESS
redirect_detected: false
login_required: false
spa_render_status: FULLY_RENDERED
page_status: user_not_found
user_header_match: false
core_detail_tabs_visible: false
expected_failure: true
failure_type: USER_NOT_FOUND
safe_to_continue: false
readonly_safety_check: PASSED
```

## 5. 页面观察

```yaml
visible_modules:
  - user_not_found_empty_state
hidden_or_missing_modules:
  - 用户信息
  - 审核日志
  - 打标日志
  - 用户分析
  - 视频作品集
  - 直播作品集
  - 粉丝列表
  - 关注列表
  - 合集列表
  - 收藏列表
  - 动态列表
identity_context:
  user_header:
    visibility: not_visible_or_not_matched
    object_type: target_user
    user_id_match: false
    value_policy: not_collected
    reason: 页面返回用户不存在，无法确认目标用户详情页
  nav_menu:
    visibility: visible_or_possible
    object_type: operator_account
    value_policy: operator_identity_redacted
    reason: 当前登录操作者信息不属于查询对象，必须隐藏
```

## 6. 只读安全结果

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

## 7. 解释边界

- `USER_NOT_FOUND` 是预期失败。
- 该状态不代表登录失败。
- 该状态不代表权限失败。
- 该状态不代表档案中心系统崩溃。
- 该状态不代表目标用户无风险。
- 应停止本次用户详情研判，并提示更换或核对 `user_id`。

## 8. 当前结论

档案中心 `userId` 不存在时可稳定返回空结果页，不误判为认证 / 权限失败。

```yaml
conclusion: archives_center_userid_not_found_expected_failure_validated
status: validated
scope: archives_center_userId_direct_url_readonly
```
