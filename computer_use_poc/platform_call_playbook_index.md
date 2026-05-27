# Platform Call Playbook Index

This index is the mandatory preflight reading list before Dennis Risk Agent calls any realtime readonly source. If memory retrieval fails, fall back to this file and the referenced playbooks instead of guessing platform behavior.

## Global Rules

- Realtime readonly API calls do not require user confirmation when required fields are present.
- DataAgent / Hive / big batch / write / high-risk operations require query plan or explicit confirmation.
- DataAgent / Hive confirmation is per call. A previous "查吧 DataAgent" only authorizes that one query; every new SQL, table, time window, question, or evidence direction requires a new confirmation.
- Do not use old observations as "no-cache" realtime results.
- Every source call must produce a checkpoint and source_quality.
- `no_data`, `blocked`, `timeout`, and `auth_failed` are source states, not no-risk counter evidence.
- Browser UI is fallback, not default.

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

1. USER_ID to DEVICE_ID graph: `graphData` with `groupKey=USER_ID`, `dimKey=DEVICE_ID`.
2. DEVICE_ID to USER_ID graph: `graphData` with `groupKey=DEVICE_ID`, `dimKey=USER_ID`.
3. Device risk uses `riskData` only after a device id is available.

Common errors:

- Treating `user_id` as `device_id` in riskData.
- Using riskData for entity resolution.
- Treating graph no relation as no risk.

Fallback:

- If graphData blocked, mark `blocked_sources`.
- If device id missing, mark `missing_required_fields`.

Source status mapping:

- graphData relation found: `completed`
- no relation found: `no_data` with relation boundary.
- auth / permission issue: `blocked` or `auth_failed`
- timeout: `timeout`

Capability status: `api_direct_confirmed` for validated `graphData` / `riskData` readonly paths.

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

1. Strategy hit inventory: `fastQueryHbase` with sourceId / sourceIds and time window.
2. Event detail: `rcpEventDetail`.
3. Feature snapshot: `rcpEventFeatureList` with `featureGroup=""` and exact `_occurTime`.
4. Policy tree node: `queryProPolicyTree`; do not guess `policyTreeNodeCode`.
5. Attribution: `nodePolicyAttribution` / `nodeBindPolicyAttribution`.

Common errors:

- Simple userId direct strategy query without sourceId/time window context.
- Confusing `hitTimestamp` with precise event `queryTime`.
- Treating strategy hit as final risk judgement.
- Treating `updateUser` or operator as responsibility attribution.

Fallback:

- Missing sourceId/eventId/queryTime becomes query plan or missing evidence.
- Timeout becomes `timeout_sources`, not no risk.

Source status mapping:

- hit overview returned: `completed`
- no hits: `no_data` with `strategy_hit_not_final_risk_judgement`
- missing fields: `skipped / missing_required_fields`
- timeout/auth/parse: `timeout`, `auth_failed`, `parse_error`

Capability status:

- `fastQueryHbase`: `api_direct_confirmed`.
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

1. Open SPA profile URL for the correct domain when browser auth activation is needed.
2. If `account.p` login page has prefilled username, click next to activate the session.
3. After same-origin is active, use API direct read such as `/archives/user/home/info?userId=...`.
4. Use DOM / selector only as fallback.

Common errors:

- Declaring Archives unavailable before recoverable preflight.
- Direct browser UI scraping before API direct read.
- Treating empty result as no risk or no behavior.

Fallback:

- `permission_blocked`, `response_shape_changed`, `key_fields_missing`, `link_url_only`, `mapping_pending_validation`, or `need_required_param` can trigger scoped fallback.
- Browser loops stop after three repeated failed actions.

Source status mapping:

- API JSON parsed: `completed` or `no_data`
- auth page / 2FA / redirect: `auth_failed`
- profile lock or browser session issue: `blocked`
- SPA loop: `timeout` with `operation_loop_detected`

Capability status: `same_origin_api_confirmed` for validated APIs that require SPA / browser auth activation before same-origin fetch. Do not declare Archives unavailable before recoverable preflight; do not treat same-origin support as generic API direct.

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

- `getLastestDateTime`
- `getDeviceIds`
- `getUseDuration`
- `profile`

Field shape:

- `getUseDuration.rows` is an object-array / dict structure, not a two-dimensional array.
- `register_time`, `fan_distribution`, and `active_days_bucket` are in `secondLevelProfile` label-value pairs, not `firstLevelProfile`.
- `NEBULA` duration `0` means no NEBULA activity in the queried app scope; it does not mean no account activity.

Common errors:

- Treating track-analysis as SPA-only after API direct coverage exists.
- Parsing `getUseDuration.rows` as a two-dimensional array.
- Looking for register time / fans / active days only under `firstLevelProfile`.
- Treating NEBULA zero duration as account inactivity.
- Infinite SPA date picker / dropdown loop.
- Treating detail sequence unavailable as platform fully unavailable.

Fallback:

- DOM / SPA fallback only when API direct fails, auth activation is needed, response shape changes, or key fields are missing.
- Detail unavailable becomes `partial_source`.
- Three repeated failed UI actions become `operation_loop_detected`.

Source status mapping:

- API JSON parsed with fields: `completed`
- API JSON empty / zero app-scope activity: `no_data` or `completed` with zero-activity summary, depending on app scope
- missing key labels: `partial_source`
- HTML / login page / redirect: `auth_failed`
- unexpected field shape: `parse_error`
- timeout / SPA loop: `timeout`

Capability status: `api_direct_confirmed` for `profile`, `getUseDuration`, `getDeviceIds`, and `getLastestDateTime` as recorded in `track_analysis_api_direct_contract_current.md`. Do not default to SPA / DOM for these covered fields.

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
