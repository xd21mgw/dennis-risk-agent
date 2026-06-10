# normal_baseline_enricher — Usage Examples

## Mode 1: Batch Enrich (主模式)

L3 输出候选池 → normal_baseline 批量补充 normal 侧背景 → 输出 enriched_candidate_pool

```bash
python3 computer_use_poc/baselines/normal_baseline/src/normal_baseline_enricher.py \
  --baseline-dir /tmp/normal_baseline_layered_v0_2 \
  --input-candidates /tmp/l3_candidates.json \
  --output /tmp/l3_candidates_enriched.json
```

输入 L3 candidates JSON 每条至少包含：
- candidate_id
- source_name
- field_path
- field_value
- risk_sample_count / risk_covered_count / risk_value_count / risk_value_ratio

输出保留原字段，并补充：
- baseline_hit / normal_status / normal_covered_count / normal_coverage_ratio
- normal_value_rank / normal_value_count / normal_value_ratio
- normal_top1_ratio / normal_top3_ratio
- high_cardinality / baseline_scope / sample_size_level / not_login_aue_specific
- baseline_caveat / recommended_l4_use

## Mode 2: Debug Single-Point Lookup

```bash
python3 computer_use_poc/baselines/normal_baseline/src/normal_baseline_enricher.py \
  --baseline-dir /tmp/normal_baseline_layered_v0_2 \
  --source-name infra_user_action_log \
  --field-path infra_user_action_log.action_type \
  --field-value REFRESH_TOKEN
```

## 消费语义

| normal_status | 含义 | L4 建议 |
|---|---|---|
| normal_low_entropy | 大盘极高频 | 降权或作为解释，不等于安全 |
| normal_popular | 大盘较高频 | 降权或作为解释，不等于安全 |
| normal_not_popular_in_sample | 大盘不常见 | 进入候选验证，不等于风险 |
| normal_referenceable | 参考级频率 | 仅参考，不做强判断 |
| normal_observable | 观察级频率 | 仅参考，不做强判断 |
| normal_sparse_or_low_coverage | 样本不足 | 不做频率判断 |
| baseline miss | baseline 中无此字段 | baseline_gap，不做负向结论 |
| high_cardinality_field | 高基数字段 | 只做 high_cardinality_summary 参考 |
