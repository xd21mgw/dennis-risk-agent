# Device SDK API Answer Contract v2.5.3

## 1. 定位

该 contract 定义 Dennis Agent 如何消化 `device_sdk_api_observation`，并在最终回答中解释设备侧证据。

设备 SDK observation 只能作为设备侧补证，不单独给最终风险结论。

## 2. 推荐回答结构

```yaml
device_evidence_answer:
  current_judgement:
  device_identity:
  device_environment_findings:
  relation_findings:
  evidence_strength:
    strong_device_evidence:
    medium_device_evidence:
    weak_or_contextual_evidence:
  counter_evidence:
  missing_evidence:
  next_checks:
  boundary_notes:
```

短答中不必强制展示所有标题，但内容必须覆盖：

- 当前只是设备侧证据。
- 已观察到的设备身份和风险信号。
- 证据强弱。
- 缺口与下一步。
- 不做最终风险定性。

## 3. 证据强弱分层

### 强证据

以下是强设备侧风险证据，但仍不等于最终账号风险定性：

- 明确 root / jailbreak。
- 明确 hook。
- 明确 frida。
- 明确 simulator / emulator。
- 明确 proxy / VPN 高风险环境。
- 明确 repack / tamper。
- 强风险标签。
- 关联封禁图谱 / 高风险设备图谱。

### 中证据

以下属于中等强度设备侧线索，需要结合登录 / 账号 / 行为补证：

- 低启动。
- 近期重置。
- SDK 异常。
- 设备环境异常。
- appList 异常。
- klink 异常。
- graphData 关系异常但未形成闭环。
- 设备型号、系统版本、APP 版本与登录链路不一致。

### 弱证据

以下只能作为上下文或弱线索：

- 字段缺失。
- 空数组。
- 单个普通 app。
- 无风险标签。
- 单一设备字段为空。
- 平台不适用字段。

## 4. no_data / platform_not_applicable 解释规则

- `no_data` 不能解释为无风险。
- `platform_not_applicable` 不能解释为未检测到。
- 字段缺失不能解释为设备正常。
- `klink data=[]` 是 no_data，不是接口失败，也不是无风险。
- iOS 无 simulator / dual 字段不能解释为无模拟器 / 无双开。
- `IOS_` 前缀查询为空不能解释为 iOS 不支持。

## 5. location 解释规则

location 默认不采集。

如果用户问“这个设备在哪里 / 经纬度 / 位置轨迹”：

```yaml
location_answer:
  status: location_excluded_by_policy
  explanation: 当前 device_sdk_api_direct_readonly hand 默认不采集定位信息。
  allowed_next_step: 如业务确需位置证据，需要单独确认权限、合规边界和最小必要字段。
```

禁止：

- 默认调用 location。
- 用 location 未采集回答“无位置”。
- 输出经纬度或位置明文。

## 6. 与其他证据的组合

设备 SDK observation 应与其他手脚组合解释：

- 登录链路：用户登录统一日志。
- 账号画像 / 历史风险：档案中心。
- 前端行为：前端埋点手脚。
- 策略命中：天狮 strategy_hit / eventList。
- 批量统计：DataAgent / Hive。

设备侧强证据 + 登录链路异常 + 档案中心风险画像一致时，结论置信度可提升。

单设备证据命中但其他证据缺失时，只能输出 `strong_suspicion` 或 `needs_more_evidence`，不能输出 definitive conclusion。

## 7. 输出话术模板

### 7.1 设备环境风险

```text
这个问题适合调用设备 SDK hand，因为你问的是设备环境风险。

我会优先看 riskData，再补 appList / klink / graphData。location 默认不采集。

如果返回 root / jailbreak / hook / frida / 模拟器 / proxy / repack 等明确字段，可以作为强设备侧证据；但它仍然不是最终账号风险定性，需要结合登录日志、档案中心或行为链路。
```

### 7.2 设备关系

```text
这个问题适合补 graphData。graphData 可以看设备与账号 / app / 关系节点的结构，但设备关系聚集不直接等同群控。

如果关系异常，需要再结合账号行为、登录链路、策略命中和业务后验判断。
```

### 7.3 location 问题

```text
当前 device SDK hand 默认不采集 location，因此不能直接回答精确位置。

这不是“无位置”，而是 location_excluded_by_policy。若确实需要位置证据，应单独确认权限、合规边界和最小必要字段。
```

## 8. 禁止误判清单

- 不把设备侧 observation 当最终风险结论。
- 不把 no_data 当无风险。
- 不把字段缺失当无风险。
- 不把 iOS 缺少 Android 字段当未检测到风险。
- 不把 iOS 无 simulator / dual 字段当无模拟器 / 无双开。
- 不把 graphData 关系聚集直接当群控。
- 不把 location 未采集当无位置。
- 不输出完整原始 JSON。
- 不输出 token / session / ticket / authorization / cookie 明文。
