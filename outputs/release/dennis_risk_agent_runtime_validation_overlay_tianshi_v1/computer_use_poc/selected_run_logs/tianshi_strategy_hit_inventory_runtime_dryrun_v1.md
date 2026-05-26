# Tianshi Strategy Hit Inventory Runtime Dry-run v1

## Goal

验证 `tianshi_strategy_hit_inventory` 轻量接入 Dennis Agent runtime 后，路由、回答模板和边界是否稳定。

本轮是文本级 dry-run：

- 不访问真实平台。
- 不调用 DataAgent。
- 不更新 release package。
- 不修改核心 Skill。
- 不提交 git。

## Capability Under Test

```yaml
capability_id: tianshi_strategy_hit_inventory
positioning: 天狮策略命中盘点能力
purpose: 从 user/source_id 维度盘点策略命中概览、TOP 策略、TOP 节点、TOP 条件、策略共现和代表事件
sub_capabilities:
  strategy_hit_overview_lookup:
    primary_entry: fastQueryHbase
    input: source_id + time_window
    output_fields:
      - eventId
      - eventType
      - riskDecision
      - hitPolicies
      - hitProductionPolicies
      - confidenceLevel
      - riskType
  event_type_detail_supplement:
    entry: eventList
    purpose: 按 eventType 补查允许事件、ec=1 事件和请求级明细
    boundary: eventList 需要 browser same-origin
  representative_event_attribution:
    entry: rcpEventDetail + nodePolicyAttribution + nodeBindPolicyAttribution
    purpose: 代表 event 深挖
    boundary: 不默认对所有事件全量归因
```

## Dry-run Cases

### Case 1: Strategy Hit Overview

```yaml
user_question: 帮我看下用户 218368298 最近命中过哪些策略。
expected_route: tianshi_strategy_hit_inventory / strategy_hit_overview_lookup
expected_primary_entry: fastQueryHbase
expected_behavior:
  - 不默认进入完整四链路策略治理。
  - 输出命中概览模板。
  - 展示 eventId / eventType / riskDecision / hitPolicies / hitProductionPolicies / confidenceLevel / riskType 字段口径。
expected_boundary:
  - 策略命中不等于最终风险定性。
  - confidenceLevel='强' 不等于最终定性。
result: pass
```

### Case 2: TOP Strategy and Co-occurrence

```yaml
user_question: 这个用户一天内哪些策略反复命中？有没有 TOP 策略和策略共现？
expected_route: tianshi_strategy_hit_inventory
expected_output_structure:
  - policy_topn
  - node_topn
  - condition_topn
  - policy_cooccurrence
  - representative_events
expected_boundary:
  - TOP 策略 / TOP 节点 / TOP 条件只是风险感知线索。
  - 策略共现不等于团伙或攻击路径定性。
result: pass
```

### Case 3: Single Event Attribution

```yaml
user_question: 这次 eventId=5370247893355116990 为什么被阻止？
expected_route: single_event_policy_attribution
expected_behavior:
  - 不是 tianshi_strategy_hit_inventory。
  - 进入单事件策略归因。
  - 可按需使用 rcpEventDetail / rcpEventFeatureList / policy version / queryProPolicyTree / nodePolicyAttribution / nodeBindPolicyAttribution。
expected_boundary:
  - 策略归因不等于最终作弊定性。
result: pass
```

### Case 4: User Risk Assessment

```yaml
user_question: 帮我看下用户 218368298 有没有风险。
expected_route: multi_evidence_orchestration
expected_behavior:
  - 天狮作为 strategy_hit_evidence 候选。
  - 不默认触发完整策略盘点。
  - 不默认触发完整策略治理四链路。
  - 需要结合用户画像、登录日志、设备、行为和内容证据。
expected_boundary:
  - 不因策略命中直接输出用户级风险定性。
result: pass
```

## Summary

```yaml
dryrun_result: pass
case_count: 4
real_platform_access: false
dataagent_called: false
release_package_updated: false
core_skill_modified: false
```

## Follow-up

- 后续如需真实 runtime 生效，需要 overlay 或重新打 patch release。
- 若要从单用户扩展到跨用户风险感知，需要设计 `multi_user_strategy_hit_inventory`，并明确跨用户样本、时间窗、分母和误伤边界。
