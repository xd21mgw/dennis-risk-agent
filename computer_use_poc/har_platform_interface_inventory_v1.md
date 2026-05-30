# HAR Platform Interface Inventory v1

## Purpose

Track valuable HAR-derived platform interfaces and decide whether each should become a browser-backed fixed action, stay as inventory/candidate, or be skipped. This inventory now records the browser-backed fixed actions v1 registration/live-smoke closure for the selected batch. It does not perform live smoke, does not access real platforms, and does not change default runtime routing.

## Global Boundary

- `default_runtime_routing=false` for every interface in this inventory.
- `live_verified=false` remains the registry default unless an explicit registry flag exists; live-smoke evidence is recorded in the action status fields and does not create default routing.
- `needs_explicit_action_call=true` for every mock-only / candidate auxiliary action outside the default four-source account-security chain.
- New mock-only actions require explicit action calls and are not added to the default account-security chain.
- Adjacent `browser-backed-api-poc` now registers the v1 closure batch: `login_logs_search`, `track_analysis_check_data_ready`, `archives_user_profile`, `archives_user_analysis`, `archives_photo_search`, `archives_related_users`, `rcp_event_detail`, `rcp_event_feature_list`, and `rcp_policy_tree_lookup`. They remain explicit-action/source-plan only.
- No DataAgent or Hive call is part of this inventory.
- Caller-provided URL/path/header/cookie/token/session remains forbidden.
- Raw HAR headers, cookies, tokens, sessions, full response bodies, full `requestParam`, and full `extraParam` are not stored.
- Risk entity identifiers such as `user_id`, `device_id`, `ip`, `event_id`, `strategy_id`, `photo_id`, and `live_id` may be retained for internal review/source chaining. Credential secrets and strict PII remain forbidden output.

## Status Summary

The summary below counts inventory interface rows. Live-smoke readiness is
tracked separately in `computer_use_poc/browser_backed_live_smoke_readiness_v1.md`
and rolls companion policy-tree rows into a single action contract where
appropriate.

| platform | live_smoke_verified | no_data_path_live | partial_observation_available | implemented_mock_only | candidate_only | blocked_missing_har | blocked_unclear_semantics | not_supported |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Archives Center | 3 | 1 | 0 | 2 | 0 | 1 | 0 | 0 |
| RCP / Tianshi | 2 | 0 | 1 | 9 | 5 | 0 | 0 | 2 |
| Track Analysis | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |
| Weapon | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 1 |
| Login Logs | 1 | 0 | 0 | 0 | 0 | 2 | 0 | 2 |
| Grafana | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| Product Studio / Kconf / Permission Config | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 1 |

Noise families skipped and intentionally not inventoried as Dennis sources: `log-sdk`, miscellaneous frontend monitor/radar, `h5-fingerprint`, generic device-info collectors, performance beacons, telemetry, collection dependencies, and unrelated static asset/config fetches.

## Browser-Backed Fixed Actions v1 Closure

| action_name | platform | registry_status | live_smoke_status | routing_boundary |
| --- | --- | --- | --- | --- |
| `login_logs_search` | Login Logs | service_registered | `live_smoke_verified` | ATO/login source; no_data/window gap is not no-risk evidence. |
| `track_analysis_check_data_ready` | Track Analysis | service_registered | `live_smoke_verified` | Readiness/provenance helper, not risk conclusion. |
| `archives_user_profile` | Archives Center | service_registered | `live_smoke_verified` | Account baseline, not final judgement. |
| `archives_user_analysis` | Archives Center | service_registered | `live_smoke_verified`; large response can be `partial_observation_available` | Operation/risk timeline; large response enters source_quality. |
| `archives_photo_search` | Archives Center | service_registered | `no_data`; path live | Abnormal-publish clue; no_data does not exclude content risk. |
| `archives_related_users` | Archives Center | service_registered | `live_smoke_verified` | Same-device spread clue, not gang conclusion. |
| `rcp_event_detail` | RCP / Tianshi | service_registered | `live_smoke_verified` | Event attribution detail, not tree governance. |
| `rcp_event_feature_list` | RCP / Tianshi | service_registered | `partial_observation_available` | Partial feature-group summary only. |
| `rcp_policy_tree_lookup` | RCP / Tianshi | service_registered | `live_smoke_verified` | Policy-tree asset governance, not event hit path. |

## Interface Inventory

| platform | endpoint_family | representative_path | method | action_name | status | priority | purpose | evidence_domain_mapping | typed_params_summary | request_body_status | response_shape_status | default_runtime_routing | live_verified | next_probe_needed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Archives Center | account_action_log | `/v3/user/log/coreLogs/fetch` | POST | `archives_user_analysis` | live_smoke_verified | P0 | core account operation timeline | account security / ATO / login-risk timeline | `user_id`, `beginTime`, `endTime`, `pageIndex`, `pageSize`, operation filters | confirmed body builder, service-owned | summary covers counts/time/device/IP/status; large response can be `partial_observation_available` | false | false | no |
| Archives Center | report_signal | `/v4/archives/report/photo/search` | POST | `archives_photo_search` | no_data_path_live | P0-conditional | abnormal publish/content/report anchoring | content abuse / ATO publish chain | `user_id`, `begin`, `end`, `page`, `count`, `matchType`, `sort` | corrected payload confirmed: `reportedIds=user_id` | live path returned `no_data` for tested window; no_data is not risk exclusion | false | false | no |
| Archives Center | account_profile | `/archives/user/home/info` | GET | `archives_user_profile` | live_smoke_verified | P0/P1-high | current account baseline/profile status | account baseline / profile context | `user_id` | path clear; optional bundle service-owned | current-state profile summary, raw body suppressed | false | false | no |
| Archives Center | relation_graph | `/archives/user/search/device` | POST | `archives_related_users` | live_smoke_verified | P1 | same-device related-user expansion | account relation / cluster clue | `user_id`, `relation_type`, `inputType=0`, `type=0/1` | corrected payload confirmed | related user counts/types; relation is clue not judgement | false | false | no |
| Archives Center | relation_graph | derived from profile/user-analysis/device summaries | TBD | `archives_related_devices` | blocked_missing_har | P1 | related-device expansion and Weapon cross-check | device relation clue | expected `user_id` or `device_id` | no standalone fixed path/body confirmed | standalone response shape not confirmed | false | false | confirm whether source is profile, user analysis, or same-device endpoint |
| Archives Center | social_interaction | `/archives/user/message/search` | POST | `archives_private_message_search` | implemented_mock_only | P2-conditional | private-message metadata count/status/time summary | social interaction clue; not default ATO source | `user_id`, `direction=sent/received`, page/count/status/sort | direction maps to `fromUserId` or `toUserId`; field semantics need live confirmation | fixture covers count/time/status/counterpart summary; plaintext suppressed | false | false | confirm direction/status semantics in controlled live smoke before production use |
| Archives Center | account_change_trace | `/v4/audit/user/fourinfo/log/search` | POST | `archives_past_four_items` | implemented_mock_only | P2-conditional | four-info metadata change-log summary | profile change clue; not default ATO source | `user_id`, `info_type=all/username/avatar/profile_description/background`, page/count/filters | validated `keyword=<user_id>` and `infoType=0..4`; field semantics need live confirmation | fixture covers count/time/type/status summary; old/new content and media URLs suppressed | false | false | confirm infoType/status semantics in controlled live smoke before production use |
| RCP / Tianshi | event_list | `/v2/rest/event/eventList` | POST | `rcp_snapshot` | implemented_mock_only | P0-explicit | strategy hit/event entry summary | policy-hit evidence entry | existing typed event/entity params; body service-owned | HAR body shape documented; dynamic query builder | fixture covers event count/dynamic columns | false | false | no |
| RCP / Tianshi | event_detail | `/v2/rest/event/rcpEventDetail` | GET | `rcp_event_detail` | live_smoke_verified | P0-explicit | single-event detail and exact `_occurTime` | event-level policy evidence | `eventType`, `eventId`, `queryTime` | path/params clear from run logs | feedback/error/effective policy/entities summary | false | false | no |
| RCP / Tianshi | feature_snapshot | `/v2/rest/event/rcpEventFeatureList` | GET | `rcp_event_feature_list` | partial_observation_available | P1-explicit | event feature snapshot summary | policy attribution context | `eventType`, `eventId`, `queryTime`, fixed `featureGroup=""` | path/params clear; non-empty `featureGroup` rejected | capped feature-count/group observation; raw values suppressed | false | false | no |
| RCP / Tianshi | policy_version | `/v2/rest/pc/policy/getPolicyVersionListByEvent` | GET | `rcp_policy_version_lookup` | implemented_mock_only | P1-explicit | policy version context | strategy attribution provenance | `eventType`, `eventId`, `policyCode`, `policyVersion`, `queryTime` | path/params documented; service-owned query builder | fixture covers version-found summary and policy metadata | false | false | no |
| RCP / Tianshi | policy_detail | `/v2/rest/pro/policy/getPolicyDetailByVersion` | GET | `rcp_policy_detail_lookup` | implemented_mock_only | strategy_governance | policy definition, version history, and binding-tree summary | strategy governance / policy explanation | `policyCode`, `policyVersion` | path/params documented; companion version-history and relation-tree reads service-owned | fixture covers condition/version/tree counts; raw detail and raw condition expressions suppressed | false | false | no |
| RCP / Tianshi | policy_tree_precise | `/v2/rest/pro/policyTree/queryProPolicyTree` | GET | `rcp_policy_tree_lookup` | live_smoke_verified | strategy_governance | precise policy tree node resolution | strategy governance / asset lookup, not event hit path | `policyTreeCode`, `policyTreeVersion`, optional `targetPolicyCode`; service maps `treeSnapshot` | HAR-confirmed query keys; recursive node resolution service-owned | resolved tree/node summary; raw tree suppressed | false | false | no |
| RCP / Tianshi | policy_tree_list | `/v2/rest/pro/policyTree/policyTreeList` | GET | `rcp_policy_tree_lookup` companion | implemented_mock_only | strategy_governance | coarse policy tree list / prefilter | strategy governance / asset discovery, not event hit path | `policyTreeCode`, optional `policyCode`, `eventTypeAssociator`, `page`, `size`, display filters | HAR-confirmed query keys; coarse list only | response shape `data.pagination` + `data.records`; raw records/operator identities suppressed | false | false | no |
| RCP / Tianshi | policy_tree_node_binding | `/v2/rest/pro/policyTree/queryBindingByNodeCode` | GET | `rcp_policy_tree_lookup` companion | implemented_mock_only | strategy_governance | node-level bound policy list | strategy governance / node binding context, not event hit path | resolved `policyTreeNodeCode`, `policyTreeCode`, `policyTreeVersion`, optional `policyCode`, page/size/order flags | HAR-confirmed query keys; node code must come from `queryProPolicyTree` parser | response shape `data.pagination` + `data.records`; raw binding list and raw policy bodies suppressed | false | false | no |
| RCP / Tianshi | policy_tree_policy_codes | `/v2/rest/pro/policyTree/getAllPolicyCodeByPage` | GET | `rcp_policy_tree_lookup` companion | implemented_mock_only | strategy_governance | full-tree policy code list | strategy governance / policy coverage context, not event hit path | `policyTreeCode`, `policyTreeVersion`, optional `code`, `page`, `size` | HAR-confirmed query keys; service-owned paging | response shape `data.pagination` + `data.records[].label/value`; raw full code list suppressed | false | false | no |
| RCP / Tianshi | policy_attribution | `/v2/rest/pc/policy/nodePolicyAttribution` | POST | `rcp_node_policy_attribution` | implemented_mock_only | P1-explicit | condition-level policy attribution | single-event policy explanation | `eventType`, `eventId`, `policyCode`, `policyVersion`, `queryTime`, fixed `type=""` | path/required fields documented; service-owned POST body | fixture covers true/false condition counts and raw condition suppression | false | false | no |
| RCP / Tianshi | node_bind_attribution | `/v2/rest/pc/policy/nodeBindPolicyAttribution` | GET | `rcp_node_bind_policy_attribution` | implemented_mock_only | strategy_governance | node-level binding attribution | strategy governance / policy tree context | `eventType`, `eventId`, `queryTime`, `policyTreeCode`, `policyTreeVersion`, `policyTreeNodeCode` | path documented; requires resolved node code | fixture covers node binding summary, target policy status, raw binding suppression | false | false | no |
| RCP / Tianshi | event_options | `/v2/rest/basicInfo/getEventTypeListByPage`, `/v2/rest/event/getEventLabelAndType` | GET | `rcp_event_type_list` | candidate_only | P2-config | eventType option discovery | config/lookup only | `keyWord`, `page`, `size` | HAR-confirmed query keys; config helper | response shape not source-card ready | false | false | implement only if explicit config lookup is needed |
| RCP / Tianshi | realtime_options | `/v2/rest/event/realTimeOpList`, `/v2/rest/basicInfo/getRealtimeOpList` | GET | `rcp_realtime_op_list` | candidate_only | P2-config | realtime action option discovery | config/lookup only | `eventType` or `policyType` | HAR-confirmed query keys; config helper | response shape not source-card ready | false | false | implement only if explicit config lookup is needed |
| RCP / Tianshi | feature_key_lookup | `/v2/rest/fc/getEventFeatureInfoByKeys` | GET | `rcp_event_feature_key_lookup` | candidate_only | P2-helper | selected feature metadata/value presence | policy attribution supplement | `eventType`, `eventId`, `featureKeys`, `queryTime`, `region`, `isPolicyTreeExperiment` | HAR-confirmed query keys | raw feature values require stricter minimization before action | false | false | define value-suppression normalizer before mock-only action |
| RCP / Tianshi | event_tree_decision | `/v2/rest/event/rcpEventTreeOrDecision` | GET | `rcp_event_tree_or_decision_lookup` | candidate_only | P2-helper | event decision tree / policy tree experiment context | attribution supplement | `eventType`, `eventId`, `queryTime`, `region`, `isPolicyTreeExperiment` | HAR-confirmed query keys | response semantics not source-card ready | false | false | summarize tree/decision shape without raw tree dump before action |
| RCP / Tianshi | policy_search | `/v2/rest/pro/policy/policySearch`, `/v2/rest/pro/policy/policyBlurSearch` | POST/GET | `rcp_policy_search_lookup` | candidate_only | strategy_governance | policy discovery by code/tree/filter | strategy governance helper | `policyCode`, `policyTreeCode`, `eventTypeAssociator`, page/size filters | HAR-confirmed query/body keys | search results are config-heavy, not evidence | false | false | require explicit policy search use case and minimization |
| RCP / Tianshi | policy_release_record | `/v2/rest/common/pipeline/selectInfo`, `/v2/rest/common/pipeline/list` | GET/POST | `rcp_policy_release_record_lookup` | implemented_mock_only | strategy_governance | policy release / gray / approval record summary | strategy governance provenance | `policyCode`, optional `statusCode`, `page`, `size`; service maps `extrbB=policyCode` | HAR/run-log confirmed filter keys; service owns `configCode/createUser/extrbA/extrbC` | fixture covers record/status/version summaries; raw records and operator identities suppressed | false | false | no |
| RCP / Tianshi | expression_dependency | `/v2/rest/basicInfo/resolveExpressionDependencyIncludesAlias` | POST | none | not_supported | denied | raw policy expression dependency resolution | config/debug helper | `expression` | requires raw policy expression body | policy expression/config dump risk | false | false | keep out of runtime source actions |
| RCP / Tianshi | test_case_config | `/v2/rest/testCase/run` and related config paths | POST | none | not_supported | low | test execution/config | config/test domain, not runtime evidence | not exposed | write/test-like execution boundary | not runtime evidence | false | false | keep out of browser-backed source actions |
| Track Analysis | account_security_bundle | existing profile/use-duration/device/latest paths | POST/GET | `track_analysis_summary` | implemented_mock_only | P0 | activity/profile/device bundle | account-security evidence | `user_id`, `appName`, `mode`, `sub_interface` | existing service-owned sub-interface calls | fixture covers four sub-interface summaries | false | false | no |
| Track Analysis | readiness | `/dp/platform/app/analytics/v2/sequence/checkDataReady` | POST | `track_analysis_check_data_ready` | live_smoke_verified | P2-helper | data readiness precheck | quality/provenance only | `device_id`, `appName`, `product`, `startTime`, `endTime`, `category`, `event`, `appPlatform`, `metric`, fixed `type=deviceId` | HAR-confirmed body keys; service generates `batchQueryId` and `_t` | response shape `code/message/data.dateStatus/traceId`; raw body and traceId value suppressed | false | false | no |
| Track Analysis | config | `/dp/platform/app/analytics/v2/sequence/config`, `/dp/platform/app/analytics/v2/kconf/get`, `/v3/dp/track/sys/proxy/kconf` | GET | `track_analysis_config_lookup` | candidate_only | P3-config | option/config lookup | helper only | `appName`, `funcType`, `product`, `type`, `key` | HAR-confirmed config/query keys | config response not evidence | false | false | inventory only unless required by a source action |
| Weapon | graph_risk_bundle | `/apiv2/graphData`, `/apiv2/riskData` | GET | `weapon_inventory` | implemented_mock_only | P0/P0-conditional | user-device graph plus conditional device risk | entity resolution / device risk | `user_id`, mode, riskData trigger prefixes | fixed paths service-owned | fixture covers graph/risk labels and safe handles | false | false | no |
| Weapon | graph_or_risk_aux | other graph/risk helper paths TBD | GET | `weapon_graph_aux_lookup` | candidate_only | P2-helper | graph/risk metadata if needed | relation provenance | none finalized | no clear additional endpoint needed | response shape unknown | false | false | only implement if related to device graph/risk |
| Weapon | config_or_page | Weapon UI/config/static endpoints | GET | none | not_supported | low | page/config only | not evidence | not exposed | not action-worthy | not evidence | false | false | do not implement |
| Login Logs | unified_search | `/rest/unified/log/search` | GET | `login_logs_search` | live_smoke_verified | P0 | online login log window | account security / ATO | `user_id`, `window`, `recallSource` | service-owned query builder | count/window/IP/device/method summary; large 7-day response can fallback to 24h | false | false | no |
| Login Logs | detail | detail modal/special event detail paths | UI modal / path TBD | `login_log_detail_lookup` | blocked_missing_har | P1-explicit | detail for selected login row | login chain supplement | `user_id`, row identifier / modal key if confirmed | run logs validate UI modal key extraction, but no fixed API path/body | JSON key shape observed; fixed response envelope not confirmed | false | false | capture safe HAR request for detail modal if one exists; otherwise keep detail as UI-only observation, not fixed browser-backed action |
| Login Logs | filter_options | filter/config option path TBD | GET/POST | `login_log_filter_options` | blocked_missing_har | P2-config | recallSource / method / logSource option discovery | config/lookup only | none finalized beyond `recallSource=2,0,1,3` | no fixed HAR path/body for filter options | response shape not confirmed | false | false | capture safe HAR path and option response shape if a separate config request exists |
| Login Logs | pagination_filter | `/rest/unified/log/search` frontend pagination | GET | none | not_supported | P1-helper | paginated visible-window search | source completeness | covered by `login_logs_search` current-window full result | evidence shows `totalCount == logSearchModels.length` and UI page changes do not trigger search request | frontend pagination only; no standalone runtime source | false | false | only revisit if future API response has `logSearchModels.length < totalCount` and exposes page/offset/cursor |
| Login Logs | export | export/download paths | GET/POST | none | not_supported | denied | bulk export | high-risk/non-runtime | not exposed | export/bulk operation | not suitable for runtime | false | false | do not implement |
| Grafana | datasource_query | `/api/datasources/proxy/5372` | POST | `grafana_datasource_query_summary` | candidate_only | P2-monitoring | trend/dashboard source | monitoring / aggregate trend | dashboard uid/query refs if sanitized | HAR path confirmed; raw datasource query body intentionally not stored | aggregate summary only if implemented | false | false | add only as explicit monitoring source with query allowlist |
| Grafana | dashboard_read | `/api/dashboards/uid/_KNf1DMMz` | GET | `grafana_dashboard_summary` | candidate_only | P2-monitoring | dashboard metadata/read-only panels | monitoring context | dashboard uid, panel ids | HAR path confirmed | config-heavy response | false | false | inventory only until a dashboard allowlist exists |
| Product Studio / Kconf / Permission Config | product_studio_config | `/dp/da/product/studio/page-func/config/list`, `/dp/da/product/studio/v3/page/list/query_by_kpn` | POST | `product_studio_config_lookup` | candidate_only | P3-config | product config context | config helper only | `envId`, `funcIds`, `language`, `pageIds`, `userName`, `kpn`, `env` | HAR-confirmed body keys | config domain, not evidence source | false | false | keep out of default runtime |
| Product Studio / Kconf / Permission Config | kconf_read | `/dp/da/product/studio/kconf/config`, `/api/kconf` | GET/POST | `kconf_config_lookup` | candidate_only | P3-config | readonly config context | config helper only | `key`, `type`, `stage` | HAR-confirmed query/body keys; key namespace allowlist needed | config response can be sensitive | false | false | require key allowlist and minimization before action |
| Product Studio / Kconf / Permission Config | permission_write_or_admin | admin/write permission paths | POST/PUT | none | not_supported | denied | writes/admin ops | not runtime evidence | not exposed | write/admin operation | not supported | false | false | do not implement |

## Candidate / Blocker Closures In This Pass

### Browser-backed service parity

Local inspection of the adjacent `browser-backed-api-poc` action allowlist and
the Dennis Python client now shows parity for the fixed actions v1 closure
batch:

- `login_logs_search`
- `track_analysis_check_data_ready`
- `archives_user_profile`
- `archives_user_analysis`
- `archives_photo_search`
- `archives_related_users`
- `rcp_event_detail`
- `rcp_event_feature_list`
- `rcp_policy_tree_lookup`

The service continues to expose the original base actions
`rcp_snapshot`, `weapon_inventory`, and `track_analysis_summary` as well. This
parity only means the action names, typed-param contracts, and fixed
service-side paths are registered consistently. It does not promote any action
to default runtime routing, and callers still cannot pass arbitrary URL, path,
header, cookie, token, or session fields.

### RCP / Tianshi config and helper candidates

Safe HAR shape inspection confirmed several RCP/Tianshi helper paths, but they
remain `candidate_only` or `not_supported` because they are config-heavy,
debug-oriented, or need stricter output minimization before becoming source
cards:

- Event option lookup: `/v2/rest/basicInfo/getEventTypeListByPage` and
  `/v2/rest/event/getEventLabelAndType`.
- Realtime operation lookup: `/v2/rest/event/realTimeOpList` and
  `/v2/rest/basicInfo/getRealtimeOpList`.
- Selected feature lookup: `/v2/rest/fc/getEventFeatureInfoByKeys`; raw feature
  values must stay suppressed before any action is added.
- Event tree / decision context:
  `/v2/rest/event/rcpEventTreeOrDecision`; raw tree dumps must stay suppressed.
- Policy search helpers:
  `/v2/rest/pro/policy/policySearch`,
  `/v2/rest/pro/policy/policyBlurSearch`.
- Policy release-record lookup is now `implemented_mock_only` because
  `/v2/rest/common/pipeline/selectInfo` and
  `/v2/rest/common/pipeline/list` have clear governance semantics and safe
  summary-only output.
- Policy tree asset lookup is now represented as one service-owned
  `rcp_policy_tree_lookup` contract over four fixed readonly paths:
  `/v2/rest/pro/policyTree/policyTreeList` for coarse list context,
  `/v2/rest/pro/policyTree/queryProPolicyTree` for precise node resolution,
  `/v2/rest/pro/policyTree/queryBindingByNodeCode` for node-level bound policy
  list, and `/v2/rest/pro/policyTree/getAllPolicyCodeByPage` for full-tree
  policy code coverage. Raw tree/list/binding bodies stay suppressed.
- Raw expression dependency resolution is `not_supported` for runtime source
  actions because it requires submitting raw policy expression content.

### Track Analysis auxiliary readiness/config

`track_analysis_check_data_ready` is now a registered browser-backed fixed
action with `live_smoke_verified` status. The original safe HAR shape
inspection confirmed `POST
/dp/platform/app/analytics/v2/sequence/checkDataReady`, body keys
`appName/startTime/endTime/include/pageSize/deviceId/batchQueryId/appPlatform/category/event/metric/product/type/funcType/_t`,
and response shape `code/message/data.dateStatus/traceId`. It is
readiness/provenance only, not account-security evidence, and it is not part of
the default source chain. The service must generate `batchQueryId` and `_t`;
Dennis must not pass caller URL/path/header/cookie/token/session or output raw
readiness body / traceId value.

`track_analysis_config_lookup` remains `candidate_only` / config helper. It is
not evidence and is not part of the default account-security source chain.

### Login Logs detail and pagination

`login_log_detail_lookup` is `blocked_missing_har`. Existing run logs validate
readonly UI modal key extraction for special-event and multi-account-login
details, but they do not expose a fixed API path/body or row identifier
contract that can safely become a browser-backed fixed action.

`login_log_filter_options` is also `blocked_missing_har`. The readonly POC
confirms `recallSource=2,0,1,3` as the default source scope for
`/rest/unified/log/search`, but no separate fixed filter/config option request
is present in the current safe evidence set.

`login_logs_search_page` is not supported as a standalone action in the current
evidence set. The v2.4.10 GET-only API POC records that `/rest/unified/log/search`
returned `totalCount == logSearchModels.length` and UI page changes did not
trigger a new search request; pagination is frontend-only for that validated
shape. The existing `login_logs_search` action covers the current-window API
result. Revisit only if a future safe HAR shows `logSearchModels.length <
totalCount` plus a real page/offset/cursor/searchAfter parameter contract.

## Mock-Only Actions Added In This Inventory Pass

### `track_analysis_check_data_ready`

```yaml
fixed_path: /dp/platform/app/analytics/v2/sequence/checkDataReady
typed_params:
  device_id: "<device risk entity id>"
  appName: KUAISHOU
  product: KUAISHOU
  startTime: <millisecond timestamp>
  endTime: <millisecond timestamp>
  include: 1
  pageSize: 100
  category:
    - "<safe category label>"
  event: []
  appPlatform: []
  metric: pv
  type: deviceId
service_side_body_builder:
  method: POST
  body_fields:
    - appName
    - startTime
    - endTime
    - include
    - pageSize
    - deviceId
    - batchQueryId
    - appPlatform
    - category
    - event
    - metric
    - product
    - type
    - funcType
    - _t
  service_generated_fields:
    - batchQueryId
    - _t
  fixed_fields:
    funcType: USER_PROFILE_QUERY
    type: deviceId
normalizer:
  source_card: track_analysis_check_data_ready_summary
  source_quality:
    track_analysis_action_contract: track_analysis_check_data_ready
    raw_readiness_body_suppressed: true
    trace_id_value_suppressed: true
    readiness_not_evidence: true
```

### `rcp_event_detail`

```yaml
fixed_path: /v2/rest/event/rcpEventDetail
typed_params:
  eventType: "<event type>"
  eventId: "<event id>"
  queryTime: <exact _occurTime ms>
service_side_body_builder:
  method: GET
  query_fields:
    - eventType
    - eventId
    - queryTime
normalizer:
  source_card: event_detail_summary
  source_quality:
    rcp_action_contract: rcp_event_detail
    raw_detail_body_suppressed: true
    strategy_event_not_final_judgement: true
```

### `rcp_event_feature_list`

```yaml
fixed_path: /v2/rest/event/rcpEventFeatureList
typed_params:
  eventType: "<event type>"
  eventId: "<event id>"
  queryTime: <exact _occurTime ms>
  featureGroup: ""
service_side_body_builder:
  method: GET
  query_fields:
    - eventType
    - eventId
    - queryTime
    - featureGroup
normalizer:
  source_card: feature_snapshot_summary
  source_quality:
    rcp_action_contract: rcp_event_feature_list
    raw_feature_values_suppressed: true
    strategy_feature_snapshot_not_final_judgement: true
```

### `rcp_policy_version_lookup`

```yaml
fixed_path: /v2/rest/pc/policy/getPolicyVersionListByEvent
typed_params:
  eventType: "<event type>"
  eventId: "<event id>"
  policyCode: "<policy code>"
  policyVersion: <positive int>
  queryTime: <exact _occurTime ms>
service_side_body_builder:
  method: GET
  query_fields:
    - eventType
    - eventId
    - policyCode
    - policyVersion
    - queryTime
normalizer:
  source_card: policy_version_summary
  source_quality:
    rcp_action_contract: rcp_policy_version_lookup
    raw_policy_version_body_suppressed: true
    policy_version_not_final_judgement: true
```

### `rcp_policy_detail_lookup`

```yaml
fixed_path: /v2/rest/pro/policy/getPolicyDetailByVersion
companion_readonly_paths:
  - /v2/rest/pro/policy/getPolicyAllVersion
  - /v2/rest/pc/policyReview/getRelationPolicyTree
typed_params:
  policyCode: "<policy code>"
  policyVersion: <positive int>
service_side_body_builder:
  method: GET
  query_fields:
    - policyCode
    - policyVersion
normalizer:
  source_card: policy_detail_summary
  source_quality:
    rcp_action_contract: rcp_policy_detail_lookup
    raw_policy_detail_body_suppressed: true
    raw_condition_expression_suppressed: true
    policy_detail_not_final_judgement: true
```

### `rcp_policy_release_record_lookup`

```yaml
fixed_path: /v2/rest/common/pipeline/list
companion_readonly_paths:
  - /v2/rest/common/pipeline/selectInfo
typed_params:
  policyCode: "<policy code>"
  statusCode: ""
  page: 1
  size: 20
service_side_body_builder:
  method: POST
  body_fields:
    - configCode
    - createUser
    - extrbA
    - extrbB
    - extrbC
    - pageInfoRequest
    - statusCode
  field_mapping:
    extrbB: policyCode
    statusCode: statusCode
    pageInfoRequest.page: page
    pageInfoRequest.size: size
  service_owned_fields:
    - configCode
    - createUser
    - extrbA
    - extrbC
normalizer:
  source_card: release_record_summary
  source_quality:
    rcp_action_contract: rcp_policy_release_record_lookup
    raw_release_records_suppressed: true
    operator_identity_suppressed: true
    release_record_not_final_judgement: true
    pipelineVersion_not_policy_version: true
```

### `rcp_policy_tree_lookup`

```yaml
fixed_path: /v2/rest/pro/policyTree/queryProPolicyTree
companion_readonly_paths:
  - /v2/rest/pro/policyTree/policyTreeList
  - /v2/rest/pro/policyTree/queryBindingByNodeCode
  - /v2/rest/pro/policyTree/getAllPolicyCodeByPage
typed_params:
  policyTreeCode: "<policy tree code>"
  policyTreeVersion: <positive int>
  targetPolicyCode: "<optional policy code>"
service_side_body_builder:
  method: GET
  query_fields:
    - policyTreeCode
    - policyTreeVersion
    - targetPolicyCode
  policyTreeList_role: coarse filter/list only
  queryBindingByNodeCode_role: node-level bound policy list; requires resolved policyTreeNodeCode
  getAllPolicyCodeByPage_role: full-tree policy code list
  node_resolution: service recursively parses queryProPolicyTree result
normalizer:
  source_card: policy_tree_summary
  source_quality:
    rcp_action_contract: rcp_policy_tree_lookup
    raw_policy_tree_body_suppressed: true
    raw_node_binding_list_suppressed: true
    raw_all_policy_code_list_suppressed: true
    policyTreeList_is_coarse_filter: true
    policy_tree_not_final_judgement: true
  forbidden_wrong_path: /v2/rest/pc/policytree/getPolicyTreeByVersion
```

### `rcp_node_policy_attribution`

```yaml
fixed_path: /v2/rest/pc/policy/nodePolicyAttribution
typed_params:
  eventType: "<event type>"
  eventId: "<event id>"
  policyCode: "<policy code>"
  policyVersion: <positive int>
  queryTime: <exact _occurTime ms>
  region: china
  type: ""
service_side_body_builder:
  method: POST
  body_fields:
    - eventType
    - eventId
    - policyCode
    - policyVersion
    - queryTime
    - region
    - type
normalizer:
  source_card: policy_attribution_summary
  source_quality:
    rcp_action_contract: rcp_node_policy_attribution
    raw_condition_dump_suppressed: true
    raw_feature_values_suppressed: true
    policy_attribution_not_final_judgement: true
```

### `rcp_node_bind_policy_attribution`

```yaml
fixed_path: /v2/rest/pc/policy/nodeBindPolicyAttribution
typed_params:
  eventType: "<event type>"
  eventId: "<event id>"
  queryTime: <exact _occurTime ms>
  policyTreeCode: "<policy tree code>"
  policyTreeVersion: <positive int>
  policyTreeNodeCode: "<resolved node code>"
service_side_body_builder:
  method: GET
  query_fields:
    - eventType
    - eventId
    - queryTime
    - policyTreeCode
    - policyTreeVersion
    - policyTreeNodeCode
  policyTreeNodeCode_rule: must come from queryProPolicyTree parser
normalizer:
  source_card: node_binding_summary
  source_quality:
    rcp_action_contract: rcp_node_bind_policy_attribution
    raw_node_binding_body_suppressed: true
    raw_condition_dump_suppressed: true
    node_binding_attribution_not_final_judgement: true
```
