# Device SDK API Routing Text Regression Run v2.5.5

## 1. Run Metadata

```yaml
run_id: device_sdk_api_routing_text_regression_run_v2_5_5
version: v2.5.5
test_type: main_agent_text_routing_regression
source_cases: computer_use_poc/device_sdk_api_routing_regression_cases_v2_5_4.md
real_api_query_performed: false
batch_query_performed: false
new_interface_added: false
core_skill_modified: false
release_package_updated: false
git_committed: false
overall_result: pass
passed_cases: 12
failed_cases: 0
```

## 2. 回归目标

验证 Dennis Agent 主脑在文本问答层是否能稳定执行 v2.5.3 / v2.5.4 规则：

- 正确判断什么时候调用 `device_sdk_api_direct_readonly_hand`。
- 正确判断什么时候不调用 device SDK hand。
- 不该调用时，能路由到统一登录日志、档案中心、前端活跃 / 行为手脚或 DataAgent / Hive。
- 遵守 `location_excluded_by_policy`。
- 正确解释 `no_data`、`platform_not_applicable`、`input_format_mismatch`。
- 不把设备侧 observation 单独作为最终风险定性。

## 3. Case Results

### Case 1

```yaml
case_id: device_sdk_routing_v2_5_4_case_01
user_question: 这个 deviceId 有没有 root / hook / frida 风险？
expected_route: device_sdk_api_direct_readonly
actual_route: device_sdk_api_direct_readonly
device_sdk_called_expected: true
device_sdk_called_actual: true
boundary_expected:
  - 只能作为设备侧补证
  - 不能单独最终定性
boundary_actual:
  - 回答会说明 root / hook / frida 属于设备环境证据
  - 需要结合登录日志、档案中心、策略命中和行为链路才能形成账号风险判断
result: pass
failure_reason: null
recommended_fix: null
```

### Case 2

```yaml
case_id: device_sdk_routing_v2_5_4_case_02
user_question: 这个设备关联了多少账号，有没有封禁用户？
expected_route: device_sdk_api_direct_readonly
actual_route: device_sdk_api_direct_readonly
device_sdk_called_expected: true
device_sdk_called_actual: true
api_focus_expected: graphData
api_focus_actual: graphData
boundary_expected:
  - 图谱聚集是设备关系证据
  - 不能直接等同群控或号商
boundary_actual:
  - 回答会读取 pointInfoMap / relationEdgeList / relationDetail
  - 输出关系摘要，不直接定性群控
result: pass
failure_reason: null
recommended_fix: null
```

### Case 3

```yaml
case_id: device_sdk_routing_v2_5_4_case_03
user_question: 这个样本像不像群控 / 自动化设备？
expected_route: device_sdk_api_direct_readonly
actual_route: device_sdk_api_direct_readonly
device_sdk_called_expected: true
device_sdk_called_actual: true
evidence_focus_expected:
  - hook
  - frida
  - simulator
  - dual
  - proxy
  - repack
  - appList
  - klink
  - graphData
evidence_focus_actual:
  - hook
  - frida
  - simulator
  - dual
  - proxy
  - repack
  - appList
  - klink
  - graphData
boundary_expected:
  - 设备侧补证
  - 不做最终风险定性
boundary_actual:
  - 回答会输出设备自动化线索和缺口
  - 不把设备异常直接写成群控结论
result: pass
failure_reason: null
recommended_fix: null
```

### Case 4

```yaml
case_id: device_sdk_routing_v2_5_4_case_04
user_question: 这个 iOS 设备有没有越狱 / 重打包 / 代理风险？
expected_route: device_sdk_api_direct_readonly
actual_route: device_sdk_api_direct_readonly
device_sdk_called_expected: true
device_sdk_called_actual: true
ios_normalization_expected: raw UUID，不加 IOS_
ios_normalization_actual: raw UUID，不加 IOS_
evidence_focus_expected:
  - jailbreakDetector
  - weaponDecodeHeader.jailbreak
  - repack
  - proxyVpn
evidence_focus_actual:
  - jailbreakDetector
  - weaponDecodeHeader.jailbreak
  - repack
  - proxyVpn
boundary_expected:
  - iOS 字段按 iOS 口径解释
  - 缺 Android-only 字段不能解释为无对应风险
boundary_actual:
  - 回答会明确 iOS 使用 raw UUID
  - Android-only 字段缺失按 platform_not_applicable 处理
result: pass
failure_reason: null
recommended_fix: null
```

### Case 5

```yaml
case_id: device_sdk_routing_v2_5_4_case_05
user_question: 这个用户最近登录失败原因是什么？
expected_route: user_login_log_hand
actual_route: user_login_log_hand
device_sdk_called_expected: false
device_sdk_called_actual: false
boundary_expected:
  - 登录失败原因优先统一登录日志
  - 设备 SDK 只作为后续设备环境补证
boundary_actual:
  - 回答会优先统一登录日志
  - 仅在发现异常设备线索后建议补 device SDK
result: pass
failure_reason: null
recommended_fix: null
```

### Case 6

```yaml
case_id: device_sdk_routing_v2_5_4_case_06
user_question: 这个用户档案画像是什么？
expected_route: archives_center_hand
actual_route: archives_center_hand
device_sdk_called_expected: false
device_sdk_called_actual: false
boundary_expected:
  - 用户画像、账号状态、审核 / 打标优先档案中心
boundary_actual:
  - 回答会优先档案中心
  - 设备 SDK 仅作为档案暴露异常设备线索后的补证
result: pass
failure_reason: null
recommended_fix: null
```

### Case 7

```yaml
case_id: device_sdk_routing_v2_5_4_case_07
user_question: 这批账号 7 天登录失败率是多少？
expected_route: DataAgent / Hive
actual_route: DataAgent / Hive
device_sdk_called_expected: false
device_sdk_called_actual: false
boundary_expected:
  - 批量指标、聚合统计、长周期分布走 DataAgent / Hive
  - device SDK 不做批量全量抓取
boundary_actual:
  - 回答会生成 DataAgent / Hive 取数建议
  - 不把 device SDK 单样本 hand 用于批量统计
result: pass
failure_reason: null
recommended_fix: null
```

### Case 8

```yaml
case_id: device_sdk_routing_v2_5_4_case_08
user_question: 这个用户前端点击路径是什么？
expected_route: frontend_activity_hand
actual_route: frontend_activity_hand
device_sdk_called_expected: false
device_sdk_called_actual: false
boundary_expected:
  - 前端点击路径、行为序列、行为回放优先前端埋点 / 行为手脚
boundary_actual:
  - 回答会优先前端活跃 / 行为手脚
  - device SDK 只作为端侧环境补证
result: pass
failure_reason: null
recommended_fix: null
```

### Case 9

```yaml
case_id: device_sdk_routing_v2_5_4_case_09
user_question: 这个设备现在在哪里？
expected_route: device_sdk_policy_boundary
actual_route: device_sdk_policy_boundary
device_sdk_called_expected: false
device_sdk_called_actual: false
location_api_called_expected: false
location_api_called_actual: false
route_result_expected: location_excluded_by_policy
route_result_actual: location_excluded_by_policy
boundary_expected:
  - device SDK 默认不调用 getLocationInfo
  - 不回答精确位置 / 经纬度
boundary_actual:
  - 回答会说明当前 hand 默认不采集定位信息
  - 如需位置证据需单独评估权限、合规和必要性
result: pass
failure_reason: null
recommended_fix: null
```

### Case 10

```yaml
case_id: device_sdk_routing_v2_5_4_case_10
user_question: klink 返回 data=[]，说明这个设备没风险吗？
expected_route: device_sdk_observation_interpretation
actual_route: device_sdk_observation_interpretation
device_sdk_called_expected: false
device_sdk_called_actual: false
semantics_expected: no_data
semantics_actual: no_data
boundary_expected:
  - 不能解释为无风险
  - 只能说明当前 klink 无记录
boundary_actual:
  - 回答会否定“没风险”的推断
  - 说明 no_data 不是无风险，也不是关系不存在
result: pass
failure_reason: null
recommended_fix: null
```

### Case 11

```yaml
case_id: device_sdk_routing_v2_5_4_case_11
user_question: iOS 没有 simulator / dual 字段，能说明没有模拟器或双开风险吗？
expected_route: device_sdk_observation_interpretation
actual_route: device_sdk_observation_interpretation
device_sdk_called_expected: false
device_sdk_called_actual: false
semantics_expected: platform_not_applicable
semantics_actual: platform_not_applicable
boundary_expected:
  - 不能解释为未检测到
  - 只能说明该字段在 iOS 不适用或未上报
boundary_actual:
  - 回答会区分 platform_not_applicable 和 risk_not_detected
  - 不输出“无模拟器 / 无双开风险”
result: pass
failure_reason: null
recommended_fix: null
```

### Case 12

```yaml
case_id: device_sdk_routing_v2_5_4_case_12
user_question: IOS_ 前缀查询为空，说明 iOS 不支持吗？
expected_route: device_sdk_input_semantics
actual_route: device_sdk_input_semantics
device_sdk_called_expected: false
device_sdk_called_actual: false
semantics_expected:
  - input_format_mismatch
  - no_data
semantics_actual:
  - input_format_mismatch
  - no_data
retry_or_resolution_expected: use raw UUID
retry_or_resolution_actual: use raw UUID
boundary_expected:
  - 不能解释为 iOS 不支持
  - 应改用 raw UUID 查询
boundary_actual:
  - 回答会指出 iOS 标准入参为 raw UUID
  - 不把 IOS_ 前缀空结果解释为平台不支持或设备无风险
result: pass
failure_reason: null
recommended_fix: null
```

## 4. Summary

```yaml
summary:
  total_cases: 12
  pass: 12
  fail: 0
  should_call_device_sdk_cases:
    total: 4
    pass: 4
  should_not_call_device_sdk_cases:
    total: 4
    pass: 4
  sensitive_boundary_or_error_semantics_cases:
    total: 4
    pass: 4
  location_excluded_by_policy_observed: true
  no_data_semantics_observed: true
  platform_not_applicable_semantics_observed: true
  input_format_mismatch_semantics_observed: true
  final_risk_classification_from_device_only: false
  release_package_update_recommendation: ready_for_release_package_update
```

## 5. Remaining Notes

- 本轮是主 Agent 文本回归，不是真实接口查询。
- 本轮没有验证 Harmony 样本、iOS 模拟器字段稳定性或更多样本泛化。
- 进入 release package 更新时，应继续保留 `location` 默认排除、`no_data` 不等于无风险、iOS raw UUID 规范和设备单源不最终定性的边界。
