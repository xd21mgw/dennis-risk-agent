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
| Track-analysis data readiness precheck | `track_analysis_check_data_ready` | `POST /actions/track_analysis_check_data_ready` |
| Archives Center user-analysis core logs | `archives_user_analysis` | `POST /actions/archives_user_analysis` |
| Archives Center photo report search | `archives_photo_search` | `POST /actions/archives_photo_search` |
| Archives Center user profile baseline | `archives_user_profile` | `POST /actions/archives_user_profile` |
| Archives Center same-device related users | `archives_related_users` | `POST /actions/archives_related_users` |
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

For clean `full_runtime` single-user account-security evidence cards, the four base fixed actions (`track_analysis_summary`, `rcp_snapshot`, `weapon_inventory`, `login_logs_search`) are the primary source path. Dennis must not first try missing legacy runners such as `bin/sso_session_runner` or `bin/track_analysis_runner`. Archives Center remains a separate optional source; if `archives_profile_runner` is still a stub, it is recorded as `source_gap` and does not block the browser-backed chain.

`archives_user_analysis`, `archives_photo_search`, `archives_user_profile`, `archives_related_users`, `archives_private_message_search`, and `archives_past_four_items` are available as optional Archives Center sources. They are not added to the default four-source account-security main chain by this adapter patch.

`rcp_event_detail`, `rcp_event_feature_list`, `rcp_policy_version_lookup`, `rcp_policy_detail_lookup`, `rcp_policy_release_record_lookup`, `rcp_policy_tree_lookup`, `rcp_node_policy_attribution`, and `rcp_node_bind_policy_attribution` are explicit RCP/Tianshi drill-down sources. They require upstream event, policy, or policy-tree identifiers; they are not part of the default four-source account-security main chain.

The HAR inventory also tracks auxiliary candidates that are intentionally not in the default four-source runtime chain:

- `track_analysis_check_data_ready`: mock-only readiness/provenance helper; fixed by HAR to `POST /dp/platform/app/analytics/v2/sequence/checkDataReady`, not account-security evidence by itself.
- `track_analysis_config_lookup`: config helper only; not evidence and not default runtime.
- `rcp_event_type_list` / `rcp_realtime_op_list` / `rcp_event_feature_key_lookup` / `rcp_event_tree_or_decision_lookup`: RCP helper candidates only; not default runtime and not implemented in this adapter pass.
- `login_log_detail_lookup`: UI modal key extraction has validation evidence, but no fixed API path/body or row identifier contract has been confirmed.
- `login_log_filter_options`: blocked until a safe HAR confirms a separate filter/config option path and response shape; current default remains `recallSource=2,0,1,3`.
- `login_logs_search_page`: not a standalone action for the current `/rest/unified/log/search` contract because validated API responses can return the full current-window result and UI pagination is frontend-only.

Current `browser-backed-api-poc` parity note: the adjacent service implementation still exposes only the four base actions (`rcp_snapshot`, `weapon_inventory`, `login_logs_search`, `track_analysis_summary`). The Track Analysis readiness helper, Archives Center optional actions, and RCP/Tianshi drill-down actions below are Dennis-side mock-only contracts until the service action allowlist is extended separately. They require explicit action calls and must not be treated as live service actions or default runtime sources.

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
  output_scope: internal_risk_review | external_share
  field_classification:
    credential_secret: []
    pii_strict: []
    risk_entity_identifier: []
    source_summary_metric: []
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

Dennis must not persist or display a raw response full body from the browser-backed service. `output_scope` defaults to `internal_risk_review`; callers may request `external_share` when the evidence card is meant for sharing outside internal risk review.

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
- `BrowserBackedServiceClient.call_account_security_sources()` is the executable single-user account-security helper. It expands Track Analysis sub-interfaces, preserves Weapon private safe handles when the service returns them, applies login-log parse fallback, and returns display-safe source results for evidence-card construction.
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

- `source_status`
- `source_card.track_analysis_check_data_ready_summary`
- `source_quality.track_analysis_action_contract=track_analysis_check_data_ready`
- `key_entities.device_id`
- `missing_fields`
- `next_action`
- `sensitive_output=false`
- `no_data_not_risk_exclusion=true`

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

- `source_status`
- `source_card`
- `source_quality`
- `key_entities`
- `missing_fields`
- `next_action`
- `sensitive_output=false`
- `no_data_not_risk_exclusion=true`

The actions return derived summaries only: `risk_event_scan`, `photo_search_summary`, `profile_summary`, `related_users_summary`, `private_message_summary`, or `four_info_change_summary`. They must not return raw full body, full `requestParam`, full `extraParam`, raw report text, raw profile body, raw related-user profile, private message plaintext, old/new profile text, media URLs, token/tokenId/open_id/sig/refresh_token, or raw records.

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

- `source_status`
- `source_card`
- `source_quality`
- `key_entities`
- `missing_fields`
- `next_action`
- `sensitive_output=false`
- `no_data_not_risk_exclusion=true`

The actions return derived `event_detail_summary`, `feature_snapshot_summary`, `policy_version_summary`, `policy_detail_summary`, `release_record_summary`, `policy_tree_summary`, `policy_attribution_summary`, and `node_binding_summary` only. They must not return raw full body, raw event detail body, raw feature values, raw policy version body, raw policy detail body, raw release records, operator identities, raw policy tree body, raw condition dumps, raw node-binding body/list, credential material, or policy configuration dumps. Strategy events, feature snapshots, policy versions/details/release records, policy-tree nodes, condition-level attribution, and node-binding attribution are evidence/provenance, not final risk judgement.

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

`sensitive_output=false` means no credential secret plaintext, no raw full body, no raw records full dump, and no raw `labelInfo` / `originalLog` full dump. It does not mean all risk entity identifiers were removed. Under `internal_risk_review`, evidence cards may display UID/user_id, DID/device_id, IP, eventId, sourceId, hitFusePolicyCode, login method, logSource, and timestamp. Under `external_share`, those risk entity identifiers must be masked.

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
  source_quality: {}
  no_data_not_risk_exclusion: true
```

The adapter does not persist raw response full bodies, raw login records full dumps, raw `labelInfo`, or raw `originalLog`. It relies on `source_card`, `source_quality`, and service-provided summaries that are already sanitized by the browser-backed service. Compact risk entity identifiers follow `output_scope`.

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
  - `device_ids_summary.device_id_sample`
  - `device_ids_summary.device_model_fields_present`
  - `device_ids_summary.last_active_fields_present`
- `track_analysis_check_data_ready`
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
  - `login_window_summary.standard_browser_backed_source_result`
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
