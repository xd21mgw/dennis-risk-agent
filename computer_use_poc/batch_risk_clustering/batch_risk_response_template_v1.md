# Batch Risk Response Template v1

## 1. 批量结论摘要

```text
一句话判断：
这批更像：
当前置信度：
是否能强判：
最大证据缺口：
```

## 2. 批量规模与处理模式

```text
entity_count:
case_count:
selected_mode:
选择原因:
- 1-2: single_entity_execution_mode
- 3-4: small_multi_case_execution_mode
- 5-9: small_batch_mode
- 10-49: batch_clustering_mode
- 50-499: large_batch_aggregation_mode
- 500+: alert_batch_or_population_analysis_mode
```

## 3. 分簇结果

```text
cluster_id:
cluster_name:
covered_cases:
key_common_features:
evidence_level:
risk_hypothesis:
cannot_conclude:
```

## 4. 不可预测矩阵 / 异常相关性矩阵

```text
relation_family:
relation_direction:
observed_pattern:
evidence_basis:
baseline_status:
denominator_status:
coverage_ratio:
enrichment_signal:
directionality:
reverse_check_result:
confounder_risk:
false_positive_risk:
relationship_strength:
attack_path_hypothesis:
possible_explanation:
required_followup:
cannot_conclude_boundary:
```

## 5. 代表样本证据卡

For 10+ entities, include 3-5 representative cases:

```text
case_id:
sample_type:
cluster_assignment:
strong_evidence:
medium_evidence:
weak_evidence:
counter_evidence:
missing_evidence:
blocked_evidence:
preliminary_judgement:
confidence_level:
```

## 6. 攻击路径假设

Sort hypotheses by evidence strength:

```text
hypothesis:
support_level:
why_possible:
missing_validation:
alternative_explanation:
```

Do not write hypotheses as facts.

## 7. 误伤与反证

```text
normal_business_explanation:
false_positive_risk:
counter_evidence:
manual_review_boundary:
```

## 8. 补证计划

```text
online_readonly_observation:
DataAgent_Hive_query_plan:
required_fields:
time_window:
hypothesis_to_validate:
```

DataAgent is only Hive / warehouse query planning unless separately authorized.

## 9. 举一返三

```text
expansion_fields:
expansion_population:
monitoring_candidates:
strategy_candidates:
grey_validation:
scope_control:
```

## 10. 不可强判声明

```text
当前不能下的结论：
不能下结论的原因：
升级判断所需证据：
```

## 11. Short KIM Version

```text
这批先按 {selected_mode} 处理：{one_sentence_judgement}。
当前只能支持 {confidence_level}，最大缺口是 {missing_evidence}。
我会先分簇 + 异常相关性矩阵 + 抽 3-5 个代表样本，不逐个在线查全量；50+ 规模先给 DataAgent/Hive 聚合计划。
```
