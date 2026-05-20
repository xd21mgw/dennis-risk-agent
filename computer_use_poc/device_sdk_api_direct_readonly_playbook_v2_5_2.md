# Dennis Agent 5 设备 SDK 基建 API-direct readonly Playbook v2.5.2

## 1. 平台定位

设备 SDK / 设备基建 API-direct readonly hand 是 Dennis Agent 的设备侧补证手脚。

它用于围绕单个 `deviceId / did` 读取设备 SDK 采集、设备画像、设备风险信号和设备关系摘要，补充账号安全、协议上号、群控、自动化、破解包、设备异常等场景的设备侧证据。

当前 v2.5.2 基于内部 Agent 已完成的 Android + iOS 单样本接口验证沉淀。

## 2. 只读边界

允许：

- 查询单个 deviceId / did。
- 调用已验证只读 API。
- 读取字段名、非凭证风控字段和派生特征。
- 输出设备画像、风险信号、关联摘要和字段可见性。

禁止：

- 批量查询。
- 修改设备状态。
- 导出敏感数据。
- 复制完整 JSON。
- 输出 token / session / ticket / authorization / cookie 等认证凭证明文。
- 自动处罚、封禁、冻结、解封或策略上线。
- 基于设备单源证据做最终风险定性。

## 3. 默认不采集定位信息

定位接口默认不调用。

原因：

- Android 样本中 location 接口虽然 HTTP 200，但 `has_permission=false`。
- iOS 样本未调用定位接口。
- 定位属于高敏信息，当前正式沉淀不纳入默认采集链路。

规则：

```yaml
location_policy:
  default_called: false
  reason: sensitive_data_excluded_by_policy
  android_observation: HTTP_200_but_has_permission_false
  ios_observation: not_called
  formal_skill_default: excluded
```

## 4. API-direct 调用顺序

默认链路：

```yaml
api_direct_sequence:
  - user_info
  - page_tree
  - weapon_config
  - risk_data
  - app_list
  - klink
  - graph_data
```

核心顺序：

1. 先完成 browser auth / API auth preflight。
2. 先查 `/apiv2/riskData`，确认 canonical device、user_id、platform、weaponPlatform 和原始日志字段。
3. 再查 `appList`，补应用安装 / 标识摘要。
4. 再查 `klink`，补关系 / 链路结果摘要。
5. 再查 `graphData`，补点边关系结构。
6. 默认不调用 location。

## 5. Android / iOS deviceId normalization

### Android

验证样本：

```yaml
raw_input_device_id: ANDROID_fc1963b93f823ebd
normalized_input_device_id: ANDROID_fc1963b93f823ebd
canonical_device_id: ANDROID_fc1963b93f823ebd
user_id: "2241990844"
```

规则：

- Android 样本使用 `ANDROID_` 前缀格式。
- canonical device ID 与输入一致。
- 不要去掉 `ANDROID_` 前缀。

### iOS

验证样本：

```yaml
raw_input_device_id: 3509C1CA-0DC3-4868-A5E8-9A88E83A8A81
normalized_input_device_id: 3509C1CA-0DC3-4868-A5E8-9A88E83A8A81
canonical_device_id: 3509C1CA-0DC3-4868-A5E8-9A88E83A8A81
user_id: "681288977"
platform: i
weaponPlatform: iOS
```

规则：

- iOS 入参格式为 raw UUID。
- 不加 `IOS_` 前缀。
- `IOS_` 前缀格式返回空时，应解释为输入格式不匹配 / no_data，不得解释为 iOS 不支持。

### 鸿蒙

```yaml
harmony_status: pending_validation
```

鸿蒙字段、前缀、platform / weaponPlatform 口径仍待样本验证。

## 6. riskData 主接口解析逻辑

`/apiv2/riskData` 是设备 SDK API-direct hand 的主接口。

核心解析：

```yaml
risk_data_parse:
  canonical_device_id:
  user_id:
  platform:
  weaponPlatform:
  originalLog_key_count:
  normalized_device_fields:
  normalized_risk_signals:
  platform_specific_fields:
```

Android 结论：

- `/apiv2/riskData` 成功。
- canonical_device_id = `ANDROID_fc1963b93f823ebd`。
- user_id = `2241990844`。
- `appList` / `klink` / `graphData` 可串联。

iOS 结论：

- `/apiv2/riskData` 成功。
- originalLog 约 170 keys。
- canonical_device_id = raw UUID。
- user_id = `681288977`。
- `platform=i`，`weaponPlatform=iOS`。
- `appList` / `klink` / `graphData` 均成功。

## 7. appList / klink / graphData 派生接口

### appList

用途：

- 补充应用列表 / 标识摘要。
- 判断应用侧字段结构和 identifier 语义。

注意：

- iOS `appList` 的 `package_name` 不是 bundle ID。
- 不能把 iOS `package_name` 当成 Android 包名同义字段。

### klink

用途：

- 补关系或链路结果摘要。

解释：

- `data=[]` 是 `no_data`，不等于接口失败。
- `no_data` 不等于设备无风险。

### graphData

用途：

- 补图谱点边关系。
- 读取 `pointInfoMap` / `relationEdgeList` 结构。

解释：

- 图结构用于关系补证，不直接等同群控。
- 需要结合账号、登录、前端行为和策略证据判断。

## 8. no_data / permission_blocked / empty_field / error 语义区分

```yaml
error_semantics:
  http_200_data_empty:
    meaning: no_data
    forbidden_interpretation:
      - 接口失败
      - 设备无风险
  http_200_has_permission_false:
    meaning: permission_blocked
    forbidden_interpretation:
      - 无位置
      - 设备无风险
  field_missing:
    meaning: platform_not_applicable_or_missing_field
    forbidden_interpretation:
      - 未检测到风险
  api_error:
    meaning: error
    forbidden_interpretation:
      - no_data
      - 无风险
```

## 9. Android / iOS 字段差异

Android 侧重点：

- api level。
- android_id / oaid。
- apk path。
- build display / ROM。
- mount risk。
- accessibility。
- sensor。

iOS 侧重点：

- idfv / idfa。
- jailbreak detector。
- repack。
- proxy / VPN。
- kern / hw / posix user 字段簇。

解释边界：

- iOS 无 simulator / dual 字段，不能解释为未检测到模拟器 / 双开。
- Android-only 字段在 iOS 缺失，应标记 `platform_not_applicable`，不是 `no_risk`。
- 字段不存在或为空，必须区分平台不适用、字段缺失、权限不足和接口无结果。

## 10. 鸿蒙字段待验证

待确认：

- Harmony deviceId normalization。
- platform / weaponPlatform 取值。
- riskData originalLog 字段结构。
- appList / klink / graphData 是否同构。
- 模拟器、多开、hook、改机相关字段口径。

## 11. 当前状态

```yaml
version: v2.5.2
capability: device_sdk_api_direct_readonly_hand
android_single_sample_verified: true
ios_single_sample_verified: true
location_default_excluded: true
harmony_verified: false
batch_query_supported: false
core_skill_modified: false
release_package_updated: false
```
