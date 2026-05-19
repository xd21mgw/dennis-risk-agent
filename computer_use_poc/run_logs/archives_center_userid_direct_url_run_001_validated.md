# 档案中心 userId Direct URL 只读查询 Run 001

## 1. 测试目标

验证 Dennis Risk Agent computer use readonly POC 是否可以通过档案中心 `userId` direct URL 完成单用户只读页面查询，并返回结构化 observation。

本次只验证档案中心单平台、单 `user_id`、只读查询链路。

## 2. 输入 user_id

```yaml
query_object: user_id
query_value_policy: redacted
query_value: user_id_redacted
```

## 3. target_url

```yaml
target_url_type: archives_center_userid_direct_url
target_url_policy: redacted
target_url: archives_center_userid_direct_url_redacted
```

说明：

- 已验证 `userId` direct URL 可用。
- run log 不记录真实 URL 参数，避免泄露用户标识和内部路径细节。

## 4. 认证路径

```text
SSO KIM Code
→ 档案中心独立登录 account.p.adm-corp.kuaishou.com
→ 进入 userId direct URL 详情页
```

认证态边界：

- 不记录 token、cookie、session、KIM code。
- 不提交或保存认证态文件到 Git。
- 如使用 state 复用，state 文件只能本地保存。

## 5. 结构化 observation

```yaml
platform: archives_center
query_object: user_id
query_value:
  visibility: provided_to_browser
  value_policy: redacted
  reason: run log 不记录真实 user_id
auth_path:
  - sso_kim_code
  - archives_independent_login
  - userid_direct_url
state_saved: true
state_file_policy: local_only_do_not_commit
login_status: logged_in
permission_status: permitted
network_status: ok
page_status: user_home_visible
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
hidden_or_missing_modules: []
key_fields_observed:
  - field_name: user_id
    visibility: visible
    value_policy: redacted
    reason: 用户标识不写入 run log
  - field_name: account_basic_info
    visibility: visible
    value_policy: not_collected
    reason: 本次只验证模块可见性
  - field_name: realtime_negative_status
    visibility: visible
    value_policy: not_collected
    reason: 不输出具体状态值
  - field_name: recent_login
    visibility: visible
    value_policy: not_collected
    reason: 不输出具体 IP、设备或时间明文
  - field_name: recent_launch
    visibility: visible
    value_policy: not_collected
    reason: 不输出具体设备或时间明文
  - field_name: registration_info
    visibility: visible
    value_policy: redacted
    reason: 注册信息可能包含敏感字段
  - field_name: account_info
    visibility: visible
    value_policy: redacted
    reason: 账户信息可能包含敏感字段
sensitive_fields_visible:
  - field_name: username_or_nickname
    visibility: visible_or_possible
    value_policy: redacted
    reason: 不输出昵称、快手号等个人信息明文
  - field_name: phone_number
    visibility: unknown_or_masked
    value_policy: masked_redacted
    reason: 脱敏手机号也不输出具体脱敏串
  - field_name: device_id
    visibility: visible_or_possible
    value_policy: redacted
    reason: 不输出设备 ID 明文
  - field_name: ip
    visibility: visible_or_possible
    value_policy: redacted
    reason: 不输出 IP 明文
risk_relevant_observations:
  - 档案中心 SPA 可完整渲染。
  - 用户详情页可通过 userId direct URL 进入。
  - 可识别用户信息、审核日志、打标日志、用户分析和作品/关系类 Tab。
  - 可识别基础信息、实时负向、最近登录、最近启动、注册信息、账户信息和同设备入口。
next_suggested_platforms:
  - user_login_unified_log
  - device_defense_platform
  - tianshi_policy_engine
  - risk_ops_center_rap
failure_reason: null
manual_review_required: true
readonly_safety_check:
  status: passed
  write_buttons_clicked: false
  export_clicked: false
  high_sensitive_values_recorded: false
```

## 6. 已通过项

- userId direct URL 可用。
- 档案中心 SPA 可完整渲染。
- 完整认证路径已验证。
- 页面可识别多类 Tab 和用户分析模块。
- 页面可识别基础信息、用户实时负向、最近登录、最近启动、注册信息、账户信息、同设备登录/注册入口等模块。
- 未点击任何写操作按钮。
- 未导出、未批量下载、未提交、未审批、未处置。
- 只读安全检查通过。

## 7. 风险边界

- 本次不代表多平台 computer use 已完成。
- 本次不代表多入参查询已完成。
- 本次不代表自动研判已完成。
- 页面 observation 不等于风险结论。
- 未保存或提交认证 token、cookie、KIM code。
- run log 不包含明文敏感字段。
- 如后续复用 saved state，state 文件必须本地保存并排除 Git。

## 8. 当前结论

档案中心 `userId` direct URL readonly POC validated。

验证范围仅限：

- 档案中心
- 单 `user_id`
- direct URL
- 只读查询
- 页面 observation
