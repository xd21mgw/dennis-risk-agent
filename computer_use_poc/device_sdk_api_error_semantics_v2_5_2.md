# Device SDK API Error Semantics v2.5.2

## 1. 目标

该文档用于统一 Dennis Agent 消化设备 SDK API-direct observation 时的错误语义，避免把 no_data、权限阻断、字段缺失误解释为设备无风险。

## 2. 标准语义

| 情况 | 标准状态 | 正确解释 | 禁止解释 |
|---|---|---|---|
| HTTP 200 + `data=[]` | `no_data` | 当前查询条件下无结果 | 接口失败、设备无风险 |
| HTTP 200 + `has_permission=false` | `permission_blocked` | 当前接口 / 字段无权限 | 无位置、无风险 |
| 字段不存在 | `platform_not_applicable` 或 `missing_field` | 平台不适用或字段缺失 | 未检测到风险 |
| API 非 2xx / 解析失败 | `error` | 当前接口不可用或响应异常 | no_data、无风险 |
| location 未调用 | `not_called_by_policy` | 默认排除定位采集 | 无位置、无风险 |

## 3. iOS appList package_name 语义

iOS `appList` 中的 `package_name` 不是 bundle ID。

规则：

- 不得把 iOS `package_name` 当成 Android package name 或 bundle ID。
- 应标记 `identifier_semantics=ios_package_name_not_bundle_id`。
- 如需确认真实 bundle ID，需要后续专项验证。

## 4. iOS 缺失字段解释

iOS 无 simulator / dual 字段时：

- 不能解释为未检测到模拟器。
- 不能解释为未检测到双开。
- 应标记 `platform_not_applicable` 或 `missing_field`。

同理，Android-only 字段在 iOS 缺失，不能作为无风险证据。

## 5. IOS_ 前缀失败解释

已验证：

- iOS 标准入参为 raw UUID。
- `IOS_` 前缀格式返回空。

解释规则：

- `IOS_` 前缀返回空是 `no_data_by_wrong_input_format`。
- 不得解释为 iOS 不支持。
- 不得解释为该设备无风险。

## 6. location 默认不调用

定位接口默认不调用。

原因：

- Android 样本 location 虽 HTTP 200，但 `has_permission=false`。
- iOS 样本未调用 location。
- 定位属于高敏数据，不进入默认正式 hand。

规则：

- `location.called=false`。
- `reason=sensitive_data_excluded_by_policy`。
- 不把 location 作为正式 Skill 默认接口。

## 7. 输出边界

- 不输出完整敏感字段值。
- 不输出完整原始 JSON。
- 不做自动风险定性。
- 不做自动处置。
- 不批量抓取。
