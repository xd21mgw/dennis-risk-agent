# Fact Table Contract v1

Status: phase4_6_contract_only. This contract defines the structured fact
input layer used by Dennis batch commonality reasoning. It does not change
runtime execution, start browser-backed service, call platforms, call
DataAgent/Hive, or refresh outputs.

Purpose:

- Keep raw details available for controlled local trace-back without putting
  raw bodies into model context.
- Project raw details into safe structured records.
- Build analysis tables from projected records.
- Make batch commonality consume structured tables, not only compressed
  per-user observations.

## Data Flow

```text
raw_detail_retention_layer
-> safe_projected_records
-> standard_detail_table
-> anchor_table / feature_table / relation_table / source_quality_table
-> round_support_table / rolling_anchor_summary
-> commonality_matrix / group_profile_candidate / candidate_features
```

`per_user_observation` is an explanation artifact for humans. It may summarize
one sample, but it must not be the only fact source for batch commonality.

## Raw Detail Retention Layer

Raw detail retention is for controlled trace-back only.

Rules:

- Do not place raw body, upstream body, capped body, `logContent`, credential
  material, or full request/response envelopes in user-visible answers.
- Do not use raw retained data as the main batch commonality input.
- Keep only safe references, source ids, counts, field paths, and projected
  values that are necessary for evidence chaining.

## Standard Detail Table

Every projected field-level fact should be representable as:

```yaml
standard_detail_table:
  - sample_id:
    entity_id:
    entity_type:
    round_id:
    source_id:
    action:
    observation_domain:
    field_name:
    field_value_or_safe_ref:
    event_time:
    source_quality:
    evidence_source: current_observation | projected_record | fixture_mock
```

## Anchor Table

Anchors are evidence handles that can drive bounded drilldown or commonality.

```yaml
anchor_table:
  - round_id:
    sample_id:
    entity_id:
    anchor_type:
    anchor_value_or_safe_ref:
    source_id:
    field_path:
    source_quality:
    anchor_class: presence_anchor | anomaly_anchor | commonality_anchor | chain_anchor
    anchor_score:
    selection_status: selected | skipped_by_domain_cap | skipped_by_type_cap | skipped_low_score | skipped_missing_anchor | plan_only
    anchor_priority_reason:
```

## Feature Table

Candidate features are not conclusions or strategies to auto-launch.

```yaml
feature_table:
  - feature_name:
    source_domains: []
    supporting_current_evidence: []
    supporting_selected_anchors: []
    signal_inputs: []
    hypothesis_inputs: []
    validation_needed: true
    false_positive_risk:
    not_final_conclusion: true
```

## Relation Table

Relations are bounded edges, not graph-wide expansion.

```yaml
relation_table:
  - from_entity:
    to_entity:
    relation_type:
    edge_type:
    edge_strength:
    source_id:
    source_quality:
    round_id:
    expansion_depth:
    stop_reason:
```

## Source Quality Table

Source quality is a first-class input to commonality and feature mining.

```yaml
source_quality_table:
  - round_id:
    entity_id:
    source_id:
    action:
    quality_class: completed | partial | no_data | skipped | timeout | missing_contract | parse_error
    reason:
    partial_subtype:
    missing_fields: []
    response_limited:
```

`no_data`, `skipped`, `timeout`, `missing_contract`, and response limits are
gaps, not low-risk counter evidence.

## Round Support Table

Rolling batch commonality must track per-round support.

```yaml
round_support_table:
  - signal_name:
    round_id:
    support_entities: []
    support_count:
    support_ratio:
    source_quality_summary:
```

## Rolling Anchor Summary

Rolling anchor summaries prevent one round from becoming a global conclusion.

```yaml
rolling_anchor_summary:
  - anchor_type:
    anchor_value_or_safe_ref:
    cumulative_support_count:
    support_rounds: []
    stability_across_rounds: stable | weakening | dropped | emerging | insufficient_rounds
    new_anchor_delta: []
    dropped_anchor_reason:
    current_status: stable | weakening | dropped | emerging | insufficient_rounds
```

Rolling batch outputs also need:

- `round_support_count`
- `cumulative_support_count`
- `support_ratio`
- `stability_across_rounds`
- `new_anchor_delta`
- `stable_anchors`
- `dropped_anchors`

## Mode Consumption

`full_observation_mode`:

- Suitable for fewer than 10 entities.
- May rely on per-sample evidence cards for human readability.
- Must still retain source quality, anchor table, and feature table references.
- Commonality should use projected facts and anchors, not narrative text alone.

`sample_expand_validate_mode`:

- Rolling batch mode: first 10, expand 10, up to 50.
- Must consume `anchor_table`, `feature_table`, `relation_table`,
  `source_quality_table`, `round_support_table`, and
  `rolling_anchor_summary`.
- Must output round support, cumulative support, stability across rounds, new
  anchor delta, stable anchors, and dropped anchors.
- Per-user observations are explanation material only.

## Mapping From Existing Artifacts

Current Phase 3/4 artifacts can map into the table layer:

- `base_summary_card` and `drilldown_evidence_card` -> `standard_detail_table`
- `candidate_anchor_pool`, `selected_drilldown_anchors`, `skipped_anchors` -> `anchor_table`
- `candidate_features` -> `feature_table`
- `relation_expansion_result` -> `relation_table`
- `source_quality` -> `source_quality_table`
- `commonality_matrix.shared_signals` -> `round_support_table`
- `anchor_scoring_summary` and cross-round deltas -> `rolling_anchor_summary`

Runtime may initially produce these as equivalent structured artifacts. Phase 4.6
only fixes the contract and checks; full runtime table emission is a later step.

## Boundaries

- Do not restore raw bodies into model context.
- Do not let per-user observation be the only batch commonality source.
- Do not treat missing, skipped, no-data, timeout, or missing-contract rows as
  counter evidence.
- Do not treat a candidate feature as a final conclusion.
- Do not treat rolling support as full coverage without validation.
- DataAgent/Hive validation remains authorization-gated and is not executed by
  this contract.
