# Batch Risk Three-Mode Routing Policy v1

Status: runtime_rule

This policy replaces the old 1-2 / 3-4 / 5-9 / 10-49 / 50+ batch mode ladder.
Dennis uses exactly three batch attack-judgement modes. Do not add a fourth
or fifth mode.

## 1. Three Modes

| entity_count / intent | selected_mode | default behavior | boundary |
|---|---|---|---|
| `entity_count <= 10` | `full_observation_mode` | Small-batch full observation: resolve entities first, run available realtime readonly sources for each sample, compare horizontally, output clusters, attack chain and strategy candidates. | Not a single-case transcript loop; every source result must feed `source_commonality_card`. |
| `entity_count > 10` and urgent / same-origin / unknown / "先看看" / no wide table yet | `sample_expand_validate_mode` | Randomly sample 10, run `full_observation_mode` on the sample, expand up to 5 rounds / 50 deep-checked entities, then stop / continue / offline validate. | Never realtime-deep-check the whole batch by default. 70% is a validation threshold, not an auto-action threshold. |
| `entity_count > 10` and wide table / feature / coverage / precision / strategy / retrospective / DataAgent/Hive intent | `wide_table_aggregate_mode` | DataAgent/Hive returns `wide_table_aggregate_report`; Dennis explains clusters, attack-chain hypotheses and strategy candidates. | DataAgent does statistics and retrieval, not final risk judgement. Execution requires per-call authorization. |

User-specified mode wins when safe, but cannot override DataAgent/Hive
authorization, no-data boundaries, source-quality requirements, or the ban on
large realtime one-by-one lookup.

## 2. Routing Rules

### full_observation_mode

Use when:

- 2-10 `user_id` / `device_id` / mixed entities.
- User asks "这几个是不是一伙 / 这几个设备有没有共性 / 帮我细查这批小样本".

Required flow:

1. `entity_resolution_first`.
2. Realtime readonly source plan.
3. Source-specific evidence cards.
4. `source_commonality_card` per source.
5. `multi_source_fusion`.
6. `cluster_summary_card`.
7. `attack_chain_renderer`.
8. Strategy candidates with evidence / coverage / false-positive boundary.

### sample_expand_validate_mode

Use when:

- More than 10 entities.
- User asks urgent same-source / unknown-risk / "先看看" / no wide-table result yet.

Defaults:

```yaml
initial_sample_size: 10
sampling_method: random
max_rounds: 5
max_deep_checked: 50
high_coverage_threshold: around_70_percent
```

Stop / continue:

- Stop to offline validate when the main risk cluster covers about 70% across
  at least two rounds.
- Continue when coverage is 40%-70%, the second round drops sharply, or there
  are multiple candidate clusters.
- Stop with insufficient support after 5 rounds or no stable commonality.

### wide_table_aggregate_mode

Use when:

- User mentions wide table, features, coverage, precision, recall, strategy,
  historical review, DataAgent/Hive, control group, or large feature set.
- Large samples already have or need aggregate statistics.

Default registered wide-table starting point:

```yaml
registered_candidate_table:
  table: ks_rc_bs.dws_risk_register_gang_user_week_feature_wide_di
  status: registered_candidate_not_executed
  use: register/gang/user weekly feature wide table candidate for aggregate mode
  boundary: table availability and field semantics must be confirmed by DataAgent/Hive before execution
```

DataAgent/Hive execution is not automatic. Dennis may produce a registry-first
query plan and the required `wide_table_aggregate_report` shape only.

## 3. Hard Guards

- Do not default to per-entity transcripts for batch questions.
- Do not realtime-deep-check every entity in large batches.
- Do not force large batches to wait for offline wide tables when the user is
  asking for urgent sampling.
- Do not execute DataAgent/Hive without explicit per-call authorization.
- Do not use strategy hits, no-data, same IP, same device, app version, model
  score, or a single weak device tag as final judgement.
- Do not let run logs or historical patches override this policy.

## 4. Legacy Mapping

The old modes are historical aliases only:

| old mode | current mapping |
|---|---|
| `small_multi_case_execution_mode`, `small_batch_mode`, `small_batch_execution_with_checkpoint` | `full_observation_mode` when entity_count <= 10 |
| `batch_clustering_mode` | `sample_expand_validate_mode` or `wide_table_aggregate_mode` depending on intent |
| `large_batch_aggregation_mode`, `alert_batch_or_population_analysis_mode` | `wide_table_aggregate_mode` |

Do not emit the old aliases in user-facing output unless explaining historical
compatibility in debug/run-log context.
