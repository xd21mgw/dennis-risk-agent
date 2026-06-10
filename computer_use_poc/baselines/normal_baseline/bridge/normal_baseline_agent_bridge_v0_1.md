# normal_baseline Agent Bridge v0.1

## 定位

这是 Agent 可调用工具桥，**不是 runtime 集成**。它为 Dennis / L3-L4 流程提供一个稳定的外部调用入口，但本轮不接入 Agent runtime，不改 L3/L4 运行链路。

## 调用关系

```
L3 输出风险样本内部候选
  → normal_baseline Agent Bridge (batch enrich)
  → enriched_candidates JSON
  → L4 基于 enriched result 做验证/排序/降权/升权/解释
```

## 标准命令

```bash
bash computer_use_poc/baselines/normal_baseline/bridge/normal_baseline_enrich_candidates.sh \
  <baseline_dir> \
  <input_candidates_json> \
  <output_enriched_json>
```

## 输入

L3 candidates JSON 数组，每条至少包含：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `candidate_id` | string | 是 | 候选唯一标识 |
| `source_name` | string | 是 | 数据源名 |
| `field_path` | string | 是 | 字段路径 |
| `field_value` | string | 否 | 字段值（用于值级排名查询） |
| `risk_sample_count` | int | 否 | 风险样本总数 |
| `risk_covered_count` | int | 否 | 风险样本覆盖数 |
| `risk_value_count` | int | 否 | 风险样本该值计数 |
| `risk_value_ratio` | float | 否 | 风险样本该值占比 |

## 输出

enriched_candidates JSON，包含 `enriched_candidates` + `enrichment_metadata`。

每条 candidate 保留原字段，只补充 normal 侧背景：

| 补充字段 | 类型 | 说明 |
|---|---|---|
| `baseline_hit` | bool | 是否命中 baseline |
| `normal_status` | string/null | normal 低熵/高频状态 |
| `normal_value_ratio` | float/null | 该值在 baseline 中的占比 |
| `normal_value_rank` | int/null | 该值在 baseline 中的排名 |
| `high_cardinality` | bool | 是否为高基数字段 |
| `baseline_caveat` | string | 消费注意事项 |
| `recommended_l4_use` | string | L4 建议动作 |

附加透传字段：`baseline_scope`, `sample_size_level`, `not_login_aue_specific`, `normal_covered_count`, `normal_coverage_ratio`, `normal_top1_ratio`, `normal_top3_ratio`, `normal_value_count`

## 消费语义

1. **normal_popular / normal_low_entropy**：大盘常见，L4 建议降权或作为解释，**不等于安全**。
2. **normal_not_popular_in_sample**：大盘不常见，可进入后续验证，**不等于风险**。
3. **normal_referenceable / normal_observable**：仅参考，不做强判断。
4. **normal_sparse_or_low_coverage**：样本不足，不做强判断。
5. **baseline miss（baseline_hit=false）**：返回 baseline_gap，不做负向结论。
6. **high_cardinality_field**：进入复用/关联验证，不走普通 TOP-N 解释。

## 失败降级规则

| 场景 | bridge 状态 | 原因 | L4 下游行为 |
|---|---|---|---|
| baseline_dir 不存在 | `bridge_failed` | `baseline_dir_missing` | 使用原始 L3 candidates + caveat |
| input candidates 不存在 | `bridge_failed` | `invalid_candidate_input` | 使用原始 L3 candidates + caveat |
| input JSON 非法 | `bridge_failed` | `invalid_candidate_input` | 使用原始 L3 candidates + caveat |
| enricher 执行失败 | `bridge_failed` | `enricher_execution_failed` | 使用原始 L3 candidates + caveat |
| 单条 candidate baseline miss | `bridge_success`（不算 failure） | 单条 `baseline_hit=false` | 该条标记 baseline_gap，其他条正常 |

**关键**：bridge 失败时 L4 可继续使用原始 L3 candidates，但必须加 caveat（无 normal 侧背景参考）。

## recommended_l4_use 枚举

| 值 | 含义 |
|---|---|
| `downgrade_or_explain` | 大盘常见，建议降权或作为解释 |
| `candidate_for_validation` | 大盘不常见，建议进入候选验证 |
| `weak_reference_only` | 参考级，不做强判断 |
| `baseline_gap_no_judgement` | baseline 缺失或样本不足，不做判断 |
| `high_cardinality_reference_only` | 高基数字段，只做 HC 摘要参考 |

## 边界

- 不调用 DataAgent/Hive
- 不接入 Agent runtime
- 不改 L3/L4 代码
- 不做风险判断
- 不输出 `risk_judgement` / `feature_candidate` / `candidate_feature_decision`
- 不新增自动编排逻辑
- 字段展示/脱敏/对外输出由 downstream output layer 处理

## 版本口径

normal_baseline v0.1 是**静态快照 baseline**，不自动刷新：

- bridge / enricher 只读取用户指定的 `baseline_dir`
- 除非用户明确要求 `refresh / rerun profiler / replace samples`，否则后续一直使用该 `baseline_dir`
- 不创建 daily refresh 自动任务
- 不创建 DataAgent/Hive 自动抽样逻辑
- bridge wrapper 不自动检测 baseline 新旧、不自动触发 profiler 重跑
- 如需更新 baseline，由用户手动执行 profiler 生成新 `baseline_dir`，再指定新路径
