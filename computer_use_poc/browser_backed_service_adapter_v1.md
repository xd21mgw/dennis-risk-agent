# Browser-Backed Service Adapter v1

This adapter lets Dennis consume the local browser-backed API service without opening a browser or handling platform auth material inside `dennis-risk-agent`.

## Scope

- Service base URL: `http://127.0.0.1:8787`.
- Dennis calls only fixed service actions.
- The browser-backed service owns persistent browser context, origin readiness, same-origin checks, and source extraction.
- Dennis receives normalized source results and writes them into the source completion matrix.
- Action failures are source quality, not Dennis runtime failures, when the service returns the standard result contract.

## Fixed Action Mapping

| Dennis source need | Browser-backed action | Endpoint |
| --- | --- | --- |
| RCP strategy hit entry | `rcp_snapshot` | `POST /actions/rcp_snapshot` |
| Weapon device relation / risk | `weapon_inventory` | `POST /actions/weapon_inventory` |
| Login log online source | `login_logs_search` | `POST /actions/login_logs_search` |
| Track-analysis activity / profile | `track_analysis_summary` | `POST /actions/track_analysis_summary` |

For clean `full_runtime` single-user account-security evidence cards, these fixed actions are the primary source path. Dennis must not first try missing legacy runners such as `bin/sso_session_runner` or `bin/track_analysis_runner`. Archives Center remains a separate optional source; if `archives_profile_runner` is still a stub, it is recorded as `source_gap` and does not block the browser-backed chain.

## Account-Security Bundle Typed Params

Default single-user account-security orchestration uses these typed params. The adapter must reject caller-provided URL, path, header, cookie, token, session, or secret fields before invocation.

```yaml
account_security_browser_backed_sequence:
  - source_name: track_analysis_account_security_bundle
    action_name: track_analysis_summary
    typed_params:
      user_id: "{user_id}"
      appName: KUAISHOU
      mode: account_security_bundle
      sub_interfaces:
        - profile
        - getUseDuration
        - getDeviceIds
        - getLastestDateTime
    boundary:
      - 只传 user_id/appName 不满足账号安全 bundle
      - profile / getUseDuration / getDeviceIds / getLastestDateTime 的完成、no_data、blocked、parse_error 必须分层进入 source_completion_matrix
  - source_name: rcp_strategy_hit_entry
    action_name: rcp_snapshot
    typed_params:
      entity_type: user_id
      entity_id: "{user_id}"
      mode: account_security_strategy_event_entry
    boundary:
      - 默认进入单用户账号安全 source_completion_matrix
      - 策略事件入口是风险线索，不是最终风险定性
  - source_name: weapon_user_to_device_graph
    action_name: weapon_inventory
    typed_params:
      user_id: "{user_id}"
      mode: account_security_user_device_graph_with_conditional_riskData
      riskData_trigger_device_prefix:
        - ANDROID_
        - IOS_
    boundary:
      - riskData 仅在 graphData 保留 raw ANDROID_/IOS_ device_id safe handle 后执行
      - raw device_id 缺失时标 missing_required_fields/not_checked，不伪装 completed
      - riskData 的标签摘要进入 evidence card，raw labelInfo / originalLog 不输出
  - source_name: user_login_unified_log
    action_name: login_logs_search
    typed_params:
      user_id: "{user_id}"
      window: last_7d
      recallSource: "2,0,1,3"
    fallback_on:
      parse_error:
        source_name: user_login_unified_log_24h_fallback
        action_name: login_logs_search
        typed_params:
          user_id: "{user_id}"
          window: last_24h
          recallSource: "2,0,1,3"
        preserve_primary_source_quality: true
        fallback_result_must_be_standard_browser_backed_source_result: true
    boundary:
      - parse_error / no_data / auth_failed / blocked 都是 source_quality
      - 不能把失败或空结果解释为无风险反证
```

All four browser-backed sources must be represented in `source_completion_matrix` by default. A 7-day `login_logs_search` `parse_error` may trigger the 24-hour fallback, but both the 7-day primary result and 24-hour fallback must be normalized as standard browser-backed source results with `source_card`, `source_quality`, `latency_ms`, and `sensitive_output=false`. `no_data`, `parse_error`, and `source_gap` are not no-risk counter-evidence.

For `track_analysis_account_security_bundle`, a single `sub_interfaces` list is only the source plan shape. The executable helper expands it into four `track_analysis_summary` calls with `sub_interface=profile|getUseDuration|getDeviceIds|getLastestDateTime`, then merges those standard action results into one Track Analysis source card. If the service returns a different observed sub-interface than requested, that requested sub-interface stays missing in `source_quality` instead of being treated as completed.

`archives_profile_readonly` is not part of the default browser-backed four-source main chain while `archives_profile_runner` remains a stub. It may be represented only as `missing_evidence.optional_source_gap` / `source_quality.missing_sources`, and it must not block Track Analysis, RCP, Weapon, or Login Logs.

## Adapter Boundary

Dennis must not:

- Start or debug a browser.
- Read `.ks_sso`, browser profile files, credential stores, or cookie DBs.
- Read, build, log, or forward cookie, token, session, authorization, or custom header material.
- Debug `sso_session_runner`, `SmartSSOSession`, auth bridge internals, gateway, or safeBins.
- Accept caller-provided `url`, `path`, `header`, `cookie`, `token`, `session`, or `secret` fields for this adapter.
- Expand the action allowlist from Dennis runtime.
- Treat `blocked`, `auth_failed`, `network_error`, or `platform_error` as a runtime crash when a standard source result is returned.

## Input Contract

The adapter passes only the minimal business identifiers required by the fixed action contract. If a required identifier is unavailable, Dennis records a source result with `source_status=invalid_parameter` or `source_status=missing_upstream_id` and does not guess values.

Forbidden input keys are rejected before service invocation:

```yaml
forbidden_input_keys:
  - url
  - path
  - header
  - cookie
  - token
  - session
  - secret
```

## Normalized Output

Every service action result entering Dennis should normalize to:

```yaml
browser_backed_source_result:
  source_name:
  action_name:
  source_status:
  failure_layer:
  error_type:
  latency_ms:
  source_card:
  source_quality:
  sensitive_output: false
  source_provenance: browser_backed_service
```

Required service fields:

- `source_card`
- `source_quality`
- `source_status` or `status`
- `error_type`
- `latency_ms`
- `sensitive_output=false`

Dennis must not persist or display a raw response full body from the browser-backed service.

## Status Normalization

| Service status / error | Dennis source_status | failure_layer | Handling |
| --- | --- | --- | --- |
| `ok` / `completed` | `completed` | `no_failure` | Enter completed source evidence. |
| `blocked` | `blocked` | `same_origin_context` or `path_permission` | Enter source completion matrix with source quality. |
| `auth_failed` | `auth_failed` | `auth_session` | Enter source completion matrix; do not start auth debug. |
| `network_error` | `blocked` | `network` | Enter source completion matrix; do not retry through browser debug. |
| `platform_error` | `platform_partial_available` | `platform_contract` | Enter source completion matrix as platform/source quality. |
| `parameter_error` | `invalid_parameter` | `parameter_contract` | Record missing or invalid action input. |
| `parse_error` | `parse_error` | `parser` | Record parser/source shape issue. |
| `timeout` | `timeout` | `timeout` | Record timeout source quality. |

If the HTTP transport to `127.0.0.1:8787` itself is unavailable, the adapter records `source_status=tool_gap` with `failure_layer=runner_invocation` and continues partial evidence.

## Partial Evidence Card Rule

Browser-backed action failures still produce a partial evidence card when any source result is standard:

```yaml
partial_evidence_card:
  source_name: login_logs_search
  source_status: auth_failed
  source_quality:
    permission_status: auth_not_ready
    freshness_status: current_task_observation
    error_type: auth_redirect
  evidence_value: missing_evidence
  next_action: "Retry after browser-backed service origin readiness is restored."
```

`blocked`, `auth_failed`, `network_error`, and `platform_error` must never be rewritten as low risk, no risk, or source absence.

## Executable Adapter

Implementation: `computer_use_poc/browser_backed_service_client.py`.

The executable client is intentionally narrow:

- Default `base_url`: `http://127.0.0.1:8787`.
- Default timeout: `10s`.
- Fixed action allowlist only:
  - `track_analysis_summary`
  - `rcp_snapshot`
  - `weapon_inventory`
  - `login_logs_search`
- Only typed params are serialized into the JSON body.
- Caller-provided route, credential, or transport override fields are rejected before service invocation.
- HTTP transport errors, connection refused, timeout, HTTP error, and non-JSON responses are normalized as source results instead of Dennis runtime failures.
- `BrowserBackedServiceClient.call_account_security_sources()` is the executable single-user account-security helper. It expands Track Analysis sub-interfaces, preserves Weapon private safe handles when the service returns them, applies login-log parse fallback, and returns display-safe source results for evidence-card construction.

Fixture self-test:

```bash
python3 computer_use_poc/browser_backed_service_client.py --self-test
```

The self-test does not require the browser-backed service to be running and does not call any live platform.

## Executable Normalization

The client reads these service fields when present:

- `source_status`
- `error_type`
- `latency_ms`
- `source_card`
- `source_quality`
- `sensitive_output`
- `status`

Normalization buckets:

| Normalized Dennis bucket | Accepted service statuses / errors |
| --- | --- |
| `completed_sources` | `completed`, `ok` |
| `no_data_sources` | `no_data`, `completed_no_data`, `completed_no_hit_for_small_window` |
| `auth_failed_sources` | `auth_failed`, `auth_redirect` |
| `blocked_sources` | `blocked`, `network_error`, `platform_error`, connection refused, service HTTP error |
| `timeout_sources` | `timeout`, service timeout |
| `parse_error_sources` | `parse_error`, non-JSON service response |
| `invalid_parameter_sources` | `parameter_error`, `invalid_parameter`, `wrong_request_body_shape` |

`sensitive_output` must be exactly `false`. If the service returns any other value, the adapter replaces the result with `source_status=blocked`, `error_type=sensitive_output_violation`, and `sensitive_output=false`.

## Partial Evidence Construction

`build_source_completion_matrix()` and `build_partial_evidence_card()` produce display-safe structures for Dennis runtime:

```yaml
partial_evidence_card:
  sensitive_output: false
  completed_sources: []
  no_data_sources: []
  blocked_sources: []
  source_quality: {}
  no_data_not_risk_exclusion: true
```

The adapter does not persist raw response full bodies, raw login records, raw device identifiers, raw IPs, raw labelInfo, or raw originalLog. It relies on `source_card`, `source_quality`, and service-provided shape summaries that are already sanitized by the browser-backed service.

## Evidence Display Summary

`build_partial_evidence_card()` now extracts display-safe business summaries from `source_card` / `source_quality` instead of only reporting whether those objects exist.

Source-specific summary fields:

- `track_analysis_summary`
  - `bundle_summary.mode`
  - `bundle_summary.sub_interfaces`
  - `bundle_summary.sub_interfaces_completed`
  - `bundle_summary.sub_interfaces_missing`
  - `latest_timestamp_summary.latest_datetime_present`
  - `latest_timestamp_summary.uid_did_relation_latest_datetime_present`
  - `profile_summary.register_time_present`
  - `profile_summary.fan_distribution_present`
  - `profile_summary.active_days_bucket_present`
  - `profile_summary.device_ids_count`
  - `use_duration_summary.rows_count`
  - `use_duration_summary.nonzero_days_count`
  - `use_duration_summary.total_duration`
  - `use_duration_summary.peak_date`
  - `device_ids_summary.device_ids_count`
  - `device_ids_summary.device_model_fields_present`
  - `device_ids_summary.last_active_fields_present`
- `rcp_snapshot`
  - `event_summary.event_count`
  - `event_summary.table_header_columns`
  - `event_summary.returned_columns_observed`
  - `event_summary.first_event_shape_keys`
  - `event_summary.dynamic_columns_observed`
  - `chaining_keys_present.hitFusePolicyCode`
  - `chaining_keys_present.eventId`
  - `chaining_keys_present._occurTime`
  - Boundary: RCP is a strategy event entry source, not final risk judgement.
- `weapon_inventory`
  - `graph_summary.graph_status`
  - `graph_summary.related_device_count`
  - `graph_summary.related_user_count`
  - `risk_summary.riskData_status`
  - `risk_summary.risk_label_count`
  - `risk_summary.risk_group_names_observed`
  - `risk_summary.readable_label_sample`
  - `risk_summary.userLevel_observed`
  - `chaining_summary.raw_device_safe_handle_retained`
  - `chaining_summary.riskData_chaining_uses_safe_handle_only`
- `login_logs_search`
  - `login_window_summary.source_status`
  - `login_window_summary.records_count`
  - `login_window_summary.time_window_observed`
  - `login_window_summary.first_login_time_observed`
  - `login_window_summary.last_login_time_observed`
  - `login_window_summary.standard_browser_backed_source_result`
  - Boundary: `no_data` means no visible rows in the observed window, not no-risk evidence.

The display layer keeps:

```yaml
sensitive_output: false
no_data_not_risk_exclusion: true
final_risk_judgement_made: false
```

The display layer must not emit raw profile body, raw deviceId, raw IP, raw login records, raw labelInfo, or raw originalLog.
