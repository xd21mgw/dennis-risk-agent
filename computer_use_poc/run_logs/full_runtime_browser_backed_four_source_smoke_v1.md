# Full Runtime Browser-Backed Four-Source Smoke v1

Date: 2026-05-29

Scope: record the completed `outputs/full_runtime` browser-backed four-source smoke result. This run log is a post-run summary only; no platform source, browser profile, auth material, SSO runner, DataAgent, or Hive was accessed while writing this file.

## Runtime

```yaml
runtime_dir: /Users/pengcheng/dennis-risk-agent/outputs/full_runtime
service: http://127.0.0.1:8787
client: computer_use_poc/browser_backed_service_client.py
```

## Validation

```yaml
py_compile: passed
self_test: passed
```

## Four-Source Smoke Result

| action | source_status | latency_ms |
| --- | --- | ---: |
| `track_analysis_summary` | `completed` | 184 |
| `rcp_snapshot` | `completed` | 4225 |
| `weapon_inventory` | `completed` | 135 |
| `login_logs_search` | `no_data` | 138 |

## Normalized Matrix

```yaml
normalized_matrix:
  completed_sources:
    - track_analysis_summary
    - rcp_snapshot
    - weapon_inventory
  no_data_sources:
    - login_logs_search
  blocked_sources: []
  auth_failed_sources: []
  timeout_sources: []
  parse_error_sources: []
  invalid_parameter_sources: []
  source_quality:
    track_analysis_summary:
      source_status: completed
      failure_layer: no_failure
      error_type: null
      latency_ms: 184
      no_data_not_risk_exclusion: true
    rcp_snapshot:
      source_status: completed
      failure_layer: no_failure
      error_type: null
      latency_ms: 4225
      no_data_not_risk_exclusion: true
    weapon_inventory:
      source_status: completed
      failure_layer: no_failure
      error_type: null
      latency_ms: 135
      no_data_not_risk_exclusion: true
    login_logs_search:
      source_status: no_data
      failure_layer: source_observation
      error_type: null
      latency_ms: 138
      no_data_not_risk_exclusion: true
```

## Mini Evidence Card Summary

```yaml
mini_evidence_card:
  card_type: partial_evidence_card
  sensitive_output: false
  completed_sources:
    - track_analysis_summary
    - rcp_snapshot
    - weapon_inventory
  no_data_sources:
    - login_logs_search
  blocked_sources: []
  final_risk_judgement_made: false
  no_data_not_risk_exclusion: true
  evidence_boundary:
    no_data_not_no_risk: true
    strategy_hit_device_risk_activity_profile_are_evidence_not_final_judgement: true
    final_risk_judgement_made: false
  evidence_summary_by_source:
    track_analysis_summary:
      source_status: completed
      source_card_exists: true
      source_quality_exists: true
      profile_summary:
        register_time_present: true
        fan_distribution_present: true
        active_days_bucket_present: true
        device_ids_count: 2
      device_ids_summary:
        device_ids_count: 2
      raw_body_suppressed: true
    rcp_snapshot:
      source_status: completed
      source_card_exists: true
      source_quality_exists: true
      event_count: 200
      chaining_keys_present:
        hitFusePolicyCode: true
        eventId: true
        _occurTime: true
      boundary: RCP is a strategy event entry source, not a final risk judgement.
      raw_body_suppressed: true
    weapon_inventory:
      source_status: completed
      source_card_exists: true
      source_quality_exists: true
      graph_status: completed
      related_device_count: 0
      related_user_count: 1
      risk_label_count: 0
      raw_weapon_fields_suppressed:
        - raw deviceId
        - raw labelInfo
        - raw originalLog
      raw_body_suppressed: true
    login_logs_search:
      source_status: no_data
      source_card_exists: true
      source_quality_exists: true
      records_count: 0
      caveat: no_data only means no visible rows in the observed window; it is not no-risk evidence.
      raw_body_suppressed: true
  missing_evidence:
    - source_name: login_logs_search
      reason: visible_window_no_data
      caveat: no_data is not no-risk evidence
  next_action:
    dataagent_hive_called: false
    dataagent_hive_boundary: recommendation_only_not_called
```

## Boundary

- No direct platform call by `full_runtime`.
- No auth material read.
- No SSO runner invoked.
- No DataAgent/Hive call.
- `sensitive_output=false`.
- `no_data_not_risk_exclusion=true`.
- No raw profile body, raw deviceId, raw IP, raw login records, raw labelInfo, or raw originalLog was included in this run log.

## Known Gap

- `computer_use_poc/smoke_tests.md` is not present in the `outputs/full_runtime` package. Record this as a runtime file gap, not as a smoke failure.

## Conclusion

```yaml
full_runtime_browser_backed_smoke_pass: true
```
