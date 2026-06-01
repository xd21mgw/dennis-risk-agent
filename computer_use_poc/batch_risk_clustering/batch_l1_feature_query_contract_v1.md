# Batch L1 Feature Query Contract v1

## Purpose

L1 feature query is the low-cost batch shallow lookup layer before deeper representative case investigation.

It converts a batch of entities into a `batch_feature_table` that supports:

- TOP dimension drilldown;
- frequent pattern / contribution analysis;
- abnormal A -> B correlation matrix;
- cluster hints;
- representative sampling;
- cluster evidence cards;
- expansion and strategy feature suggestions.

This contract is a query plan and schema contract only. It does not execute Hive SQL or call DataAgent.

## Workflow Position

```text
批量输入
→ L1 宽表 / 画像浅查
→ TOP 维度下探
→ 频繁项 / 贡献度分析
→ A→B 有向相关矩阵
→ cluster hint
→ 代表抽样
→ cluster evidence card
→ 举一反三 / 策略建议
```

## L1 Source Families

| family | low-cost fields | purpose |
|---|---|---|
| user profile | user_age_bucket, register_time, account_status, user_level, risk_profile_summary | base population and false-positive boundary |
| device profile | device_id, device_model, os_type, os_version, app_version, emulator/root/hook/frida indicators | device farm / toolchain cluster hints |
| IP / network | ip, ip24, country/region/city, ASN, proxy/VPN signal | infrastructure clustering and denominator comparison |
| login security | login_type, login_method, login_success_count, login_fail_count, kick_out_count, token_revoke_count, login_device_change | ATO / OAuth / credential-stuffing differentiation |
| behavior | abnormal_action, action_count, publish/comment/private_message/withdraw/order counts, action_sequence_summary | downstream risk behavior clustering |
| frontend chain | frontend_event_count, backend_request_count, frontend_missing_rate, UA, endpoint, response_code_distribution | protocol / crawler / frontend gap validation |
| strategy hit | strategy_id, hit_reason, hit_strength, control_action, appeal/complaint marker | secondary attribution and false-positive review |
| content behavior | publish_type, content_delete/blocked count, interaction pattern, private message target count | content abuse and downstream harm |
| channel / campaign | channel, campaign_id, entry_source, reward_claim, retention bucket, conversion signal | arbitrage and channel fake traffic |
| baseline / control | denominator_count, same_period_control_count, historical_normal_baseline_count, population_rate | enrichment and denominator protection |

## ATO Cluster Lens L1 Fields

When the batch may include compromised-account / stolen-account posting risk, request these ATO lens fields in addition to the generic L1 feature families. This is still a query plan and schema contract only; it does not call Hive or DataAgent.

| lens family | fields | purpose |
|---|---|---|
| `web_untrusted_login_cluster` | recent_web_h5_pc_login, historical_login_source_distribution, login_source_shift, login_device_baseline_match, login_ip_ua_baseline_match | Identify WEB / H5 / PC control-chain commonality beyond generic login count. |
| `abnormal_login_type_cluster` | login_type, login_method, token_issued, refreshToken, passToken, byToken, OAuth, scan_login, one_click_login, resetPwd, kick_out, account_protection | Separate credential stuffing, token/session takeover, OAuth/scan and one-click takeover paths. |
| `login_to_action_delta` | suspicious_login_time, downstream_action_time, action_type, delta_minutes, anchor_source | Detect WEB/control-chain event followed by diversion publish/comment/live/private message/profile change. |
| `content_action_deep_dive` | photo_id, live_id, comment_id, publish_time, publish_source, publish_device, publish_ip, publish_ua, audit_reason, strategy_reason, diversion_reason, four_items_available | Prove downstream content/action chain for representative samples. |
| `device_identity_inconsistency_cluster` | device_id_commonness, first_seen_time, active_days_30_90_180, device_model_drift, os_drift, app_version_drift, ua_drift, browser_fingerprint_drift, ip_asn_drift, login_source_drift, login_type_drift | Avoid treating common device_id as owner proof; detect possible spoofing. |
| `shared_infrastructure` | shared_ip, shared_ip24, shared_asn, shared_ua, shared_browser_fingerprint, shared_login_source, shared_login_type, shared_landing_page, shared_contact_info, shared_diversion_wording, publish_cadence | Backfill cluster-level infra coverage and confidence. |
| `historical_behavior_shift` | historical_publish_category, current_publish_category, historical_web_login_rate, current_web_login_rate, historical_publish_device, current_publish_device, historical_action_baseline | Distinguish compromised normal accounts from content-abuse-only or fake-account clusters. |

## batch_feature_table Schema

| field | type | required | description |
|---|---|---|---|
| `batch_id` | string | yes | Batch identifier or generated safe reference. |
| `case_id` | string | yes | Case-level id. |
| `entity_type` | string | yes | user / device / ip / account / request / event. |
| `entity_id_safe_ref` | string | yes | Safe reference for entity. UID/DID/IP can be internally retained, but external output should use safe_ref or bucket. |
| `event_time` | timestamp/string | recommended | Main risk event time. |
| `time_window_start` | timestamp/string | yes | Query window start. |
| `time_window_end` | timestamp/string | yes | Query window end. |
| `user_profile_fields` | object | optional | Low-cost user profile fields. |
| `device_profile_fields` | object | optional | Device and environment fields. |
| `ip_network_fields` | object | optional | IP, IP bucket, proxy/ASN derived fields. |
| `login_security_fields` | object | optional | Login method, kick out, token status, failure signals. |
| `behavior_fields` | object | optional | Action counts, abnormal actions, sequence summary. |
| `frontend_chain_fields` | object | optional | Frontend/backend gap, UA, endpoint, response codes. |
| `strategy_hit_fields` | object | optional | Strategy id, hit reason, hit strength and action. |
| `content_behavior_fields` | object | optional | Publish, comment, message, content outcome. |
| `channel_campaign_fields` | object | optional | Channel, campaign, reward, retention and conversion fields. |
| `fake_account_fields` | object | optional | Fake account tags, downstream badness, audit labels. |
| `baseline_fields` | object | recommended | Historical normal, same-period control, population denominator. |
| `ato_cluster_lens_fields` | object | conditional | WEB login, login-to-action, content-action, device identity consistency, shared infrastructure and historical shift fields for compromised-account analysis. |
| `source_metadata` | object | yes | Source table, partition, freshness, permission and reliability. |
| `missing_fields` | list | yes | Fields requested but unavailable. |
| `sensitivity_flags` | list | yes | phone, identity, credential, raw payload, high-sensitive personal fields. |

## Query Plan Fields

An L1 query plan should specify:

```yaml
l1_query_plan:
  input_entities:
  entity_key:
  time_window:
  source_families:
  requested_fields:
  join_keys:
  baseline_plan:
  privacy_policy:
  expected_output: batch_feature_table
  not_execute_now: true
```

## Baseline Requirements

- For enrichment claims, request historical normal baseline or same-period control group.
- If only current batch exists, output `only_current_batch_available` and `batch_internal_concentration`.
- If denominator is missing, set `denominator_status=denominator_required`.
- Strategy recall batches must mark `selection_bias_risk`.

## Sensitive Field Policy

- Credential material, request headers, raw payloads, phone, identity number, and real-name fields are not output in plaintext.
- IP may be bucketed as `ip24` or masked when shared broadly.
- UID/DID can be kept as internal entity keys but should be safe_ref in user-facing summaries unless the audience and channel allow controlled internal identifiers.
