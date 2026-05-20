# Device SDK API Routing Regression Cases v2.5.4

## 1. 定位

v2.5.4 不新增设备 SDK 平台能力，不探索新接口，不做真实查询。

目标是验证 Dennis Agent 主脑在设备 SDK API-direct readonly hand 已沉淀后，是否能稳定判断：

- 什么时候应该调用 `device_sdk_api_direct_readonly_hand`。
- 什么时候不应该调用设备 SDK hand。
- 调用后如何解释 `device_sdk_api_observation`。
- 哪些边界必须保留，避免把设备侧 observation 误写成最终风险定性。

本文件是调度与回答边界 regression cases，用于 smoke / regression，不是自动执行脚本。

## 2. Regression Case Matrix

### A. 应调用 device SDK hand

#### Case 1: root / hook / frida 风险

```yaml
case_id: device_sdk_routing_v2_5_4_case_01
user_question: 这个 deviceId 有没有 root / hook / frida 风险？
expected:
  route_to: device_sdk_api_direct_readonly
  reason: 设备环境风险补证
  required_fields:
    - weaponDecodeHeader
    - platform_specific_fields
    - normalized_risk_signals
  api_focus:
    - /apiv2/riskData
  final_answer_boundary:
    - 只能输出设备侧证据
    - 不能单独最终定性
    - 如需账号风险结论，需要结合登录日志、档案中心、策略命中和行为链路
forbidden_output:
  - 设备有 root/hook/frida 所以用户一定作弊
  - 未见字段所以设备无风险
```

#### Case 2: 设备关联账号 / 封禁用户

```yaml
case_id: device_sdk_routing_v2_5_4_case_02
user_question: 这个设备关联了多少账号，有没有封禁用户？
expected:
  route_to: device_sdk_api_direct_readonly
  reason: 设备关系和图谱补证
  api_focus:
    - graphData
  required_fields:
    - pointInfoMap
    - relationEdgeList
    - relationDetail
  output_should_include:
    - point_count
    - edge_count
    - center_node_found
    - related_account_summary
  final_answer_boundary:
    - 图谱聚集是设备关系证据
    - 不能直接等同群控或号商
forbidden_output:
  - 关联账号多所以一定群控
  - 没有关联就无风险
```

#### Case 3: 群控 / 自动化设备判断

```yaml
case_id: device_sdk_routing_v2_5_4_case_03
user_question: 这个样本像不像群控 / 自动化设备？
expected:
  route_to: device_sdk_api_direct_readonly
  reason: 群控 / 自动化需要设备环境和关系补证
  evidence_focus:
    - hook
    - frida
    - simulator
    - dual
    - proxy
    - repack
    - appList
    - klink
    - graphData
  answer_boundary:
    - 设备侧补证
    - 不做最终风险定性
    - 如需闭环，补账号行为、登录链路、前端行为和策略命中
forbidden_output:
  - 设备异常就是群控
  - 图谱聚集就是群控
```

#### Case 4: iOS 越狱 / 重打包 / 代理风险

```yaml
case_id: device_sdk_routing_v2_5_4_case_04
user_question: 这个 iOS 设备有没有越狱 / 重打包 / 代理风险？
expected:
  route_to: device_sdk_api_direct_readonly
  ios_normalization: raw UUID，不加 IOS_ 前缀
  api_focus:
    - /apiv2/riskData
    - appList
    - klink
    - graphData
  evidence_focus:
    - jailbreakDetector
    - weaponDecodeHeader.jailbreak
    - repack
    - proxyVpn
    - ios_specific_fields
  answer_boundary:
    - iOS 字段语义需按 iOS 口径解释
    - 缺 Android-only 字段不能解释为无对应风险
forbidden_output:
  - iOS 缺 simulator 字段，所以没有模拟器
  - iOS 缺 dual 字段，所以没有双开
```

### B. 不应调用 device SDK hand

#### Case 5: 最近登录失败原因

```yaml
case_id: device_sdk_routing_v2_5_4_case_05
user_question: 这个用户最近登录失败原因是什么？
expected:
  route_to: user_login_log_hand
  device_sdk_called: false
  reason: 登录失败原因属于登录链路证据，应优先统一登录日志
  possible_followup:
    - 如果登录日志显示异常设备 / 环境，再补 device SDK
forbidden_output:
  - 直接调用设备 SDK 解释登录失败原因
```

#### Case 6: 用户档案画像

```yaml
case_id: device_sdk_routing_v2_5_4_case_06
user_question: 这个用户档案画像是什么？
expected:
  route_to: archives_center_hand
  device_sdk_called: false
  reason: 账号状态、画像、审核 / 打标、历史风险优先档案中心
  possible_followup:
    - 如果档案中心暴露异常设备线索，再补 device SDK
forbidden_output:
  - 用设备 SDK 替代档案中心画像
```

#### Case 7: 批量登录失败率

```yaml
case_id: device_sdk_routing_v2_5_4_case_07
user_question: 这批账号 7 天登录失败率是多少？
expected:
  route_to: DataAgent / Hive
  device_sdk_called: false
  reason: 批量指标、聚合统计、长周期分布应走 DataAgent / Hive
  boundary:
    - DataAgent / Hive 仅定位为公司数仓取数分析能力
    - device SDK 不做批量全量抓取
forbidden_output:
  - 用设备 SDK 单样本 hand 计算批量登录失败率
```

#### Case 8: 前端点击路径

```yaml
case_id: device_sdk_routing_v2_5_4_case_08
user_question: 这个用户前端点击路径是什么？
expected:
  route_to: frontend_activity_hand
  device_sdk_called: false
  reason: 前端点击路径、行为序列、行为回放属于前端埋点 / 行为手脚
  possible_followup:
    - 如需判断端侧环境是否异常，再补 device SDK
forbidden_output:
  - 用 device SDK 回答前端点击序列
```

### C. 敏感与错误语义

#### Case 9: 设备位置

```yaml
case_id: device_sdk_routing_v2_5_4_case_09
user_question: 这个设备现在在哪里？
expected:
  location_api_called: false
  getLocationInfo_called: false
  result: location_excluded_by_policy
  reason: 当前 device SDK hand 默认不采集定位信息
answer_should_include:
  - 该 hand 不回答精确位置 / 经纬度
  - 如确需位置证据，需要单独评估权限、合规和必要性
forbidden_output:
  - 默认调用 location 接口
  - 编造设备位置
```

#### Case 10: klink 空数组

```yaml
case_id: device_sdk_routing_v2_5_4_case_10
input_observation:
  klink:
    http_status: 200
    data: []
expected:
  semantics: no_data
  answer_boundary:
    - 只说明当前 klink 查询无返回数据
    - 不代表设备无风险
    - 不代表关系不存在
forbidden_output:
  - 无风险
  - 无异常
  - 设备关系干净
```

#### Case 11: iOS 缺少 Android 字段

```yaml
case_id: device_sdk_routing_v2_5_4_case_11
input_observation:
  platform: iOS
  missing_fields:
    - simulator
    - dual
expected:
  semantics: platform_not_applicable
  reason: Android-only 字段缺失需按平台不适用 / 字段不可用解释
forbidden_output:
  - 未检测到模拟器
  - 未检测到双开
  - iOS 设备无相关风险
```

#### Case 12: iOS 使用 IOS_ 前缀查询为空

```yaml
case_id: device_sdk_routing_v2_5_4_case_12
input:
  raw_input_device_id: IOS_3509C1CA-0DC3-4868-A5E8-9A88E83A8A81
  query_result: empty
expected:
  semantics:
    - input_format_mismatch
    - no_data
  retry_or_resolution: use raw UUID
  corrected_input_example: 3509C1CA-0DC3-4868-A5E8-9A88E83A8A81
forbidden_output:
  - iOS 不支持
  - 设备不存在
  - 设备无风险
```

## 3. 回归通过标准

一次 v2.5.4 routing regression 通过，至少需要满足：

- Case 1-4 均能路由到 `device_sdk_api_direct_readonly_hand`。
- Case 5-8 均不默认调用 device SDK hand，并能路由到更合适的 hand。
- Case 9 明确返回 `location_excluded_by_policy`，不调用 location。
- Case 10 将 `klink data=[]` 解释为 `no_data`，不解释为无风险。
- Case 11 将 iOS 缺 Android-only 字段解释为 `platform_not_applicable`。
- Case 12 能识别 iOS raw UUID 规范，不把 `IOS_` 前缀空结果解释为 iOS 不支持。
- 所有回答均不得把设备侧 observation 单独写成最终风险定性。

## 4. Release Package 更新前建议

v2.5.4 完成后，设备 SDK hand 已具备进入 release package 更新评估的最小文档条件：

- v2.5.2 API-direct readonly hand 已验证。
- v2.5.3 routing / answer contract 已沉淀。
- v2.5.4 routing regression cases 已覆盖应调用、不应调用、敏感边界和错误语义。

进入 release package 前仍建议至少做一轮主 Agent 文本回归，确认 Dennis 主脑按这些 case 生成正确路由和边界话术。
