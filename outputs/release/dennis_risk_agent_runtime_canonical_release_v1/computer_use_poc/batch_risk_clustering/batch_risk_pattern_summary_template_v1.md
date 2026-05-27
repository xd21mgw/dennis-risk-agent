# Batch Risk Pattern Summary Template v1

```yaml
batch_overview:
  batch_id:
  risk_domain:
  scenario_type:
  time_window:
  entity_count:
  case_count:
  selected_mode:
  one_sentence_judgement:
  confidence_level:

input_coverage:
  provided_fields:
  missing_fields:
  source_coverage:
  sensitivity_level:

data_quality_assessment:
  freshness_status:
  permission_status:
  source_gap:
  baseline_status:
  no_data_boundary:

cluster_summary:
  - cluster_id:
    cluster_name:
    covered_cases:
    coverage_ratio:
    key_common_features:
    evidence_level:
    risk_hypothesis:
    cannot_conclude:

abnormal_correlation_matrix_summary:
  - relation_direction:
    observed_pattern:
    baseline_comparison:
    enrichment_signal:
    coverage_ratio:
    directionality:
    attack_path_hypothesis:
    evidence_level:
    required_followup:
    risk_of_false_positive:

representative_samples:
  - case_id:
    sample_type:
    cluster_assignment:
    why_selected:
    evidence_card_ref:

common_evidence:
  raw_evidence:
  derived_evidence:
  current_task_observation:

attack_path_hypotheses:
  - hypothesis:
    support_level:
    supporting_evidence:
    missing_evidence:
    alternative_explanation:

counter_evidence_and_false_positive_risk:
  normal_business_explanations:
  false_positive_samples:
  counter_evidence:
  manual_review_needed:

missing_evidence_and_source_gap:
  missing_evidence:
  blocked_evidence:
  timeout_sources:
  partial_sources:
  source_gap:

recommended_followup_plan:
  online_readonly_observation:
  representative_sample_deep_dive:
  baseline_comparison_needed:
  manual_review_plan:

dataagent_hive_query_plan_if_needed:
  dataagent_needed:
  hive_required:
  query_scope:
  time_window:
  group_by_fields:
  metrics:
  hypothesis_to_validate:

strategy_recommendations:
  candidate_rules:
  abuse_boundary:
  false_positive_control:
  do_not_auto_launch:

monitoring_recommendations:
  indicators:
  alert_thresholds:
  dashboard_slices:
  rollback_signals:

grey_release_or_control_suggestions:
  control_type:
  grey_scope:
  holdout_group:
  review_queue:
  success_metrics:

manual_review_boundary:
  requires_human_review:
  review_samples:
  escalation_conditions:

cannot_conclude_statement:
  current_limits:
  evidence_needed_to_upgrade:
```

## Required Statements

- Batch summary is a pattern hypothesis unless supported by raw / derived evidence from current batch.
- Historical similar pattern is not current evidence.
- no_data / blocked / timeout cannot be used as no-risk counter evidence.
- Similarity alone cannot support same-gang judgement.
