# realtime_entity_batch_design v0.1

> **⚠️ v0.1 版本口径**：normal_baseline v0.1 是静态快照 baseline，不自动刷新，不创建实时 pipeline。本文档仅为未来实时设计的参考。

## 定位

实时 entity batch 设计文档（v0.1 仅保留设计，不做实现）。

目标是支持后续将 normal_baseline 用于实时场景：
- 当 Dennis Agent 研判一个具体 entity（如 userId）时，
- 可以从 normal_baseline 中查找对应分层的 normal 侧统计参考，
- 用于判断该 entity 的某个 field_value 是否在 normal 侧是大众值 / 低熵 / 不大众。

## 设计理念

normal_baseline 当前是 batch 级离线资产，不是实时查询服务。

实时 entity batch 的目标是：
1. 预加载分层 baseline 的 low_entropy_profile 到内存
2. 当具体 entity 的 field_value 需要参考时，快速查找对应分层的 normal_status
3. 不做实时 profiler，只做查找

## 架构草图

```
[具体 entity 研判请求]
    ↓
[Dennis Agent / L4 模块]
    ↓
[normal_baseline 实时查找接口]
    ↓
[预加载的 low_entropy_profile 内存索引]
    ↓
[返回: field_value -> normal_status 映射]
```

## 数据流

### 离线侧

1. DataAgent 定期抽取各分层样本（daily / weekly）
2. local profiler 生成各分层 baseline 资产
3. baseline 资产存储为 YAML/JSON 文件

### 实时侧

1. baseline 加载器：启动时从文件加载 low_entropy_profile 到内存
2. 分层索引：按 segment_key 组织内存索引
3. entity lookup API：接受 (segment_key, field_path, field_value) → 返回 normal_status
4. 缓存策略：baseline 文件变更时增量更新内存索引

## 接口设计

```yaml
realtime_lookup_request:
  segment_key: "LOGIN_AUE_52_mature_user_medium_follower_success"
  field_path: "deviceInfo.deviceModel"
  field_value: "OPPO A5"
  lookup_mode: field_value_grain  # field_value 粒度查找

realtime_lookup_response:
  segment_key: "LOGIN_AUE_52_mature_user_medium_follower_success"
  field_path: "deviceInfo.deviceModel"
  field_value: "OPPO A5"
  field_value_norm: "deviceInfo.deviceModel=OPPO+A5"
  normal_status: normal_popular
  top1_ratio: 0.92
  coverage_ratio: 0.95
  sample_entity_count: 3500
  rule_source: "sample_low_entropy_rule_v0_1"
  sampling_bias_declaration:
    scene_bias: "仅来自 LOGIN_AUE 登录验证成功后"
    # ... 其他偏置
```

## 边界声明

1. 实时查找只返回 normal_status，不做风险判断
2. normal_popular 不等于白用户，不等于无风险
3. normal_not_popular_in_sample 不等于风险嫌疑
4. 消费方必须自行声明使用偏置
5. 不做 automatic entity expansion
6. 不接入 Dennis runtime（消费方自行选择是否使用）
7. 不实时 profiler，只查找预计算 baseline
8. 实时查找超时或 baseline 缺失时，返回 `normal_unknown_sampling_bias`

## v0.1 状态

- 只有设计文档，不做实现
- 不创建实时服务
- 不创建加载器
- 不创建内存索引
- 不创建 API 接口
- 等后续 profiler 实现后再考虑实时查找