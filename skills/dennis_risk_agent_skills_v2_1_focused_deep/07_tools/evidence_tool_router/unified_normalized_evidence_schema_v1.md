# Unified Normalized Evidence Schema v1

## 0. 目标

本文件定义跨 provider 的统一 `normalized_evidence` schema。所有 provider 的返回都必须归一化为该结构后，再交给 Dennis Agent 解释。

## 1. 标准结构

```yaml
normalized_evidence:
  evidence_id:
  source_query_intent_id:
  source_provider_request_id:
  provider:
  provider_response_id:
  status:
  evidence_type:
  applicable_skill:
  evidence_summary:
  key_findings:
    - finding:
      evidence_direction:
      evidence_strength:
      provider:
      quality_note:
  strong_evidence:
    - evidence:
      reason:
      provider:
  medium_evidence:
    - evidence:
      reason:
      provider:
  weak_evidence:
    - evidence:
      reason:
      provider:
  counter_evidence:
    - counter_item:
      related_misjudgment_risk:
      whether_closed:
      provider:
  missing_evidence:
    - missing_item:
      impact_on_conclusion:
      recommended_next_provider:
  quality_risks:
    - risk:
      affected_evidence:
      degrade_rule:
  freshness_notes:
  permission_notes:
  provider_limitations:
    - limitation:
      impact:
  conclusion_support:
    level:
    reason:
  next_query_intent:
  recommended_next_provider:
  manual_review_required:
  raw_result_reference:
  audit_reference:
```

## 2. 字段说明

- `evidence_id`：统一证据对象标识。
- `source_query_intent_id`：来源 query intent。
- `source_provider_request_id`：来源 provider request。
- `provider`：产生证据的 provider。
- `provider_response_id`：provider 返回标识，真实字段由内部平台补充。
- `status`：归一化后的状态。
- `evidence_type`：证据类型，如链路一致性、设备证据、策略证据、关系证据、离线分析证据。
- `applicable_skill`：适用 Skill。
- `evidence_summary`：证据摘要。
- `key_findings`：关键发现。
- `strong_evidence`：强证据。
- `medium_evidence`：中证据。
- `weak_evidence`：弱证据。
- `counter_evidence`：反证。
- `missing_evidence`：缺失证据。
- `quality_risks`：质量风险。
- `freshness_notes`：时效说明。
- `permission_notes`：权限说明。
- `provider_limitations`：provider 局限。
- `conclusion_support`：该证据对结论的支持程度。
- `next_query_intent`：下一步补证意图。
- `recommended_next_provider`：建议下一步 provider。
- `manual_review_required`：是否需要人工确认。
- `raw_result_reference`：原始结果内部引用。
- `audit_reference`：审计引用。

## 3. 结论支持等级

`conclusion_support.level` 可选：

- `clear_support`
- `highly_suspicious_support`
- `insufficient_support`
- `reverse_or_exclusion_support`

要求：

- normalized evidence 只表达证据支持程度，不替代最终风控结论。
- 不同 provider 的证据要保留 `provider_limitations`。
- 如果关键反证未闭合，不得 `conclusion_support.level = clear_support`。
- `manual_review_required` 必须可被上层使用。
- `raw_result_reference` 不等于可回放证据。

## 4. Provider Limitations 示例类型

- `dataagent_markdown_not_structured`
- `dataagent_sql_not_result`
- `realtime_log_delay_or_sampling`
- `risk_engine_hit_not_fact`
- `device_sdk_delay_or_version_gap`
- `relation_graph_edge_not_malicious_fact`
- `feature_schema_or_freshness_risk`
- `manual_review_subjective_or_pending`

## 5. 强结论保护

以下情况必须降级：

- 关键反证未闭合。
- provider 返回 partial。
- provider no_permission。
- provider empty result 且覆盖范围未知。
- provider parse failed。
- provider conflict。
- 质量风险影响核心证据。

