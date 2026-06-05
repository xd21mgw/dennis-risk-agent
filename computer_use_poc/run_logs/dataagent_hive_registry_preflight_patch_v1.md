# DataAgent / Hive Registry Preflight Patch v1

## Goal

Ensure Dennis Risk Agent uses the account-security Hive source registry before prompting DataAgent in ATO / login-chain scenarios, so DataAgent does not start from generic business login tables when Dennis already has risk-recommended sources.

## Background

In the `62950989` live retest, realtime API multi-source behavior improved. After the user explicitly said "查吧，DataAgent", DataAgent first found `dw_fact_user_login_di` before the Dennis registry was recovered. The desired behavior is to read `account_security_hive_source_registry_v1.md` first and pass recommended tables into the DataAgent 提示词.

## Updated Rules

- Run `hive_source_registry_preflight` before account-security / ATO DataAgent or Hive prompt generation.
- Read `computer_use_poc/batch_risk_clustering/account_security_hive_source_registry_v1.md`.
- Successful login starts with `ks_rc_bs.ks_account_login_basic_info`.
- Login failure / credential stuffing / password reset starts with `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info`.
- Non-registry tables are `candidate_secondary_source` until registry sources are unavailable or insufficient.
- Output separates `online_api_evidence`, `hive_registry_recommended_source`, `dataagent_candidate_source`, and `missing_hive_result`.
- Pending Hive/DataAgent jobs are not completed evidence.

## Files Updated

- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## Not Done

- Did not access real platforms.
- Did not call DataAgent.
- Did not execute Hive SQL.
- Did not change gateway / safeBins / tools config.
- Did not rebuild release package.
