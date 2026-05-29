# Browser-Backed Live Smoke Readiness v1

## Purpose

Classify HAR-derived browser-backed fixed actions before any live smoke. This
document is a readiness matrix only: it does not run live smoke, does not access
real platforms, and does not change default runtime routing.

## Global Boundary

- `default_runtime_routing=false` for every action below.
- `live_verified=false` for every action below.
- `needs_explicit_action_call=true` for every action outside an explicitly
  selected source plan.
- Caller-provided URL/path/header/cookie/token/session is forbidden.
- Raw HAR headers, cookies, tokens, sessions, full response bodies, full
  `requestParam`, and full `extraParam` are forbidden.
- Risk entity identifiers such as `user_id`, `device_id`, `ip`, `event_id`,
  `strategy_id`, `photo_id`, and `live_id` are evidence indices for internal
  review/source chaining and are not PII by default.
- Cookie/token/session/header/password, full phone number, ID card, real name,
  and detailed address remain forbidden output.

## Readiness Tier Definitions

| tier | meaning |
| --- | --- |
| `live_smoke_ready` | Fixed path, typed params, body builder, mock fixture, normalizer, and output boundary are clear enough for a minimal controlled live smoke. |
| `conditional_ready` | Minimal live smoke is possible, but enum meaning, field semantics, companion-path behavior, or upstream prerequisite fields still need confirmation. |
| `contract_only` | Keep as contract/inventory for now; not urgent for live smoke because value is governance/config/helper context or not single-case evidence. |
| `not_ready` | Missing fixed path/body, unstable semantics, or output minimization not ready. Do not live smoke yet. |
| `not_supported` | Write/export/high-risk/noise/config dump. Do not implement or smoke. |

## Platform Tier Counts

Counts are by unique action contract where possible. Companion policy-tree rows
are rolled into `rcp_policy_tree_lookup`.

| platform | live_smoke_ready | conditional_ready | contract_only | not_ready | not_supported |
| --- | ---: | ---: | ---: | ---: | ---: |
| Archives Center | 4 | 2 | 0 | 1 | 0 |
| RCP / Tianshi | 4 | 3 | 5 | 2 | 2 |
| Track Analysis | 2 | 0 | 1 | 0 | 0 |
| Weapon | 1 | 0 | 0 | 1 | 1 |
| Login Logs | 1 | 0 | 0 | 2 | 2 |
| Grafana | 0 | 0 | 2 | 0 | 0 |
| Product Studio / Kconf / Permission Config | 0 | 0 | 2 | 0 | 1 |

## Recommended First Live Smoke Batch

This is the first batch for newly HAR-derived optional contracts. The four base
actions (`track_analysis_summary`, `rcp_snapshot`, `weapon_inventory`,
`login_logs_search`) remain separately live-smoke-ready but are not included in
this optional-action batch.

| order | action_name | platform | minimum live params | reason |
| ---: | --- | --- | --- | --- |
| 1 | `archives_user_analysis` | Archives Center | `user_id`, `beginTime`, `endTime`, `pageIndex=1`, `pageSize<=20` | Highest account-baseline evidence value. |
| 2 | `archives_user_profile` | Archives Center | `user_id` | Smallest profile baseline smoke surface. |
| 3 | `archives_photo_search` | Archives Center | `user_id`, `begin`, `end`, `page=1`, `count<=20` | Valuable for abnormal publish/content-report chains. |
| 4 | `archives_related_users` | Archives Center | `user_id`, `relation_type=same_device_registered` or `same_device_login` | Validates relation graph body mapping. |
| 5 | `rcp_event_detail` | RCP / Tianshi | `eventType`, `eventId`, exact `queryTime` | Required to anchor exact `_occurTime` and event context. |
| 6 | `rcp_event_feature_list` | RCP / Tianshi | `eventType`, `eventId`, exact `queryTime`, fixed `featureGroup=""` | Validates raw-feature suppression and feature-group summary. |
| 7 | `rcp_policy_tree_lookup` | RCP / Tianshi | `policyTreeCode`, `policyTreeVersion`, optional `targetPolicyCode` | Validates strategy asset chain; not an event hit path. |
| 8 | `track_analysis_check_data_ready` | Track Analysis | `device_id`, `startTime`, `endTime`, `appName`, `product`, category/event/platform filters | Low-risk readiness/provenance helper. |

## Archives Center

| action_name | platform | current_status | priority | evidence_value | live_smoke_readiness | readiness_reason | required_live_params | expected_response_shape | normalizer_risk | field_semantics_risk | safe_to_smoke_test | default_runtime_routing | live_verified | next_step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `archives_user_analysis` | Archives Center | implemented_mock_only | P0 | Core account operation timeline. | live_smoke_ready | Fixed POST path/body, typed params, fixture, source_card/source_quality, and raw-body suppression are in place. | `user_id`, `beginTime`, `endTime`, `pageIndex`, `pageSize`, optional operation filters. | Summary counts/time/device/IP/status from `/v3/user/log/coreLogs/fetch`. | low | low | true | false | false | First-batch smoke candidate. |
| `archives_photo_search` | Archives Center | implemented_mock_only | P0-conditional | Abnormal publish/content/report anchoring. | live_smoke_ready | `reportedIds=user_id` body mapping is fixed and fixture covers summary-only output. | `user_id`, `begin`, `end`, `page`, `count`, `matchType`, `sort`. | Count/time/status/report context from `/v4/archives/report/photo/search`. | low | low-medium | true | false | false | First-batch smoke candidate when publish/report evidence matters. |
| `archives_user_profile` | Archives Center | implemented_mock_only | P0/P1-high | Current account baseline/profile status. | live_smoke_ready | Single typed `user_id` GET path; profile summary suppresses raw body. | `user_id`. | Current-state profile fields from `/archives/user/home/info`. | low | low | true | false | false | First-batch smoke candidate. |
| `archives_related_users` | Archives Center | implemented_mock_only | P1 | Same-device related-user expansion. | live_smoke_ready | Fixed POST path/body and enum mapping `type=0/1` are covered by fixture. | `user_id`, `relation_type=same_device_registered|same_device_login`. | Related-user counts/types from `/archives/user/search/device`. | low | medium | true | false | false | First-batch smoke candidate; relation is candidate evidence, not judgement. |
| `archives_private_message_search` | Archives Center | implemented_mock_only | P2-conditional | Private-message metadata count/status/time clue. | conditional_ready | Path/body are fixed, but direction/status semantics should be confirmed live before use. | `user_id`, `direction=sent|received`, `page`, `count`, `status`, `sort`. | Count/time/status/counterpart metadata from `/archives/user/message/search`; plaintext suppressed. | medium | high | true | false | false | Keep optional; smoke only after P0 Archives actions pass. |
| `archives_past_four_items` | Archives Center | implemented_mock_only | P2-conditional | Profile-change metadata clue. | conditional_ready | Path/body are fixed, but `infoType`, mark/punish status semantics should be confirmed live. | `user_id`, `info_type`, `page`, `count`, `markResult`, `punishResult`. | Count/time/type/status summary from `/v4/audit/user/fourinfo/log/search`; old/new content suppressed. | medium | high | true | false | false | Keep optional; smoke only after profile baseline passes. |

## RCP / Tianshi

| action_name | platform | current_status | priority | evidence_value | live_smoke_readiness | readiness_reason | required_live_params | expected_response_shape | normalizer_risk | field_semantics_risk | safe_to_smoke_test | default_runtime_routing | live_verified | next_step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `rcp_snapshot` | RCP / Tianshi | implemented_mock_only | P0-explicit | Strategy hit/event entry summary. | live_smoke_ready | Existing base browser-backed action with fixture and standard source_card. | Existing typed event/entity params and service-owned body. | Event count/dynamic-column summary from `/v2/rest/event/eventList`. | low | medium | true | false | false | Base action smoke candidate outside optional batch. |
| `rcp_event_detail` | RCP / Tianshi | implemented_mock_only | P0-explicit | Single-event detail and exact `_occurTime`. | live_smoke_ready | Fixed GET path/params and fixture cover event detail summary. | `eventType`, `eventId`, exact `queryTime`. | Feedback/error/effective-policy/entities from `/v2/rest/event/rcpEventDetail`. | low | medium | true | false | false | First-batch smoke candidate. |
| `rcp_event_feature_list` | RCP / Tianshi | implemented_mock_only | P1-explicit | Event feature snapshot summary. | live_smoke_ready | Fixed `featureGroup=""`; non-empty group rejected; raw values suppressed. | `eventType`, `eventId`, exact `queryTime`, fixed `featureGroup=""`. | Feature count/group/key summary from `/v2/rest/event/rcpEventFeatureList`. | medium | medium | true | false | false | First-batch smoke candidate after event detail. |
| `rcp_policy_tree_lookup` | RCP / Tianshi | implemented_mock_only | strategy_governance | Policy-tree asset/node resolution, not event hit path. | live_smoke_ready | HAR confirms precise tree path and companion asset paths; node code resolution is service-owned. | `policyTreeCode`, `policyTreeVersion`, optional `targetPolicyCode`. | Tree node summary plus optional binding/code-list counts from `queryProPolicyTree`, `policyTreeList`, `queryBindingByNodeCode`, `getAllPolicyCodeByPage`. | medium | medium | true | false | false | First-batch smoke candidate for strategy asset governance only. |
| `rcp_policy_version_lookup` | RCP / Tianshi | implemented_mock_only | P1-explicit | Policy version provenance for event attribution. | conditional_ready | Path/params are fixed, but policy-version semantics should be confirmed against real event snapshots. | `eventType`, `eventId`, `policyCode`, `policyVersion`, exact `queryTime`. | Version-found summary and policy metadata from `/v2/rest/pc/policy/getPolicyVersionListByEvent`. | medium | high | true | false | false | Smoke after `rcp_event_detail` provides a valid event/policy tuple. |
| `rcp_node_policy_attribution` | RCP / Tianshi | implemented_mock_only | P1-explicit | Condition-level attribution, not final judgement. | conditional_ready | Fixed POST body and raw-condition suppression exist; condition semantics require live confirmation. | `eventType`, `eventId`, `policyCode`, `policyVersion`, exact `queryTime`, `region`, fixed `type=""`. | True/false condition counts and error-feature summary from `/v2/rest/pc/policy/nodePolicyAttribution`. | medium | high | true | false | false | Smoke only with a known representative event/policy tuple. |
| `rcp_node_bind_policy_attribution` | RCP / Tianshi | implemented_mock_only | strategy_governance | Node-level binding attribution/context. | conditional_ready | Fixed path is clear but requires a node code resolved by `queryProPolicyTree`. | `eventType`, `eventId`, exact `queryTime`, `policyTreeCode`, `policyTreeVersion`, resolved `policyTreeNodeCode`. | Node binding summary and target policy status from `/v2/rest/pc/policy/nodeBindPolicyAttribution`. | medium | high | true | false | false | Smoke only after `rcp_policy_tree_lookup` resolves node code. |
| `rcp_policy_detail_lookup` | RCP / Tianshi | implemented_mock_only | strategy_governance | Policy definition/version/binding-tree context. | contract_only | Useful governance contract, but not urgent first live smoke and not single-case evidence. | `policyCode`, `policyVersion`. | Condition/version/tree counts from `/v2/rest/pro/policy/getPolicyDetailByVersion`; raw expressions suppressed. | medium | high | true | false | false | Keep as explicit governance follow-up. |
| `rcp_policy_release_record_lookup` | RCP / Tianshi | implemented_mock_only | strategy_governance | Policy lifecycle/release provenance. | contract_only | Lifecycle context; not single-event attribution and not risk judgement. | `policyCode`, optional `statusCode`, `page`, `size`. | Record/status/version summaries from `/v2/rest/common/pipeline/list`; operator identities suppressed. | medium | high | true | false | false | Keep as explicit governance follow-up. |

## Track Analysis

| action_name | platform | current_status | priority | evidence_value | live_smoke_readiness | readiness_reason | required_live_params | expected_response_shape | normalizer_risk | field_semantics_risk | safe_to_smoke_test | default_runtime_routing | live_verified | next_step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `track_analysis_summary` | Track Analysis | implemented_mock_only | P0 | Activity/profile/device bundle. | live_smoke_ready | Existing base action expands four subinterfaces and fixture covers source summary. | `user_id`, `appName`, `mode`, optional sub-interface controls. | Four-subinterface summary for profile/use-duration/device/latest. | low | medium | true | false | false | Base action smoke candidate outside optional batch. |
| `track_analysis_check_data_ready` | Track Analysis | implemented_mock_only | P2-helper | Data readiness/source-quality provenance only. | live_smoke_ready | Fixed POST body keys from HAR; service generates `batchQueryId` and `_t`; trace value suppressed. | `device_id`, `appName`, `product`, `startTime`, `endTime`, `category`, `event`, `appPlatform`, `metric`, fixed `type=deviceId`. | `code/message/data.dateStatus/traceId` presence from `/dp/platform/app/analytics/v2/sequence/checkDataReady`. | low | medium | true | false | false | First-batch optional smoke candidate; never count as completed account-security evidence. |

## Weapon

| action_name | platform | current_status | priority | evidence_value | live_smoke_readiness | readiness_reason | required_live_params | expected_response_shape | normalizer_risk | field_semantics_risk | safe_to_smoke_test | default_runtime_routing | live_verified | next_step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `weapon_inventory` | Weapon | implemented_mock_only | P0/P0-conditional | User-device graph and conditional device risk. | live_smoke_ready | Existing base action with fixed `graphData` and conditional `riskData` paths. | `user_id`; device risk only when graph/login/publish/track source yields a raw device reference. | Graph/risk labels and safe handles from `/apiv2/graphData` and `/apiv2/riskData`. | low | medium | true | false | false | Base action smoke candidate outside optional batch. |

## Login Logs

| action_name | platform | current_status | priority | evidence_value | live_smoke_readiness | readiness_reason | required_live_params | expected_response_shape | normalizer_risk | field_semantics_risk | safe_to_smoke_test | default_runtime_routing | live_verified | next_step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `login_logs_search` | Login Logs | implemented_mock_only | P0 | Online login-log reliable window. | live_smoke_ready | Existing base action with fixed `/rest/unified/log/search` and `recallSource=2,0,1,3`. | `user_id`, reliable online window, `recallSource=2,0,1,3`. | Count/window/IP/device/method summary from `/rest/unified/log/search`. | low | medium | true | false | false | Base action smoke candidate outside optional batch. |

## Contract-Only And Not-Ready Closures

| platform | inventory item | readiness_layer | reason | next_step |
| --- | --- | --- | --- | --- |
| Archives Center | `archives_related_devices` | not_ready | No standalone fixed path/body; may be derived from profile/user-analysis/device summaries. | Keep blocker until safe HAR confirms a standalone source. |
| RCP / Tianshi | `rcp_event_type_list` | contract_only | Config option lookup, not evidence. | Keep inventory-only unless explicit config lookup is required. |
| RCP / Tianshi | `rcp_realtime_op_list` | contract_only | Config option lookup, not evidence. | Keep inventory-only unless explicit config lookup is required. |
| RCP / Tianshi | `rcp_event_feature_key_lookup` | not_ready | Raw feature values require stronger minimization before action. | Define value-suppression normalizer first. |
| RCP / Tianshi | `rcp_event_tree_or_decision_lookup` | not_ready | Response semantics/tree dump minimization not source-card ready. | Summarize tree/decision shape before action. |
| RCP / Tianshi | `rcp_policy_search_lookup` | contract_only | Policy discovery helper; config-heavy and not evidence. | Require explicit governance use case. |
| RCP / Tianshi | expression dependency | not_supported | Requires raw policy expression body/config dump. | Do not implement. |
| RCP / Tianshi | test case/config paths | not_supported | Test/write-like execution boundary. | Do not implement. |
| Track Analysis | `track_analysis_config_lookup` | contract_only | Config helper only, not evidence. | Keep inventory-only. |
| Weapon | `weapon_graph_aux_lookup` | not_ready | No clear additional graph/risk endpoint needed. | Implement only if device graph/risk HAR appears. |
| Weapon | Weapon UI/config/static paths | not_supported | Page/config only, not evidence. | Do not implement. |
| Login Logs | `login_log_detail_lookup` | not_ready | UI modal detail shape observed, but no fixed API path/body contract. | Capture safe HAR request if it exists. |
| Login Logs | `login_log_filter_options` | not_ready | No fixed filter/config option path beyond default `recallSource`. | Capture safe HAR path if one exists. |
| Login Logs | pagination frontend | not_supported | Current evidence shows frontend-only pagination for validated shape. | Revisit only if API exposes page/offset/cursor. |
| Login Logs | export/download | not_supported | Bulk export/high-risk operation. | Do not implement. |
| Grafana | datasource/dashboard reads | contract_only | Monitoring/trend context, not single-case evidence. | Require dashboard/query allowlist before action. |
| Product Studio / Kconf / Permission Config | product studio / kconf reads | contract_only | Config domain; not default runtime evidence. | Require key/page allowlist and minimization before action. |
| Product Studio / Kconf / Permission Config | permission write/admin | not_supported | Write/admin operation. | Do not implement. |

## This Pass Decision

No new mock-only action is added in this pass. `archives_related_devices`,
login-log detail/filter options, and the remaining RCP helper candidates do not
yet meet the path/body/semantics/minimization bar for a new fixed action.
