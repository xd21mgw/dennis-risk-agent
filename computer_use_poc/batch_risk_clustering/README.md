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
- `account_risk_data_source_registry_v1.md`: account-risk L1 data source registry.
- `account_security_hive_source_registry_v1.md`: account-security Hive source registry for ATO / login-chain / successful login / failed login / resetPwd / Web RCP / App RCP.
- `account_security_hive_query_plan_templates_v1.md`: DataAgent/Hive query plan templates for account-security offline evidence.
- `batch_l1_feature_query_contract_v1.md`: L1 wide table / profile shallow query contract and `batch_feature_table` schema.
- `batch_top_dimension_drilldown_template_v1.md`: TOP dimension drilldown and `top_dimension_summary` schema.
- `batch_frequent_pattern_contribution_template_v1.md`: frequent pattern / contribution analysis template.
- `batch_risk_clustering_methodology_v1.md`: clustering dimensions and workflow.
- `batch_ato_cluster_lens_v1.md`: ATO / compromised-account cluster lens overlay on top of existing batch clustering.
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
3. Generate L1 wide table / profile shallow query plan.
4. Produce `batch_feature_table` from DataAgent/Hive when executed by the data layer.
5. Run TOP dimension drilldown.
6. Run frequent pattern / contribution analysis.
7. Build abnormal A -> B correlation matrix.
8. Convert L1 results into cluster hints.
9. Apply domain lens overlays when relevant, including `ato_cluster_lens` for compromised-account / stolen-account posting analysis.
10. Select representative samples.
11. Produce cluster evidence cards for representative samples.
12. Produce pattern summary and attack-path hypotheses.
13. Produce missing evidence, source gap and follow-up plan.
14. Produce expansion, strategy, monitoring, grey release and manual review suggestions.

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
- L1 high-contribution pattern can only be cluster hint / candidate feature hint before validation.
- ATO batch is not "no clustering"; existing clusters remain, then `ato_cluster_lens` checks WEB non-trusted login, `login_to_action_delta`, device identity drift, content-action deep dive, representative single-case proof, and `cluster_level_backfill`.
- Dennis explains and reasons; DataAgent/Hive extracts and aggregates batch data.
