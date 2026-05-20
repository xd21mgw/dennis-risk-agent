# User ↔ Device Entity Resolution Text Regression Run v2.6.0

## 1. Run Metadata

```yaml
run_id: entity_resolution_user_device_text_regression_run_v2_6_0
version: v2.6.0
test_type: main_agent_text_routing_regression
source_cases: computer_use_poc/entity_resolution_user_device_smoke_tests_v2_6_0.md
real_query_performed: false
graphData_called_in_reality: false
device_sdk_called_in_reality: false
batch_query_performed: false
new_interface_added: false
core_skill_modified: false
release_package_updated: false
git_committed: false
overall_result: pass
total_cases: 10
passed_cases: 10
failed_cases: 0
```

## 2. 验证口径

本轮只验证主 Agent 文本层路由和边界，不执行真实 Weapon graphData、Device SDK、用户登录统一日志或其他内部 hand。

当前口径：

- User ↔ Device 双向实体解析主入口统一使用 Weapon `graphData`。
- `user_to_device`: `groupValue={userId}`, `groupKey=USER_ID`, `dimKey=DEVICE_ID`。
- `device_to_user`: `groupValue={deviceId}`, `groupKey=DEVICE_ID`, `dimKey=USER_ID`。
- Device SDK `riskData` 不作为实体解析主入口，只作为后续设备侧风险补证 hand。
- 档案中心用户分析 API 只作为近期关联设备补充排序来源。

## 3. Case Results

### Case 1: userId + hook / frida

```yaml
case_id: entity_resolution_user_device_text_v2_6_0_case_01
user_question: 用户 123456 有没有 hook / frida 风险？
expected_route:
  first_route: user_to_device
  first_hand: weapon_graphData
  graphData_params:
    groupValue: "123456"
    groupKey: USER_ID
    dimKey: DEVICE_ID
  second_route_after_resolved: device_sdk_api_direct_readonly
actual_route:
  first_route: user_to_device
  first_hand: weapon_graphData
  graphData_params:
    groupValue: "123456"
    groupKey: USER_ID
    dimKey: DEVICE_ID
  second_route_after_resolved: device_sdk_api_direct_readonly
boundary_expected:
  - 禁止直接拿 userId 调 Device SDK
  - Device SDK riskData 不作为 user_to_device 主入口
boundary_actual:
  - 先做 Weapon graphData 实体转译
  - 拿到 candidate_device_id 后再进 Device SDK 补证
result: pass
failure_reason: null
recommended_fix: null
```

### Case 2: userId + frida / root / jailbreak

```yaml
case_id: entity_resolution_user_device_text_v2_6_0_case_02
user_question: 用户 123456 有没有 frida / root / jailbreak？
expected_route:
  first_route: user_to_device
  first_hand: weapon_graphData
  graphData_params:
    groupValue: "123456"
    groupKey: USER_ID
    dimKey: DEVICE_ID
  second_route_after_resolved: device_sdk_api_direct_readonly
actual_route:
  first_route: user_to_device
  first_hand: weapon_graphData
  graphData_params:
    groupValue: "123456"
    groupKey: USER_ID
    dimKey: DEVICE_ID
  second_route_after_resolved: device_sdk_api_direct_readonly
boundary_expected:
  - 实体解析只找候选设备，不做风险定性
  - 设备侧风险由 Device SDK hand 补证
boundary_actual:
  - 文本回答会说明先查用户关联设备，再对设备查 frida/root/jailbreak 证据
result: pass
failure_reason: null
recommended_fix: null
```

### Case 3: userId + 改机设备

```yaml
case_id: entity_resolution_user_device_text_v2_6_0_case_03
user_question: 这个用户是不是改机设备？
expected_route:
  first_route: user_to_device
  first_hand: weapon_graphData
  second_route_after_candidate_found: device_sdk_api_direct_readonly
actual_route:
  first_route: user_to_device
  first_hand: weapon_graphData
  second_route_after_candidate_found: device_sdk_api_direct_readonly
boundary_expected:
  - 只能说明该用户关联设备侧证据
  - 不能直接定性用户作弊
boundary_actual:
  - 回答会说明“该用户关联设备是否存在改机线索”，不直接说用户作弊
result: pass
failure_reason: null
recommended_fix: null
```

### Case 4: userId + 登录流水

```yaml
case_id: entity_resolution_user_device_text_v2_6_0_case_04
user_question: 用户 123456 最近登录失败原因是什么？
expected_route:
  route_to: user_login_log_hand
  entity_resolution_needed: false
  graphData_called: false
  device_sdk_called: false
actual_route:
  route_to: user_login_log_hand
  entity_resolution_needed: false
  graphData_called: false
  device_sdk_called: false
boundary_expected:
  - 登录流水问题不需要 user_to_device
boundary_actual:
  - 文本路由直接进入用户登录统一日志，不调用 graphData / Device SDK
result: pass
failure_reason: null
recommended_fix: null
```

### Case 5: userId + 最近登录记录

```yaml
case_id: entity_resolution_user_device_text_v2_6_0_case_05
user_question: 这个用户最近登录记录是什么？
expected_route:
  route_to: user_login_log_hand
  entity_resolution_needed: false
  graphData_called: false
  device_sdk_called: false
actual_route:
  route_to: user_login_log_hand
  entity_resolution_needed: false
  graphData_called: false
  device_sdk_called: false
boundary_expected:
  - 登录记录问题直接走 user_login_log hand
boundary_actual:
  - 文本路由未引入 Entity Resolution
result: pass
failure_reason: null
recommended_fix: null
```

### Case 6: deviceId + 设备环境风险

```yaml
case_id: entity_resolution_user_device_text_v2_6_0_case_06
user_question: ANDROID_xxx 有没有 hook / frida？
expected_route:
  route_to: device_sdk_api_direct_readonly
  entity_resolution_needed: false
  graphData_called: false
actual_route:
  route_to: device_sdk_api_direct_readonly
  entity_resolution_needed: false
  graphData_called: false
boundary_expected:
  - 输入已是 deviceId，不需要 user-device translation
  - 设备 observation 不能单独最终定性
boundary_actual:
  - 文本路由直接进入 Device SDK hand，并保留设备侧补证边界
result: pass
failure_reason: null
recommended_fix: null
```

### Case 7: deviceId + 关联用户

```yaml
case_id: entity_resolution_user_device_text_v2_6_0_case_07
user_question: ANDROID_xxx 关联哪些用户？
expected_route:
  first_route: device_to_user
  first_hand: weapon_graphData
  graphData_params:
    groupValue: ANDROID_xxx
    groupKey: DEVICE_ID
    dimKey: USER_ID
  output:
    - related_user_ids
    - graph_summary
actual_route:
  first_route: device_to_user
  first_hand: weapon_graphData
  graphData_params:
    groupValue: ANDROID_xxx
    groupKey: DEVICE_ID
    dimKey: USER_ID
  output:
    - related_user_ids
    - graph_summary
boundary_expected:
  - 禁止直接定性为团伙作弊
boundary_actual:
  - 回答会输出关联用户摘要，不做风险定性
result: pass
failure_reason: null
recommended_fix: null
```

### Case 8: deviceId + 团伙节点

```yaml
case_id: entity_resolution_user_device_text_v2_6_0_case_08
user_question: 这个设备是不是团伙节点？
expected_route:
  first_route: device_to_user
  first_hand: weapon_graphData
  graphData_params:
    groupValue: "{deviceId}"
    groupKey: DEVICE_ID
    dimKey: USER_ID
  output:
    - related_user_ids
    - graph_summary
    - banned_user_count
    - abnormal_user_count
actual_route:
  first_route: device_to_user
  first_hand: weapon_graphData
  graphData_params:
    groupValue: "{deviceId}"
    groupKey: DEVICE_ID
    dimKey: USER_ID
  output:
    - related_user_ids
    - graph_summary
    - banned_user_count
    - abnormal_user_count
boundary_expected:
  - 关联封禁 / 异常用户是风险线索，不等于团伙作弊定性
boundary_actual:
  - 文本回答会要求结合登录、行为、设备环境和策略证据再判断
result: pass
failure_reason: null
recommended_fix: null
```

### Case 9: 泛化设备风险

```yaml
case_id: entity_resolution_user_device_text_v2_6_0_case_09
user_questions:
  user_id_question: 这个用户有没有设备风险？
  device_id_question: 这个设备有风险吗？
expected_route:
  user_id_question:
    first_route: user_to_device
    first_hand: weapon_graphData
    second_route_after_selected_candidate: device_sdk_api_direct_readonly
  device_id_question:
    route_to: device_sdk_api_direct_readonly
    entity_resolution_needed: false
    graphData_called: false
actual_route:
  user_id_question:
    first_route: user_to_device
    first_hand: weapon_graphData
    second_route_after_selected_candidate: device_sdk_api_direct_readonly
  device_id_question:
    route_to: device_sdk_api_direct_readonly
    entity_resolution_needed: false
    graphData_called: false
boundary_expected:
  - answer_boundary 必须说明设备侧补证不能单独最终定性
boundary_actual:
  - 文本回答保留“设备侧补证，不是最终风险定性”
result: pass
failure_reason: null
recommended_fix: null
```

### Case 10: 候选过多

```yaml
case_id: entity_resolution_user_device_text_v2_6_0_case_10
user_question: 用户 123456 关联了很多设备，都查一下有没有风险
expected_route:
  first_route: user_to_device
  first_hand: weapon_graphData
  if_too_many: too_many_candidates
  default_bulk_deep_check: false
  output:
    - top_candidates
    - rank_reason
    - ask_user_to_narrow_scope
actual_route:
  first_route: user_to_device
  first_hand: weapon_graphData
  if_too_many: too_many_candidates
  default_bulk_deep_check: false
  output:
    - top_candidates
    - rank_reason
    - ask_user_to_narrow_scope
boundary_expected:
  - 不默认批量深查
  - 不默认进入 DataAgent / Hive
  - 不把未覆盖候选解释为全量已查
boundary_actual:
  - 文本回答会要求缩小时间范围、风险事件或指定设备
result: pass
failure_reason: null
recommended_fix: null
```

## 4. Summary

```yaml
summary:
  total_cases: 10
  pass: 10
  fail: 0
  user_to_device_cases:
    total: 4
    pass: 4
  device_to_user_cases:
    total: 2
    pass: 2
  no_entity_resolution_cases:
    total: 3
    pass: 3
  too_many_candidates_cases:
    total: 1
    pass: 1
  graphData_direction_validated:
    user_to_device:
      groupKey: USER_ID
      dimKey: DEVICE_ID
    device_to_user:
      groupKey: DEVICE_ID
      dimKey: USER_ID
  device_sdk_riskData_as_entity_resolution_entry: false
  docs_need_fix: false
  release_package_recommendation: ready_for_release_package_update_after_packaging_review
```

## 5. Findings

未发现需要修正文档的问题。

仍需保留的上线前边界：

- 本轮是文本回归，不是真实 Weapon graphData 查询。
- graphData no_data、permission_blocked、auth blocker 等真实失败语义尚未实跑。
- 候选排序规则仍依赖 graphData 的 `relationDetail / weight / tags / color`，正式接入前应做一轮真实样本回归。
- Device SDK `riskData` 仍只能作为设备侧风险补证，不承担实体解析主入口。
