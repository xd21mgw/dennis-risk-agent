# normal_baseline Skill Quickstart

从零到产出 enriched candidates 的最短路径。

## Step 1: 运行 Profiler

```bash
cd computer_use_poc/baselines/normal_baseline

python3 src/normal_baseline_profiler.py \
  --input-dir input_excels \
  --contract recon/profiler_input_contract_20260609_v0_1.yaml \
  --output-dir /tmp/normal_baseline_output \
  --topn-limit 20
```

预期输出：7 个 JSON + 完成摘要

## Step 2: 查看 Run Report

```bash
cat population_baseline_v0_1_run_report.md | head -40
```

关键看：normal_status 分布、各状态示例

## Step 3: 准备 L3 Candidates JSON

创建 `/tmp/l3_candidates.json`：

```json
[
  {
    "candidate_id": "c001",
    "source_name": "infra_user_action_log",
    "field_path": "infra_user_action_log.action_type",
    "field_value": "REFRESH_TOKEN",
    "risk_sample_count": 100,
    "risk_covered_count": 95,
    "risk_value_count": 60,
    "risk_value_ratio": 0.6
  },
  {
    "candidate_id": "c002",
    "source_name": "passport_action_log",
    "field_path": "passport_action_log.status",
    "field_value": "SUCCESS",
    "risk_sample_count": 50,
    "risk_covered_count": 50,
    "risk_value_count": 48,
    "risk_value_ratio": 0.96
  }
]
```

## Step 4: 运行 Batch Enricher

```bash
python3 src/normal_baseline_enricher.py \
  --baseline-dir /tmp/normal_baseline_output \
  --input-candidates /tmp/l3_candidates.json \
  --output /tmp/l3_candidates_enriched.json
```

## Step 5: 查看 Enriched 输出

```bash
python3 -c "
import json
r = json.load(open('/tmp/l3_candidates_enriched.json'))
for e in r['enriched_candidates']:
    print('%s: status=%s hit=%s caveat=%s' % (
        e['candidate_id'], e.get('normal_status'), e.get('baseline_hit'),
        (e.get('baseline_caveat','') or '')[:40]))
"
```

## 验收命令

```bash
# Tests
python -m pytest computer_use_poc/baselines/normal_baseline/tests/ -v

# Forbidden key check
grep -R "risk_judgement" computer_use_poc/baselines/normal_baseline/src/ || true
grep -R "feature_candidate" computer_use_poc/baselines/normal_baseline/src/ || true
```
