# Browser-Backed Service Adapter Dry-Run v1

Date: 2026-05-29

Scope: offline contract validation only. This dry-run does not start browser-backed-api-poc, does not access real platforms, does not call DataAgent/Hive, and does not read browser profile or auth material.

## Simulated Service Results

| action_name | source_status | error_type | required fields |
| --- | --- | --- | --- |
| `rcp_snapshot` | `blocked` | `platform_error` | `source_card`, `source_quality`, `latency_ms`, `sensitive_output=false` |
| `weapon_inventory` | `blocked` | `network_error` | `source_card`, `source_quality`, `latency_ms`, `sensitive_output=false` |
| `login_logs_search` | `auth_failed` | `auth_redirect` | `source_card`, `source_quality`, `latency_ms`, `sensitive_output=false` |
| `track_analysis_summary` | `completed` | `null` | `source_card`, `source_quality`, `latency_ms`, `sensitive_output=false` |

## Expected Source Completion Matrix

```yaml
source_completion_matrix:
  - source_name: rcp_strategy_hit_entry
    action_name: rcp_snapshot
    source_status: blocked
    failure_layer: platform_contract
    error_type: platform_error
    source_card: present
    source_quality: present
    sensitive_output: false
    runtime_failure: false
  - source_name: weapon_device_relation_or_risk
    action_name: weapon_inventory
    source_status: blocked
    failure_layer: network
    error_type: network_error
    source_card: present
    source_quality: present
    sensitive_output: false
    runtime_failure: false
  - source_name: login_log_online_source
    action_name: login_logs_search
    source_status: auth_failed
    failure_layer: auth_session
    error_type: auth_redirect
    source_card: present
    source_quality: present
    sensitive_output: false
    runtime_failure: false
  - source_name: track_analysis_activity_or_profile
    action_name: track_analysis_summary
    source_status: completed
    failure_layer: no_failure
    error_type: null
    source_card: present
    source_quality: present
    sensitive_output: false
    runtime_failure: false
```

## Expected Partial Evidence Card

```yaml
partial_evidence_card:
  evidence_state: partial
  completed_sources:
    - track_analysis_activity_or_profile
  blocked_or_failed_sources:
    - rcp_strategy_hit_entry
    - weapon_device_relation_or_risk
    - login_log_online_source
  source_quality_required: true
  no_risk_counterevidence_from_source_failure: false
  browser_debug_triggered: false
  sso_runner_triggered: false
  credential_material_accessed: false
```

## Pass Criteria

- `blocked`, `auth_failed`, `network_error`, and `platform_error` are source quality states, not Dennis runtime failures.
- The matrix retains all four source results and preserves `source_card`, `source_quality`, `latency_ms`, and `sensitive_output=false`.
- Partial evidence card is emitted because at least one source is completed and the failed sources are standard source results.
- `no_data`, `auth_failed`, `blocked`, and `timeout` are never treated as no-risk counterevidence.
- No browser debug, no `.ks_sso` read, no `sso_session_runner` call, and no cookie/token/session/header read or output.
