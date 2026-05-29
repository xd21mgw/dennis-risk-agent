# DataAgent Prompt Templates v1

## Global Boundary

These templates target the current DataAgent Conversational API MVP channel. They do not assume SDK / CLI / RPC / MCP / structured-query API availability.

All templates must preserve source layering:

- `recommended_source`: Dennis Hive registry / playbook selected table.
- `candidate_source`: DataAgent-suggested table or additional table requiring review.

If DataAgent output conflicts with the Dennis Hive registry, do not overwrite the registry. Mark the conflict as `candidate_source_conflict`.

Priority recommended tables:

- `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info`
- `ks_rc_arch.antispam_feature_map_default_partitioned`
- `ks_rc_bs.account_security_basic_info`
- `kscdm.dim_ks_user_all`
- `ks_rc_bs.fake_account_tag_all_detail_snapshot`

Also preserve previously registered Dennis Hive sources, including:

- `ks_rc_bs.ks_account_login_basic_info`
- `ks_raw_log_v2.antispam_feature_map_partitioned`
- `ks_rc_bs.fake_account_tag_all_summary_snapshot`
- `ks_rc_bs.fake_account_tag_di`
- `ks_rc_bs.fake_account_tag_online_detail`
- `ks_rc_bs.fake_account_tag_offline_detail`
- `ks_rc_bs.fake_account_high_recall_snapshot`

Sensitive output boundary:

- Do not output phone, cookie, token, session, header, email, id card, password, or credential plaintext.
- Prefer masked entity aliases, counts, distributions, and safe refs.
- `no_data` is not no-risk evidence.
- Dry-run SQL generation is not executed evidence.

## Template: single_user_ato_evidence

Purpose: Build a bounded offline evidence query for one suspected ATO user when online sources are over-window or incomplete.

Recommended tables:

```yaml
recommended_source:
  primary:
    - ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
  auxiliary:
    - ks_rc_bs.ks_account_login_basic_info
    - ks_rc_arch.antispam_feature_map_default_partitioned
    - ks_rc_bs.account_security_basic_info
candidate_source:
  optional:
    - kscdm.dim_ks_user_all
```

Recommended fields:

```yaml
fields:
  - user_id
  - op_time
  - device_id
  - source_ip
  - login_type
  - finalloginresult
  - p_action_type
  - code
  - punish
  - hit_policies
  - product
  - client
```

Prompt template:

```text
Task: single_user_ato_evidence
Mode: dry_run=${dry_run}
Max rows: ${max_rows}
Time window: ${time_window}
Entity: user_id=${user_id_safe_ref}

Use Dennis recommended sources first:
- ks_rc_bs.dwd_risk_usr_accnt_login_orign_info for full login success/failure/resetPwd chain.
- ks_rc_bs.ks_account_login_basic_info only for successful login trail.
- ks_rc_arch.antispam_feature_map_default_partitioned for Web RCP risk events within retention.
- ks_rc_bs.account_security_basic_info if account baseline is needed.

Generate SQL or return bounded table output. Use p_date and p_action_type where applicable.
Do not output sensitive plaintext fields. If no rows, explain no_data boundary: no rows under this bounded filter is not no ATO.
Return final SQL/results only in MODEL_ANSWER.
```

No-data boundary:

```yaml
no_data_boundary:
  - no rows in login request table under bounded filters is not no ATO
  - no resetPwd row is not proof of no account takeover
  - missing Web RCP rows can be retention or source-scope gap
```

## Template: batch_user_ato_clustering

Purpose: Generate a batch aggregation query plan for multiple ATO users or suspected victims.

Recommended tables:

```yaml
recommended_source:
  primary:
    - ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
  auxiliary:
    - ks_rc_bs.fake_account_tag_all_detail_snapshot
    - ks_rc_bs.fake_account_tag_all_summary_snapshot
    - ks_rc_arch.antispam_feature_map_default_partitioned
candidate_source:
  optional:
    - kscdm.dim_ks_user_all
    - ks_rc_bs.fake_account_tag_di
```

Recommended fields:

```yaml
fields:
  - user_id
  - device_id
  - source_ip
  - login_type
  - finalloginresult
  - hit_policies
  - p_action_type
  - op_time
  - fake_account_tag
```

Prompt template:

```text
Task: batch_user_ato_clustering
Mode: dry_run=${dry_run}
Max rows: ${max_rows}
Time window: ${time_window}
Entities: ${user_id_safe_refs}

Use Dennis recommended sources first. Generate aggregation SQL by user/device/IP/login_type/policy/fake-account-tag.
Output only aggregate counts, top dimensions, and representative safe refs. Do not output sensitive plaintext.
Do not claim same attacker group from similarity alone; mark required_validation.
If no rows, state no_data boundary and missing evidence.
Return final SQL/results only in MODEL_ANSWER.
```

No-data boundary:

```yaml
no_data_boundary:
  - no aggregation rows under current filters does not prove no shared attack
  - fake-account tags are auxiliary and may be stale or high-recall
  - representative samples require follow-up validation
```

## Template: strategy_hit_login_timeline_alignment

Purpose: Align strategy-hit or RCP timing with login-chain timing for ATO / account-security evidence.

Recommended tables:

```yaml
recommended_source:
  primary:
    - ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
    - ks_rc_arch.antispam_feature_map_default_partitioned
  auxiliary:
    - ks_raw_log_v2.antispam_feature_map_partitioned
    - ks_rc_bs.account_security_basic_info
candidate_source:
  optional:
    - kscdm.dim_ks_user_all
```

Recommended fields:

```yaml
fields:
  - user_id
  - source_id
  - action_type
  - p_action_type
  - time
  - op_time
  - device_id
  - source_ip
  - code
  - punish
  - hit_policies
```

Prompt template:

```text
Task: strategy_hit_login_timeline_alignment
Mode: dry_run=${dry_run}
Max rows: ${max_rows}
Time window: ${time_window}
Entity: user_id/source_id=${entity_safe_ref}

Use Dennis recommended sources first:
- Login chain: ks_rc_bs.dwd_risk_usr_accnt_login_orign_info.
- Web RCP: ks_rc_arch.antispam_feature_map_default_partitioned.
- App RCP only if product/app context requires it: ks_raw_log_v2.antispam_feature_map_partitioned.

Generate SQL that aligns login op_time and RCP time into a bounded timeline.
Do not output sensitive plaintext. Strategy/RCP hit is auxiliary evidence, not final ATO judgement.
If no rows, explain whether it is table retention, partition, p_action_type, or source-scope no_data.
Return final SQL/results only in MODEL_ANSWER.
```

No-data boundary:

```yaml
no_data_boundary:
  - no RCP row is not no strategy hit unless source/table/window are correct and retention covers the event
  - no login row is not no ATO when online/warehouse source scope is incomplete
  - timeline alignment cannot replace online source evidence
```

