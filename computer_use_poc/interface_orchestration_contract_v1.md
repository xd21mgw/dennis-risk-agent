# Interface Orchestration Contract v1

Status: phase2_contract_only. This document defines Dennis-side interface
orchestration language for the current browser-backed service action registry.
It does not change runtime execution, browser-backed service behavior, or
`default_runtime_routing=false`.

Source of truth:

- Service action truth: `/Users/pengcheng/dennis-local/browser-backed-api-poc/ACTION_REGISTRY.md`.
- Current service count: `action_count=74`.
- Dennis asset table: `computer_use_poc/browser_backed_interface_asset_table_v1.yaml`.
- Drift check: `python3 computer_use_poc/interface_asset_table_check.py --format json`.

Business naming rule: call service actions and HAR inventory rows "interfaces"
when discussing business orchestration. Implementation may still use the
service word `action` at API boundaries.

## Implementation Orchestration Layers

| layer_id | 中文名 | Purpose | Main artifacts |
|---|---|---|---|
| `input_route_layer` | 输入识别与路由 | Classify seed entity and choose allowed interface families. This is routing, not full entity expansion. | `task_route`, `seed_entity`, `base_interface_plan` |
| `base_summary_layer` | 基础摘要层 | Run low-cost, low-dependency summary interfaces and discover the first anchor pool. | `base_summary_card`, `base_commonality`, `candidate_anchor_pool` |
| `anchor_drilldown_layer` | 追踪下钻层 | Follow valuable anchors such as `photo_id`, `device_id`, `event_id`, `comment_id`, `live_id`, or relation anchors. Multi-round tracking is allowed only with caps and stop reasons. | `drilldown_evidence_card`, `new_anchor_pool`, `tracking_commonality`, `stop_reason` |
| `cross_domain_commonality_layer` | 交叉共性分析层 | Combine base and drilldown observations across domains to find shared fields, shared anchors, chain commonality, and abnormal correlations. | `commonality_matrix`, `abnormal_correlation`, `representative_samples`, `candidate_features`, `group_profile_candidate` |
| `validation_layer` | 补证验证层 | Validate candidate patterns with offline/aggregate evidence, replay, control groups, or wide-table statistics when authorized. | `validation_plan`, `validation_result`, `coverage_gap`, `false_positive_risk` |
| `judgement_output_layer` | 研判输出层 | Render evidence, pattern summaries, group candidates, strategy recommendations, missing evidence, and boundaries. | `final_evidence_card`, `pattern_summary`, `group_profile`, `strategy_recommendation`, `missing_evidence` |

## Business Observation Dimensions

Risk object domains:

- `account_domain` / 账号域: registration, profile, account status, labels, account-change timeline.
- `device_domain` / 设备域: DID, device_id, user-device graph, device risk, device consistency.
- `network_domain` / 网络域: IP, UA, region, ASN/IDC/proxy, login network, publish network.
- `content_domain` / 内容域: photo, live, moment, content template, diversion copy, audit object, report object.
- `social_domain` / 社交域: comments, private messages, fans, follows, likes/favorites, social handoff.
- `behavior_domain` / 行为域: backend login/register/publish/comment/message/token/session actions; frontend Track activity, duration, page/action alignment; front-backend consistency.

Aggregate object domain:

- `group_domain` / 团伙域: risk clusters, group-profile candidates, device/IP/content/social/strategy shared clusters. Default output is `group_profile_candidate` or `risk_cluster_candidate`; only strong multi-source closure can upgrade to `confirmed_group` / `fraud_ring`.

Risk signal domains:

- `strategy_domain` / 策略域: strategy hits, policy_code, sourceId, event_id, feature keys, policy tree/version/release data. Strategy hit is a signal, not final judgement.
- `enforcement_domain` / 处置域: block, punish, ban, limit, secondary verification, content takedown, gray rollout, policy tuning. This is platform action/state.
- `feedback_domain` / 反馈域: reports, complaints, appeals, manual review feedback, false-positive feedback. Feedback can point back to account/content/social objects but is not enforcement.

Horizontal analysis capabilities:

- `relation_expansion` / 关联扩散: traverse bounded edges such as account-device-account, account-IP-account, account-content-commenter, account-fans/follow-message-account, or sample-policy-sourceId peers. It is not a domain and must have `expansion_depth`, `entity_cap`, `edge_type`, `edge_strength`, and `stop_reason`.
- `commonality_discovery` / 共性发现: discover shared fields, anchors, behavior, chains, and governance signals at every layer.
- `abnormal_correlation` / 异常相关性: identify directional cross-domain correlations that normal populations should not strongly share.
- `representative_sampling` / 代表样本: choose high-confidence, boundary, and counter-evidence samples for batch reasoning or validation.
- `candidate_feature_mining` / 候选特征: convert commonality and abnormal correlation into candidate strategy/model/monitoring features.

## Interface Call Roles

| role | Meaning |
|---|---|
| `first_hop_candidate` | May be selected for `base_summary_layer` when seed input and scene fit. |
| `anchor_triggered_drilldown` | Requires a prior anchor such as `photo_id`, `device_id`, `event_id`, `policy_code`, `comment_id`, `live_id`, or relation anchor. |
| `multi_round_drilldown` | Can create new anchors and continue tracking, but only under explicit caps and stop reasons. |
| `validation_only` | Used for validation/replay/coverage checks; not default realtime conclusion evidence. |
| `governance_only` | Strategy/policy governance or explanation; not ordinary user-risk evidence unless an event/policy anchor exists. |
| `parameter_only` | Parameter, dimension, option, or schema discovery. It must not enter final risk evidence by itself. |
| `unavailable_or_missing_contract` | Inventory or desired interface lacks a registered fixed service contract. It must be marked missing/skipped, never fabricated as checked. |

The same interface may have different roles by input. Example: `archives_photo_meta`
is a first-hop candidate when the user directly provides `photo_id`, but an
anchor-triggered drilldown when the seed is `user_id` and `photo_id` was
discovered by `archives_photo_search`.

## Structured Fact Table Input Layer

Detailed fact-table schema is defined in
`computer_use_poc/fact_table_contract_v1.md` and checked by
`python3 computer_use_poc/fact_table_contract_check.py --format json`.

The fact-table layer prevents batch commonality from depending only on
compressed per-user observations. Current orchestration artifacts can map into
these tables:

- `base_summary_card` / `drilldown_evidence_card` -> `standard_detail_table`.
- `candidate_anchor_pool`, `selected_drilldown_anchors`, `skipped_anchors` -> `anchor_table`.
- `candidate_features` -> `feature_table`.
- `relation_expansion_result` -> `relation_table`.
- `source_quality` -> `source_quality_table`.
- `commonality_matrix.shared_signals` -> `round_support_table`.
- `anchor_scoring_summary` and cross-round deltas -> `rolling_anchor_summary`.

Mode consumption:

- `full_observation_mode`: may use per-sample evidence cards for readability,
  but commonality must still retain structured source quality, anchor, and
  feature references.
- `sample_expand_validate_mode`: must consume `anchor_table`,
  `feature_table`, `relation_table`, `source_quality_table`,
  `round_support_table`, and `rolling_anchor_summary`. It must not compute
  rolling commonality from per-user observation summaries alone.

Raw detail retention is trace-back only. `safe_projected_records` and analysis
tables must not expose raw body, capped body, `logContent`, or credential-like
raw values.

## Artifact Schemas

```yaml
task_route:
  task_type:
  route_mode:
  seed_entity_types: []
  allowed_layers: []
  forbidden_expansion: []
  authorization_boundary:

seed_entity:
  entity_type: user_id | device_id | photo_id | ip | event_id | policy_code | live_id | comment_id
  value:
  source: user_input | prior_anchor
  confidence:

base_interface_plan:
  layer: base_summary_layer
  candidate_interfaces: []
  skipped_interfaces: []
  cap:
  expected_anchor_types: []

base_summary_card:
  entity:
  observation_domains: []
  source_quality:
  base_facts: []
  candidate_anchors: []
  no_data_boundary:

candidate_anchor_pool:
  anchors:
    - anchor_type:
      value:
      produced_by:
      confidence:
      next_allowed_interfaces: []
      cap_key:
      anchor_class: presence_anchor | anomaly_anchor | commonality_anchor | chain_anchor
      anchor_score:
        anchor_presence:
        anomaly_strength:
        batch_support_count:
        cross_domain_support:
        chain_value:
        cost_level:
        expansion_risk:
        false_positive_risk:
        evidence_quality:
        current_observation_support:
        total_score:
        supporting_entities: []
        supporting_sources: []
      selection_status: selected | skipped_by_cap | skipped_by_domain_cap | skipped_by_type_cap | skipped_low_score | duplicate_anchor | low_value_anchor | plan_only
      anchor_priority_reason: []

anchor_scoring_summary:
  candidate_anchor_count:
  selected_anchor_count:
  skipped_anchor_count:
  max_selected_drilldown_anchors:
  max_selected_per_domain:
  max_selected_per_anchor_type:
  domain_distribution: {}
  selected_domain_distribution: {}
  skipped_domain_distribution: {}
  anchor_type_distribution: {}
  selected_anchor_type_distribution: {}
  skipped_anchor_type_distribution: {}
  batch_support_count_semantics: distinct_sampled_entity_count
  limited_commonality:

selected_drilldown_anchors:
  anchors: []

skipped_anchors:
  - anchor:
    skip_reason: skipped_by_cap | skipped_by_domain_cap | skipped_by_type_cap | skipped_low_score | duplicate_anchor | low_value_anchor
    anchor_priority_reason: []

drilldown_evidence_card:
  anchor:
  interface:
  extracted_facts: []
  new_anchors: []
  missing_fields: []
  stop_reason:

new_anchor_pool:
  anchors: []
  dedupe_policy:
  cap_status:

tracking_commonality:
  source_anchors: []
  shared_tracking_signals: []
  differentiating_tracking_signals: []
  source_quality:

commonality_matrix:
  rows: []
  columns: []
  shared_signals: []
  differentiating_signals: []
  counter_evidence: []
  limited_commonality:

abnormal_correlation:
  relation_family:
  source_domain:
  target_domain:
  evidence_basis:
  expected_normal_pattern:
  abnormal_pattern:
  strength:
  caveat:

candidate_features:
  - feature_name:
    source_domains: []
    supporting_current_evidence: []
    supporting_selected_anchors: []
    unselected_signal_hypothesis:
    signal_inputs:
      - evidence_source: current_observation
        signals: []
        supporting_selected_anchors: []
        usage_boundary: supports_candidate_feature_only_not_final_conclusion
    hypothesis_inputs:
      - evidence_source: historical_risk_pattern | expert_hypothesis
        signal:
        usage_boundary: expert_hypothesis_only_not_current_evidence
    expert_risk_signal_input:
      compatibility_alias_only: true
      boundary: do_not_use_as_evidence_or_conclusion
    confidence:
    validation_needed: true
    false_positive_risk:
    not_final_conclusion: true

relation_expansion_result:
  seed_anchor:
  edge_type:
  expansion_depth:
  entity_cap:
  returned_entities: []
  edge_strength:
  stop_reason:

group_profile_candidate:
  cluster_id:
  representative_entities: []
  shared_domains: []
  shared_signals: []
  supporting_selected_anchors: []        # compatibility field; batch-support anchors only
  supporting_selected_batch_anchors: []  # anchors that can support batch/group candidate
  context_selected_anchors: []           # single-entity/explanatory anchors; not group support
  supporting_anchor_boundary:
  missing_evidence: []
  confidence:
  not_confirmed_as_group: true

validation_plan:
  validation_goal:
  required_data: []
  dataagent_or_hive_required:
  authorization_required:
  expected_output:

validation_result:
  coverage:
  precision_or_lift:
  false_positive_risk:
  data_freshness:
  caveats: []

final_evidence_card:
  conclusion_state:
  strong_evidence: []
  medium_evidence: []
  weak_evidence: []
  counter_evidence: []
  missing_evidence: []
  source_quality:
  boundary:

pattern_summary:
  pattern_id:
  affected_domains: []
  evidence_support:
  representative_samples: []
  cannot_conclude_boundary:

strategy_recommendation:
  priority: P0 | P1 | P2
  action_group:
  feature_or_strategy:
  evidence_support:
  coverage_estimate:
  precision_estimate:
  false_positive_risk:
  rollout_suggestion:
  not_recommended_usage:

missing_evidence:
  missing_item:
  missing_domain:
  reason: no_data | skipped | timeout | missing_contract | authorization_required | cap_reached
  next_action:
```

## Cap And Stop Rules

Default planning caps:

- `max_l1_interfaces_per_entity`: 6 unless a mode-specific contract is stricter.
- `max_l2_interfaces_per_anchor_type`: 2 by default.
- `max_anchor_items_per_domain`: 3 to 5 by default.
- `max_relation_expansion_depth`: 1 unless explicitly authorized.
- `max_relation_entities_per_edge_type`: 20 by default.
- Runtime chunk caps may be lower and must win over planning caps.

Allowed stop reasons:

- `cap_reached`
- `missing_anchor`
- `missing_contract`
- `skipped_unavailable_action`
- `source_timeout`
- `source_no_data_not_counter_evidence`
- `low_value_anchor`
- `duplicate_anchor`
- `authorization_required`
- `no_new_evidence_after_round`
- `service_contract_gap`
- `parse_error`

## Required Boundaries

- Input recognition is route selection, not full entity expansion.
- `base_summary_layer` is not "run all interfaces".
- Do not draw the registered interfaces as one process node per interface; group by observation domain and call role.
- Strategy hits are `strategy_domain` signals, not the center of all risk reasoning.
- Feedback and enforcement are separate domains.
- `group_domain` is an aggregate object domain. Use `group_profile_candidate` by default; do not output `confirmed_group` or `fraud_ring` without strong multi-source closure and validation.
- `relation_expansion` must not become full graph scanning.
- `no_data`, `skipped`, `timeout`, `missing_contract`, and `cap_reached` are not low-risk counter-evidence.
- `inventory_only` or `missing_contract` interfaces must never be presented as checked.
- Historical Dennis risk patterns and expert hypotheses may be used only as `expert_risk_signal_input` for `commonality_matrix`, `abnormal_correlation`, and `candidate_features`. They must be labelled as `historical_risk_pattern` or `expert_hypothesis`, combined with current observation and source quality, and sent to validation before becoming strategy recommendations or conclusions.
- DataAgent/Hive and wide-table validation require explicit per-call authorization.
