# Account Security Hive Source Registry v1

## Purpose

This registry records offline Hive / warehouse sources for account security, ATO, login-chain, login-failure, password-reset and RCP risk-event analysis.

It is a local data-source registry only. It does not execute Hive SQL, call DataAgent, access internal platforms, or authorize enforcement.

DataAgent remains a Hive / warehouse extraction and aggregation capability. It is not a universal risk execution substrate.

## Core Source Summary

| table | role | coverage | retention | update | partition | scale | primary use |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ks_rc_bs.ks_account_login_basic_info` | successful login table | successful login only | 9999 days, full history | daily incremental | `p_date` | about 1.30TB / 12.7B rows | successful login trail, abnormal successful login, device/IP distribution |
| `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info` | full login request table | success + failure + password reset | 9999 days, full history | daily incremental | `p_date`, `p_action_type` | about 1.80TB / 18.4B rows | login failure, credential stuffing, brute force, resetPwd, full login chain |
| `ks_rc_arch.antispam_feature_map_default_partitioned` | Web RCP risk logs | Web-side risk/intercept events | 30 days | hourly | `p_date`, `p_hourmin`, `p_action_type` | C4, time-sensitive | Web/H5 risk hit, login/post/API risk event |
| `ks_raw_log_v2.antispam_feature_map_partitioned` | App RCP risk logs | App-side risk/intercept events | 50 days | hourly | `p_date`, `p_hourmin`, `p_action_type` | about 5.61PB / 600B rows | mobile App risk hit, login/post/interaction/device/protocol risk |

## 1. `ks_rc_bs.ks_account_login_basic_info`

### Positioning

Account successful login log table. It only contains successful login records and is dedicated to login-success data.

### Data Characteristics

- Range: successful login only.
- Retention: 9999 days, full history.
- Update: daily incremental.
- Partition: `p_date`.
- Scale: about 1.30TB, 12.7B rows.

### Applicable Scenarios

- Analyze successful login user behavior.
- Trace historical successful login records.
- Inspect user login device/IP distribution.
- Analyze normal account usage.
- In ATO analysis, confirm abnormal successful login, cross-device successful login, and login-to-downstream behavior chain entry point.

### Notes

- Account-security internal table; not externally provided.
- Business-side login logs can refer to `ks_dw_fact.dw_fact_user_login_di` if needed.
- It only covers successful logins; it is not suitable for login failure, credential stuffing failures, or brute-force failures.

### Core Field Categories

- `user_id`
- `op_time`
- `device_id`
- `source_ip`
- `client`
- `login_type`
- `province`
- `city`
- `phone_model`
- `sid`
- `did_active_day`
- `kpn`
- `product`
- `app_ver`
- `sys_ver`
- `code`
- `punish`
- `hit_policies`
- `hit_pro_policies`
- `risk_factor_map`
- `high_risk_factor_cnt`
- `medium_risk_factor_cnt`
- `low_risk_factor_cnt`
- `login_tag_1` ~ `login_tag_10`
- `fakeaccounttagsmax`
- `isuserban`
- `isusersocialban`
- `register_day`
- `register_did`
- `register_ip`
- `register_province`
- `latestactivedate`
- `latestactivedateinterval`

### No-data Interpretation

No rows in this table for a date partition only means no successful login found in that partition under the query filter. It does not mean no failed login, no unfinished login flow, no resetPwd event, or no ATO.

## 2. `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info`

### Positioning

Account login request log table. It is the full login data source, including login success, login failure, and password-reset login events.

Important spelling: table name uses `orign`, not `origin`. Do not correct the spelling.

### Data Characteristics

- Range: login success + login failure + password reset.
- Retention: 9999 days, full history.
- Update: daily incremental.
- Partitions: `p_date`, `p_action_type`.
- Scale: about 1.80TB, 18.4B rows.

### Applicable Scenarios

- Login failure analysis.
- Credential stuffing and brute-force analysis.
- Full login-chain tracing.
- Abnormal login behavior detection.
- ATO / account takeover investigation.
- Password-reset related login event analysis.

### Core Fields

- `user_id`
- `op_time`
- `device_id`
- `source_ip`
- `login_type`
- `finalloginresult`
- `p_action_type`
- `code`
- `punish`
- `hit_policies`
- `risk_factor_map`
- `client`
- `kpn`
- `product`
- `app_ver`
- `sys_ver`
- `province`
- `city`

### Key Field Semantics

- `finalloginresult`: final login result. `1` means success; other values mean failure; null means the flow did not finish or the state is uncertain.
- `p_action_type`: event type. `login` means login, `resetPwd` means password reset.
- `code`: risk errorCode.
- `punish`: risk punishment list, such as captcha, block, or ban.
- `hit_policies`: hit strategies.

### Notes

- Compared with `ks_account_login_basic_info`, this table adds `finalloginresult`, so success/failure can be separated.
- Login failure, credential stuffing, and brute force should prioritize this table.
- Query must include `p_date`; it should also include `p_action_type`.
- Do not treat `finalloginresult is null` as failure. Mark it as unfinished flow or uncertain state.

### No-data Interpretation

No rows under a narrow filter cannot be used as "no ATO" proof. Check successful login table, resetPwd partition, RCP tables, and downstream behavior where applicable.

## 3. `ks_rc_arch.antispam_feature_map_default_partitioned`

### Positioning

RCP core table for Web-side risk logs and Web-side risk interception / risk event analysis.

### Data Characteristics

- Range: Web-side risk interception logs.
- Retention: 30 days.
- Update: hourly.
- Security level: C4.
- Partitions: `p_date`, `p_hourmin`, `p_action_type`.

### Applicable Scenarios

- Web risk event analysis.
- Near-30-day Web risk interception query.
- Web/H5 login, posting, API request risk event drilldown.
- In ATO analysis, supplement Web-side risk interception and strategy hit evidence.

### Core Fields

- `source_id`: actor ID, usually userId.
- `target_id`: target ID.
- `action_type`: action type.
- `p_action_type`: partition field, action type.
- `device_id`
- `source_ip`
- `time`
- `params`: JSON parameters.

### Notes

- Retention is only 30 days.
- Production timeliness is not guaranteed; high-priority needs should be separately raised to the owner.
- Query must constrain `p_date`, `p_hourmin`, and `p_action_type`.
- Historical Web risk data beyond the window must be marked as `source_gap`, not no-risk counter evidence.

## 4. `ks_raw_log_v2.antispam_feature_map_partitioned`

### Positioning

RCP core table for App-side risk logs and App-side risk interception / risk event analysis.

### Data Characteristics

- Range: App-side risk interception logs.
- Retention: 50 days.
- Update: hourly.
- Scale: about 5.61PB, 600B rows.
- Partitions: `p_date`, `p_hourmin`, `p_action_type`.
- Table type: external table, pointing to the same underlying source.

### Applicable Scenarios

- App-side risk event analysis.
- Mobile strategy hit analysis.
- App-side posting, login, interaction, device, and protocol risk evidence.

### Core Fields

- `source_id`
- `target_id`
- `action_type`
- `p_action_type`
- `device_id`
- `source_ip`
- `time`
- `params`

### Notes

- Data volume is extremely large. Queries must force partition constraints.
- Must include `p_date`, `p_hourmin`, and `p_action_type`.
- Do not generate full-table scan or weak-partition SQL.
- Beyond 50 days, mark `source_gap` or route to another historical source; do not treat no-data as no-risk counter evidence.

## Scenario Quick Routing

| scenario | recommended table | use when | key boundary |
| --- | --- | --- | --- |
| Successful login records for one user | `ks_rc_bs.ks_account_login_basic_info` | successful login trail, cross-device success, login IP/device distribution, historical successful login | success-only; cannot analyze failed login or credential stuffing |
| Login failure / credential stuffing / abnormal attempts | `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info` | login failure, brute force, abnormal login attempt, resetPwd event | use `p_action_type='login'` for login and `p_action_type='resetPwd'` for reset; null result is uncertain |
| Web risk/interception events | `ks_rc_arch.antispam_feature_map_default_partitioned` | Web/H5 login/post/interaction/API risk event within 30 days | must constrain `p_date + p_hourmin + p_action_type` |
| App risk/interception events | `ks_raw_log_v2.antispam_feature_map_partitioned` | App-side login/post/interaction/device/protocol risk within 50 days | must constrain `p_date + p_hourmin + p_action_type`; no weak partition SQL |

## ATO Offline Routing Rules

1. Online login log window is insufficient:
   - Do not output "no abnormal login" as a strong conclusion.
   - Mark `login_log_window_incomplete`.
   - Generate DataAgent/Hive query plan.
   - Successful login: `ks_rc_bs.ks_account_login_basic_info`.
   - Failure / credential stuffing / reset: `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info`.

2. ATO successful login chain:
   - Primary table: `ks_rc_bs.ks_account_login_basic_info`.
   - Key fields: `op_time`, `device_id`, `source_ip`, `login_type`, `app_ver`, `client`, `province`, `city`, `login_tag_1` ~ `login_tag_10`, `risk_factor_map`, `hit_policies`.

3. Credential stuffing / brute force / login failure:
   - Primary table: `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info`.
   - Key fields: `finalloginresult`, `code`, `punish`, `hit_policies`, `source_ip`, `device_id`, `login_type`, `p_action_type`.

4. Password-reset events:
   - Primary table: `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info`.
   - Partition condition: `p_action_type='resetPwd'`.

5. Web/H5 risk interception:
   - Primary table: `ks_rc_arch.antispam_feature_map_default_partitioned`.
   - Window: 30 days.

6. App risk interception:
   - Primary table: `ks_raw_log_v2.antispam_feature_map_partitioned`.
   - Window: 50 days.

7. RCP query protection:
   - App table must include `p_date + p_hourmin + p_action_type`.
   - Web table must include `p_date + p_hourmin + p_action_type`.
   - No full-table scan or weak-partition SQL.

## Output Boundary

- This registry only supports query planning and evidence source selection.
- It does not authorize real DataAgent execution.
- It does not execute Hive SQL.
- It does not replace online readonly observation when the online window is sufficient.
- `no_data`, over-window, blocked source, or missing source cannot be used as no-risk counter evidence.
