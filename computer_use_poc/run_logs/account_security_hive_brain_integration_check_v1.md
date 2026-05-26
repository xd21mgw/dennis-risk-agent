# Account Security Hive Brain Integration Check v1

## Goal

Check whether Dennis Risk Agent's expert brain and runtime summaries can reference the newly added account-security Hive sources when answering ATO / account takeover / login-chain questions.

This run is a local documentation and regression sanity check only.

## Checked Files

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/account_security_expert_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/account_security_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/general_runtime_summary_manifest_v1.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/smoke_tests.md`

## Finding

The registry, query plan templates, routing and capability registry already referenced the new account-security Hive sources. The expert skill and account-security runtime summary still needed explicit table-level selection rules.

## Changes Made

Added explicit runtime / expert-brain rules:

- Online login log window gaps must be marked `login_log_window_incomplete`.
- Online no_data / over-window no_data is not a no-risk or no-ATO counter evidence.
- Successful login chain uses `ks_rc_bs.ks_account_login_basic_info`.
- Login failure / credential stuffing / brute force uses `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info` with `p_action_type='login'`.
- Password reset uses `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info` with `p_action_type='resetPwd'`.
- Web RCP uses `ks_rc_arch.antispam_feature_map_default_partitioned`, 30-day retention.
- App RCP uses `ks_raw_log_v2.antispam_feature_map_partitioned`, 50-day retention, with mandatory `p_date + p_hourmin + p_action_type`.
- DataAgent remains Hive / warehouse extraction and aggregation only.
- If online data is missing, runtime answers should output Hive query plan rather than vague "supplement login logs".

## Text Regression Samples

| case | input | expected result | pass/fail |
| --- | --- | --- | --- |
| HIVE-BRAIN-001 | 这个 5 月 12 日的盗号，今天在线日志查不到，是不是没异常？ | Do not say no anomaly; mark `login_log_window_incomplete`; generate Hive plan. | pass |
| HIVE-BRAIN-002 | 有没有异设备成功登录？ | Use `ks_rc_bs.ks_account_login_basic_info`. | pass |
| HIVE-BRAIN-003 | 是不是被撞库？ | Use `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info`, `p_action_type='login'`. | pass |
| HIVE-BRAIN-004 | 有没有改密？ | Use `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info`, `p_action_type='resetPwd'`. | pass |
| HIVE-BRAIN-005 | App 发布行为有没有风控命中？ | Use `ks_raw_log_v2.antispam_feature_map_partitioned` with `p_date + p_hourmin + p_action_type`. | pass |

## Not Done

- No real platform access.
- No DataAgent call.
- No Hive SQL execution.
- No auth/gateway change.
- No release package update.
- No git commit.

## Release Need

No immediate release rebuild is required for this sanity check. If a new semi-open release is prepared, include the updated skill/runtime summaries and the account-security Hive registry/templates.
