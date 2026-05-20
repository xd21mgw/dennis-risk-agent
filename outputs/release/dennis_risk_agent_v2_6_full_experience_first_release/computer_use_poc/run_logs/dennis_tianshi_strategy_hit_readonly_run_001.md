# Dennis 天狮策略平台 readonly Run 001

## 1. 测试目标

验证 Dennis Agent 可消化内部 Agent 返回的天狮策略平台 / rcp 极简只读查询结果，用于判断指定 `sourceId` 在指定时间窗口内是否命中生产反作弊 / 风控策略。

本 run log 仅沉淀内部 Agent 已验证结果。Codex 未访问内部平台。

## 2. 执行结果

```yaml
test_stage: v2.5.5
platform: tianshi_strategy_platform_rcp
query_type: fastQueryHbase
capability: readonly_strategy_hit_check
query_object: sourceId
query_value: "4231737183"
query_status: success
api_response_status: 200
api_message: 成功
raw_record_count: 4
has_strategy_hit: true
production_policy_hit_count: 4
evidence_strength: strong
```

## 3. 分布统计

```yaml
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

## 4. 固化判断规则

```yaml
status_200_and_message_success:
  output: query_status=success
data_non_empty:
  output: raw_record_count > 0
any_hitProductionPolicy_true:
  output: has_strategy_hit=true
production_policy_hit_count:
  rule: count(data[*].hitProductionPolicy == true)
distribution_fields:
  - riskDecision
  - eventType
  - riskType
sample_hits_max_items: 3
trace_policy:
  host: not_recorded
  port: not_recorded
  traceId: not_recorded
  has_trace: boolean_only
```

## 5. 已验证范围

- 查询成功。
- API 状态为 200，message 为成功。
- data 数组非空。
- 4 条记录均命中生产策略。
- 可统计 `riskDecision`、`eventType`、`riskType`、置信度分布。
- 只读安全边界通过。

## 6. 边界

- 天狮命中是策略证据，不等于最终作弊定性。
- `riskDecision=阻止/验证` 代表策略返回动作，不代表最终执行成功。
- 无命中不代表无风险。
- 本手脚不替代 DataAgent / Hive、用户登录统一日志、档案中心、前端埋点、设备 SDK / 设备平台。
- 不记录 `host`、`port`、`traceId` 原值。

## 7. 当前结论

```yaml
validation_status: tianshi_strategy_hit_readonly_validated
readonly_strategy_hit_check: validated
schema_ready: true
release_package_updated: false
core_skill_modified: false
```
