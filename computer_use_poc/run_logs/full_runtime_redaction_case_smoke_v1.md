# Full Runtime Redaction Case Smoke v1

Date: 2026-05-29

Scope: record the completed `outputs/full_runtime` redaction case smoke result for
`internal_risk_review`. This is a post-run summary only. No smoke was rerun while
writing this file, and no platform source, Chrome profile, cookie, token,
session, header, `.ks_sso`, SSO runner, SmartSSOSession, DataAgent, or Hive was
accessed while writing this file.

## Runtime

```yaml
runtime_dir: outputs/full_runtime
service: http://127.0.0.1:8787
case:
  user_id: "2871834924"
  case_type: single_user_account_security_evidence_card
  output_scope: internal_risk_review
  final_risk_judgement_made: false
```

## Fixed Actions

Only the four browser-backed fixed actions were used by the smoke:

```yaml
fixed_actions:
  track_analysis_summary:
    planned_calls: 4
    reason: account_security_bundle expands profile/getUseDuration/getDeviceIds/getLastestDateTime
  rcp_snapshot:
    planned_calls: 1
  weapon_inventory:
    planned_calls: 1
  login_logs_search:
    planned_calls: 1
disallowed_paths_not_used:
  direct_platform_access: false
  chrome_profile_or_cookie_read: false
  sso_session_runner_or_smart_sso: false
  dataagent_hive: false
  archives_profile_runner_stub_default_chain: false
```

## Source Completion

```yaml
source_completion_matrix:
  completed_sources:
    - track_analysis_summary
    - rcp_snapshot
    - weapon_inventory
    - login_logs_search
  no_data_sources: []
  blocked_sources: []
  auth_failed_sources: []
  timeout_sources: []
  parse_error_sources: []
```

```yaml
source_status_by_action:
  track_analysis_summary: completed
  rcp_snapshot: completed
  weapon_inventory: completed
  login_logs_search: completed
```

## Evidence Summary

```yaml
evidence_summary_by_source:
  track_analysis_summary:
    source_status: completed
    sub_interfaces_completed:
      - profile
      - getUseDuration
      - getDeviceIds
      - getLastestDateTime
    device_ids_count: 9
    device_id_sample_displayed: true
    raw_body_suppressed: true
    raw_records_full_dump_suppressed: true
  rcp_snapshot:
    source_status: completed
    event_count: 200
    first_event_entity_samples_present:
      sourceId: true
      eventId: true
      deviceId: true
      _occurTime: true
      hitFusePolicyCode: true
    raw_body_suppressed: true
    raw_records_full_dump_suppressed: true
  weapon_inventory:
    source_status: completed
    graph_status: completed
    related_user_count: 1
    related_user_id_sample_displayed: true
    risk_label_count: 0
    raw_labelInfo_originalLog_suppressed: true
  login_logs_search:
    source_status: completed
    records_count: 19
    user_id_sample_displayed: true
    device_id_sample_displayed: true
    method_sample_displayed: true
    logSource_sample_displayed: true
    timestamp_fields_displayed: true
    raw_login_records_suppressed: true
```

## Display Field Check

`internal_risk_review` allowed the display layer to show minimum necessary risk
entity identifiers for risk analysis:

```yaml
internal_risk_entity_fields_displayed:
  user_id: true
  device_id: true
  eventId: true
  sourceId: true
  method: true
  logSource: true
  timestamp: true
  ip: false
ip_not_present_in_this_case: true
```

## Redaction And Safety Check

```yaml
credential_secret_not_output: true
raw_body_not_output: true
raw_login_records_not_output: true
raw_labelInfo_originalLog_not_output: true
sensitive_output: false
final_risk_judgement_made: false
redaction_case_smoke_pass: true
```

## Boundary

- The run produced evidence observation only, not a final risk judgement.
- `internal_risk_review` may display risk entity identifiers such as `user_id`,
  `device_id`, `eventId`, `sourceId`, method, `logSource`, and timestamp when
  they are needed for internal risk analysis.
- Credential secrets and raw source dumps remain forbidden in all output scopes.
- IP was not present in this case output, so no IP display behavior was validated
  by this smoke.
