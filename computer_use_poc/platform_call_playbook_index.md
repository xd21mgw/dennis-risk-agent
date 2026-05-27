# Platform Call Playbook Index

This index is the mandatory preflight reading list before Dennis Risk Agent calls any realtime readonly source. If memory retrieval fails, fall back to this file and the referenced playbooks instead of guessing platform behavior.

## Global Rules

- Realtime readonly API calls do not require user confirmation when required fields are present.
- DataAgent / Hive / big batch / write / high-risk operations require query plan or explicit confirmation.
- Do not use old observations as "no-cache" realtime results.
- Every source call must produce a checkpoint and source_quality.
- `no_data`, `blocked`, `timeout`, and `auth_failed` are source states, not no-risk counter evidence.
- Browser UI is fallback, not default.

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
2. If SSO executor is unavailable, return structured `blocked`.
3. If auth fails, return `auth_failed`.
4. If timeout, return `timeout`.

Common errors:

- Missing `SmartSSOSession`: `blocked / sso_executor_unavailable`
- HTTP redirect / login page: `auth_failed / auth_session_issue`
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

## Track Analysis

Reference:

- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`

Input:

- `user_id` or `device_id`

Preferred path:

1. stats-first.
2. Read monthly active days, device type, region, register time, fans distribution, user/device profile.
3. Behavior sequence detail is optional supplement, not prerequisite.

Common errors:

- Infinite SPA date picker / dropdown loop.
- Treating detail sequence unavailable as platform fully unavailable.

Fallback:

- Detail unavailable becomes `partial_source`.
- Three repeated failed UI actions become `operation_loop_detected`.

Source status mapping:

- stats read: `completed`
- detail unavailable: `no_data` or `skipped` with `partial_source`
- SPA loop: `timeout`

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
- Non-registry sources, including `ks_dw_fact.dw_fact_user_login_di`, are `candidate_secondary_source` unless registry tables are unavailable or insufficient.
- DataAgent prompt must include table name, use, time window, partition filters and key fields.
- Pending Hive execution is not evidence. Output `missing_hive_result` or `hive_query_pending`.

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
