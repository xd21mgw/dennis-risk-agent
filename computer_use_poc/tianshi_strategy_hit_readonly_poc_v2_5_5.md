# v2.5.5 天狮策略平台极简 readonly 手脚

## 1. 定位

v2.5.5 是 Dennis Agent 的天狮策略平台 / rcp 极简只读手脚沉淀。

当前能力只覆盖：

- 查询类型：`fastQueryHbase`
- 能力：`readonly_strategy_hit_check`
- 目标：判断 `sourceId` 在指定时间窗口内是否命中生产反作弊 / 风控策略。

该手脚用于补充“线上策略是否命中”的策略证据，不负责最终作弊定性，也不负责处置。

## 2. 已验证范围

本轮结果来自内部 Agent 已验证返回，不是 Codex 直接访问平台。

```yaml
platform: tianshi_strategy_platform_rcp
query_type: fastQueryHbase
capability: readonly_strategy_hit_check
source_id: "4231737183"
query_status: success
api_response_status: 200
raw_record_count: 4
has_strategy_hit: true
production_policy_hit_count: 4
evidence_strength: strong
riskDecision_distribution:
  阻止: 3
  验证: 1
eventType_distribution:
  USER_REGISTER_NEW: 3
  LOGIN_AUDIT: 1
riskType_distribution:
  其他: 3
  账号: 1
confidence_distribution:
  强: 4
```

## 3. 标准判断规则

```yaml
decision_rules:
  query_success:
    condition:
      - status == 200
      - message == 成功
    output: query_status=success
  raw_record_count:
    condition: data 数组非空
    output: raw_record_count > 0
  strategy_hit:
    condition: 任一 data[*].hitProductionPolicy == true
    output: has_strategy_hit=true
  production_policy_hit_count:
    rule: 统计 hitProductionPolicy == true 的记录数
  distributions:
    fields:
      - riskDecision
      - eventType
      - riskType
    rule: 做简单分布统计
  sample_hits:
    max_items: 3
  trace_policy:
    host: not_in_standard_observation
    port: not_in_standard_observation
    traceId: not_in_standard_observation
    has_trace: allowed_boolean_only
```

## 4. Observation schema

```yaml
tianshi_strategy_hit_observation:
  platform: tianshi_strategy_platform_rcp
  query_type: fastQueryHbase
  capability: readonly_strategy_hit_check
  query_object: sourceId
  query_value_policy: source_id_allowed
  time_window:
  query_status:
  api_response_status:
  api_message:
  raw_record_count:
  has_strategy_hit:
  production_policy_hit_count:
  evidence_strength:
  riskDecision_distribution:
  eventType_distribution:
  riskType_distribution:
  confidence_distribution:
  sample_hits:
    max_items: 3
    fields:
      - riskDecision
      - eventType
      - riskType
      - confidence
      - hitProductionPolicy
  trace_observation:
    has_trace:
    trace_value_policy: not_recorded
  readonly_safety_check:
  limitations:
```

## 5. 解释规则

- `has_strategy_hit=true` 说明当前查询条件下存在生产策略命中记录。
- `production_policy_hit_count` 是命中生产策略的记录数，不等于最终处置成功次数。
- `riskDecision=阻止 / 验证` 代表策略返回动作，不代表最终执行成功。
- `eventType` 可用于区分命中发生在注册、登录审核等链路。
- `riskType` 可用于粗分账号、其他等风险类型，但不能单独作为本质定性。
- 置信度为“强”代表策略侧信号强，不等于单源证据足以输出最终作弊结论。

## 6. 边界

- 天狮命中是策略证据，不等于最终作弊定性。
- 无命中不代表无风险，可能是时间窗不对、策略未覆盖、数据缺失或离线链路另有证据。
- 该手脚不替代 DataAgent / Hive。
- 该手脚不替代用户登录统一日志、档案中心、前端埋点、设备 SDK / 设备平台。
- 该手脚不做自动处罚、封禁、冻结、审批或策略上线。
- 该手脚不记录 `host`、`port`、`traceId` 原值；如需表达链路可用性，只记录 `has_trace=true/false`。

## 7. 下一步建议

当天狮策略命中需要继续解释时：

- 账号安全 / 登录链路：补用户登录统一日志、档案中心、设备 SDK。
- 前端活跃 / 行为真实性：补前端活跃画像或行为序列。
- 批量归因 / 长周期统计：转 DataAgent / Hive。
- 策略误伤：补策略配置、命中样本、审核 / 打标日志、业务后验表现。
