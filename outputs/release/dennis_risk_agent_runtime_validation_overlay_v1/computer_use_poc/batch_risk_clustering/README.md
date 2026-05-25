# Batch Risk Clustering Analysis Pack

## 1. Capability Positioning

Batch Risk Clustering Analysis Pack solves the jump from single-case judgement to multi-case batch reasoning.

It is for:

- multi case / multi entity risk batches.
- alert batches and strategy recall secondary attribution.
- interface traffic spikes.
- channel / campaign abnormal cohorts.
- device group-control batches.
- ATO batches.
- activity arbitrage batches.
- crawler / protocol / request-pattern batches.

It is not for:

- deciding whether one user is risky.
- deciding whether one device is suspicious.
- explaining one strategy hit.
- running one online query per case in a large batch.

Core questions:

- Are these cases one risk mode or multiple clusters?
- Is there abnormal correlation or abnormal enrichment?
- Which cases are representative samples?
- Which evidence supports batch attribution?
- Which signals are weak clues or hypotheses only?
- Is expansion / 举一返三 needed?
- Is DataAgent / Hive offline aggregation needed?
- What strategy, monitoring, grey release or manual review action is appropriate?

## 2. Files

- `batch_risk_case_schema_v1.md`: batch input schema.
- `batch_risk_threshold_policy_v1.md`: entity count threshold policy and routing modes.
- `batch_risk_clustering_methodology_v1.md`: clustering dimensions and workflow.
- `abnormal_correlation_matrix_v1.md`: 不可预测矩阵 / 异常相关性矩阵.
- `batch_risk_representative_sampling_v1.md`: representative sampling rules.
- `batch_risk_evidence_card_template_v1.md`: evidence card template with evidence type separation.
- `batch_risk_pattern_summary_template_v1.md`: batch pattern summary template.
- `batch_risk_response_template_v1.md`: user-facing response template.
- `batch_risk_runtime_validation_cases_v1.yaml`: runtime validation cases.

## 3. Runtime Boundary

- This pack is documentation, templates and regression only.
- It does not call real platforms.
- It does not call DataAgent.
- It does not modify auth / gateway.
- It does not auto-dispose users or launch strategies.
- It does not repackage release artifacts.

DataAgent is only a future Hive / warehouse query planning path when batch scale, time window, or aggregation complexity requires offline analysis.

## 4. Minimal Flow

1. Intake batch schema and threshold policy.
2. Select mode by entity count and user intent.
3. Build initial clusters.
4. Build abnormal correlation matrix.
5. Select representative samples.
6. Produce evidence cards for representative samples.
7. Produce pattern summary and attack-path hypotheses.
8. Produce missing evidence, source gap and follow-up plan.
9. Produce strategy, monitoring, grey release and manual review suggestions.

## 5. Hard Boundaries

- 5 个以下可全量深查.
- 10+ 默认 `batch_clustering_mode`，不逐个在线查.
- 50+ 默认 aggregation / DataAgent-Hive query plan.
- `no_data` 不能作为无风险反证.
- blocked / timeout / partial source 必须标记 `source_gap`.
- manual_input 不能单独支撑 strong conclusion.
- model_inference 不能当 raw evidence.
- user_claim 不能单独支撑强风险结论.
- 不能仅凭相似性判断同团伙.
- 历史 case 不能污染当前批次事实证据.
