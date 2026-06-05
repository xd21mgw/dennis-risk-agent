# Batch Risk Case Schema v1

Status: runtime_schema

This schema standardizes Dennis batch attack judgement for the three supported
modes: `full_observation_mode`, `sample_expand_validate_mode`, and
`wide_table_aggregate_mode`.

## 1. Batch Input

| field | required | meaning |
|---|---|---|
| `batch_id` | yes | Stable batch identifier or safe_ref. |
| `risk_domain` | yes | Account security, group control, anti-crawler, activity abuse, diversion, strategy recall, etc. |
| `scenario_type` | yes | ATO, device farm, protocol automation, content diversion, strategy false-positive review, etc. |
| `time_window_start` / `time_window_end` | yes | Evidence window. |
| `entity_count` | yes | Unique input entities. |
| `case_count` | yes | Rows / alerts / cases. |
| `input_users` | conditional | User IDs. |
| `input_devices` | conditional | Device IDs / DID. |
| `user_goal` | yes | Observation, urgent sampling, clustering, strategy, wide-table review, etc. |
| `selected_mode` | yes | One of the three supported modes. |
| `available_evidence_summary` | no | Existing evidence and quality. |
| `missing_evidence_summary` | no | Known gaps. |
| `sensitivity_level` | yes | internal_only, cross_team_safe_ref, external_redacted. |

## 2. entity_resolution_first

All three modes start with entity resolution before source lookup or aggregate
reasoning.

```yaml
entity_graph:
  input_users: []
  input_devices: []
  expanded_users: []
  expanded_devices: []
  user_device_edges:
    - user_id:
      device_id:
      edge_type: login | publish | register | graph | track | archive | inferred
      first_seen:
      last_seen:
      source:
      source_quality:
  high_degree_devices:
    - device_id:
      linked_user_count:
      reason:
  high_degree_users:
    - user_id:
      linked_device_count:
      reason:
  unresolved_entities:
    - entity:
      reason:
  entity_resolution_source:
  entity_resolution_quality: completed | partial | no_data | blocked | timeout | auth_failed | parse_error
  missing_or_blocked_reason: []
```

Rules:

- User input expands user -> device.
- Device input expands device -> user.
- Mixed input builds a user-device graph before downstream source use.
- High-degree entities are capped and marked, not expanded without control.
- Entity resolution failure enters `source_quality` and `conclusion_boundary`.

## 3. source_commonality_card

Realtime source outputs in `full_observation_mode` and
`sample_expand_validate_mode` must be compared horizontally before final
judgement.

```yaml
source_commonality_card:
  source_name:
  entity_coverage:
  records_coverage:
  shared_signals:
    - signal_name:
      support_entities: []
      support_count:
      support_ratio:
      strength: high | medium | low
      reason:
      risk_interpretation:
      evidence_type: raw | behavior | strategy_hit | inference | hypothesis | counter_evidence
      can_be_used_for_strategy: yes | no | with_combination_only
  differentiating_signals: []
  counter_evidence: []
  missing_data: []
  source_quality:
  boundary_notes: []
```

### login_log_commonality_card example

```yaml
source_name: login_log
entity_coverage: 8/10
records_coverage: partial_online_window
shared_signals:
  - signal_name: web_sms_login_then_quick_login
    support_count: 7
    support_ratio: 0.7
    strength: high
    reason: same 30-minute window, WEB login_source, QUICK_LOGIN handoff
    risk_interpretation: candidate account-control entry commonality
    evidence_type: raw
    can_be_used_for_strategy: with_combination_only
missing_data:
  - login_log_window_incomplete
boundary_notes:
  - no_data_not_risk_exclusion
  - source_window_boundary
```

### weapon_commonality_card example

```yaml
source_name: Weapon graphData/riskData
entity_coverage: 9/10
shared_signals:
  - signal_name: few_devices_many_users
    support_count: 8
    support_ratio: 0.8
    strength: high
    reason: two devices each link 4+ users
    risk_interpretation: device-farm or shared-control infrastructure candidate
    evidence_type: raw
    can_be_used_for_strategy: with_combination_only
counter_evidence:
  - two users have stable historical personal devices
boundary_notes:
  - same_device_relation_not_gang_conclusion
```

### strategy_hit_commonality_card example

```yaml
source_name: RCP/Tianshi strategy hits
entity_coverage: 10/10
shared_signals:
  - signal_name: same_policy_code_hit
    support_count: 10
    support_ratio: 1.0
    strength: medium
    reason: same source_id and policy_code hit in the same hour
    risk_interpretation: strategy response commonality; needs raw behavior confirmation
    evidence_type: strategy_hit
    can_be_used_for_strategy: with_combination_only
boundary_notes:
  - strategy_hit_not_final_judgement
```

## 4. multi_source_fusion

```yaml
multi_source_fusion:
  strong_shared_signals: []
  medium_shared_signals: []
  weak_signals: []
  conflicting_signals: []
  counter_evidence: []
  possible_normal_mixed_entities: []
  risk_clusters: []
  conclusion_boundary: []
```

Rules:

- Strong commonality generally needs at least two source families to agree.
- Single strategy hit / single IP / app_version concentration / weak device tag
  cannot finalize a risk cluster.
- Normal mixed entities stay visible and must not be forced into the main risk
  cluster.

Example:

```yaml
strong_shared_signals:
  - login_log.web_quick_login_window
  - weapon.few_devices_many_users
  - strategy.same_policy_code_hit
possible_normal_mixed_entities:
  - user_id: "U7"
    reason: stable historical device and normal login source
risk_clusters:
  - cluster_id: device_farm_cluster_A
    evidence: login + device graph + strategy hit
conclusion_boundary:
  - two users require manual review before broad action
```

## 5. cluster_summary_card

```yaml
cluster_summary_card:
  cluster_id:
  sample_count:
  sample_ratio:
  representative_entities: []
  boundary_entities: []
  counter_evidence_entities: []
  risk_type: device_farm | group_control | ato | protocol_automation | content_diversion | spam_abuse_behavior | crawler_anti_crawler | mixed_or_unknown | normal_or_insufficient_evidence
  shared_signals: []
  confidence: high | medium | low | insufficient
  attack_chain_status: complete_chain | partial_chain | hypothesis_chain | no_chain
  missing_evidence: []
  counter_evidence: []
  recommended_next_action:
```

Rules:

- Output by cluster, not one forced full-batch attack chain.
- Multiple risk clusters can coexist.
- Main cluster below 70% is not no-risk; it may mean mixed clusters.
- Normal mixed entities above 30% require false-positive warning.

## 6. attack_chain_renderer

```yaml
attack_chain:
  chain_status: complete_chain | partial_chain | hypothesis_chain | no_chain | statistical_chain_hypothesis
  entry_point:
  infrastructure:
  account_control:
  behavior_execution:
  monetization_or_goal:
  platform_response:
  missing_links: []
  confidence:
  evidence_support:
    strong: []
    inferred: []
    missing: []
```

Examples:

```yaml
device_farm_group_control_diversion:
  entry_point: shared device/IP pool
  infrastructure: two high-degree DID + one ASN
  behavior_execution: synchronized publish/comment
  chain_status: partial_chain
  missing_links: [operator identity, historical baseline]
ato_abnormal_publish:
  entry_point: WEB SMS login + quickLogin
  account_control: WEB DID handoff
  behavior_execution: publish by same WEB DID
  chain_status: partial_chain
  missing_links: historical WEB baseline
protocol_automation_anti_crawler:
  entry_point: repeated endpoint access without frontend activity
  infrastructure: UA/endpoint pattern
  behavior_execution: high-frequency request sequence
  chain_status: hypothesis_chain
  missing_links: normal traffic denominator
```

## 7. wide_table_aggregate_report

DataAgent/Hive should return a statistics package, not a `select *` dump.

```yaml
wide_table_aggregate_report:
  input_summary:
    case_count:
    feature_count:
    time_window:
    data_sources:
    join_keys:
    control_group: available | missing
    data_freshness:
    authorization_status:
  field_quality:
    usable_fields: []
    low_coverage_fields: []
    constant_fields: []
    high_cardinality_fields: []
    missing_rate_by_field: {}
    top_values_by_field: {}
    field_semantic_notes: []
  top_univariate_signals:
    - field_name:
      bucket_or_value:
      case_support_count:
      case_support_rate:
      normal_support_rate:
      lift:
      interpretation_hint:
      false_positive_hint:
      evidence_type:
  candidate_feature_combinations: []
  cluster_candidates: []
  representative_samples:
    high_confidence: []
    boundary: []
    counter_evidence: []
    suggested_followup_mode: full_observation_mode
  missing_or_unreliable: []
  recommended_next_queries: []
```

Examples:

- 500 cases x 500 fields with control group: output top fields, combinations,
  cluster candidates, lift and false-positive hints.
- No control group: output case-internal commonality only; precision/lift is
  not evaluable.
- Main cluster found: recommend representative samples into
  `full_observation_mode` before attack-chain confirmation.

Registered candidate table for first wide-table plan:
`ks_rc_bs.dws_risk_register_gang_user_week_feature_wide_di`.

## 8. strategy_recommendation_card

Strategy candidates expose both a user-visible priority and an action group.
Priority is an ordering label, not an enforcement instruction.

```yaml
strategy_recommendation_card:
  priority: P0 | P1 | P2
  action_group: ready_for_controlled_gray_validation | combine_before_use | monitor_or_expand_only
  feature_or_strategy:
  target_cluster:
  reason:
  evidence_support:
  coverage_estimate:
  precision_estimate: value | not_evaluable
  false_positive_risk:
  stability:
  rollout_suggestion:
  required_validation_data: []
  not_recommended_usage:
```

Priority mapping:

- `P0` -> `ready_for_controlled_gray_validation`: multi-source evidence is
  consistent, covers the main risk cluster, and false-positive boundary is
  controllable. It may enter controlled gray validation; it is not direct
  launch or disposition.
- `P1` -> `combine_before_use`: has separation value but is unsafe alone; use
  with other features, scoring, second verification, review, or gray
  observation.
- `P2` -> `monitor_or_expand_only`: weak signal for monitoring, offline mining
  or clue expansion; not recommended for direct treatment.

Examples:

- Multi-source combination candidate: shared WEB login window + shared DID +
  abnormal publish device; gray validate on representative cluster first.
- Assistive feature candidate: risk score / model score used only with raw
  behavior evidence, not standalone action.
- Monitoring candidate: weak UA or app-version concentration; use for offline
  exploration and drift monitoring.
