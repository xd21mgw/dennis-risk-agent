# L5 Candidate Generation v0.2

L5 consumes only L4 `review_candidates` and generates two relation-candidate
`candidate_signal` lines:

- value-level relation candidates for L6
- pattern-level relation candidates for Candidate Eval / L6 review

`pair` and `path` are retained as compatibility/debug fields. The main L5
contract is relation candidate:

- `value_relation_candidate`: concrete field/value relation.
- `pattern_relation_candidate`: abstract role/structure relation.
- `A && B` and `A -> B` are not separate candidate families. Both are evaluated
  through `CNT(A_AND_B)`, `CNT(A_AND_B) / CNT(A)`, and
  `CNT(A_AND_B) / CNT(B)`.
- Multi-hop relations use incremental next-hop logic, such as
  `CNT(A_AND_B_AND_C) / CNT(A_AND_B)`.

L5 does not:

- read L4 all cards as its main input
- access realtime platforms
- call DataAgent or Hive
- make production strategies
- verify final features
- run L6/L7 or unpredictability-anom

Core flow:

```text
L4 review_candidates
  -> input guard
  -> value nodes
  -> inverted indexes
  -> value ranking with value_score / anchor_score / next_node_score
  -> value-level relation candidates with in-sample CNT / conversion scoring
  -> shallow multi-hop value relations
  -> top-K selection
  -> pattern-level relation abstraction from selected top-K
  -> l6_next_tasks_from_l5.json
  -> l5_pattern_candidates.json
```

Primary output for L6:

- `l6_next_tasks_from_l5.json`
- `l5_pattern_candidates.json`

Audit/debug outputs:

- `l5_execution_candidates.json`
- `l5_contract_violations.json`
- `l5_prior_seed_input.json`
- `llm_field_pair_prior_overlay.example.json`
- `l5_prior_promotion_candidates.json`
- `l5_anchor_scoring_audit.md`
- `l5_knowledge_base_snapshot.json`
- `l5_summary.md`

Every relation candidate is a `candidate_signal` with the fixed evidence
boundary:

```text
仅基于当前风险样本空间和 L4 review_candidates 的样本内 CNT / conversion 关系发现，未经过 Hive 大盘、偏白样本、历史召回、时序稳定性验证。
```

v0.2 keeps all generated value-level relation candidates in
`l5_execution_candidates.json`, but `l6_next_tasks_from_l5.json` only contains
selected top-K candidates after score, quota, near-duplicate, and
uncertain-prior controls.

## Role-specific Scoring

L5 scores a value node differently by path position:

- `anchor_score`: whether the value is suitable as A, the first space-cutting
  anchor. It favors high normal entropy, low local-normal value rate, high risk
  hit rate, high risk/normal lift, adequate support, and safe granularity.
- `next_node_score`: whether the value is suitable as B/C/D. It supports both
  secondary anchors that further constrain the space and explaining/confirming
  nodes such as weak device labels or behavior signals.

`oneRisk`, result labels, post-action fields, and broad profile/context fields
are downgraded for A. They may still remain useful as B/C/D confirming nodes.

## Local Normal Baseline

When available, the CLI loads local baseline artifacts from
`/tmp/normal_baseline_layered_v0_2/`. These values are used only for in-sample
ranking support:

- `normal_field_non_null_count`
- `normal_field_distinct_count`
- `normal_field_entropy`
- `normal_value_count`
- `normal_value_rate`
- `risk_normal_lift`

If the local baseline is missing, L5 keeps running with
`normal_baseline_status=missing` and null normal fields. This is not Hive or
global validation.

## Prior Seed / Overlay

L5 runtime does not call LLMs. Prior enrichment is batch-first and split into
long-term field knowledge and run-level value relation overlays.

Long-term field-level knowledge:

- `l5_knowledge_base_v0_1.json`
- `l5_field_prior_kb.json`

These contain stable judgements such as unique-ID fields, leakage fields,
over-general profile/context fields, natural field relations, and field-family
roles.

Run-level value relation overlay:

- `l5_value_relation_prior_overlay.json`

This file is scoped to one replay/run. It may express value-conditioned
judgements such as `ip24=value -> device_model=value` or
`accessibilityServiceList=value -> oneRisk=value`. It is not promoted into the
long-term KB automatically.

1. L5 emits `l5_prior_seed_input.json` with unique fields, field pairs, examples,
   and current KB summary.
2. A human or offline LLM process may produce field-level seeds or a run-level
   value overlay following `llm_field_pair_prior_overlay.example.json`.
3. L5 runtime only loads these files as tables. High-confidence judgements can
   affect ranking; medium confidence keeps an uncertainty penalty; low confidence
   remains uncertain.
4. `need_human_review=true` judgements remain visible in summaries.

Lookup priority:

1. run-level value relation overlay
2. long-term value relation KB, if added later
3. field-level KB / `l5_knowledge_base_v0_1.json`
4. base hardcoded knowledge
5. missing prior -> `uncertain`

Promotion into long-term KB is explicit. L5 writes
`l5_prior_promotion_candidates.json` with pending candidates; human review or
Candidate Eval must approve promotion.

Pattern-level relation candidates are rule-template abstractions from selected
value-level relations. They are not verified features or production rules. Each
pattern candidate carries `relation_expression`, `observed_metrics`,
`thresholds`, and a Candidate Eval request for base rate, white-sample contrast,
historical recall, temporal stability, and false-positive review.

Candidate Eval / Hive should later consume `relation_expression` and validate:

- `CNT(A)`
- `CNT(B)`
- `CNT(A_AND_B)`
- `CNT(A_AND_B) / CNT(A)`
- `CNT(A_AND_B) / CNT(B)`
- incremental CNT / conversion for multi-hop relations
