# Browser-Backed Service Executable Adapter Dry Run v1

Date: 2026-05-29

Scope: Dennis-side executable adapter fixture validation only. No live platform was accessed, the browser-backed service was not started, and no browser profile or authentication material was read.

## Simulated Source Results

| Source | Action | Simulated source_status | Error type | sensitive_output |
| --- | --- | --- | --- | --- |
| Track Analysis | `track_analysis_summary` | `completed` | null | `false` |
| RCP eventList | `rcp_snapshot` | `completed` | null | `false` |
| Weapon graph/risk | `weapon_inventory` | `completed` | null | `false` |
| Login Logs | `login_logs_search` | `no_data` | null | `false` |

## Expected Source Completion Matrix

```yaml
source_completion_matrix:
  completed_sources:
    - track_analysis_summary
    - rcp_snapshot
    - weapon_inventory
  no_data_sources:
    - login_logs_search
  auth_failed_sources: []
  blocked_sources: []
  timeout_sources: []
  parse_error_sources: []
  invalid_parameter_sources: []
  source_quality:
    track_analysis_summary:
      source_status: completed
      failure_layer: no_failure
      error_type: null
      no_data_not_risk_exclusion: false
    rcp_snapshot:
      source_status: completed
      failure_layer: no_failure
      error_type: null
      no_data_not_risk_exclusion: false
    weapon_inventory:
      source_status: completed
      failure_layer: no_failure
      error_type: null
      no_data_not_risk_exclusion: false
    login_logs_search:
      source_status: no_data
      failure_layer: source_observation
      error_type: null
      no_data_not_risk_exclusion: true
```

## Expected Partial Evidence Card

```yaml
partial_evidence_card:
  card_type: partial_evidence_card
  sensitive_output: false
  completed_sources:
    - track_analysis_summary
    - rcp_snapshot
    - weapon_inventory
  no_data_sources:
    - login_logs_search
  blocked_sources: []
  no_data_not_risk_exclusion: true
  evidence_sections:
    - source_name: track_analysis_summary
      source_status: completed
      source_card_present: true
      source_quality_present: true
    - source_name: rcp_snapshot
      source_status: completed
      source_card_present: true
      source_quality_present: true
    - source_name: weapon_inventory
      source_status: completed
      source_card_present: true
      source_quality_present: true
    - source_name: login_logs_search
      source_status: no_data
      source_card_present: true
      source_quality_present: true
      no_data_not_risk_exclusion: true
```

## Boundary Assertions

- `no_data` is missing online-window evidence, not no-risk counterevidence.
- `blocked`, `network_error`, `platform_error`, `auth_failed`, and `timeout` are source quality, not Dennis runtime crashes.
- The adapter does not trigger browser debug or SSO debug.
- The adapter does not read browser profile files, `.ks_sso`, cookie DBs, or credential material.
- The adapter does not output source response summary full bodies, raw login records, raw device identifiers, raw IPs, raw labelInfo, or raw originalLog.

## Evidence Display Layer Enhancement

This patch improves `build_partial_evidence_card()` so the evidence card is readable by strategy users, not only a technical source-card existence check.

Added display-safe source summaries:

- Track Analysis:
  - `profile_summary`: `register_time_present`, `fan_distribution_present`, `active_days_bucket_present`, `device_ids_count`
  - `use_duration_summary`: `rows_count`, `nonzero_days_count`, `total_duration`, `peak_date`
  - `device_ids_summary`: `device_ids_count`, `device_model_fields_present`, `last_active_fields_present`
- RCP:
  - `event_count`, `table_header_columns`, `returned_columns_observed`, `first_event_shape_keys`, `dynamic_columns_observed`
  - chaining-key presence for `hitFusePolicyCode`, `eventId`, `_occurTime`
  - boundary: RCP is not final risk judgement
- Weapon:
  - `graph_status`, `related_device_count`, `related_user_count`
  - `riskData_status`, `risk_label_count`, `risk_group_names_observed`, `readable_label_sample`, `userLevel_observed`
  - raw `deviceId`, `labelInfo`, and `originalLog` remain suppressed
- Login Logs:
  - `records_count`, `time_window_observed`, `first_login_time_observed`, `last_login_time_observed`
  - `no_data_not_risk_exclusion=true`

The enhanced evidence card now includes:

- `source_completion_matrix`
- `source_quality`
- `evidence_summary_by_source`
- `evidence_boundary`
- `missing_evidence`
- `next_action`

Validation:

- `python3 -m py_compile computer_use_poc/browser_backed_service_client.py`: passed.
- `python3 computer_use_poc/browser_backed_service_client.py --self-test`: passed, 15 fixture tests.
- New fixture coverage:
  - completed four-source fixture generates business summaries
  - login logs `no_data` enters missing evidence / caveat
  - Weapon raw `labelInfo` is not emitted
  - RCP event list is not final judgement
  - `sensitive_output=true` remains rejected

This patch did not access the live platform, did not start browser-backed service, did not read Chrome profile / cookie / token / session / header / `.ks_sso`, did not call DataAgent/Hive, did not package, and did not commit git.
