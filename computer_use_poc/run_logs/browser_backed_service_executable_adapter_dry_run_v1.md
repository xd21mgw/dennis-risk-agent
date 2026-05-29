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
- The adapter does not output raw response full bodies, raw login records, raw device identifiers, raw IPs, raw labelInfo, or raw originalLog.
