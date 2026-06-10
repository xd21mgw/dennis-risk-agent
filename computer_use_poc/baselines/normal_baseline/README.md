# normal_baseline v0.1

normal / population baseline 统计资产 — 为风控研判提供 normal 侧字段覆盖率、缺失率、TOP-N、低熵/高频状态和高基数字段摘要。

## 这个 Skill 是什么

normal_baseline 提供大盘字段级统计基线，帮助风控分析者理解"正常用户"在某个字段/取值上的常见程度。它只输出统计事实，不做风险判断。

**核心产出**：
- 7 个 profiler JSON：字段发现、统计、TOP-N 分布、缺失率、低熵状态、高基数摘要、元数据
- enriched candidates JSON：L3 候选池补充 normal 侧背景
- consumer contract：下游消费边界

## 什么时候用

- 需要知道某个字段/取值在大盘中是否常见
- L3 候选池需要补充 normal 侧背景用于 L4 验证
- 新接入数据源需要做字段侦察和基线统计
- 需要区分"大盘常见"和"case 中异常"的参照

## 怎么跑

### 1. 运行 Profiler

```bash
cd computer_use_poc/baselines/normal_baseline

python3 src/normal_baseline_profiler.py \
  --input-dir input_excels \
  --contract recon/profiler_input_contract_20260609_v0_1.yaml \
  --output-dir /tmp/normal_baseline_output \
  --topn-limit 20
```

### 2. 查看产物

7 个 JSON 在 `--output-dir` 中：

| 文件 | 内容 |
|---|---|
| `normal_field_inventory.json` | 字段发现清单 |
| `normal_field_profile_sample.json` | 字段级统计 |
| `normal_discrete_field_distribution.json` | TOP-N 分布 |
| `normal_field_missingness_profile.json` | 缺失率 |
| `normal_low_entropy_profile.json` | 低熵/高频状态 |
| `high_cardinality_summary.json` | 高基数摘要 |
| `profiler_metadata.json` | 元数据 |

### 3. 运行 Batch Enricher

```bash
python3 src/normal_baseline_enricher.py \
  --baseline-dir /tmp/normal_baseline_output \
  --input-candidates /tmp/l3_candidates.json \
  --output /tmp/l3_candidates_enriched.json
```

### 4. Debug 单点查询

```bash
python3 src/normal_baseline_enricher.py \
  --baseline-dir /tmp/normal_baseline_output \
  --source-name infra_user_action_log \
  --field-path infra_user_action_log.action_type \
  --field-value REFRESH_TOKEN
```

## 产物在哪里

- Profiler 输出：`--output-dir` 指定目录
- Run report：`population_baseline_v0_1_run_report.md`
- Consumer contract：`consumer/normal_baseline_consumer_contract_v0_1.yaml`
- Enricher 示例输出：`/tmp/l3_candidates_enriched.json`

## 怎么给下游消费

下游（L4 / Dennis / 人工审核）按 `consumer/normal_baseline_consumer_contract_v0_1.yaml` 消费：

| normal_status | 含义 | L4 建议 |
|---|---|---|
| `normal_low_entropy` | 大盘极高频 | 降权或作为解释，**不等于安全** |
| `normal_popular` | 大盘较高频 | 降权或作为解释，**不等于安全** |
| `normal_not_popular_in_sample` | 大盘不常见 | 进入候选验证，**不等于风险** |
| `normal_referenceable` | 参考级频率 | 仅参考，不做强判断 |
| `normal_observable` | 观察级频率 | 仅参考，不做强判断 |
| `normal_sparse_or_low_coverage` | 样本不足 | baseline_gap，不做判断 |
| baseline miss | baseline 无此字段 | baseline_gap，不做负向结论 |
| `high_cardinality_field` | 高基数字段 | 只做 HC 摘要参考 |

## 不做什么

- 不做风险判断
- 不输出 `risk_judgement` / `feature_candidate` / `candidate_feature_decision`
- 不接入 Agent runtime
- 不修改 L3/L4 运行逻辑
- 不调用 DataAgent/Hive
- 字段展示/脱敏/对外输出由 downstream output layer 处理

## 版本口径

normal_baseline v0.1 是**静态快照 baseline**，不自动刷新：

- bridge / enricher 只读取用户指定的 `baseline_dir`
- 除非用户明确要求 `refresh / rerun profiler / replace samples`，否则后续一直使用该 `baseline_dir`
- 不创建 daily refresh 自动任务
- 不创建 DataAgent/Hive 自动抽样逻辑
- 如需更新 baseline，由用户手动执行 profiler 生成新 `baseline_dir`，再指定新路径

## 文件结构

```
normal_baseline/
  SKILL.md                         — Skill 定义
  README.md                        — 使用者入口（本文件）
  population_baseline_v0_1_run_report.md — 运行结果报告
  src/
    normal_baseline_profiler.py    — Profiler
    normal_baseline_enricher.py   — Batch enricher
  tests/
    test_normal_baseline_profiler.py
    test_normal_baseline_enricher.py
  recon/
    profiler_input_contract_*.yaml — Contract
    *.xlsx                         — 字段侦察 Excel
  input_excels/                    — 输入样本
  consumer/
    normal_baseline_consumer_contract_v0_1.yaml
  sampling/
    population_20260609/           — 抽样 SQL + runner
  sample_batches/                  — 批次定义
  schemas/                         — Schema YAML
  examples/
    run_normal_baseline_enricher.md
    normal_baseline_skill_quickstart.md
  refresh/                         — 刷新计划
  realtime/                        — 实时设计
```
