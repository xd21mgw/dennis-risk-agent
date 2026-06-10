# normal_baseline Skill v0.1

## Skill 定位

normal_baseline 是 normal / population baseline 统计资产 Skill。只提供 normal 侧字段覆盖率、缺失率、TOP-N、低熵/高频状态、高基数字段摘要。

**不做的事情**：
- 不做风险判断
- 不输出 `risk_judgement` / `feature_candidate` / `candidate_feature_decision`
- 不做人审结论
- 不接入 Agent runtime
- 不修改 L3/L4 运行逻辑

## 核心能力

| 能力 | 入口 | 产物 |
|---|---|---|
| Source field recon | `recon/` | 字段侦察报告 + `profiler_input_contract_*.yaml` |
| Profiler input contract | `recon/profiler_input_contract_*.yaml` | 字段裁剪 / JSON 展开 / 高基数字段声明 |
| Local profiler | `src/normal_baseline_profiler.py` | 7 个 profiler JSON |
| Population baseline result report | `population_baseline_v0_1_run_report.md` | 运行结果汇总 |
| Batch enricher | `src/normal_baseline_enricher.py` | enriched candidates JSON |
| Consumer contract | `consumer/normal_baseline_consumer_contract_v0_1.yaml` | 下游消费边界 |

## 标准流程

```
1. 准备样本 → Excel / CSV / parquet 放入 input_excels/
2. 运行 profiler → 7 个 JSON 输出
3. 查看 run report → 字段发现 / normal_status 分布 / 示例
4. 准备 L3 candidates JSON
5. 运行 batch enricher → enriched_candidates JSON
6. 下游 L4 / Dennis 按 consumer contract 消费（本 Skill 不接 runtime）
```

## 输入输出

### Profiler 输入

| 参数 | 说明 |
|---|---|
| `--input-dir` | 样本目录（Excel / CSV） |
| `--contract` | profiler_input_contract YAML |
| `--output-dir` | 输出目录 |
| `--topn-limit` | TOP-N 限制（默认 20） |

### Profiler 输出（7 个 JSON）

| 文件 | 内容 |
|---|---|
| `normal_field_inventory.json` | 字段发现清单 |
| `normal_field_profile_sample.json` | 字段级统计（类型、基数、覆盖等） |
| `normal_discrete_field_distribution.json` | 离散字段 TOP-N 分布 |
| `normal_field_missingness_profile.json` | 字段缺失率档案 |
| `normal_low_entropy_profile.json` | 低熵/高频状态 |
| `high_cardinality_summary.json` | 高基数字段摘要 |
| `profiler_metadata.json` | 元数据 |

### Enricher 输入

L3 candidates JSON 数组，每条至少：
- `candidate_id` / `source_name` / `field_path` / `field_value`
- `risk_sample_count` / `risk_covered_count` / `risk_value_count` / `risk_value_ratio`

### Enricher 输出

保留原 candidate 字段，补充：
- `baseline_hit` / `normal_status` / `normal_covered_count` / `normal_coverage_ratio`
- `normal_value_rank` / `normal_value_count` / `normal_value_ratio`
- `normal_top1_ratio` / `normal_top3_ratio` / `high_cardinality`
- `baseline_scope` / `sample_size_level` / `not_login_aue_specific`
- `baseline_caveat` / `recommended_l4_use`

## 分层高频规则

rule_source: `sample_frequency_rule_v0_1`

| 参数 | 值 | 含义 |
|---|---|---|
| `observable_min_covered_count` | 200 | 可观察频率的最低 covered 数 |
| `referenceable_min_covered_count` | 300 | 可引用频率的最低 covered 数 |
| `strong_low_entropy_min_covered_count` | 1000 | 强低熵判断的最低 covered 数 |
| `min_coverage_ratio_for_strong` | 0.8 | 强低熵判断的最低覆盖率 |
| `top1_ratio_threshold` | 0.9 | top1 集中度阈值 |
| `top3_ratio_threshold` | 0.97 | top3 集中度阈值 |

## normal_status 语义

| normal_status | covered_count | 含义 | L4 消费建议 |
|---|---|---|---|
| `normal_sparse_or_low_coverage` | < 200 | 样本不足观察 | baseline_gap，不做判断 |
| `normal_observable` | 200-299 | 可观察频率 | 仅参考，不做强判断 |
| `normal_referenceable` | 300-999 | 可引用频率 | 参考，不做强判断 |
| `normal_low_entropy` | >= 1000, top1>=0.9 或 top3>=0.97 | 大盘极高频 | 降权或作为解释，**不等于安全** |
| `normal_popular` | >= 1000, top1>=0.5 | 大盘较高频 | 降权或作为解释，**不等于安全** |
| `normal_not_popular_in_sample` | >= 1000, 未达高频 | 大盘不常见 | 进入候选验证，**不等于风险** |

## 版本口径

normal_baseline v0.1 是**静态快照 baseline**，不自动刷新。

- bridge / enricher 只读取用户指定的 `baseline_dir`
- 除非用户明确要求 `refresh / rerun profiler / replace samples`，否则后续一直使用该 `baseline_dir`
- 不创建 daily refresh 自动任务
- 不创建 DataAgent/Hive 自动抽样逻辑
- 不创建自动更新 baseline 的 cron / scheduler / pipeline
- 如需更新 baseline，由用户手动执行 profiler 生成新 `baseline_dir`，再指定新路径

## 边界声明

1. 不调用 DataAgent/Hive
2. 不接 Agent runtime
3. 不改 L3/L4 运行逻辑
4. 不做风险判断
5. 不输出 `risk_judgement` / `feature_candidate` / `candidate_feature_decision`
6. 字段展示、脱敏、是否对外输出由 downstream output layer 处理
7. high_cardinality 字段只做摘要，不进入普通 TOP-N 解释
8. baseline miss 返回 `baseline_gap`，不做负向结论
9. v0.1 是静态快照，不自动刷新 baseline，不创建自动抽样逻辑

## DataAgent 结论

- DataAgent Conversational API 可用于元数据理解和小规模探查
- DataAgent 服务账号权限与用户本地 Hive 权限是独立链路
- 本轮正式 population baseline 样本**不依赖 DataAgent**
- 推荐路径：用户在 Jupyter/Notebook 中执行 `sampling/population_20260609/normal_population_sample_extraction_sql_v0_1.sql`，导出 CSV 后运行 profiler

## 验收命令

```bash
# Profiler tests
python -m pytest computer_use_poc/baselines/normal_baseline/tests/test_normal_baseline_profiler.py -v

# Enricher tests
python -m pytest computer_use_poc/baselines/normal_baseline/tests/test_normal_baseline_enricher.py -v

# Profiler CLI
python3 src/normal_baseline_profiler.py \
  --input-dir input_excels \
  --contract recon/profiler_input_contract_20260609_v0_1.yaml \
  --output-dir /tmp/normal_baseline_output \
  --topn-limit 20

# Enricher batch
python3 src/normal_baseline_enricher.py \
  --baseline-dir /tmp/normal_baseline_output \
  --input-candidates /tmp/l3_candidates.json \
  --output /tmp/l3_candidates_enriched.json

# Forbidden key check
grep -R "risk_judgement" src/ tests/ || true
grep -R "feature_candidate" src/ tests/ || true
grep -R "candidate_feature_decision" src/ tests/ || true

# Whitespace check
git diff --check
```
