# Account Security Hive Query Plan Templates v1

## Purpose

This document provides DataAgent/Hive query plan templates for ATO, account takeover, login-chain, login-failure, password reset, Web RCP and App RCP investigations.

It is a planning template only. It does not call DataAgent, execute Hive SQL, access real platforms, or authorize enforcement.

Every generated plan should include:

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

## Template 1: Successful Login Records

Use table: `ks_rc_bs.ks_account_login_basic_info`

Use when:

- Successful login trail.
- Cross-device successful login.
- Login IP/device distribution.
- Historical successful login tracing.
- ATO chain entry point.

SQL template:

```sql
SELECT
    user_id,
    op_time,
    device_id,
    source_ip,
    client,
    login_type,
    province,
    city
FROM ks_rc_bs.ks_account_login_basic_info
WHERE p_date = '${p_date}'
  AND user_id = ${user_id};
```

Query plan block:

```yaml
query_goal: 查询某用户历史成功登录
selected_table: ks_rc_bs.ks_account_login_basic_info
reason_for_table_selection: 该表仅成功登录，9999 天全量历史，适合追溯异设备成功登录
partition_filters:
  - p_date = ${p_date}
entity_filters:
  - user_id = ${user_id}
key_fields:
  - user_id
  - op_time
  - device_id
  - source_ip
  - client
  - login_type
  - province
  - city
expected_signal: 是否存在异常时间、异常设备、异常 IP、异常 login_type 的成功登录
risk_if_missing: 如果无数据，只能说明该日期分区未发现成功登录，不代表没有登录失败、未走完流程或 resetPwd 事件
fallback_table: ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
no_data_interpretation: 不得作为无 ATO 反证，需要结合登录请求全量表和 RCP 风控表
```

## Template 2: Login Failure / Credential Stuffing / Abnormal Attempts

Use table: `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info`

Important spelling: `orign`, not `origin`.

Use when:

- Login failure.
- Credential stuffing.
- Brute force.
- Abnormal login attempts.
- Login full-chain tracing.

SQL template:

```sql
SELECT
    user_id,
    op_time,
    device_id,
    source_ip,
    login_type,
    finalloginresult,
    code,
    punish,
    hit_policies
FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
WHERE p_date = '${p_date}'
  AND p_action_type = 'login'
  AND user_id = ${user_id}
  AND finalloginresult != '1';
```

Query plan block:

```yaml
query_goal: 查询登录失败 / 撞库 / 异常尝试
selected_table: ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
reason_for_table_selection: 该表包含登录成功、失败和未完成流程，适合登录失败、撞库和暴力破解分析
partition_filters:
  - p_date = ${p_date}
  - p_action_type = 'login'
entity_filters:
  - user_id = ${user_id}
key_fields:
  - user_id
  - op_time
  - device_id
  - source_ip
  - login_type
  - finalloginresult
  - code
  - punish
  - hit_policies
expected_signal: 是否存在密集失败、验证码/拦截/封禁、异常 IP/设备、异常 login_type
risk_if_missing: 仅说明该过滤条件下未发现失败记录，不能排除成功接管、resetPwd 或其他渠道接管
fallback_table: ks_rc_bs.ks_account_login_basic_info
no_data_interpretation: 不得作为无盗号反证；需结合成功登录表、resetPwd 分区和 RCP 表
```

## Template 3: Password Reset Events

Use table: `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info`

SQL template:

```sql
SELECT
    user_id,
    op_time,
    device_id,
    source_ip,
    login_type,
    finalloginresult,
    code,
    punish,
    hit_policies
FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
WHERE p_date = '${p_date}'
  AND p_action_type = 'resetPwd'
  AND user_id = ${user_id};
```

Query plan block:

```yaml
query_goal: 查询改密相关登录事件
selected_table: ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
reason_for_table_selection: 该表按 p_action_type 区分 login / resetPwd，适合改密链路补证
partition_filters:
  - p_date = ${p_date}
  - p_action_type = 'resetPwd'
entity_filters:
  - user_id = ${user_id}
key_fields:
  - user_id
  - op_time
  - device_id
  - source_ip
  - login_type
  - finalloginresult
  - code
  - punish
  - hit_policies
expected_signal: 改密是否发生在异常成功登录后、是否存在异常设备/IP、是否命中风控
risk_if_missing: 无 resetPwd 记录不代表无 ATO；可能是其他接管后置动作
fallback_table: ks_rc_bs.ks_account_login_basic_info
no_data_interpretation: 只作为改密链路缺口，不作为无风险反证
```

## Template 4: Web-side RCP Risk Events

Use table: `ks_rc_arch.antispam_feature_map_default_partitioned`

Use when:

- Web login / posting / interaction / API risk events.
- Web/H5 ATO or protocol risk evidence.
- Near-30-day Web RCP risk/interception.

SQL template:

```sql
SELECT
    source_id,
    target_id,
    action_type,
    device_id,
    source_ip,
    time,
    params
FROM ks_rc_arch.antispam_feature_map_default_partitioned
WHERE p_date = '${p_date}'
  AND p_hourmin BETWEEN '${start_hourmin}' AND '${end_hourmin}'
  AND p_action_type = '${p_action_type}'
  AND source_id = '${user_id}'
LIMIT 100;
```

Query plan block:

```yaml
query_goal: 查询 Web 端风控拦截事件
selected_table: ks_rc_arch.antispam_feature_map_default_partitioned
reason_for_table_selection: 该表是 Web 端 RCP 风控日志，30 天窗口内适合补 Web/H5 风控事件
partition_filters:
  - p_date = ${p_date}
  - p_hourmin between ${start_hourmin} and ${end_hourmin}
  - p_action_type = ${p_action_type}
entity_filters:
  - source_id = ${user_id}
key_fields:
  - source_id
  - target_id
  - action_type
  - device_id
  - source_ip
  - time
  - params
expected_signal: Web/H5 登录、发布、互动或接口风控事件是否与 ATO 时间线对齐
risk_if_missing: 超过 30 天或无命中只能标 source_gap，不能作为无风险反证
fallback_table: ks_raw_log_v2.antispam_feature_map_partitioned
no_data_interpretation: Web RCP no_data 不是无 ATO 证明；需结合 App RCP、登录表和发布/行为审计
```

## Template 5: App-side RCP Risk Events

Use table: `ks_raw_log_v2.antispam_feature_map_partitioned`

Use when:

- App-side risk events.
- Mobile strategy hits.
- App posting / login / interaction / protocol risk evidence.

SQL template:

```sql
SELECT
    source_id,
    target_id,
    action_type,
    device_id,
    source_ip,
    time,
    params
FROM ks_raw_log_v2.antispam_feature_map_partitioned
WHERE p_date = '${p_date}'
  AND p_hourmin BETWEEN '${start_hourmin}' AND '${end_hourmin}'
  AND p_action_type = '${p_action_type}'
  AND source_id = '${user_id}'
LIMIT 100;
```

Query plan block:

```yaml
query_goal: 查询 App 端风控拦截事件
selected_table: ks_raw_log_v2.antispam_feature_map_partitioned
reason_for_table_selection: 该表是 App 端 RCP 风控日志，50 天窗口内适合补移动端登录/发布/互动/协议风险事件
partition_filters:
  - p_date = ${p_date}
  - p_hourmin between ${start_hourmin} and ${end_hourmin}
  - p_action_type = ${p_action_type}
entity_filters:
  - source_id = ${user_id}
key_fields:
  - source_id
  - target_id
  - action_type
  - device_id
  - source_ip
  - time
  - params
expected_signal: App 端风控事件是否与异常登录、改密、发布或互动链路对齐
risk_if_missing: 超过 50 天或无命中只能标 source_gap；不能作为无风险反证
fallback_table: ks_rc_arch.antispam_feature_map_default_partitioned
no_data_interpretation: App RCP no_data 不是无 ATO 证明；需结合登录成功表、登录请求全量表和业务行为审计
```

## Batch ATO Query Plan Shape

When Batch Risk Clustering meets ATO / login-chain batch problems, output:

```yaml
query_goal:
selected_table:
reason_for_table_selection:
partition_filters:
entity_filters:
key_fields:
expected_signal:
risk_if_missing:
fallback_table:
no_data_interpretation:
```

Example:

```yaml
query_goal: 查询批量用户历史成功登录
selected_table: ks_rc_bs.ks_account_login_basic_info
reason_for_table_selection: 该表仅成功登录，9999 天全量历史，适合追溯异设备成功登录
partition_filters: p_date between ${start_date} and ${end_date}
entity_filters: user_id in (...)
key_fields: user_id, op_time, device_id, source_ip, login_type, app_ver, province, city
expected_signal: 是否存在异常时间、异常设备、异常 IP、异常 login_type 的成功登录
risk_if_missing: 如果无数据，只能说明该日期分区未发现成功登录，不代表没有登录失败或未走完流程
fallback_table: ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
no_data_interpretation: 不得作为无 ATO 反证，需要结合登录请求全量表和 RCP 风控表
```

## Safety Guardrails

- Do not execute SQL.
- Do not call DataAgent.
- Do not generate SQL without partition filters.
- For App/Web RCP tables, require `p_date + p_hourmin + p_action_type`.
- Do not treat online login log no-data as historical no-login proof.
- Do not mix success-only and full-login-request tables.
- Do not output raw `params`, raw request payloads, credential fields, cookie, token, session, authorization, or headers.
