# Batch Risk Representative Sampling v1

Status: runtime_rule

Representative sampling is now the execution loop for
`sample_expand_validate_mode`. It is not a loose "pick a few examples" note and
it is not permission to deep-check every entity online.

## 1. Default Parameters

```yaml
sample_expand_validate_defaults:
  initial_sample_size: 10
  sampling_method: random
  max_rounds: 5
  max_deep_checked: 50
  high_coverage_threshold: around_70_percent
  realtime_deep_check_scope: sampled_entities_only
```

70% is the default threshold for entering full-batch validation or offline
validation. It is not an automatic disposition threshold.

## 2. Round Result

Each round must produce:

```yaml
round_result:
  round_id:
  sampled_count:
  sampled_entities:
  sampling_method:
  source_completion:
  discovered_clusters:
  main_shared_signals:
  coverage_in_round:
  cumulative_coverage:
  decision:
    action: continue | offline_validate | stop
    reason:
```

## 3. Cumulative Result

```yaml
cumulative_result:
  checked_count:
  total_input_count:
  cluster_coverage:
  main_cluster:
  secondary_clusters:
  normal_or_counter:
  current_confidence:
  next_action:
```

## 4. Stop / Continue Rules

Stop and move to validation when:

- The main risk cluster reaches about 70% cumulative coverage and is stable
  across at least two rounds.
- Multiple clear risk clusters together reach about 70% coverage and each major
  cluster has a coherent evidence chain.
- Five rounds have completed or 50 realtime deep checks have been used.
- Multiple rounds show no stable commonality or source quality is mostly
  blocked / timeout / no_data; output evidence insufficiency and recommend
  `wide_table_aggregate_mode` or tighter filters.

Continue sampling when:

- Coverage is 40%-70%.
- Round one is high coverage but round two drops sharply.
- Multiple candidate clusters exist but evidence chains are incomplete.
- Normal/counter samples are high enough that the boundary needs validation.

## 5. Sample Types

- `high_confidence_positive_sample`: overlapping raw / behavior / relation
  evidence for a likely main cluster.
- `boundary_ambiguous_sample`: has risk clues but incomplete evidence; used to
  draw false-positive boundary.
- `suspected_false_positive_sample`: strategy hit or weak clue exists, but
  profile, history or context may be normal.
- `source_gap_sample`: key evidence is blocked, over-window, unavailable or
  needs authorized offline aggregation.
- `high_impact_sample`: high value / high propagation / high business impact
  sample for manual review planning.

## 6. Required Representative Sample Card

```yaml
representative_sample_card:
  sample_id:
  sample_type:
  cluster_assignment:
  why_selected:
  raw_evidence:
  derived_evidence:
  source_quality:
  missing_evidence:
  counter_evidence:
  preliminary_judgement:
  required_followup:
```

## 7. ATO Lens Sampling

For compromised-account / stolen-account posting clusters, select:

- 2-3 high-suspicion samples.
- 1-2 medium-suspicion samples.
- 1 boundary sample.
- 1 counter-example when available.

Selection priority:

- WEB / H5 / PC non-trusted login is clear.
- `login_to_action_delta` is short.
- `device_identity_inconsistency` is strong.
- diversion content is typical.
- source gap is small.

Representative ATO samples run the current single-case evidence chain through
the controlled runtime harness, then backfill cluster-level fields:

- `login_to_action_delta` distribution.
- `device_identity_inconsistency` coverage.
- shared IP / UA / ASN / browser fingerprint coverage.
- content similarity and diversion wording coverage.
- historical behavior shift coverage.
- strategy-hit combination coverage.
- source quality and missing evidence coverage.

## 8. Boundaries

- Sampling is not proof that all cluster members are risky.
- Heterogeneous clusters need representative samples per major cluster.
- One sample cannot prove a full batch.
- DataAgent/Hive validation requires explicit authorization and is not executed
  by this contract.
