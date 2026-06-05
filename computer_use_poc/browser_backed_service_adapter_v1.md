# Browser-Backed Service Adapter v1

This adapter lets Dennis consume the local browser-backed API service without opening a browser or handling platform auth material inside `dennis-risk-agent`.

## Scope

- Service base URL: `http://127.0.0.1:8787`.
- Dennis calls only fixed service actions.
- The browser-backed service owns persistent browser context, origin readiness, same-origin checks, typed params, safe passthrough, transport status, and controlled parallel batch execution.
- The service no longer returns business normalization fields such as `normalized_observation`, `source_quality`, `source_card`, `evidence_card_inputs`, `compat_summary`, `risk_event_scan`, or `feature_group_summary`.
- Dennis consumes the pure passthrough envelope, transport metadata, capped body presence/truncation signals, and batch transport matrices.
- Dennis generates observation, `source_quality_matrix`, evidence cards, missing evidence, and final answer boundaries locally.
- Dennis may apply evidence projection before local observation when capped/body JSON is visible: drop obvious UI/debug/blob/repeated/empty low-value fields, preserve risk anchors, and convert credential-control-chain fields to safe presence/path/hash handles. This is not a service normalizer and raw credential values remain forbidden in final answers.
- Action failures are source quality inputs, not Dennis runtime failures, when the service returns a passthrough envelope or transport status.

## Pure Passthrough Envelope Contract

Service action output is a safe transport envelope. Dennis must not require service-side observation builders or evidence summaries.

Required single-source envelope fields:

```yaml
passthrough_envelope:
  action_name:
  source_id:
  platform:
  http_status:
  content_type:
  body_present:
  body_truncated:
  observed_bytes:
  elapsed_ms:
  transport_error:
  platform_error:
  invalid_params:
  timeout:
  auth_redirect_detected:
  raw_body_handling: suppressed | capped | metadata_only
```

Optional upstream metadata that Dennis may inspect when present:

```yaml
upstream_metadata:
  api_code:
  result_count:
  result_array_length:
  pagination_applied:
  field_projection_applied:
  body_excerpt_available:
```

Required batch envelope fields:

```yaml
batch_passthrough_envelope:
  batch_status:
  source_results: []
  transport_status_matrix:
    completed: []
    no_data: []
    partial: []
    auth_failed: []
    blocked: []
    timeout: []
    parse_error: []
  missing_or_failed_sources: []
```

Dennis-generated fields:

```yaml
dennis_generated_from_passthrough:
  observation:
  source_quality_matrix:
  evidence_card:
  missing_evidence:
  final_answer_boundary:
```

Mapping rules:

- `body_truncated=true` -> `partial_observation_available`; do not claim complete detail coverage.
- `http_status` 2xx + `body_present=true` + `body_truncated=true` -> transport success with partial observation / response-too-large boundary, not `network_error`, `auth_failed`, or permission denial.
- `auth_redirect_detected=true` or `api_code=302` -> `auth_flow_not_completed_in_bound_context`; do not say the user has no permission unless a permission denial is explicit.
- `body_present=false` with empty result semantics -> `no_data` source quality; never low-risk/no-risk counter evidence.
- `timeout=true`, `platform_error`, transport error, invalid params, or parse failure -> missing evidence and partial answer where other sources are usable.
- `raw_body_handling=suppressed|capped` -> raw body is intentionally withheld, not `body_missing`; only limited observation is allowed, but Dennis may retain safe field handles such as device, time, source, and field path.
- Dennis may use model understanding over capped passthrough bodies for high-value sources, but full standard observation builders remain incremental Dennis-owned work, not service responsibility.

## Fixed Action Mapping

| Dennis source need | Browser-backed action | Endpoint |
| --- | --- | --- |
| RCP strategy hit entry | `rcp_snapshot` | `POST /actions/rcp_snapshot` |
| Weapon device relation / risk | `weapon_inventory` | `POST /actions/weapon_inventory` |
| Login log online source | `login_logs_search` | `POST /actions/login_logs_search` |
| Track-analysis activity / profile (legacy alias, not current default case execution) | `track_analysis_summary` | `POST /actions/track_analysis_summary` |
| Track-analysis data readiness precheck | `track_analysis_check_data_ready` | `POST /actions/track_analysis_check_data_ready` |
| Archives Center user-analysis core logs | `archives_user_analysis` | `POST /actions/archives_user_analysis` |
| Archives Center photo report search | `archives_photo_search` | `POST /actions/archives_photo_search` |
| Archives Center user profile baseline | `archives_user_profile` | `POST /actions/archives_user_profile` |
| Archives Center same-device related users | `archives_related_users` | `POST /actions/archives_related_users` |
| Archives Center photo profile detail | `archives_photo_profile` | `POST /actions/archives_photo_profile` |
| Archives Center photo meta detail | `archives_photo_meta` | `POST /actions/archives_photo_meta` |
| Archives Center photo report aggregate | `archives_photo_report_aggregate` | `POST /actions/archives_photo_report_aggregate` |
| Archives Center photo autonomy/action context | `archives_photo_user_autonomy` | `POST /actions/archives_photo_user_autonomy` |
| Archives Center gallery photo list | `archives_gallery_photo_list` | `POST /actions/archives_gallery_photo_list` |
| Archives Center private-message summary | `archives_private_message_search` | `POST /actions/archives_private_message_search` |
| Archives Center four-info change log | `archives_past_four_items` | `POST /actions/archives_past_four_items` |
| RCP event detail | `rcp_event_detail` | `POST /actions/rcp_event_detail` |
| RCP event feature snapshot | `rcp_event_feature_list` | `POST /actions/rcp_event_feature_list` |
| RCP policy version context | `rcp_policy_version_lookup` | `POST /actions/rcp_policy_version_lookup` |
| RCP policy detail context | `rcp_policy_detail_lookup` | `POST /actions/rcp_policy_detail_lookup` |
| RCP policy release record context | `rcp_policy_release_record_lookup` | `POST /actions/rcp_policy_release_record_lookup` |
| RCP policy tree node lookup | `rcp_policy_tree_lookup` | `POST /actions/rcp_policy_tree_lookup` |
| RCP condition-level policy attribution | `rcp_node_policy_attribution` | `POST /actions/rcp_node_policy_attribution` |
| RCP node-binding policy attribution | `rcp_node_bind_policy_attribution` | `POST /actions/rcp_node_bind_policy_attribution` |
| RCP event tree / decision context | `rcp_event_tree_or_decision` | `POST /actions/rcp_event_tree_or_decision` |
| RCP fast query hbase | `rcp_fast_query_hbase` | `POST /actions/rcp_fast_query_hbase` |
| RCP feature info by keys | `rcp_feature_info_by_keys` | `POST /actions/rcp_feature_info_by_keys` |
| RCP policy basic info | `rcp_policy_basic_info` | `POST /actions/rcp_policy_basic_info` |
| RCP relation policy tree | `rcp_relation_policy_tree` | `POST /actions/rcp_relation_policy_tree` |
| RCP policy binding list | `rcp_policy_binding_info_list` | `POST /actions/rcp_policy_binding_info_list` |
| RCP policy search | `rcp_policy_search` / `rcp_policy_blur_search` | `POST /actions/rcp_policy_search`, `POST /actions/rcp_policy_blur_search` |
| RCP policy versions | `rcp_policy_all_version` / `rcp_pipeline_policy_versions_by_code` | `POST /actions/rcp_policy_all_version`, `POST /actions/rcp_pipeline_policy_versions_by_code` |
| Track auxiliary discovery | `track_analysis_product_list`, `track_sequence_dimension_list`, `track_data_type_list` | `POST /actions/<name>` |

For clean `full_runtime` single-user ATO/account-security execution, the primary path is `runtime_case_execution_runner.py` building an explicit controlled batch payload. The default ATO realtime P0 sources are `login_logs_search`, `archives_user_profile`, `track_analysis_check_data_ready`, `archives_photo_search`, and dependent `archives_user_analysis`; suspicious anchors are derived from those observations, not requested as a standalone source. Weapon and RCP/Tianshi are conditional follow-ups when device or event identifiers exist. Dennis requests passthrough envelopes and then creates Dennis-owned observations, source quality, evidence summaries, and missing-evidence rows. Dennis must not try legacy runners such as `bin/sso_session_runner`, `bin/track_analysis_runner`, or `bin/archives_profile_runner` after browser-backed source gaps. These additions do not change `default_runtime_routing=false`.

`archives_user_analysis`, `archives_photo_search`, `archives_user_profile`, and `archives_related_users` are the Archives Center sources in the v1 routing-closure batch. The current service contract also exposes photo detail actions: `archives_photo_profile`, `archives_photo_meta`, `archives_photo_report_aggregate`, `archives_photo_user_autonomy`, and `archives_gallery_photo_list`. Dennis must not default-call all of them. If ATO / abnormal publish already has `photo_id` and the publish fact chain lacks `publish_source`, `publish_device`, `publish_ip_ua`, `uploadSource`, or `photoMethod`, Dennis plans `archives_photo_profile + archives_photo_meta` as auth-sensitive next-hop and consumes their passthrough body into the publish/device evidence chain. If `photo_id` is missing, Dennis plans `archives_gallery_photo_list` / `archives_photo_search` for photo anchor discovery first. `auth_failed`, `no_data`, `partial_observation_available`, `timeout`, `blocked`, `service_body_visibility_gap`, and `parser_mapping_gap` enter source quality and missing evidence, then Dennis returns partial evidence. `archives_photo_search no_data` is not a risk exclusion; `archives_related_users` is an account-spread clue, not a gang conclusion. Private-message, past-four-items / profile-change, and related-device style sources remain conditional follow-up only; do not describe them as default verified sources unless a stable interface or explicit user-provided clue is present.

`rcp_event_detail`, `rcp_event_feature_list`, `rcp_policy_version_lookup`, `rcp_policy_detail_lookup`, `rcp_policy_release_record_lookup`, `rcp_policy_tree_lookup`, `rcp_node_policy_attribution`, and `rcp_node_bind_policy_attribution` are explicit RCP/Tianshi drill-down sources. They require upstream event, policy, or policy-tree identifiers; they are not part of the default four-source account-security main chain. `rcp_event_detail -> rcp_event_feature_list` is the v1 event-attribution chain. `rcp_policy_tree_lookup` is strategy asset governance only and must not be used as a single-case event-hit path.

The HAR inventory also tracks auxiliary actions that are intentionally not in the default ATO realtime P0 runtime chain:

- `track_analysis_check_data_ready`: live-smoke verified readiness/provenance helper; fixed by HAR to `POST /dp/platform/app/analytics/v2/sequence/checkDataReady`; it is default ATO P0 auxiliary for front/backend activity alignment but not account-security evidence by itself.
- `track_analysis_product_list` / `track_sequence_dimension_list` / `track_data_type_list`: Track parameter / dimension / data-type discovery only; not risk evidence and not default conclusion chain.
- `rcp_event_tree_or_decision` / `rcp_fast_query_hbase` / `rcp_feature_info_by_keys` / `rcp_policy_basic_info` / `rcp_relation_policy_tree` / `rcp_policy_binding_info_list` / `rcp_policy_search` / `rcp_policy_blur_search` / `rcp_policy_all_version` / `rcp_pipeline_policy_versions_by_code`: registered strategy governance / event attribution helpers. They require explicit event/policy/feature context and must not be inserted into ordinary ATO judgement unless the user asks strategy hit, policy attribution, false-positive review, or strategy governance.
- `login_log_detail_lookup`: UI modal key extraction has validation evidence, but no fixed API path/body or row identifier contract has been confirmed.
- `login_log_filter_options`: blocked until a safe HAR confirms a separate filter/config option path and response shape; current default remains `recallSource=2,0,1,3`.
- `login_logs_search_page`: not a standalone action for the current `/rest/unified/log/search` contract because validated API responses can return the full current-window result and UI pagination is frontend-only.

Current `browser-backed-api-poc` parity note: the adjacent service action registry now reports `action_count=70` in `ACTION_REGISTRY.md` and `src/actions.js`, including Archives profile / analysis / photo / live / fans / follow / collect / comment / private message / report / four-items interfaces, login log `json_array_capped`, RCP event / feature / policy / policy-tree / attribution helpers, and Track sequence device / duration / profile / readiness / parameter discovery interfaces. Registration parity does not imply default routing: every interface still requires an explicit source plan, dependency anchor, cap, and stop reason; no caller-provided URL/path/header/cookie/token/session input is accepted. Dennis maps these service actions as business interfaces through `interface_orchestration_contract_v1.md` and `browser_backed_interface_asset_table_v1.yaml`, not as 70 default call nodes.

## Controlled Parallel Batch Contract

The browser-backed service exposes controlled batch entrypoints:

- `POST /actions/multi_source_plan`: plan/contract shape for explicit multi-source orchestration.
- `POST /actions/batch`: execution entry for a caller-provided explicit source plan.

Dennis must not add browser-backed actions through this adapter. Batch mode only combines already registered fixed actions and preserves `default_runtime_routing=false`.

Each source plan item must carry:

```yaml
source_id:
action:
execution_group: independent_parallel | dependency_serial | large_response_serial | auth_sensitive_serial
depends_on: []
dependency:
timeout_class: short_readiness | standard_readonly | auth_sensitive | large_response
failure_policy: non_blocking_partial | dependent_only_block
source_priority:
expected_observation:
```

Execution group mapping:

- `independent_parallel`: `login_logs_search`, `archives_user_profile`, and `track_analysis_check_data_ready` in ATO/login-anomaly plans when no upstream entity is required.
- `dependency_serial`: `rcp_event_detail -> rcp_event_feature_list`, and `archives_related_users -> profile/login/track` follow-up validation.
- `large_response_serial`: `rcp_event_feature_list` or `archives_user_analysis` when page size, feature scope, or partial response pressure is large.
- `auth_sensitive_serial`: Archives same-origin chains such as `archives_photo_search -> archives_user_profile -> archives_user_analysis`.

Batch service results align to Dennis-owned merging:

```yaml
batch_result:
source_results: []
transport_status_matrix: {}   # keyed by source_id in current service; Dennis also accepts list form
classifications:
  completed: []
  no_data: []
  partial: []
  auth_failed: []
  blocked: []
  timeout: []
  parse_error: []
  planned: []
missing_or_failed_sources: []
raw_upstream_body_user_visible: false
final_risk_conclusion_generated_by_service: false
```

Dennis converts `transport_status_matrix` and `source_results` into `source_quality_matrix`, evidence card inputs, and missing evidence. `completed` and usable `partial` sources can enter Dennis evidence cards. `no_data`, `auth_failed`, `blocked`, `timeout`, `parse_error`, missing upstream IDs, and dependent skips enter Dennis `source_quality_matrix` and `missing_evidence`; they do not block partial answers and cannot be used as low-risk counter-evidence.

`runtime_case_execution_runner.py` is the only live case execution caller for this contract. If the harness receives an HTTP/service/parse error from `/actions/batch`, it returns structured `harness_error` and source gaps; Codex must not manually reconstruct the payload with `curl /actions/batch` outside the harness.

## ATO Realtime P0 And Login Log Contract Patch

For ATO single-case questions, Dennis must use the browser-backed fixed actions to collect realtime P0 evidence and derive suspicious anchors, not to print a flat source-status list or call a standalone suspicious-anchor source. The business chain is:

```text
user_id -> realtime P0 source collection (login/profile/analysis/photo/Track)
-> multi-source suspicious anchor derivation -> candidate_control_endpoint_extraction
-> device_identity_consistency
-> historical_baseline_comparison -> business evidence card
```

`login_logs_search` response boundary:

- `response_too_large` means the wrapper could not parse or transport the bounded result. It is not evidence that there were many logins, and it is not completed login evidence.
- If manual UI observation says no data while the wrapper returns `response_too_large`, Dennis marks `wrapper_response_mismatch`, `source_contract_gap`, `actual_ui_no_data_unverified_by_wrapper`, and `login_log_evidence_unusable`.
- Wrapper diagnostic metadata is internal-only: `request_window_start`, `request_window_end`, `recallSource`, `filter_params`, `http_status`, `response_bytes`, `totalCount`, `result_array_path`, `result_array_length`, `is_html_or_auth_page`, `is_error_envelope`, `is_large_non_result_envelope`, `pagination_applied`, and `field_projection_applied`.
- When an `anchor_time` is derived from realtime P0 sources, the next plan should shrink to `anchor_time +/- 2-6h`; without anchor time, keep source gaps explicit and do not blindly widen the login window.

The local service remains a safe passthrough + transport envelope. Dennis may use model understanding of passthrough/capped body/transport metadata for ATO, and should only standardize high-value observation builders incrementally. Do not move generic risk normalizer responsibility into the local browser-backed service.

## Legacy Field Handling

The following fields are legacy service-output dependencies and must not be required from the browser-backed service:

| legacy field | treatment |
| --- | --- |
| `normalized_observation` | Removed as service dependency. Dennis may create Dennis-owned observation from passthrough. |
| `source_quality` | Removed as service dependency. Dennis generates source quality from transport status and envelope fields. |
| `source_quality_matrix` | Removed as service dependency. Dennis merges it from `transport_status_matrix` and `source_results`. |
| `evidence_card_inputs` | Removed as service dependency. Dennis generates the evidence card directly from completed/partial observations. |
| `source_card` | Removed as service dependency. Dennis evidence output must not require service-rendered source cards. |
| `compat_summary` | Historical migration label only; not a runtime fallback and not used in pure passthrough mode. |
| `risk_event_scan` | Historical Archives DOM/API derived scan name; not a required service output. |
| `feature_group_summary` | Dennis-side limited interpretation of RCP feature passthrough; not a required service output. |

## Browser-Backed Fixed Actions v1 Closure Status

| action_name | routing status | source-quality boundary |
| --- | --- | --- |
| `login_logs_search` | `live_smoke_verified` | Online login-window no_data/window gap cannot exclude ATO. |
| `track_analysis_check_data_ready` | `live_smoke_verified` | Readiness/provenance only; not a risk conclusion. |
| `archives_user_profile` | `live_smoke_verified` | Account baseline/profile context; not final judgement. |
| `archives_user_analysis` | `live_smoke_verified` | Large page size may be `partial_observation_available` / `large_response_limited`; shrink window, page size, or paginate. |
| `archives_photo_search` | `no_data` with live path verified | `no_data_not_risk_exclusion`; does not exclude abnormal publish/content handoff. |
| `archives_related_users` | `live_smoke_verified` | Same-device relation is spread clue, not gang conclusion. |
| `rcp_event_detail` | `live_smoke_verified` | Event detail is event-level strategy evidence, not policy-tree asset lookup. |
| `rcp_event_feature_list` | `partial_observation_available` | Partial feature output supports feature-group summary only. |
| `rcp_policy_tree_lookup` | `live_smoke_verified` | Strategy asset governance only; not event-hit path and not single-case risk judgement. |

## Account-Security Bundle Typed Params

Default single-user account-security orchestration uses these typed params. The adapter must reject caller-provided URL, path, header, cookie, token, session, or secret fields before invocation.

```yaml
account_security_browser_backed_sequence:
  - source_name: track_analysis_frontend_backend_alignment
    action_name: track_analysis_check_data_ready
    typed_params:
      device_id: "{candidate_device_id_if_available}"
      appName: KUAISHOU
      mode: track_analysis_data_readiness_precheck
    boundary:
      - 缺 device_id 标 missing_required_fields / blocked，不导致 batch fail
      - readiness / no_data / blocked / parse_error 必须分层进入 source_completion_matrix
      - Track readiness 不是本人操作证明
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
        - HARMONY_
    boundary:
      - riskData 仅在 graphData 保留 raw Android/Harmony/UUID-like/long non-numeric device_id safe handle 后执行
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
        preserve_primary_transport_status: true
        fallback_result_must_be_passthrough_envelope: true
    boundary:
      - parse_error / no_data / auth_failed / blocked 都进入 Dennis-generated source_quality
      - 不能把失败或空结果解释为无风险反证
```

ATO single-case execution must be represented by the harness-generated controlled batch plan: `login_logs_search`, `archives_user_profile`, `archives_photo_search`, `track_analysis_check_data_ready`, and dependent `archives_user_analysis`. In the passthrough default path, Dennis records passthrough parser failures directly in Dennis-generated `source_quality` and `missing_evidence`; it must not silently fall back to summary mode, service-side `compat_summary`, old runners, or freeform single actions. `no_data`, `parse_error`, `body_missing`, `response_too_large`, and `source_gap` are not no-risk counter-evidence.

For ATO default execution, Track is the `track_analysis_check_data_ready` readiness/provenance source. Historical `track_analysis_account_security_bundle` helper behavior is unit-test/manual helper scope, not the default case execution path. If Track lacks `device_id` or returns no/partial data, that gap stays missing in Dennis-generated `source_quality` instead of becoming owner proof or low-risk evidence.

Legacy `archives_profile_readonly` / `archives_profile_runner` stub status must not be used to suppress the v1 Archives Center actions. In browser-backed fixed actions v1, `archives_user_profile` and `archives_user_analysis` are default ATO source-plan items; if they fail, Dennis represents the failure as local `source_quality.missing_sources` / `missing_evidence` and continues partial evidence. The legacy stub still must not block Track Analysis, RCP, Weapon, or Login Logs.

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

## Response Mode

`passthrough` is the only target main-chain mode. Dennis sends fixed typed params and receives a safe transport envelope. The service does not provide `normalized_observation`, `source_card`, `source_quality`, `evidence_card_inputs`, or `compat_summary`.

Pure passthrough service responses are expected to contain the envelope fields defined above: action/source identity, platform, HTTP/content metadata, body presence and truncation, observed byte count, elapsed time, transport/platform/parameter/timeout/auth redirect signals, and raw body handling. Batch responses additionally contain `batch_status`, `source_results`, `transport_status_matrix`, and `missing_or_failed_sources`.

Dennis must not persist or display source response summary full bodies. `output_scope` defaults to `internal_risk_review`; callers may request `external_share` when the evidence card is meant for sharing outside internal risk review.

## Dennis-Generated Output

Every passthrough service action result entering Dennis is interpreted locally:

```yaml
dennis_browser_backed_source_result:
  source_name:
  action_name:
  passthrough_envelope:
    http_status:
    content_type:
    body_present:
    body_truncated:
    observed_bytes:
    elapsed_ms:
    transport_error:
    platform_error:
    invalid_params:
    timeout:
    auth_redirect_detected:
    raw_body_handling:
  dennis_observation:
  dennis_source_quality:
  missing_evidence:
  raw_body_user_visible: false
```

Legacy service summary fields are historical only:

- `normalized_observation`: Dennis-owned output when needed, not a service dependency.
- `source_card`: historical service display artifact, not a runtime dependency.
- `source_quality`: Dennis quality classification, not a service dependency.
- `source_quality_matrix`: Dennis batch merge output, not a service dependency.
- `evidence_card_inputs`: historical service selection artifact; Dennis now generates evidence cards directly.
- `compat_summary`: historical label only, not a runtime fallback and not used by pure passthrough.
- `risk_event_scan` / `feature_group_summary`: historical derived summary names; Dennis may infer limited observations, but service need not emit them.

## Passthrough Status Interpretation

| Passthrough signal | Dennis source_status | failure_layer | Handling |
| --- | --- | --- | --- |
| usable envelope with no error/timeout/auth redirect | `completed` | `no_failure` | Enter completed source evidence after Dennis interpretation. |
| HTTP 2xx + `body_present=true` + `body_truncated=true` | `partial` | `response_size_boundary` | Treat as transport success with partial observation / response-too-large boundary. |
| `body_truncated=true` or capped body | `partial` | `response_size_boundary` | Enter partial observation and avoid complete-detail claims. |
| empty result metadata or `body_present=false` without error | `no_data` | `observed_empty_result` | Record no-data source quality; not no-risk evidence. |
| `auth_redirect_detected=true` or `api_code=302` | `auth_failed` | `auth_session` | Record auth flow not completed in bounded context; do not start auth debug. |
| `transport_error` | `blocked` | `network_or_runner` | Enter source completion matrix; do not retry through browser debug. |
| `platform_error` | `blocked` or `partial` | `platform_contract` | Enter source quality / missing evidence depending on body availability. |
| `invalid_params=true` | `invalid_parameter` | `parameter_contract` | Record missing or invalid action input. |
| Dennis parser cannot interpret capped body | `parse_error` | `parser` | Record parser/source shape issue without blocking other sources. |
| `timeout=true` | `timeout` | `timeout` | Record timeout source quality and missing evidence. |

If the HTTP transport to `127.0.0.1:8787` itself is unavailable, the adapter records `source_status=tool_gap` with `failure_layer=runner_invocation` and continues partial evidence.

## Partial Evidence Card Rule

Browser-backed action failures still produce a partial evidence card when any passthrough envelope is usable:

```yaml
partial_evidence_card:
  source_name: login_logs_search
  dennis_source_status: auth_failed
  dennis_source_quality:
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
  - `track_analysis_check_data_ready`
  - `rcp_snapshot`
  - `weapon_inventory`
  - `login_logs_search`
  - `archives_user_analysis`
  - `archives_photo_search`
  - `archives_user_profile`
  - `archives_related_users`
  - `archives_private_message_search`
  - `archives_past_four_items`
  - `rcp_event_detail`
  - `rcp_event_feature_list`
  - `rcp_policy_version_lookup`
  - `rcp_policy_detail_lookup`
  - `rcp_policy_release_record_lookup`
  - `rcp_policy_tree_lookup`
  - `rcp_node_policy_attribution`
  - `rcp_node_bind_policy_attribution`
- Only typed params are serialized into the JSON body.
- Caller-provided route, credential, or transport override fields are rejected before service invocation.
- HTTP transport errors, connection refused, timeout, HTTP error, and non-JSON responses are normalized as source results instead of Dennis runtime failures.
- `BrowserBackedServiceClient.call_account_security_sources()` is a legacy/unit helper, not the default case execution entry. Runtime case execution must use `runtime_case_execution_runner.py` and controlled batch; helper output must not become fallback after browser-backed source gaps.
- `build_small_batch_evidence_output()` is the small-batch display helper. In `internal_risk_review`, user titles must use raw copyable risk entity identifiers such as `用户 772671837`; in `external_share`, user titles must use aliases / masks such as `用户 U1（user_***1837）`. This only changes display; credential secrets and raw source dumps remain suppressed in every scope.
- `build_track_analysis_check_data_ready_browser_backed_request()` maps typed `device_id`, time window, app/product, category/event/platform filters, and metric to service-owned `POST /dp/platform/app/analytics/v2/sequence/checkDataReady`; service generates `batchQueryId` and `_t`. The result is readiness/provenance context only, not evidence completion.
- `build_archives_user_analysis_browser_backed_request()` builds the fixed typed-param plan for `archives_user_analysis`. The browser-backed service maps it to `POST /v3/user/log/coreLogs/fetch`; Dennis never passes URL/path/header/cookie/token/session.
- `build_archives_photo_search_browser_backed_request()` maps typed `user_id` plus time/page filters to service-owned `POST /v4/archives/report/photo/search` body fields `reportedIds`, `matchType`, `sort`, `begin`, `end`, `page`, and `count`.
- `build_archives_user_profile_browser_backed_request()` maps typed `user_id` to service-owned `GET /archives/user/home/info?userId=...`; optional label/shop/risk bundle paths stay service-owned.
- `build_archives_related_users_browser_backed_request()` maps typed `user_id` and `relation_type` to service-owned `POST /archives/user/search/device` body fields `keyword`, `inputType=0`, and validated `type=0/1`.
- `build_archives_private_message_search_browser_backed_request()` maps typed `user_id` and `direction=sent/received` to service-owned `POST /archives/user/message/search` body fields `fromUserId` or `toUserId`, plus page/count/status/sort.
- `build_archives_past_four_items_browser_backed_request()` maps typed `user_id` and four-info `info_type` to service-owned `POST /v4/audit/user/fourinfo/log/search` body fields `keyword`, `infoType`, `markResult`, `punishResult`, `page`, and `count`.
- `build_rcp_event_detail_browser_backed_request()` maps typed `eventType`, `eventId`, and exact `queryTime` to service-owned `GET /v2/rest/event/rcpEventDetail`.
- `build_rcp_event_feature_list_browser_backed_request()` maps typed `eventType`, `eventId`, exact `queryTime`, and fixed `featureGroup=""` to service-owned `GET /v2/rest/event/rcpEventFeatureList`.
- `build_rcp_policy_version_lookup_browser_backed_request()` maps typed event and policy identifiers to service-owned `GET /v2/rest/pc/policy/getPolicyVersionListByEvent`.
- `build_rcp_policy_detail_lookup_browser_backed_request()` maps typed `policyCode` and `policyVersion` to service-owned `GET /v2/rest/pro/policy/getPolicyDetailByVersion`; companion readonly version-history and relation-tree reads stay service-owned. Policy detail is strategy-governance context, not final judgement.
- `build_rcp_policy_release_record_lookup_browser_backed_request()` maps typed `policyCode`, optional `statusCode`, and page/size to service-owned `POST /v2/rest/common/pipeline/list`, with `extrbB=policyCode`; companion `selectInfo` stays service-owned. Release records are lifecycle provenance, not risk judgement.
- `build_rcp_policy_tree_lookup_browser_backed_request()` maps typed policy-tree identifiers to service-owned `GET /v2/rest/pro/policyTree/queryProPolicyTree`; the strategy-tree asset chain may also use fixed companion reads `/v2/rest/pro/policyTree/policyTreeList` (coarse list only), `/v2/rest/pro/policyTree/queryBindingByNodeCode` (node-level binding policy list), and `/v2/rest/pro/policyTree/getAllPolicyCodeByPage` (full-tree policy code list). Node resolution stays service-owned and guessed node codes are not accepted from the caller.
- `build_rcp_node_policy_attribution_browser_backed_request()` maps typed event and policy identifiers to service-owned `POST /v2/rest/pc/policy/nodePolicyAttribution` with fixed `type=""`.
- `build_rcp_node_bind_policy_attribution_browser_backed_request()` maps typed event and resolved policy-tree node identifiers to service-owned `GET /v2/rest/pc/policy/nodeBindPolicyAttribution`.

## Track Analysis Auxiliary Actions

```yaml
source_name: track_analysis_check_data_ready
action_name: track_analysis_check_data_ready
local_service_endpoint: POST /actions/track_analysis_check_data_ready
representative_platform_path: /dp/platform/app/analytics/v2/sequence/checkDataReady
typed_params:
  device_id: "<device risk entity id>"
  appName: KUAISHOU
  product: KUAISHOU
  startTime: <millisecond timestamp>
  endTime: <millisecond timestamp>
  include: 1
  pageSize: 100
  category: ["<safe category label>"]
  event: []
  appPlatform: []
  metric: pv
  type: deviceId
  mode: track_analysis_data_readiness_precheck
service_generated_fields:
  - batchQueryId
  - _t
fixed_fields:
  funcType: USER_PROFILE_QUERY
  type: deviceId
```

Output contract:

- Service returns pure passthrough envelope / transport metadata / capped body only.
- Dennis generates `source_status`, readiness summary, `dennis_source_quality`, `key_entities.device_id`, `missing_fields`, `next_action`, and `no_data_not_risk_exclusion=true`.

This action summarizes `data.dateStatus` presence/status and `trace_id_present=true/false` only. It must not output raw readiness body, trace ID value, caller-provided URL/path/header/cookie/token/session, or credential material. It is a readiness/source-quality helper and must not be counted as completed account-security evidence by itself.

## Archives Center Actions

Landscape: `computer_use_poc/archives_center_integration_landscape_v1.md`.

Implemented actions:

```yaml
source_name: archives_user_analysis
action_name: archives_user_analysis
local_service_endpoint: POST /actions/archives_user_analysis
representative_platform_path: /v3/user/log/coreLogs/fetch
typed_params:
  user_id: "<decimal user id>"
  mode: focused_login_risk_core_logs
  beginTime: <millisecond timestamp>
  endTime: <millisecond timestamp>
  pageIndex: 1
  pageSize: 30
  haveParamAuth: 1
  operation_filters:
    loginStart: 1
    registerBind: 1
    resetPass: 1
    protectAccount: 1
    liveStream: 1
    scanCode: 1
    logout: 1
    frozen: 1
---
source_name: archives_photo_search
action_name: archives_photo_search
local_service_endpoint: POST /actions/archives_photo_search
representative_platform_path: /v4/archives/report/photo/search
typed_params:
  user_id: "<decimal user id>"
  mode: archives_photo_report_search
  begin: <millisecond timestamp>
  end: <millisecond timestamp>
  page: 1
  count: 20
  matchType: "0"
  sort: "0"
---
source_name: archives_user_profile
action_name: archives_user_profile
local_service_endpoint: POST /actions/archives_user_profile
representative_platform_path: /archives/user/home/info
typed_params:
  user_id: "<decimal user id>"
  mode: archives_user_home_profile
---
source_name: archives_related_users
action_name: archives_related_users
local_service_endpoint: POST /actions/archives_related_users
representative_platform_path: /archives/user/search/device
typed_params:
  user_id: "<decimal user id>"
  mode: archives_same_device_related_users
  relation_type: same_device_registered | same_device_login
  inputType: 0
  type: 0 | 1
---
source_name: archives_private_message_search
action_name: archives_private_message_search
local_service_endpoint: POST /actions/archives_private_message_search
representative_platform_path: /archives/user/message/search
typed_params:
  user_id: "<decimal user id>"
  mode: archives_private_message_summary
  direction: sent | received
  page: 1
  count: 20
  status: ""
  sort: "0"
---
source_name: archives_past_four_items
action_name: archives_past_four_items
local_service_endpoint: POST /actions/archives_past_four_items
representative_platform_path: /v4/audit/user/fourinfo/log/search
typed_params:
  user_id: "<decimal user id>"
  mode: archives_four_info_change_log_summary
  info_type: all | username | avatar | profile_description | background
  infoType: 0 | 1 | 2 | 3 | 4
  page: 1
  count: 20
  markResult: ""
  punishResult: ""
```

Output contract:

- Service returns pure passthrough envelope / transport metadata / capped body only.
- Dennis generates source status, local source card if needed, source quality, key entity summary, missing fields, next action, and no-data boundary.

The actions return safe passthrough only. Dennis may derive limited summaries such as photo/profile/related-user/four-info context, but must not require service-side `risk_event_scan`, `photo_search_summary`, `profile_summary`, `related_users_summary`, `private_message_summary`, or `four_info_change_summary`. They must not return raw full body, full `requestParam`, full `extraParam`, raw report text, raw profile body, raw related-user profile, private message plaintext, old/new profile text, media URLs, token/tokenId/open_id/sig/refresh_token, or raw records.

## RCP / Tianshi Drill-Down Actions

Inventory: `computer_use_poc/har_platform_interface_inventory_v1.md`.

Implemented mock-only actions:

```yaml
source_name: rcp_event_detail
action_name: rcp_event_detail
local_service_endpoint: POST /actions/rcp_event_detail
representative_platform_path: /v2/rest/event/rcpEventDetail
typed_params:
  eventType: USER_REGISTER_NEW
  eventId: "<event id>"
  queryTime: <exact _occurTime millisecond timestamp>
  mode: rcp_event_detail_readonly
---
source_name: rcp_event_feature_list
action_name: rcp_event_feature_list
local_service_endpoint: POST /actions/rcp_event_feature_list
representative_platform_path: /v2/rest/event/rcpEventFeatureList
typed_params:
  eventType: USER_REGISTER_NEW
  eventId: "<event id>"
  queryTime: <exact _occurTime millisecond timestamp>
  featureGroup: ""
  mode: rcp_event_feature_snapshot_readonly
---
source_name: rcp_policy_version_lookup
action_name: rcp_policy_version_lookup
local_service_endpoint: POST /actions/rcp_policy_version_lookup
representative_platform_path: /v2/rest/pc/policy/getPolicyVersionListByEvent
typed_params:
  eventType: USER_REGISTER_NEW
  eventId: "<event id>"
  policyCode: "<policy code>"
  policyVersion: 5
  queryTime: <exact _occurTime millisecond timestamp>
  mode: rcp_policy_version_lookup_readonly
---
source_name: rcp_policy_detail_lookup
action_name: rcp_policy_detail_lookup
local_service_endpoint: POST /actions/rcp_policy_detail_lookup
representative_platform_path: /v2/rest/pro/policy/getPolicyDetailByVersion
companion_readonly_paths:
  - /v2/rest/pro/policy/getPolicyAllVersion
  - /v2/rest/pc/policyReview/getRelationPolicyTree
typed_params:
  policyCode: "<policy code>"
  policyVersion: 5
  mode: rcp_policy_detail_lookup_readonly
---
source_name: rcp_policy_release_record_lookup
action_name: rcp_policy_release_record_lookup
local_service_endpoint: POST /actions/rcp_policy_release_record_lookup
representative_platform_path: /v2/rest/common/pipeline/list
companion_readonly_paths:
  - /v2/rest/common/pipeline/selectInfo
typed_params:
  policyCode: "<policy code>"
  statusCode: ""
  page: 1
  size: 20
  mode: rcp_policy_release_record_lookup_readonly
body_builder:
  extrbB: policyCode
  statusCode: statusCode
  pageInfoRequest:
    page: page
    size: size
  service_owned_fields:
    - configCode
    - createUser
    - extrbA
    - extrbC
---
source_name: rcp_policy_tree_lookup
action_name: rcp_policy_tree_lookup
local_service_endpoint: POST /actions/rcp_policy_tree_lookup
representative_platform_path: /v2/rest/pro/policyTree/queryProPolicyTree
companion_readonly_paths:
  - /v2/rest/pro/policyTree/policyTreeList
  - /v2/rest/pro/policyTree/queryBindingByNodeCode
  - /v2/rest/pro/policyTree/getAllPolicyCodeByPage
typed_params:
  policyTreeCode: USER_REGISTER_NEW
  policyTreeVersion: 887
  targetPolicyCode: "<optional policy code>"
  mode: rcp_policy_tree_lookup_readonly
---
source_name: rcp_node_policy_attribution
action_name: rcp_node_policy_attribution
local_service_endpoint: POST /actions/rcp_node_policy_attribution
representative_platform_path: /v2/rest/pc/policy/nodePolicyAttribution
typed_params:
  eventType: USER_REGISTER_NEW
  eventId: "<event id>"
  policyCode: "<policy code>"
  policyVersion: 5
  queryTime: <exact _occurTime millisecond timestamp>
  region: china
  type: ""
  mode: rcp_node_policy_attribution_readonly
---
source_name: rcp_node_bind_policy_attribution
action_name: rcp_node_bind_policy_attribution
local_service_endpoint: POST /actions/rcp_node_bind_policy_attribution
representative_platform_path: /v2/rest/pc/policy/nodeBindPolicyAttribution
typed_params:
  eventType: USER_REGISTER_NEW
  eventId: "<event id>"
  queryTime: <exact _occurTime millisecond timestamp>
  policyTreeCode: USER_REGISTER_NEW
  policyTreeVersion: 887
  policyTreeNodeCode: "<resolved node code from queryProPolicyTree>"
  mode: rcp_node_bind_policy_attribution_readonly
```

Output contract:

- Service returns pure passthrough envelope / transport metadata / capped body only.
- Dennis generates source status, local source card if needed, source quality, key entity summary, missing fields, next action, and no-data boundary.

The actions return safe passthrough only. Dennis may derive limited event, feature, policy, release, tree, attribution, or node-binding context, but must not require service-side summary fields. They must not return raw full body, raw event detail body, raw feature values, raw policy version body, raw policy detail body, raw release records, operator identities, raw policy tree body, raw condition dumps, raw node-binding body/list, credential material, or policy configuration dumps. Strategy events, feature snapshots, policy versions/details/release records, policy-tree nodes, condition-level attribution, and node-binding attribution are evidence/provenance, not final risk judgement.

Fixture self-test:

```bash
python3 computer_use_poc/browser_backed_service_client.py --self-test
```

The self-test does not require the browser-backed service to be running and does not call any live platform.

## Executable Passthrough Interpretation

The client reads these pure passthrough service fields:

- `action_name`
- `source_id`
- `platform`
- `http_status`
- `content_type`
- `body_present`
- `body_truncated`
- `observed_bytes`
- `elapsed_ms`
- `transport_error`
- `platform_error`
- `invalid_params`
- `timeout`
- `auth_redirect_detected`
- `raw_body_handling`
- `batch_status`
- `source_results`
- `transport_status_matrix`
- `missing_or_failed_sources`
- `classifications`

Dennis interpretation buckets:

| Dennis bucket | Passthrough signal |
| --- | --- |
| `completed_sources` | response envelope present, no timeout/error/auth redirect, usable body or explicit empty result metadata |
| `partial_sources` | `body_truncated=true` or `raw_body_handling=capped` |
| `no_data_sources` | empty result metadata or `body_present=false` without transport/platform error |

### Source-specific time windows

ATO source windows are source-specific. `login_logs_search` defaults to the reliable online login-log window, currently 7 days unless a playbook overrides it. `archives_user_profile`, `archives_user_analysis`, and `archives_photo_search` use the scene/action window and are not constrained by login logs' 7-day reliability window. `track_analysis_check_data_ready`, Weapon, and RCP use their own source capability windows. A response gap in one window must enter `source_quality_matrix`; it must not shrink other source windows or become low-risk counter-evidence.

| `auth_failed_sources` | `auth_redirect_detected=true`, `api_code=302`, or HTTP auth redirect |
| `blocked_sources` | `transport_error`, `platform_error`, or service HTTP error |
| `timeout_sources` | `timeout=true` |
| `parse_error_sources` | invalid params, malformed passthrough envelope, or Dennis parser failure on capped body |
| `invalid_parameter_sources` | `invalid_params=true` or missing typed params before action call |

### ATO passthrough interpretation layer

Dennis adds a `user_device_entity_resolution` layer for ATO/account takeover cases. It extracts candidate `device_id` / DID from login logs, Archives user analysis, Archives photo search, Weapon, and Track readiness results, then uses those candidates for Track, Weapon, publish-device alignment, and historical device baseline comparison. If the initial source set has no candidate, Dennis must actively run the current next-hop resolution plan over existing observations and available low-cost sources before marking the gap. Only after that resolution fails may Track be marked `missing_required_fields` / `candidate_device_id_missing_after_resolution` in Dennis `source_quality_matrix` and `missing_evidence`; this must not fail the whole batch.

Source-specific interpretation must stay Dennis-owned:

- Dennis may safely parse visible `body`, `raw_body`, `response_body`, `upstream_body`, `raw_payload`, `capped_body`, `body_excerpt`, or `body_snippet` fields in memory. The parser returns only allowlisted risk handles, field paths, observation gaps, and evidence-chain tags; it must not return or persist raw full body content.
- `cookie`, `token`, `session`, `header`, `authorization`, `password`, `secret`, and credential-like values are dropped. Token/OAuth/scan control-chain presence may be retained only as a redacted presence handle, never as a credential value.
- Strict PII such as phone number, ID card number, real name, or detailed address is not allowed in user-visible evidence. If encountered, mark `pii_strict_redacted` and use only safe summaries or handles.
- `login_logs_search`: `response_too_large` / `body_truncated` means partial observation. If a visible capped body/snippet is present, Dennis first parses the safe prefix and marks `partial_login_log_parsed_from_capped_body`; if `body_present=true` but no capped/snippet is visible to Dennis, mark `service_body_visibility_gap_for_truncated_login_log`. Window shrink should use publish time, user-claim time, abnormal event time, strategy-hit time, or recent publish time as anchors; if no anchor exists, generate `login_log_window_shrink_anchor_missing` and first look for an anchor in photo/user-analysis/strategy observations. `network_error` must be subtyped as transport, service, batch-contract, passthrough-interpretation, or invalid-params gap.
- `archives_user_analysis`: completed transport is not behavior-chain closure; if password/binding/protection/profile/publish operation fields are unavailable, mark `behavior_chain_business_fields_missing`.
- `archives_photo_search`: completed transport is not content handoff closure; if `photo_id`, publish time, publish device, or publish source are unavailable, mark `content_chain_business_fields_missing`. `no_data` does not exclude abnormal publish or ATO.
- `track_analysis_check_data_ready`: readiness/provenance only; it does not prove owner operation or low risk.

When realtime evidence is incomplete, Dennis should expose selectable offline authorization modules generated from the current missing fields and chain breakpoints rather than asking for broad Hive/DataAgent permission. Typical dynamic `module_id` values include `web_publish_fact`, `web_login_history`, `device_history_baseline`, `token_oauth_scan_chain`, `security_action_chain`, and `post_action_chain`, but only modules triggered by the current evidence gap should be offered. Unselected modules remain `missing_evidence`.

Before offline escalation, Dennis should run the active missing-evidence next-hop loop on the current passthrough observations: missing entity -> entity resolution, missing time anchor -> behavior/event/strategy/content anchor lookup, large response -> capped parse plus shrink-window planning, completed transport without visible body -> body visibility gap, and every new field -> evidence-chain/conclusion recompute. This is Dennis-owned orchestration and must not restore service-side normalizers or add unregistered browser-backed actions.

The service no longer needs to return `sensitive_output=false`; safe passthrough is enforced by raw-body suppression/capping and fixed typed actions. If a response contains credential material or an uncapped raw full body, Dennis treats it as `blocked` with a source contract gap and excludes the body from evidence.

Safe passthrough means no credential secret plaintext, no raw full body, no raw records full dump, and no raw `labelInfo` / `originalLog` full dump. It does not mean all risk entity identifiers were removed. Under `internal_risk_review`, evidence cards may display UID/user_id, DID/device_id, IP, eventId, sourceId, hitFusePolicyCode, login method, logSource, and timestamp. Under `external_share`, those risk entity identifiers must be masked.

Phone numbers are `pii_strict`: `internal_risk_review` may display `1381234****`, while `external_share` may display only `138********`; full phone numbers are never allowed. Full ID card numbers and real names are never displayed; only weak summaries such as `id_card_present=true`, `birth_year_present=true`, or `name_present=true` are allowed.

## Partial Evidence Construction

`build_source_completion_matrix()` and `build_partial_evidence_card()` produce display-safe structures for Dennis runtime:

```yaml
partial_evidence_card:
  sensitive_output: false
  output_scope: internal_risk_review
  field_classification: {}
  completed_sources: []
  no_data_sources: []
  blocked_sources: []
  dennis_generated_source_quality: {}
  no_data_not_risk_exclusion: true
```

The adapter does not persist source response summary full bodies, raw login records full dumps, raw `labelInfo`, or raw `originalLog`. It relies on pure passthrough envelope fields, transport metadata, capped body snippets, and Dennis-generated local observations/source quality. Compact risk entity identifiers follow `output_scope`.

## Evidence Display Summary

`build_partial_evidence_card()` extracts display-safe business summaries from Dennis-generated local observations and source quality instead of depending on service-provided `source_card` / `source_quality`.

Source-specific summary fields:

- `track_analysis_check_data_ready`
  - `readiness_status`
  - `missing_required_fields`
  - `front_backend_activity_alignment`
  - `readiness_summary.readiness_status`
  - `readiness_summary.date_status_present`
  - `readiness_summary.trace_id_present`
  - `key_entities.device_id`
  - Boundary: readiness is source-quality/provenance context, not account-security evidence by itself.
- `rcp_snapshot`
  - `event_summary.event_count`
  - `event_summary.table_header_columns`
  - `event_summary.returned_columns_observed`
  - `event_summary.first_event_shape_keys`
  - `event_summary.dynamic_columns_observed`
  - `first_event_entity_samples.eventId`
  - `first_event_entity_samples.sourceId`
  - `first_event_entity_samples.deviceId`
  - `first_event_entity_samples.hitFusePolicyCode`
  - `first_event_entity_samples._occurTime`
  - `chaining_keys_present.hitFusePolicyCode`
  - `chaining_keys_present.eventId`
  - `chaining_keys_present._occurTime`
  - Boundary: RCP is a strategy event entry source, not final risk judgement.
- `weapon_inventory`
  - `graph_summary.graph_status`
  - `graph_summary.related_device_count`
  - `graph_summary.related_user_count`
  - `graph_summary.related_device_id_sample`
  - `graph_summary.related_user_id_sample`
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
  - `login_window_summary.ip_sample`
  - `login_window_summary.device_id_sample`
  - `login_window_summary.user_id_sample`
  - `login_window_summary.method_sample`
  - `login_window_summary.logSource_sample`
  - `login_window_summary.passthrough_envelope_interpreted`
  - Boundary: `no_data` means no visible rows in the observed window, not no-risk evidence.
- `archives_photo_search`
  - `photo_search_summary.photo_count`
  - `photo_search_summary.publish_time_range`
  - `photo_search_summary.status_summary`
  - `photo_search_summary.risk_context_summary`
  - `key_entities.photo_ids`
  - Boundary: report/content signals are not final risk judgement.
- `archives_user_profile`
  - `profile_summary.account_status_summary`
  - `profile_summary.registration_summary`
  - `profile_summary.profile_state_summary`
  - `profile_summary.label_summary`
  - `profile_summary.risk_info_summary`
  - Boundary: current-state profile baseline is not full history.
- `archives_related_users`
  - `related_users_summary.related_user_count`
  - `related_users_summary.relation_type_summary`
  - `related_users_summary.status_summary`
  - `key_entities.related_user_ids`
  - Boundary: same-device relation is an expansion clue, not standalone judgement.
- `archives_private_message_search`
  - `private_message_summary.private_message_count`
  - `private_message_summary.direction_summary`
  - `private_message_summary.message_time_range`
  - `private_message_summary.status_summary`
  - `private_message_summary.counterpart_count`
  - Boundary: private-message plaintext and counterpart profile details stay suppressed.
- `archives_past_four_items`
  - `four_info_change_summary.total_changes`
  - `four_info_change_summary.change_time_range`
  - `four_info_change_summary.info_type_summary`
  - `four_info_change_summary.status_summary`
  - `four_info_change_summary.profile_change_risk_summary`
  - Boundary: old/new profile content, media URL, and operator name stay suppressed.
- `rcp_event_detail`
  - `event_detail_summary.event_detail_status`
  - `event_detail_summary._occurTime`
  - `event_detail_summary.real_time_feedback`
  - `event_detail_summary.error_code`
  - `event_detail_summary.effective_policy_summary`
  - `event_detail_summary.hit_policy_count`
  - `key_entities.eventId`
  - `key_entities.sourceId`
  - `key_entities.deviceId`
  - Boundary: event detail is single-event strategy evidence, not final judgement.
- `rcp_event_feature_list`
  - `feature_snapshot_summary.feature_count`
  - `feature_snapshot_summary.feature_group_distribution`
  - `feature_snapshot_summary.feature_key_samples`
  - `feature_snapshot_summary.check_result_summary`
  - Boundary: feature snapshots are attribution context; raw feature values stay suppressed.
- `rcp_policy_version_lookup`
  - `policy_version_summary.version_found`
  - `policy_version_summary.policyCode`
  - `policy_version_summary.policyVersion`
  - `policy_version_summary.snapshotVersion`
  - `policy_version_summary.version_metadata_summary`
  - Boundary: policy version context is attribution prerequisite, not judgement.
- `rcp_policy_detail_lookup`
  - `policy_detail_summary.policy_detail_status`
  - `policy_detail_summary.policyCode`
  - `policy_detail_summary.policyVersion`
  - `policy_detail_summary.condition_count`
  - `policy_detail_summary.version_count`
  - `policy_detail_summary.relation_policy_tree_count`
  - Boundary: policy detail explains strategy definition and versions; raw condition expressions stay suppressed and this is not final judgement.
- `rcp_policy_release_record_lookup`
  - `release_record_summary.release_record_status`
  - `release_record_summary.policyCode`
  - `release_record_summary.record_count`
  - `release_record_summary.parsed_policy_versions`
  - `release_record_summary.pipeline_versions`
  - `release_record_summary.status_distribution`
  - Boundary: release records explain lifecycle/version provenance; raw records and operator identities stay suppressed and this is not final judgement.
- `rcp_policy_tree_lookup`
  - `policy_tree_summary.policyTreeCode`
  - `policy_tree_summary.policyTreeVersion`
  - `policy_tree_summary.policyTreeNodeCode`
  - `policy_tree_summary.node_code_source`
  - `policy_tree_summary.target_policy_found`
  - Boundary: policy-tree lookup is governance context; do not guess node codes.
- `rcp_node_policy_attribution`
  - `policy_attribution_summary.attribution_status`
  - `policy_attribution_summary.policyCode`
  - `policy_attribution_summary.policyVersion`
  - `policy_attribution_summary.condition_count`
  - `policy_attribution_summary.true_condition_count`
  - `policy_attribution_summary.false_condition_count`
  - Boundary: condition attribution explains a policy result; raw condition and feature dumps stay suppressed.
- `rcp_node_bind_policy_attribution`
  - `node_binding_summary.node_binding_status`
  - `node_binding_summary.node_name_summary`
  - `node_binding_summary.policyTreeNodeCode`
  - `node_binding_summary.effective_policy_summary`
  - `node_binding_summary.target_policy_online`
  - `node_binding_summary.target_policy_result`
  - Boundary: node binding explains strategy-tree context; raw binding lists stay suppressed.

The display layer keeps:

```yaml
sensitive_output: false
no_data_not_risk_exclusion: true
final_risk_judgement_made: false
```

The display layer must not emit raw profile body, raw login records full dump, raw `labelInfo`, raw `originalLog`, credential material, full phone numbers, full ID card numbers, or real names. Risk entity identifiers are allowed only by `output_scope`.
