# normal_baseline CHANGELOG

## v0.1 — 2026-06-10

### 版本口径

normal_baseline v0.1 是**静态快照 baseline**，不自动刷新。bridge / enricher 只读取用户指定的 `baseline_dir`。除非用户明确要求 `refresh / rerun profiler / replace samples`，否则后续一直使用该 `baseline_dir`。不创建 daily refresh 自动任务，不创建 DataAgent/Hive 自动抽样逻辑。

### 新增

- **Source field recon**: 4 个 Excel 样例字段侦察，5 个字段侦察报告
- **Profiler input contract**: `profiler_input_contract_20260609_v0_1.yaml`，外置字段裁剪 / JSON 展开 / 高基数字段声明
- **Local profiler**: `normal_baseline_profiler.py`，输出 7 个 JSON（field_inventory, field_profile_sample, discrete_field_distribution, field_missingness_profile, low_entropy_profile, high_cardinality_summary, profiler_metadata）
- **分层高频规则**: `sample_frequency_rule_v0_1`，从单一 `min_entity_count=3000` 改为 6 参数分层门槛：
  - observable_min_covered_count = 200
  - referenceable_min_covered_count = 300
  - strong_low_entropy_min_covered_count = 1000
  - min_coverage_ratio_for_strong = 0.8
  - top1_ratio_threshold = 0.9
  - top3_ratio_threshold = 0.97
- **normal_status 分层**: 移除 `normal_unknown_small_sample`，新增 `normal_observable` / `normal_referenceable`
- **Population baseline run report**: `population_baseline_v0_1_run_report.md`
- **Batch enricher**: `normal_baseline_enricher.py`，主模式 batch enrich + debug 单点 lookup
- **Consumer contract**: `normal_baseline_consumer_contract_v0_1.yaml`，含 L4 查询协议 + normal_status 消费语义
- **DataAgent population client**: `dataagent_population_client.py` v0.2（POST 300s timeout, componentInfo.props.content 解析, 表名可见性检查）
- **Sampling SQL**: 4 个 deterministic hash sample SQL 模板
- **Schema YAML**: 6 个 schema 定义文件
- **Skill 文档**: SKILL.md / README.md / quickstart / examples

### DataAgent 验证结论

- DataAgent Conversational API POST 可稳定返回 HTTP 200（timeout >= 120s）
- DataAgent 服务账号缺少 `ks_raw_log_v3` / `ks_rc_bs` 的 SQL 执行权限
- 用户本人 Hive 权限通过本地导出 Excel 证明
- 推荐路径：用户 Jupyter/Notebook 执行 SQL → 导出 CSV → 运行 profiler

### 边界

- 不做风险判断
- 不输出 `risk_judgement` / `feature_candidate` / `candidate_feature_decision`
- 不接入 Agent runtime
- 不修改 L3/L4 运行逻辑
- 不调用 DataAgent/Hive 执行正式抽样
