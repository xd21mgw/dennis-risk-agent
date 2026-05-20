# Device SDK API Routing Rules v2.5.3

## 1. 定位

v2.5.3 不新增设备 SDK 平台能力，只补齐 Dennis Agent 主脑对 `device_sdk_api_direct_readonly_hand` 的调度规则。

目标：

- 判断什么时候应该调用设备 SDK hand。
- 判断什么时候不应该调用设备 SDK hand。
- 防止把设备侧 observation 误当成最终风险定性。
- 防止将定位问题、登录流水问题、Hive 聚合问题误路由到设备 SDK。

## 2. 适合调用 device_sdk hand 的问题

当用户问题需要设备侧补证时，可以调用 `device_sdk_api_direct_readonly_hand`。

典型触发场景：

- 需要判断设备环境风险。
- 需要补证 root / jailbreak / hook / frida / 模拟器 / 双开 / debug / proxy / repack。
- 需要查看 SDK 采集状态。
- 需要查看设备与账号 / app / 图谱关系。
- 需要判断 deviceId 是否近期重置、低启动、异常环境、关联封禁账号。
- 需要为 ATO / 插件 / 群控 / 自动化 / 改机风险补设备证据。

典型用户问法：

- “这个 deviceId 有没有 root / hook 风险？”
- “这个设备是不是模拟器 / 双开？”
- “这个设备环境正常吗？”
- “这个设备关联了多少账号？”
- “这个设备有没有关联封禁账号？”
- “这个 ATO case 需要补设备侧证据。”
- “这个疑似插件 / 改机 / 自动化，设备侧先看什么？”

## 3. 不适合调用 device_sdk hand 的问题

| 用户问题类型 | 优先手脚 | 设备 SDK 角色 |
|---|---|---|
| 纯登录流水、登录失败、token、OAuth、扫码 | 用户登录统一日志 | 后续补设备环境 |
| 用户画像、账号状态、审核 / 打标、历史风险 | 档案中心 | 后续补设备侧风险 |
| Hive 聚合统计、批量样本、长周期指标 | DataAgent / Hive | 不替代数仓 |
| 前端操作行为细查、行为序列、行为回放 | 前端埋点 / 行为手脚 | 后续补设备环境 |
| 精确定位、经纬度、位置轨迹 | 默认不查 location | 返回 location_excluded_by_policy |

明确不触发：

- “这个用户最近登录失败原因是什么？”优先统一登录日志。
- “这个用户档案状态是什么？”优先档案中心。
- “批量看一万设备风险分布。”优先 DataAgent / Hive 或离线能力。
- “这个设备在哪里？”本 hand 默认不采集 location。

## 4. 最小入参

```yaml
required_inputs:
  raw_input_device_id:
    required: true
    examples:
      - ANDROID_fc1963b93f823ebd
      - 3509C1CA-0DC3-4868-A5E8-9A88E83A8A81
optional_inputs:
  suspected_platform:
  product:
  time_window:
  related_user_id:
```

如缺少 deviceId / did，应先追问或从上游 observation 取已确认的 deviceId。

补充 v2.6.0 实体解析规则：

- Device SDK hand 的直接入参是 `deviceId / did / deviceceid`。
- 如果用户输入的是 `userId`，但询问 hook / frida / root / jailbreak / 改机 / 模拟器 / 双开 / proxy / repack 等设备风险，不得直接调用 Device SDK hand。
- 此时应先进入 `User → Device Entity Resolution Layer`，主入口使用 Weapon `graphData`：
  - `groupValue={userId}`
  - `groupKey=USER_ID`
  - `dimKey=DEVICE_ID`
- 找到 `candidate_device_id` 后，再调用 Device SDK hand。
- 找不到时返回 `missing_device_id`；候选过多时返回 `too_many_candidates`，不默认批量深查。
- Device SDK `riskData` 本轮不作为 `user_to_device` 主实体解析入口，只负责拿到 deviceId 后的设备侧风险补证。

## 5. deviceId normalization 路由规则

```yaml
device_id_normalization:
  android:
    rule: 保留 ANDROID_ 前缀
    example: ANDROID_fc1963b93f823ebd
  ios:
    rule: 使用 raw UUID，不加 IOS_ 前缀
    example: 3509C1CA-0DC3-4868-A5E8-9A88E83A8A81
  ios_wrong_prefix:
    input: IOS_<uuid>
    interpretation: no_data_by_wrong_input_format
    forbidden_interpretation:
      - iOS 不支持
      - 设备无风险
  harmony:
    status: pending_validation
```

## 6. 查询计划模板

```yaml
device_sdk_query_plan:
  intent: device_sdk_evidence_check
  tool_name: device_sdk_api_direct_readonly_hand
  query:
    raw_input_device_id:
    normalized_input_device_id:
    platform_guess:
    location_extraction_enabled: false
  api_sequence:
    - /apiv2/riskData
    - appList
    - klink
    - graphData
  excluded_by_policy:
    - location
  expected_outputs:
    - identity.canonical_device_id
    - identity.user_id
    - identity.platform
    - identity.weapon_platform
    - normalized_device_fields
    - normalized_risk_signals
    - app_list_summary
    - klink_summary
    - graph_summary
  readonly_boundary:
    batch_query_allowed: false
    final_risk_classification_allowed: false
    enforcement_allowed: false
```

## 7. Observation 消费规则

- `/apiv2/riskData` 是主接口，用于确认 canonical device、user_id、platform / weaponPlatform 和核心设备字段。
- appList / klink / graphData 是派生补证接口。
- location 默认不调用。
- `no_data` 不等于设备无风险。
- `permission_blocked` 不等于设备无数据。
- `platform_not_applicable` 不等于未检测到。
- iOS 无 simulator / dual 字段不能解释为无模拟器 / 无双开。
- 设备图谱关系用于补证，不直接等同群控。

## 8. 与其他手脚组合关系

| 场景 | 设备 SDK 作用 | 组合手脚 |
|---|---|---|
| ATO / 异常登录 | 补设备环境、设备一致性、root / hook / proxy 线索 | 用户登录统一日志、档案中心 |
| 协议上号 | 补 SDK 采集状态、端侧环境异常 | 登录统一日志、前端埋点 |
| 群控 / 号商 | 补 graphData 关系、设备聚集和风险标签 | 档案中心关联图谱、DataAgent / Hive |
| 插件 / 破解包 | 补 hook / frida / repack / debug 线索 | 前端埋点、策略命中 |
| 自动化 / 改机 | 补模拟器、多开、proxy、设备重置线索 | 登录日志、行为链路 |

## 9. 禁止事项

- 不默认调用 location。
- 不用设备单源 observation 下最终结论。
- 不把 `no_data` 写成无风险。
- 不把 `platform_not_applicable` 写成未检测到风险。
- 不把 iOS 缺少 Android 字段写成 iOS 无风险。
- 不把 graphData 关系聚集直接写成群控。
- 不替代统一登录日志、档案中心、前端埋点或 DataAgent / Hive。
