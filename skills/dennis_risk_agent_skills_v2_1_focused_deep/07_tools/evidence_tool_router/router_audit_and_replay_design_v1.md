# Router Audit and Replay Design v1

## 0. 目标

本文件定义 Evidence Tool Router 的跨 provider 审计与回放设计。当前阶段只定义记录规范，不调用真实 provider。

## 1. 必须记录

每次 Router 执行必须记录：

- 用户原问题。
- Skill 路由。
- query_intent。
- router decision。
- selected provider。
- provider_request。
- provider_response 摘要。
- normalized_evidence。
- Dennis Agent 结论。
- 人工最终判断。
- 是否回写 Skill / schema / join path / threshold / tool routing。
- provider 错误。
- 权限和质量风险。
- audit_reference。

## 2. router decision 记录

```yaml
router_decision:
  source_query_intent_id:
  evidence_type:
  selected_providers:
    - provider:
      role:
      reason:
      expected_evidence:
  rejected_providers:
    - provider:
      reason:
  fallback_plan:
  manual_review_required:
```

## 3. provider_request 审计

记录：

- request_id。
- source_query_intent_id。
- provider。
- request_type。
- target_evidence。
- time_window。
- query_dimensions。
- quality_checks。
- permission_boundary。
- safety_boundary。

不记录：

- 不应外泄的敏感明细。
- 未脱敏原始结果。
- 不必要的样本级明细。

## 4. provider_response 摘要

记录：

- provider_response_id。
- status。
- returned_type。
- response_summary。
- key_findings。
- missing_evidence。
- counter_evidence。
- quality_risks。
- permission_notes。
- raw_result_reference。

说明：

- Data Agent queryId 不能回放，只能作为弱引用。
- 未来 provider 如果有 result_id / task_id / trace_id，应记录为 raw_result_reference。
- raw_result_reference 不等于外部可见材料。

## 5. normalized_evidence 审计

记录：

- evidence_id。
- source_query_intent_id。
- source_provider_request_id。
- provider。
- evidence_type。
- strong / medium / weak evidence。
- counter evidence。
- missing evidence。
- provider limitations。
- conclusion support。
- next query intent。
- recommended next provider。
- manual review required。

## 6. 回放原则

- 回放优先使用脱敏摘要和 normalized evidence。
- 审计记录不能外泄敏感明细。
- 原始 provider 结果只通过内部引用访问。
- 回放必须能解释当时为什么选择 provider、为什么降级、为什么需要人工确认。
- provider 不可回放时，必须保留不可回放原因。

## 7. 回写记录

```yaml
backwrite_decision:
  need_backwrite:
  target:
    - skill:
    - query_intent_schema:
    - data_join_paths:
    - conclusion_thresholds:
    - normalized_evidence_schema:
    - tool_routing:
  reason:
  priority:
  approved_by:
```

## 8. 安全要求

- 审计记录不自动触发处罚、冻结、扣除、封禁或策略上线。
- 敏感样本明细不得进入通用材料。
- 权限不足不得通过换 provider 绕过。
- 人工最终判断必须独立记录，不覆盖原始 evidence。

