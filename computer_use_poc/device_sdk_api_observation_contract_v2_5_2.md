# Device SDK API Observation Contract v2.5.2

## 1. 标准 Observation

```yaml
device_sdk_api_observation:
  query:
    raw_input_device_id:
    normalized_input_device_id:
    product:
    platform_guess:
    location_extraction_enabled: false
  api_status:
    user_info:
    page_tree:
    weapon_config:
    risk_data:
    app_list:
    klink:
    graph_data:
  identity:
    canonical_device_id:
    user_id:
    platform:
    weapon_platform:
  normalized_device_fields:
    device_model:
    brand:
    os_version:
    app_version:
    sdk_version:
    risk_level:
    risk_tags:
    source_ip_redacted:
  normalized_risk_signals:
    jailbreak_or_root:
    hook:
    frida:
    simulator:
    dual_or_multi_open:
    debug:
    proxy:
    repack_or_tamper:
  android_specific_fields:
    api_level:
    android_id_present:
    oaid_present:
    apk_path_present:
    build_display_rom:
    mount_risk:
    accessibility_present:
    sensor_present:
  ios_specific_fields:
    idfv_present:
    idfa_enable:
    device_model:
    jailbreak_detector_present:
    repack:
    proxy_vpn:
    kern_fields_count:
    hw_fields_count:
    posix_user_fields_count:
  app_list_summary:
    app_count:
    identifier_field:
    identifier_semantics:
    sample_count:
  klink_summary:
    result_semantics:
    data_count:
    field_keys:
  graph_summary:
    point_count:
    edge_count:
    center_node_found:
    relation_format:
  location_policy:
    called: false
    reason: sensitive_data_excluded_by_policy
  limitations:
    harmony_verified: false
    location_not_collected: true
    platform_specific_semantics_required: true
```

## 2. 字段解释

### query

- `raw_input_device_id`：用户或上游 observation 给出的原始设备 ID。
- `normalized_input_device_id`：按平台规则归一后的查询 ID。
- `platform_guess`：根据输入格式和 API response 推断的平台，不作为唯一事实。
- `location_extraction_enabled=false`：正式 hand 默认不采集定位。

### api_status

每个接口状态必须区分：

- `success`
- `no_data`
- `permission_blocked`
- `error`
- `not_called_by_policy`

### identity

- `canonical_device_id` 以 `/apiv2/riskData` 返回为准。
- `user_id` 是设备关联的用户 ID，不等同账号风险定性。
- `platform` / `weapon_platform` 需保留原始口径。

### normalized_risk_signals

设备风险信号是设备侧线索，不是最终风险定性。

字段缺失必须区分：

- `platform_not_applicable`
- `missing_field`
- `permission_blocked`
- `query_no_result`

## 3. Android 样本映射

```yaml
android_sample:
  raw_input_device_id: ANDROID_fc1963b93f823ebd
  normalized_input_device_id: ANDROID_fc1963b93f823ebd
  canonical_device_id: ANDROID_fc1963b93f823ebd
  user_id: "2241990844"
  risk_data_status: success
  app_list_status: success
  klink_status: success
  graph_data_status: success
  location_status: permission_blocked_if_called
  location_default_called: false
```

## 4. iOS 样本映射

```yaml
ios_sample:
  raw_input_device_id: 3509C1CA-0DC3-4868-A5E8-9A88E83A8A81
  normalized_input_device_id: 3509C1CA-0DC3-4868-A5E8-9A88E83A8A81
  ios_prefixed_input: IOS_3509C1CA-0DC3-4868-A5E8-9A88E83A8A81
  ios_prefixed_result: no_data
  canonical_device_id: 3509C1CA-0DC3-4868-A5E8-9A88E83A8A81
  user_id: "681288977"
  platform: i
  weapon_platform: iOS
  risk_data_status: success
  originalLog_key_count: approximately_170
  app_list_status: success
  klink_status: success
  graph_data_status: success
  location_default_called: false
```

解释：

- iOS 标准入参是 raw UUID。
- `IOS_` 前缀返回空，只能解释为输入格式不匹配 / no_data，不得解释为 iOS 不支持。

## 5. 敏感字段策略

保留：

- deviceId / did。
- user_id。
- device model / brand / OS / app / SDK version。
- root / jailbreak / hook / frida / simulator / dual / proxy / repack 等风险字段。
- 图谱点边计数和关系格式。

限制：

- 不输出完整原始 JSON。
- 不输出 token / session / ticket / authorization / cookie 明文。
- 不默认调用定位接口。
- IP 类字段如需输出，按 redacted 或地域 / 前缀派生摘要处理。

## 6. 解释边界

- 设备风险信号不等于最终账号风险定性。
- 字段缺失不等于设备无风险。
- iOS 无 Android-only 字段不等于未检测到对应风险。
- `klink data=[]` 不等于失败。
- `location has_permission=false` 是权限阻断，不是“无位置”。
- 位置接口默认不调用。
