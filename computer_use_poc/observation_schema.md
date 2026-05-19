# Observation Schema

## 1. 输出结构

```yaml
platform:
query_object:
query_value:
auth_path:
state_saved:
state_file_policy:
login_status:
permission_status:
network_status:
page_status:
expected_failure:
failure_type:
safe_to_continue:
visible_modules:
hidden_or_missing_modules:
key_fields_observed:
sensitive_fields_visible:
identity_context:
risk_relevant_observations:
next_suggested_platforms:
failure_reason:
manual_review_required:
readonly_safety_check:
```

## 2. 字段说明

| 字段 | 含义 | 示例取值 |
|---|---|---|
| platform | 查询平台 | archives_center |
| query_object | 查询对象类型 | user_id |
| query_value | 查询值 | 只记录用户输入，不额外扩展 |
| auth_path | 认证路径 | sso_kim_code, archives_independent_login, userid_direct_url |
| state_saved | 是否保存认证态 | true / false / unknown |
| state_file_policy | state 文件策略 | local_only_do_not_commit / not_saved |
| login_status | 登录状态 | logged_in / not_logged_in / unknown |
| permission_status | 权限状态 | permitted / no_permission / unknown |
| network_status | 网络状态 | ok / vpn_required / timeout / failed |
| page_status | 页面状态 | user_home_visible / no_result / load_failed / blocked |
| expected_failure | 是否为预期失败 | true / false |
| failure_type | 失败类型 | USER_NOT_FOUND / no_permission / saved_state_expired |
| safe_to_continue | 是否可继续当前查询 | true / false |
| visible_modules | 可见模块 | 用户基础信息、处罚状态、设备信息 |
| hidden_or_missing_modules | 不可见或缺失模块 | 登录信息、审核记录 |
| key_fields_observed | 关键字段可见性 | user_id visible, punish_status visible |
| sensitive_fields_visible | 高敏字段是否可见 | phone visible with masked_redacted |
| identity_context | 页面身份信息归属 | user_header target_object_allowed, nav_menu operator_identity_redacted |
| risk_relevant_observations | 风险相关页面观察 | 仅记录页面事实，不做最终结论 |
| next_suggested_platforms | 下一步建议平台 | 用户登录统一日志、设备攻防基建平台、天狮 |
| failure_reason | 失败原因 | no_permission / no_result / invalid_user_id |
| manual_review_required | 是否需要人工复核 | true / false |
| readonly_safety_check | 只读安全检查 | passed / stopped_due_to_write_risk |

## 3. 输出边界

- observation 不等于 final judgement。
- 不记录高敏明文。
- 不输出用户名、手机号、设备 ID、IP、昵称、快手号等明文。
- 脱敏手机号也不输出具体脱敏串，只记录 `visible_masked_value_redacted`。
- 不生成封禁、解封、冻结、审批、策略上线等处置结论。
- 如页面无法确认字段含义，应写入 `failure_reason` 或 `risk_relevant_observations` 的“不确定”说明。
- `USER_NOT_FOUND` 时 `expected_failure=true`、`safe_to_continue=false`，但 `readonly_safety_check` 仍可为 `PASSED`。

## 4. 敏感字段观测格式

敏感字段必须使用以下结构：

```yaml
- field_name:
  visibility:
  value_policy: redacted / masked_redacted / not_collected
  reason:
```

示例：

```yaml
- field_name: phone_number
  visibility: visible_masked
  value_policy: masked_redacted
  reason: 脱敏手机号可见，但 run log 不输出具体脱敏串
```

## 5. 身份信息观测格式

页面身份信息必须区分查询目标对象和当前登录操作者。

```yaml
identity_context:
  user_header:
    visibility:
    object_type: target_user
    user_id_match:
    value_policy: target_object_allowed / redacted
    reason:
  nav_menu:
    visibility:
    object_type: operator_account
    value_policy: operator_identity_redacted
    reason:
```

解释规则：

- `user_header` 如果展示的是查询目标用户，可用于确认页面对象是否与 `query_value` 匹配。
- `nav_menu`、右上角头像、当前登录账号名、操作者邮箱等属于 operator 身份，必须隐藏。
- 如果无法判断某个身份信息属于 target object 还是 operator，默认按 operator 处理并 redacted。
