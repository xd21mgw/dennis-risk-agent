# Agent Bridge Smoke Test

## 测试场景

### 场景 1：正常 enrich

```bash
bash computer_use_poc/baselines/normal_baseline/bridge/normal_baseline_enrich_candidates.sh \
  /tmp/normal_baseline_layered_v0_2 \
  computer_use_poc/baselines/normal_baseline/examples/l3_candidates_bridge_example_v0_1.json \
  /tmp/l3_candidates_bridge_enriched.json
```

预期：
- exit 0 (bridge_success)
- 输出 enriched JSON，6 条 candidates
- 至少覆盖：normal_popular / normal_low_entropy / normal_not_popular_in_sample / high_cardinality_field / baseline_gap

### 场景 2：baseline_dir 不存在

```bash
bash computer_use_poc/baselines/normal_baseline/bridge/normal_baseline_enrich_candidates.sh \
  /tmp/nonexistent_dir \
  computer_use_poc/baselines/normal_baseline/examples/l3_candidates_bridge_example_v0_1.json \
  /tmp/l3_enriched_fail.json
```

预期：
- exit 1 (bridge_failed)
- reason=baseline_dir_missing

### 场景 3：input candidates 不存在

```bash
bash computer_use_poc/baselines/normal_baseline/bridge/normal_baseline_enrich_candidates.sh \
  /tmp/normal_baseline_layered_v0_2 \
  /tmp/nonexistent_candidates.json \
  /tmp/l3_enriched_fail.json
```

预期：
- exit 1 (bridge_failed)
- reason=invalid_candidate_input

### 场景 4：input JSON 非法

```bash
echo "not valid json" > /tmp/bad_candidates.json
bash computer_use_poc/baselines/normal_baseline/bridge/normal_baseline_enrich_candidates.sh \
  /tmp/normal_baseline_layered_v0_2 \
  /tmp/bad_candidates.json \
  /tmp/l3_enriched_fail.json
```

预期：
- exit 1 (bridge_failed)
- reason=invalid_candidate_input

## 验收检查

```bash
# 输出 JSON 有效
python3 -m json.tool /tmp/l3_candidates_bridge_enriched.json > /dev/null

# 覆盖 5 种 normal_status
python3 -c "
import json
r = json.load(open('/tmp/l3_candidates_bridge_enriched.json'))
statuses = set(e.get('normal_status') for e in r['enriched_candidates'] if e.get('normal_status'))
required = {'normal_popular', 'normal_low_entropy', 'normal_not_popular_in_sample', 'high_cardinality_field'}
print('Covered statuses:', statuses)
assert required.issubset(statuses), 'Missing: %s' % (required - statuses)
# baseline_gap check
gaps = [e for e in r['enriched_candidates'] if not e.get('baseline_hit')]
assert len(gaps) > 0, 'No baseline_gap candidates found'
print('baseline_gap candidates:', len(gaps))
print('PASS')
"

# Forbidden key check
grep -R "risk_judgement\|feature_candidate\|candidate_feature_decision" \
  /tmp/l3_candidates_bridge_enriched.json || echo "(no forbidden keys in output)"

# Git check
git diff --check
git status --short
```
