# User ↔ Device Entity Resolution Smoke Tests v2.6.0

## 1. Case 1: userId 问 hook / frida 风险

```yaml
case_id: entity_resolution_user_device_v2_6_0_case_01
user_question: 用户 123456 有没有 hook / frida 风险？
input_entity: userId
intent: 设备环境风险
expected:
  first_route: user_to_device entity resolution
  first_hand: weapon_graphData
  graphData_params:
    groupValue: "123456"
    groupKey: USER_ID
    dimKey: DEVICE_ID
  second_route: device_sdk_api_direct_readonly
  if_no_deviceId: missing_device_id
forbidden:
  - 直接调用 device SDK 且无 deviceId
  - 把 userId 当 deviceId
  - 把 Device SDK riskData 当作 user_to_device 主入口
```

## 2. Case 2: userId 问改机设备

```yaml
case_id: entity_resolution_user_device_v2_6_0_case_02
user_question: 这个用户是不是改机设备？
input_entity: userId
intent: 设备环境 / 改机风险
expected:
  first_route: user_to_device
  first_hand: weapon_graphData
  second_route_after_candidate_found: device_sdk_api_direct_readonly
  answer_boundary: 只能说明该用户关联设备侧证据，不能直接定性用户作弊
```

## 3. Case 3: userId 问最近登录设备 iOS 风险

```yaml
case_id: entity_resolution_user_device_v2_6_0_case_03
user_question: 这个用户最近登录设备有没有越狱或代理风险？
input_entity: userId
intent: 最近登录设备 + iOS 风险
expected:
  first_route: user_to_device
  first_hand: weapon_graphData
  supplement_source: archives_center_user_analysis_recent_devices 可作为补充排序来源
  second_route: device SDK hand
  ios_normalization_if_applicable: raw UUID，不加 IOS_
  answer_boundary: 登录设备侧补证，不是最终账号风险定性
```

## 4. Case 4: deviceId 问关联用户

```yaml
case_id: entity_resolution_user_device_v2_6_0_case_04
user_question: 设备 ANDROID_xxx 关联哪些用户？
input_entity: deviceId
intent: 设备关联用户
expected:
  route_to: device_to_user resolution
  first_hand: weapon_graphData
  graphData_params:
    groupValue: ANDROID_xxx
    groupKey: DEVICE_ID
    dimKey: USER_ID
  output:
    - related_user_ids summary
    - graph_summary
  answer_boundary: 设备关联关系不能直接等同群控或账号团伙
```

## 5. Case 5: deviceId 问谁在用

```yaml
case_id: entity_resolution_user_device_v2_6_0_case_05
user_question: 这个 deviceId 是谁在用？
input_entity: deviceId
intent: 设备归属 / 使用用户
expected:
  route_to: device_to_user
  first_hand: weapon_graphData
  output:
    - primary_user_id
    - related_user_ids
  forbidden:
    - 直接做风险定性
```

## 6. Case 6: userId 问登录失败

```yaml
case_id: entity_resolution_user_device_v2_6_0_case_06
user_question: 这个用户最近登录失败原因是什么？
input_entity: userId
intent: 登录失败
expected:
  route_to: user_login_log hand
  entity_resolution_needed: false
  graphData_called: false
  device_sdk_called: false
```

## 7. Case 7: userId 问泛化设备风险

```yaml
case_id: entity_resolution_user_device_v2_6_0_case_07
user_question: 这个用户有没有设备风险？
input_entity: userId
intent: 泛化设备风险
expected:
  first_route: user_to_device
  first_hand: weapon_graphData
  if_multiple_devices: rank candidates
  if_too_many: too_many_candidates
  default_bulk_deep_check: false
  second_route_after_selected_candidate: device_sdk hand
```

## 8. Case 8: deviceId 问泛化设备风险

```yaml
case_id: entity_resolution_user_device_v2_6_0_case_08
user_question: 这个设备有风险吗？
input_entity: deviceId
intent: 泛化设备风险
expected:
  no_user_device_translation_needed: true
  route_to: device_sdk hand
  graphData_called: false
  answer_boundary: 设备侧补证，不能单独最终定性
```

## 9. Case 9: deviceId 问团伙节点

```yaml
case_id: entity_resolution_user_device_v2_6_0_case_09
user_question: 这个设备是不是团伙节点？
input_entity: deviceId
intent: 设备关联用户 / 团伙节点
expected:
  first_route: device_to_user
  first_hand: weapon_graphData
  output:
    - related_user_ids
    - graph_summary
    - banned_user_count
    - abnormal_user_count
  forbidden:
    - 直接定性为团伙作弊
```

## 10. Case 10: userId 问关联设备

```yaml
case_id: entity_resolution_user_device_v2_6_0_case_10
user_question: 用户 2241990844 关联哪些设备？
input_entity: userId
intent: 用户关联设备
expected:
  first_route: user_to_device
  first_hand: weapon_graphData
  graphData_params:
    groupValue: "2241990844"
    groupKey: USER_ID
    dimKey: DEVICE_ID
  output:
    - candidate_device_ids
    - graph_summary
  device_sdk_called: false
  note: 除非用户进一步问设备风险，否则不调用 Device SDK
```

## 11. 通过标准

- Case 1 / 2 / 3 / 7 / 10 能先进入 `user_to_device`，主入口为 Weapon graphData。
- Case 4 / 5 / 9 能进入 `device_to_user`，主入口为 Weapon graphData。
- Case 6 不触发 Entity Resolution，不调用 graphData，不调用 Device SDK。
- Case 8 直接进入 Device SDK hand，不额外做 user-device 转译。
- 所有 case 均保留“实体解析不是风险结论”的边界。

## 12. Error Case 1: graphData code != 0

```yaml
case_id: entity_resolution_user_device_v2_6_0_error_01
input: graphData response code != 0 or msg != success
expected:
  status: graphdata_error
  next_action: return_error_summary
forbidden:
  - 解释为无关联
  - 解释为无风险
```

## 13. Error Case 2: graphData auth_required

```yaml
case_id: entity_resolution_user_device_v2_6_0_error_02
input: redirect_to_login / auth expired / no valid cookie
expected:
  status: auth_required
  next_action: 提示需要重新认证态
forbidden:
  - 解释为接口无数据
  - 解释为用户无关联设备
```

## 14. Error Case 3: graphData permission_denied

```yaml
case_id: entity_resolution_user_device_v2_6_0_error_03
input: permission denied / no graphData permission
expected:
  status: permission_denied
  next_action: 提示当前账号无 graphData / 关联图谱权限
forbidden:
  - 解释为无关联
  - 解释为无风险
```

## 15. Error Case 4: user_to_device 无 DEVICE_ID

```yaml
case_id: entity_resolution_user_device_v2_6_0_error_04
input: user_to_device pointInfoMap has no DEVICE_ID candidate
expected:
  status: missing_device_id
  device_sdk_called: false
forbidden:
  - 直接拿 userId 调 Device SDK
  - 输出设备无风险
```

## 16. Error Case 5: device_to_user 无 USER_ID

```yaml
case_id: entity_resolution_user_device_v2_6_0_error_05
input: device_to_user pointInfoMap has no USER_ID candidate
expected:
  status: no_related_user / missing_user_id
forbidden:
  - 解释为设备干净
  - 解释为无风险
```

## 17. Error Case 6: relationEdgeList 为空但 pointInfoMap 有节点

```yaml
case_id: entity_resolution_user_device_v2_6_0_error_06
input:
  pointInfoMap: non_empty
  relationEdgeList: []
expected:
  status: no_direct_relation
  next_action: 保留节点摘要，说明未见直接关联边
forbidden:
  - 解释为没有任何关联线索
  - 解释为无风险
```

## 18. Error Case 7: 候选过多

```yaml
case_id: entity_resolution_user_device_v2_6_0_error_07
input: candidate_count > max_candidates
expected:
  status: too_many_candidates
  next_action: 返回 top candidates，要求缩小范围
forbidden:
  - 默认批量深查
  - 默认进入 DataAgent / Hive
  - 声称已覆盖全量候选
```

## 19. Error Case 8: 返回结构字段缺失

```yaml
case_id: entity_resolution_user_device_v2_6_0_error_08
input: response shape changed / required fields missing
expected:
  status: parse_error
  next_action: 保留 raw_summary，要求人工复核
forbidden:
  - 降级成 no_data
  - 输出无风险结论
```

## 20. Error Case 通过标准

- 8 个 error case 都必须输出执行状态，而不是风险结论。
- auth / permission / parse error 不得解释为无数据。
- no_related_entity / no_direct_relation 不得解释为无风险。
- missing_device_id 时不得调用 Device SDK。
- too_many_candidates 时不得默认批量深查。
