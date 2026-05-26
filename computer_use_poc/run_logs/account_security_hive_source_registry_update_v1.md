# Account Security Hive Source Registry Update v1

## Goal

Update Dennis Risk Agent's offline Hive data-source capability for account security, especially ATO / account takeover / login-chain analysis.

This run only updates local documentation, registry, query plan templates, routing notes and smoke tests.

## Added Files

- `computer_use_poc/batch_risk_clustering/account_security_hive_source_registry_v1.md`
- `computer_use_poc/batch_risk_clustering/account_security_hive_query_plan_templates_v1.md`
- `computer_use_poc/run_logs/account_security_hive_source_registry_update_v1.md`

## Modified Files

- `computer_use_poc/batch_risk_clustering/account_risk_data_source_registry_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_response_template_v1.md`
- `computer_use_poc/batch_risk_clustering/README.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/smoke_tests.md`

## Core Table Summary

| table | purpose | retention | partitions | main boundary |
| --- | --- | --- | --- | --- |
| `ks_rc_bs.ks_account_login_basic_info` | successful login only | 9999 days | `p_date` | not suitable for login failure / credential stuffing |
| `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info` | full login request: success/failure/reset | 9999 days | `p_date`, `p_action_type` | spelling is `orign`; null `finalloginresult` is unfinished/uncertain |
| `ks_rc_arch.antispam_feature_map_default_partitioned` | Web RCP risk events | 30 days | `p_date`, `p_hourmin`, `p_action_type` | over-window no_data is source_gap |
| `ks_raw_log_v2.antispam_feature_map_partitioned` | App RCP risk events | 50 days | `p_date`, `p_hourmin`, `p_action_type` | very large table; no weak partition SQL |

## ATO / Account Takeover Routing Fix

- Online login log window is not the only source.
- Online over-window / no_data must be marked `login_log_window_incomplete`.
- Successful login chain routes to `ks_rc_bs.ks_account_login_basic_info`.
- Login failure / credential stuffing / brute force routes to `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info` with `p_action_type='login'`.
- Password reset routes to `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info` with `p_action_type='resetPwd'`.
- Web/H5 risk interception routes to `ks_rc_arch.antispam_feature_map_default_partitioned`.
- App-side risk interception routes to `ks_raw_log_v2.antispam_feature_map_partitioned`.

## DataAgent / Hive Query Plan Fix

Batch Risk Clustering ATO / login-chain plans now require:

- `query_goal`
- `selected_table`
- `reason_for_table_selection`
- `partition_filters`
- `entity_filters`
- `key_fields`
- `expected_signal`
- `risk_if_missing`
- `fallback_table`
- `no_data_interpretation`

The templates are plans only. They do not execute Hive SQL or call DataAgent.

## Smoke Test Summary

Added smoke tests:

- `HIVE-LOGIN-001`
- `HIVE-LOGIN-002`
- `HIVE-LOGIN-003`
- `HIVE-LOGIN-004`
- `HIVE-LOGIN-005`
- `HIVE-RCP-001`
- `HIVE-RCP-002`
- `HIVE-RCP-003`
- `HIVE-RCP-004`
- `HIVE-ATO-001`
- `HIVE-ATO-002`
- `HIVE-ATO-003`

## Not Done

- Did not call DataAgent.
- Did not execute Hive SQL.
- Did not access real platforms.
- Did not update auth/gateway.
- Did not repackage release.
- Did not commit git changes.

## Release Need

No immediate release package was generated. If the semi-open release is rebuilt later, include the new account-security Hive registry and query plan templates.
