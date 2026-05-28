# Platform Call Playbook Index

This index is the mandatory preflight reading list before Dennis Risk Agent calls any realtime readonly source. If memory retrieval fails, fall back to this file and the referenced playbooks instead of guessing platform behavior.

## Global Rules

- Realtime readonly API calls do not require user confirmation when required fields are present.
- Platform Access Execution v0.1 contracts are indexed under `computer_use_poc/platform_access/`. Use them as execution contracts, not merely diagnosis notes.
- Classify failures in this order: runner invocation, runner dependency, base domain / endpoint contract, parameter contract, upstream id availability, same-origin context, path permission, then auth / permission.
- 先判调用链路，再判认证；先判参数契约，再判权限；先判局部 API，再判平台不可用。
- DataAgent / Hive / big batch / write / high-risk operations require query plan or explicit confirmation.
- DataAgent / Hive confirmation is per call. A previous "查吧 DataAgent" only authorizes that one query; every new SQL, table, time window, question, or evidence direction requires a new confirmation.
- Do not use old observations as "no-cache" realtime results.
- Every source call must produce a checkpoint and source_quality.
- `no_data`, `blocked`, `timeout`, and `auth_failed` are source states, not no-risk counter evidence.
- Browser UI is fallback, not default.

Plan-only diagnostic boundary:

- `plan_only_diagnostic` does not call platform sources. It can validate route/source design but cannot prove live auth, safeBins, runner availability, or API execution.
- Plan-only output still needs `routing_metadata` with `execution_mode=plan_mode_only`, `platform_called=false`, `dataagent_called=false`, and `reason_not_executed`.
- If the user explicitly asks for strategy hit, Tianshi strategy hit is an explicit target source in the plan.
- Strategy hit remains cross-validation only, not final ATO / cheating judgement.
- Browser is not P0 when API runner / API direct can answer.
- DataAgent/Hive remains per-call authorized even after a successful plan.
- Source priority and access method are separate: evidence value decides `source_priority`; execution path decides `access_method`. API direct first is a low-cost / stable collection preference among sources with equal evidence value, not the P0/P1/P2 criterion.
- Use `source_priority: P0 | P0-explicit | P0-conditional | P1 | P2 | conditional` and `access_method: api_direct | controlled_runner | browser_cookie_activation | same_origin_fetch | manual_gap | hive_authorized`.
- Non-API sources are not automatically downgraded. Archives user analysis and publish-chain evidence can be P0 even when their controlled access method is browser cookie activation / same-origin fetch.
- Browser is not a general fallback. It is allowed only when the source contract names it as the controlled access method and must keep `executor_agent=dennis-risk-agent`, `main_direct_tool_bypass=false`, readonly mode, checkpointing, timeout, and source_quality fallback.

ATO time_window_inference:

- Before executing the ATO source plan, infer candidate windows from user input and P0 anchors instead of using the latest 7 days as the only window.
- Candidate anchors: `user_report_time`, `archive_user_analysis_time`, `audit_log_time`, `publish_time`, `publish_device_time`, `strategy_hit_time`, `login_event_time`, `device_first_seen_time`, `frontend_activity_time`.
- Audit reason guides investigation direction and time windows only; it is not ATO judgement.
- Abnormal publish / traffic-diversion content makes publish time and publish device P0 anchors. Look backward for login, scan/OAuth, device switch, token/session, and strategy hit; look forward for audit, punishment, and complaint.
- Login-log online window gaps must become `login_log_window_incomplete` / `offline_hive_required`; Hive still requires per-call user authorization.

## Platform Capability Status Taxonomy

Do not use a binary "API direct / non API direct" classification. Every platform source must be labeled with one of the following capability statuses:

- `api_direct_confirmed`: HTTP + SSO / controlled cookie-state can call a structured API directly. Highest priority. Examples: unified login log runner, Weapon `graphData` / `riskData`, track-analysis `profile` / `getUseDuration` / `getDeviceIds` / `getLastestDateTime`, Tianshi `fastQueryHbase`.
- `same_origin_api_confirmed`: API is structured but requires browser / SPA auth activation before same-origin fetch. Priority is lower than API direct and higher than DOM. Example: Archives Center partially validated same-origin APIs after profile SPA activation.
- `partial_api_direct`: API exists but depends on precise `eventId` / `sourceId` / `deviceId` / `eventType` / time-window context, or only some event types succeed while others timeout. Examples: RCP event detail and some Tianshi event drilldown paths.
- `pending_api_direct_confirmation`: API likely exists but is not stable enough to claim automatic read support. Examples: publish audit, long-window token / OAuth / passToken chains if not yet validated.

Capability status must be carried into `source_quality` or platform preflight when relevant.

## Low-cost Source Priority

When multiple sources can answer the same question, select the lowest-cost, most stable, most structured source first:

1. `api_direct_confirmed`
2. `same_origin_api_confirmed`
3. `partial_api_direct` with precise required fields
4. browser UI / DOM / selector observation
5. DataAgent / Hive for long-window, cross-table, offline history, or realtime window gaps

Routing rules:

- If API direct can answer, do not start with browser.
- If same-origin fetch can answer, do not parse DOM.
- If precise `sourceId` / `eventId` / `deviceId` / `eventType` can answer, do not broad-scan a large time window.
- If realtime readonly API can answer, do not call DataAgent / Hive first.
- If completed low-cost sources can support a partial evidence card, do not block the main conclusion on P1/P2 browser sources.
- DataAgent / Hive remains per-call authorized and is used for long-period history, cross-table joins, offline evidence, or realtime source-window gaps.

Boundary rules:

- Low-cost source `no_data`, `blocked`, `timeout`, or `auth_failed` is not a low-risk or no-risk conclusion.
- If source coverage is incomplete, mark `source_window_boundary`, `missing_evidence`, or `offline_hive_required`.
- If a later higher-quality source returns new evidence, recompute the conclusion with `conclusion_recompute_after_new_evidence`.
- When sources conflict, prefer the source with longer time window, fuller behavior chain, and closer raw behavior evidence. Strategy hits, model scores, and rule names remain cross-validation leads only.
- If API `no_data` conflicts with Hive abnormal evidence, do not keep the API-first initial judgement; explain that the online API window was shorter and Hive historical coverage is more complete.

## General Source Quality Semantics

These source states affect evidence quality only. They cannot directly become risk conclusions:

- `no_data`: queried source returned no records under current filters; not risk exclusion.
- `no_data_due_to_window`: source window does not cover target event time; requires offline or alternate source.
- `blocked`: permission, profile lock, or runtime boundary blocked the source; source gap only.
- `auth_failed`: authentication or session issue; not no-data.
- `timeout`: source did not finish in budget; not counter evidence.
- `parse_error`: response could not be parsed; source quality degraded.
- `partial_source`: some fields or pages were read, but key fields are missing.
- `stale_source`: old observation or cache; cannot satisfy no-cache realtime request.

Any answer using these states must reflect them in `source_quality`, `missing_evidence`, and conclusion confidence.

## Platform Access Execution v0.1

Reference contracts:

- `computer_use_poc/platform_access/platform_access_inventory_v0_1.yaml`
- `computer_use_poc/platform_access/observation_schema_v0_1.yaml`
- `computer_use_poc/platform_access/failure_taxonomy_v0_1.yaml`
- `computer_use_poc/platform_access/runner_invocation_contract_v0_1.md`
- `computer_use_poc/platform_access/browser_same_origin_adapter_contract_v0_1.md`
- `computer_use_poc/platform_access/tianshi_rcp_api_contract_v0_1.yaml`
- `computer_use_poc/platform_access/weapon_api_contract_v0_1.yaml`
- `computer_use_poc/platform_access/archives_center_contract_v0_1.yaml`
- `computer_use_poc/platform_access/track_analysis_api_contract_v0_1.yaml`

Every platform hand should return `platform_access_observation` or a source-specific card that can be losslessly mapped into it: `platform_key`, `source_name`, `api_name`, `invocation_method`, `input_entity_type`, `required_params`, `upstream_source`, `params_valid`, `source_status`, `records_count`, `schema_valid`, `output_fields_observed`, `failure_layer`, `source_quality`, `raw_reference_retained_for_followup`, `redaction_applied`, and `next_action`.

## Unified Login Log

Reference:

- `computer_use_poc/user_login_log_api_readonly_internal_agent_playbook_v2_4_10.md`
- `computer_use_poc/sso_session_runner.py`

Input:

- `user_id`
- optional `from_timestamp` / `to_timestamp`

Preferred path:

1. Use controlled runner:
   `python3 computer_use_poc/sso_session_runner.py --platform login_log --action query_user_login_log --user-id <user_id> --timeout 30 --format json`
2. If the first request returns HTTP 302, HTML login page, SSO login URL, access-proxy redirect, or `auth_failed`, the runner performs one controlled SSO refresh with its internally built whitelist URL.
3. After refresh, retry the same runner request once.
4. If refresh fails or the retry still returns auth failure, return structured `auth_failed`.
5. If SSO executor is unavailable, return structured `blocked`.
6. If timeout, return `timeout`.

Common errors:

- Missing `SmartSSOSession`: `blocked / sso_executor_unavailable`
- HTTP redirect / login page: `auth_failed / auth_session_issue`
- auth expired before refresh: `auth_failed_before_refresh`, then one controlled refresh and retry
- refresh script missing / failed: `auth_failed` or `blocked` with `auth_refresh_status=failed`
- JSON parse failure: `parse_error`
- Online window gap: `login_log_window_incomplete`

Fallback:

- Do not use curl+cookie.
- Do not let main agent take over.
- For long historical windows, generate Hive / DataAgent query plan only.

Source status mapping:

- JSON records returned: `completed`
- JSON no records: `no_data` with `no_data_not_risk_exclusion`
- SSO blocked or runner unavailable: `blocked` or `auth_failed`
- Request timeout: `timeout`
- Non-JSON response: `parse_error` or `auth_failed` if HTML/login-like.
- `auth_refresh_attempted`, `auth_refresh_status`, `retry_after_refresh`, and `source_status_before_refresh` must be present in runner output.

Capability status: `api_direct_confirmed`.

## Weapon

Reference:

- `computer_use_poc/entity_resolution_user_device_layer_v2_6_0.md`
- `computer_use_poc/device_sdk_foundation_internal_agent_playbook_v2_5_0.md`

Input:

- `user_id` for entity resolution.
- `device_id` for device risk.

Preferred path:

1. For Dennis runtime execution, use the controlled runner when available:
   - `python3 computer_use_poc/sso_session_runner.py --platform weapon --action graph_data --user-id {userId} --timeout 30 --format json`
   - `python3 computer_use_poc/sso_session_runner.py --platform weapon --action risk_data --device-id {deviceId} --timeout 30 --format json`
2. USER_ID to DEVICE_ID graph: `/apiv2/graphData?product=KUAISHOU&productName=KUAISHOU&groupValue={userId}&groupKey=USER_ID&dimKey=DEVICE_ID&searchLevel=2`.
3. DEVICE_ID to USER_ID graph: `/apiv2/graphData?product=KUAISHOU&productName=KUAISHOU&groupValue={deviceId}&groupKey=DEVICE_ID&dimKey=USER_ID&searchLevel=2`.
4. Device risk uses `/apiv2/riskData?product=KUAISHOU&deviceIds={deviceId}` only after a device id is available.

Hard rules:

- `/apiv2/graphData` and `/apiv2/riskData` are the default readonly API paths.
- The runner must not accept arbitrary URL input and must not open the Weapon frontend.
- Runner output must include `source_card`, `source_quality`, `response_type`, `records_count`, `real_platform_request_executed`, and redaction markers.
- Do not use `/api/graphData` as default execution guidance.
- Do not strip mobile device prefixes such as `ANDROID_` or `IOS_` before calling Weapon riskData. Preserve the observed device id string unless a validated platform contract explicitly says otherwise.
- Do not switch to arbitrary frontend or guessed API paths when `/apiv2/*` returns `auth_failed`, `blocked`, or `timeout`; record the source status and continue the evidence card.
- In single-user account security / ATO / login anomaly cases, Weapon graphData is a P0 user-to-device resolution source. Weapon riskData is conditional on a deviceId resolved from graphData, login log, publish chain, track-analysis, or another current-task source. Login log `no_data` does not end the judgement.

Common errors:

- Treating `user_id` as `device_id` in riskData.
- Using riskData for entity resolution.
- Treating graph no relation as no risk.
- Treating Weapon graphData count `0` as "user has no device". It only means the Weapon graph source currently returned no relation edge. Use track-analysis `getDeviceIds` as a cross-source device candidate supplement, then mark `cross_source_device_id=true` if the device id is used for Weapon riskData.

Fallback:

- If graphData blocked, mark `blocked_sources`.
- If device id missing, mark `missing_required_fields`.
- If `/apiv2/*` auth fails, times out, or is blocked, mark `auth_failed_sources`, `timeout_sources`, or `blocked_sources`; do not silently replace it with `/api/graphData`.

Source status mapping:

- graphData relation found: `completed`
- no relation found: `no_data` with relation boundary.
- auth / permission issue: `blocked` or `auth_failed`
- timeout: `timeout`

Capability status: `api_direct_confirmed` for validated `/apiv2/graphData` / `/apiv2/riskData` readonly paths.

Runner wrapper:

- Preferred child-agent entry: `computer_use_poc/bin/sso_session_runner`.
- The wrapper handles dependency invocation. The agent should not construct ad hoc `python3 ...` or `uv ...` calls.
- Wrong runner path / missing dependency maps to `runner_invocation_error` / `runner_dependency_error`, not auth failure.

## Tianshi Strategy Platform

Reference:

- `computer_use_poc/strategy_governance/tianshi_strategy_governance_readonly_capability_v1.md`
- `computer_use_poc/strategy_governance/single_user_event_strategy_inventory_poc_v1.md`
- `computer_use_poc/strategy_governance/tianshi_policy_attribution_api_read_poc_v1.md`

Input:

- `source_id` for strategy hit inventory.
- `event_id`, `event_type`, `query_time`, `policy_code`, `policy_version` for single-event attribution.
- `device_id` only when the specific event/playbook requires device-level lookup.

Preferred path:

1. RCP realtime hit list: `POST /v2/rest/event/eventList` on `rcp.corp.kuaishou.com`.
2. Event detail: `GET /v2/rest/event/rcpEventDetail`.
3. Feature snapshot: `GET /v2/rest/event/rcpEventFeatureList` with `featureGroup=""` and exact `_occurTime`.
4. Policy version: `GET /v2/rest/pc/policy/getPolicyVersionListByEvent`.
5. Attribution: `POST /v2/rest/pc/policy/nodePolicyAttribution`.
6. Fallback / optional HBase: `GET /v2/rest/pc/event/fastQueryHbase` on `rcp.corp.kuaishou.com`.

`eventList` input contract:

- Role: `primary_strategy_hit_entry`.
- Interface type: `query_conditions_plus_dynamic_columns`.
- Invocation context: `browser_same_origin`.
- Smoke ready: `true_for_browser_same_origin`.
- HTTP SSO direct: `optional_unverified`.
- Required: `eventType`, `timeRange`.
- Optional: `sourceIds`, `policyFilter`, `feedback`, `conditionGroups`, `tableHeaderList`, `customColumns`, `selectedColumns`, `featureList`, `pageInfo`, `eventV2`.
- Dynamic column params: `tableHeaderList: har_confirmed`; `customColumns: candidate_scenario_dependent`; `selectedColumns: candidate_scenario_dependent`; `featureList: candidate_scenario_dependent`.
- HAR-confirmed request body keys: `tableHeaderList`, `pageIndex`, `pageSize`, `eventV2`, `startTime`, `endTime`, `currentTime`.
- HAR-confirmed `eventV2` keys: `eventType`, `hitPolicies`, `version`, `status`, `snapshotVersion`, `sourceIds`, `realTimeOp`, `isPolicyTreeExperiment`, `conditionList`, `grayFeature`, `grayQueryStatus`, `region`.

HAR-confirmed `tableHeaderList` / response fields. These are observed dynamic fields, not a fixed output schema:

- default / core: `sourceId`, `eventId`, `_occurTime`, `_realTimeOp`, `_errorCode`, `_sideEffectOps`, `time`, `photoId`
- custom / evidence fields: `deviceId`, `hitFusePolicyCode`, `userRegisterIp`, `ipCity_zh`, `openId`, `appealPhoneModel`, `deviceClientEventLogCnt3h`, `deviceIdWeaponAndroidPluginBaseReportCnt`, `deviceIdWeaponLogCnt`, `weaponDataMap`, `weaponDecodeDataWeapon`

Custom policy-code, selected-column, and feature-list fields are scenario-dependent candidates when unobserved; do not mark the whole RCP chain unknown. If eventList lacks `policyCode`, `deviceId`, or strategy-detail fields, supplement via `rcpEventDetail`.

Common errors:

- Simple userId direct strategy query without sourceId/time window context.
- Confusing `hitTimestamp` with precise event `queryTime`.
- Treating strategy hit as final risk judgement.
- Treating `updateUser` or operator as responsibility attribution.
- Treating `fastQueryHbase` blocked as RCP/Tianshi unavailable.
- Calling detail / feature / attribution with `userId` instead of upstream `eventId/eventType/queryTime`.

Fallback:

- Missing sourceId/eventId/queryTime/policyCode/policyVersion becomes query plan, `missing_upstream_id`, or missing evidence.
- Timeout becomes `timeout_sources`, not no risk.

Source status mapping:

- hit overview returned: `completed`
- no hits: `no_data` with `strategy_hit_not_final_risk_judgement`
- missing fields: `skipped / missing_required_fields`
- timeout/auth/parse: `timeout`, `auth_failed`, `parse_error`

Capability status:

- `eventList`: primary source, `browser_same_origin` / partial API direct depending on runtime.
- `fastQueryHbase`: fallback / optional HBase source.
- Event detail / event drilldown: `partial_api_direct` when it depends on event type, exact event context, or has known timeout behavior.
- Do not generalize one successful event type into all event types.

## Archives Center

Reference:

- `computer_use_poc/archives_center_core_capability_map_v2_6_1.md`
- `computer_use_poc/archives_center_internal_agent_playbook.md`
- `computer_use_poc/browser_auth_preflight_checklist_v2_4_9.md`

Input:

- `user_id` for profile.
- `photo_id` / `liveStreamId` for content or live capabilities.

Preferred path:

1. Use the confirmed entry `https://admin.p.adm-corp.kuaishou.com` and SPA profile URL for the correct domain when browser auth activation is needed.
2. In a separate `archives_center_auth_activation_fix` / platform auth activation task, if `account.p.adm-corp.kuaishou.com` shows only a username input and the username is prefilled, known, or provided in the current conversation, fill it and click next. If password / QR / SMS / MFA appears, pause for manual SSO.
3. Save `archives_auth_state.json` after user SSO completes, then health check by closing browser, state loading `archives_auth_state.json`, opening the Archives user home page, confirming no login redirect, and same-origin fetching `/archives/user/home/info?userId=...` with HTTP 200 and `hasData=true`.
4. After same-origin is active, use API direct read such as `/archives/user/home/info?userId=...`.
5. Use DOM / selector only as fallback.

Latest recoverable preflight backport:

- `ARCHIVES-CENTER-BROWSER-ACTIVATION-PREFLIGHT-001` passed in live validation.
- `recoverable_preflight=completed`.
- Browser state was valid and directly entered Archives SPA.
- No SSO / `account.p` middle page appeared.
- No account identifier entry or next-step click was required.
- Profile page was reachable, so account baseline can be `completed`.
- Publish-chain / 视频作品集 tab was visible with seven video works.
- Visible publish-chain fields include video ID, upload time, play count, comment count, like count, collect count, and status.
- No credential material was output, no DataAgent/Hive was called, and no business risk judgement was made.

Preferred SPA entry:

- `/frontend/archives/index.html#/archives/user/profile?userId={userId}`

Wrong entry boundary:

- `/admin/search/user?keyword={userId}` can hit AMC/IP block.
- `wrong_entry_amc_blocked_not_platform_unavailable`: wrong entry blocked does not prove preferred SPA entry is unavailable.

SPA tab fallback:

- `.ks-tabs__item` click by agent-browser ref may not trigger Vue / ks-tabs state change.
- Try accessible click once.
- If selected state does not change, use DOM eval click by text content and call `HTMLElement.click()`.
- If still failed, try URL hash / route navigation when the contract has a registered route.
- If still failed, mark `tab_switch_failed`, not source unavailable.
- `publish_chain_visible=true` marks abnormal-publish P0-conditional source completed.
- If publish device is not visible, mark `missing_evidence`; do not mark publish-chain unavailable.

Common errors:

- Declaring Archives unavailable before recoverable preflight.
- Treating the `account.p.adm-corp.kuaishou.com` login page as IP whitelist failure without explicit AccessProxy / IP allowlist evidence.
- Re-asking for username that is already known or provided in the current conversation.
- Performing username entry / next click inside KNC, single-user, or batch business case execution instead of a separate auth activation task.
- Direct browser UI scraping before API direct read.
- Treating empty result as no risk or no behavior.
- Treating `tab_switch_failed` as Archives unavailable.
- Treating wrong-entry AMC/IP block as preferred SPA entry failure.
- Hardcoding Dennis environment account identifier for other users; `muguangwu` is an example only.

Fallback:

- `permission_blocked`, `response_shape_changed`, `key_fields_missing`, `link_url_only`, `mapping_pending_validation`, or `need_required_param` can trigger scoped fallback.
- Browser loops stop after three repeated failed actions.

Source status mapping:

- API JSON parsed: `completed` or `no_data`
- auth page / 2FA / redirect: `auth_failed`
- saved state redirects to `account.p`: `auth_state_expired` / `manual_sso_required`, not IP block
- profile lock or browser session issue: `blocked`
- SPA loop: `timeout` with `operation_loop_detected`
- browser timeout: `archives_browser_timeout`, not `auth_failed`
- tab switch fallback success: `tab_switch_completed`
- tab switch fallback failed: `tab_switch_failed`
- publish-chain visible: `publish_chain_visible`
- publish-chain not visible or missing fields: `publish_chain_missing` / `missing_evidence`

Capability status: `same_origin_api_confirmed_if_auth_ready` for validated APIs that require SPA / browser auth activation before same-origin fetch. Do not declare Archives unavailable before recoverable preflight; do not treat same-origin support as generic API direct. In business case execution, auth recovery is not performed inline; `account.p` redirect becomes `archives_auth_session_issue` and a remaining source gap.

## Track Analysis

Reference:

- `computer_use_poc/track_analysis_api_direct_contract_current.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`

Input:

- `user_id` or `device_id`
- `appName`: `KUAISHOU` or `NEBULA`

Preferred path:

1. API direct first, not SPA / DOM first.
2. Call `profile` first to read profile card, `deviceIds`, register time, fan distribution, and active-days bucket.
3. Call `getUseDuration` to read 30-day activity-day and duration distribution.
4. If device-level judgement is needed, query deviceId dimension after userId profile / deviceIds resolution.
5. Interpret `KUAISHOU` and `NEBULA` separately.
6. Behavior sequence detail remains optional supplement, not prerequisite.

Supported API groups:

- `getLastestDateTime`: `GET /dp/platform/app/analytics/v2/sequence/getLastestDateTime`
- `getDeviceIds`: `POST /dp/platform/app/analytics/v2/sequence/getDeviceIds`
- `getUseDuration`: `POST /dp/platform/app/analytics/v2/sequence/getUseDuration`
- `profile`: `POST /dp/platform/app/analytics/v2/sequence/profile`

Request shape:

- `getLastestDateTime` is a GET query contract, not a body call: `product=KUAISHOU|NEBULA`, `type=userId|deviceId`, `funcType=USER_PROFILE_QUERY`, `_t=<cache_buster>`.
- `getLastestDateTime` code `603` means `invalid_parameter` / `missing_required_param` / `parameter_contract_missing`; do not write `auth_failed`.
- `getDeviceIds` and `getUseDuration` are POST body calls with `appName=KUAISHOU|NEBULA`, `funcType=USER_PROFILE_QUERY`, `_t`, and the selected userId/deviceId entity value. HAR confirms the `deviceId` body key; userId mode is supported by run logs, and body-key variants remain `needs_har_confirmation` if not present in the HAR.
- `profile` uses millisecond `startTime` / `endTime`; do not use `startDate` / `endDate`.
- `profile` also requires `appName`, `include=1`, `pageSize=100`, `funcType=USER_PROFILE_QUERY`, `_t`, and the selected entity value.
- Do not guess `/api/profile`, `/rest/profile`, or `/api/user/profile`.

Field shape:

- `getUseDuration.rows` is an object-array / dict structure, not a two-dimensional array.
- `getUseDuration.rows` items contain `date` and `duration`; compute `total_duration`, `peak_day`, and `event_day_duration` from rows.
- `register_time`, `fan_distribution`, and `active_days_bucket` are in `secondLevelProfile` label-value pairs, not `firstLevelProfile`.
- `NEBULA` duration `0` means no NEBULA activity in the queried app scope; it does not mean no account activity.
- `completed_zero_duration` is source quality, not no-risk evidence.

Common errors:

- Treating track-analysis as SPA-only after API direct coverage exists.
- Guessing `/api/profile`, `/rest/profile`, or `/api/user/profile`.
- Sending `startDate` / `endDate` to `profile` instead of millisecond `startTime` / `endTime`.
- Parsing `getUseDuration.rows` as a two-dimensional array.
- Looking for register time / fans / active days only under `firstLevelProfile`.
- Treating NEBULA zero duration as account inactivity.
- Infinite SPA date picker / dropdown loop.
- Treating detail sequence unavailable as platform fully unavailable.
- Treating code `603` as auth failure.
- Marking SPA discovery as completed API execution before API probe is verified; use `discovery_completed_api_probe_pending`.

Fallback:

- DOM / SPA fallback only when API direct fails, auth activation is needed, response shape changes, or key fields are missing.
- Detail unavailable becomes `partial_source`.
- Three repeated failed UI actions become `operation_loop_detected`.

Source status mapping:

- API JSON parsed with fields: `completed`
- API JSON empty / zero app-scope activity: `no_data` or `completed` with zero-activity summary, depending on app scope
- API JSON valid with zero duration: `completed_zero_duration`
- missing required params: `missing_required_param`
- code 603 / incomplete contract: `invalid_parameter` or `parameter_contract_missing`
- SPA visible but API not verified: `discovery_completed_api_probe_pending`
- missing key labels: `partial_source`
- HTML / login page / redirect: `auth_failed`
- unexpected field shape: `parse_error`
- timeout / SPA loop: `timeout`

Capability status: `api_direct_confirmed_with_cookie_state_fallback` for `profile`, `getUseDuration`, `getDeviceIds`, and `getLastestDateTime` as recorded in `track_analysis_api_direct_contract_current.md`. Do not default to SPA / DOM for these covered fields.

Execution warning:

- A source can be marked `completed` only when the current runtime has a verified executable endpoint for the selected track-analysis action.
- If the contract exists but the executable endpoint is not available or not verified in live runtime, mark `pending_api_direct_confirmation` / `source_gap`, not `completed`.
- Do not block the account-security P0 evidence card on track-analysis endpoint probing; this source remains supporting evidence until executable endpoint verification is present.

Evidence boundary:

- Activity duration, active days, profile card, and device activity are behavior-supporting evidence.
- They can support long-inactive-then-active, abnormal same-day activity, or user/device activity mismatch analysis.
- Use `getUseDuration` for day-level alignment against login success date, scan-login date, device-switch date, abnormal-device-login date, and strategy-hit date.
- If backend login / scan / abnormal device login / strategy hit exists on a day but track-analysis userId/deviceId duration is `0` or no frontend activity, mark `front_backend_activity_mismatch`.
- `front_backend_activity_mismatch` is a medium/high-value lead for protocol login, token/session use, or non-real-client behavior, but not standalone final judgement.
- They cannot independently prove ATO, protocol attack, group control, or no risk.
- Cross-validate with login chain, device risk, strategy hit, publish / request / interaction behavior, and other raw evidence.

## DataAgent / Hive Registry Preflight

Reference:

- `computer_use_poc/batch_risk_clustering/account_security_hive_source_registry_v1.md`
- `computer_use_poc/batch_risk_clustering/account_security_hive_query_plan_templates_v1.md`

Applies to:

- ATO / account security historical login-chain analysis.
- Login anomaly, successful login, failed login, credential stuffing, password reset, passToken, kick out.
- Web/App RCP risk hit evidence when online source is over-window or incomplete.

Required preflight:

```yaml
hive_source_registry_preflight:
  registry_read: computer_use_poc/batch_risk_clustering/account_security_hive_source_registry_v1.md
  scenario:
  recommended_tables:
    - table:
      purpose:
      time_window:
      partition_filters:
      key_fields:
      no_data_interpretation:
  dataagent_prompt_includes_registry_sources: true
```

Recommended account-security tables:

- Successful login: `ks_rc_bs.ks_account_login_basic_info`.
- Login success + failure + resetPwd: `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info`.
- Web RCP: `ks_rc_arch.antispam_feature_map_default_partitioned`.
- App RCP: `ks_raw_log_v2.antispam_feature_map_partitioned`.

Rules:

- DataAgent must not start by guessing generic login tables when registry sources apply.
- DataAgent / Hive execution requires explicit user confirmation for each query.
- A prior confirmation authorizes only the current query. New SQL, new time range, new table, new question, or new evidence direction requires a new confirmation.
- Non-registry sources, including `ks_dw_fact.dw_fact_user_login_di`, are `candidate_secondary_source` unless registry tables are unavailable or insufficient.
- DataAgent prompt must include table name, use, time window, partition filters and key fields.
- Pending Hive execution is not evidence. Output `missing_hive_result` or `hive_query_pending`.

Allowed without confirmation:

- Generate a DataAgent query plan.
- Generate recommended SQL.
- List tables and fields to query.
- Summarize already returned DataAgent / Hive results.
- Analyze existing Hive results.

Before asking for confirmation, output:

- why DataAgent / Hive is needed
- recommended table
- query scope and time window
- question to be answered
- cost / scan risk if relevant
- explicit confirmation request

Output separation:

```yaml
online_api_evidence:
hive_registry_recommended_source:
dataagent_candidate_source:
missing_hive_result:
```

## Platform Call Preflight Output

Before calling a source, the agent must be able to state:

```yaml
platform_call_preflight:
  playbook_read: true
  selected_platform:
  selected_source:
  input_fields:
  required_fields_missing: []
  access_method: readonly_wrapper_api | browser_same_origin_fetch | browser_ui_observation
  fallback_allowed:
  no_data_boundary:
```
