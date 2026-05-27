# Batch Risk Evidence Card Template v1

## 1. Evidence Type Separation

### raw evidence

Facts explicitly present in platform logs, warehouse tables, user-provided structured data, or current task observation.

### derived evidence

Statistics, aggregates, ratios, distributions, conditional distributions, enrichment signals and cluster-level features computed from raw evidence.

### model inference

Model output or risk score. It can be hypothesis or weak clue only; model_inference 不能当 raw evidence.

### user claim

User complaint, appeal, ops feedback or manual claim. It can trigger investigation or weak evidence only.

### missing evidence

Evidence that should exist but is not currently available.

### blocked evidence

Evidence unavailable due to permission, auth, timeout, platform issue, parsing failure or reliable-window limits.

### historical similar pattern

Past similar cases. Historical case can only be similar pattern / hypothesis, not current batch fact.

## 2. Strong Rules

- manual_input 不能单独支撑 strong conclusion.
- model_inference 不能当 raw evidence.
- user_claim 不能单独支撑 ATO / 群控 / 爬虫 / 套利等强结论.
- login log 超出在线可靠窗口后的 no_data 不能作为无风险反证.
- no_data 不能作为无风险反证.
- blocked/timeout/partial source 必须 source_gap.
- blocked / timeout / partial source must downgrade to `permission_or_runtime_gap` / `source_gap`.
- 批量 case 中不能因为某两个 case 相似就直接写“同团伙”，除非有明确 join key 或基础设施共用证据.
- 历史 case 不能污染当前批次事实证据.
- 当前批次事实证据必须来自 `current_input` 或 `current_task_observation`.

## 3. Evidence Card Template

```yaml
case_id:
entity_summary:
  user_id:
  device_id:
  ip:
  interface:
  channel:
risk_event:
cluster_assignment:
  cluster_id:
  cluster_name:
  sample_type:
strong_evidence:
  - evidence_type: raw_evidence
    evidence_summary:
    evidence_source:
    source_quality:
medium_evidence:
  - evidence_type: derived_evidence
    evidence_summary:
    evidence_source:
    source_quality:
weak_evidence:
  - evidence_type:
    evidence_summary:
    evidence_source:
    source_quality:
counter_evidence:
  - evidence_type:
    evidence_summary:
    evidence_source:
    source_quality:
user_claim:
  - claim_summary:
    strength: weak
model_inference:
  - inference_summary:
    strength: hypothesis_only
missing_evidence:
  - evidence_name:
    why_needed:
blocked_evidence:
  - source_name:
    blocked_reason:
    source_gap: true
evidence_source_metadata:
  - source_name:
    source_type:
    source_platform:
    collected_at:
    evidence_time_range:
    freshness_status:
    permission_status:
    reliability_level:
    raw_reference:
historical_similar_pattern:
  - pattern_summary:
    use_policy: hypothesis_only
preliminary_judgement:
confidence_level:
required_followup:
```

## 4. Output Boundary

- Do not output cookie / token / session / header / phone / API key.
- UID / DID / IP can be internal risk analysis entity fields, but cross-team output should use safe_ref or aggregation.
- raw_reference must be a safe internal reference, not source response.
