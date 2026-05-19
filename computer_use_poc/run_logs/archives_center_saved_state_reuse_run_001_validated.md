# 档案中心 Saved State 复用 Run 001

## 1. 测试目标

验证内部 Agent 环境在已有档案中心认证 state 的前提下，是否可以复用 saved state 直接打开档案中心 `userId` direct URL，并完成只读页面观察。

本次只验证：

- 档案中心
- saved state 复用
- `userId` direct URL
- 单用户只读查询
- 页面 observation

## 2. 前置条件

```yaml
environment: internal_agent_runtime
saved_state_available: true
saved_state_scope: archives_center
state_file_policy: local_only_do_not_commit
auth_secret_recorded: false
```

说明：

- 内部 Agent 环境已有保存的档案中心认证 state。
- run log 不记录 state 文件内容、token、cookie、session、KIM code 或认证 header。
- state 文件不提交 Git。

## 3. 执行入口

```yaml
entry_mode: userId_direct_url
query_object: user_id
query_value_policy: redacted
target_url_policy: redacted
state_loaded: true
```

## 4. 执行结果

```yaml
state_reuse_status: SUCCESS
redirect_detected: false
login_required: false
spa_render_status: FULLY_RENDERED
readonly_safety_check: PASSED
write_buttons_clicked: false
export_clicked: false
operator_identity_recorded: false
auth_secret_recorded: false
```

## 5. visible_modules

只记录模块名，不记录模块内敏感明文：

```yaml
visible_modules:
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
  - 基本信息
  - 用户实时负向
  - 最近登录
  - 最近启动
  - 注册信息
  - 账户信息
  - 同设备登录入口
  - 同设备注册入口
```

## 6. identity_context

```yaml
identity_context:
  user_header:
    visibility: visible
    object_type: target_user
    user_id_match: true
    value_policy: target_object_allowed
    reason: 用于核验 direct URL 打开的页面对象是否与 query_value 匹配
  nav_menu:
    visibility: visible_or_possible
    object_type: operator_account
    value_policy: operator_identity_redacted
    reason: 当前登录操作者信息不属于查询对象，不记录明文
```

## 7. 只读安全结果

```yaml
readonly_safety_check:
  status: PASSED
  no_write_action_clicked: true
  no_submit_clicked: true
  no_approval_clicked: true
  no_export_clicked: true
  no_batch_download_clicked: true
  sensitive_values_redacted: true
  operator_account_redacted: true
```

## 8. 风险边界

- 本次不代表多平台 computer use 已完成。
- 本次不代表多入参或批量查询已完成。
- 本次不代表自动研判已完成。
- observation 仅说明页面可访问、可渲染、模块可识别。
- 风险结论仍需 Dennis Risk Agent 基于多证据综合判断。
- state 失效时应回退到人工登录 / 重新保存 state。

## 9. 当前结论

档案中心 saved state 复用验证通过。

```yaml
conclusion: archives_center_saved_state_reuse_validated
status: validated
scope: archives_center_userId_direct_url_readonly
```
