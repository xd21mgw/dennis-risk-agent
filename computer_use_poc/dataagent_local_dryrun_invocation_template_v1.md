# DataAgent Local Dry-Run Invocation Template v1

## Shared Conversational API Payload

```yaml
method: POST
endpoint: /v1/chat/completions/full
payload:
  messages:
    - role: system
      content: Dennis DataAgent readonly contract, MODEL_ANSWER-only evidence, sensitive-output boundary
    - role: user
      content: structured prompt
  stream: false
  session_id: local_dryrun_parity_<case_id>
  user_id: dennis_full_runtime_local
```

`dry_run=true` means SQL generation only. It is not evidence that rows were queried.

## Case 1: single_user_ato

Input:

```yaml
case_id: single_user_ato
task_type: SINGLE_USER_QUERY
user_id: "544963630"
time_window: 近 7 天
dry_run: true
max_rows: 1000
goal: 生成登录日志 / 设备 / IP / 安全行为补证 SQL
```

Structured prompt:

```text
Task type: SINGLE_USER_QUERY
Business context: single user ATO evidence dry-run
Entity: user_id=544963630
Time window: last 7 days, Asia/Shanghai, bounded
dry_run: true
max_rows: 1000

Recommended source tables:
- ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
- ks_rc_bs.ks_account_login_basic_info
- ks_rc_bs.account_security_basic_info
- kscdm.dim_ks_user_all

Recommended fields:
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

Generate SQL only. Do not execute Hive. Return final SQL or dry-run result only in MODEL_ANSWER.
No-data boundary: no rows under this bounded query is not no ATO and not no risk.
Sensitive output boundary: do not output phone, cookie, token, session, header, email, id_card or credential plaintext.
```

Conversational API payload:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "Dennis DataAgent readonly contract. Return step-based JSON. MODEL_ANSWER is the only evidence explanation. TOOL_CALL/query_id/generated_sql/trace are provenance only. Do not output sensitive plaintext."
    },
    {
      "role": "user",
      "content": "<structured prompt above>"
    }
  ],
  "stream": false,
  "session_id": "local_dryrun_parity_single_user_ato",
  "user_id": "dennis_full_runtime_local"
}
```

Expected response status:

- preferred: `sql_generated`
- possible dry-run response: `completed` only if DataAgent returns a synthetic dry-run table, not Hive result
- failure states: `permission_denied`, `failed`, `timeout`

Normalization expectation:

- extract `MODEL_ANSWER`
- parse generated SQL
- if no table result rows, normalize to `status=sql_generated`
- `pending_execution_not_evidence=true`

Source quality mapping:

```yaml
source_quality:
  dry_run: true
  dataagent_called: true only if future live dry-run HTTP is explicitly allowed
  hive_called: false
  sql_submitted: false
  no_data_not_risk_exclusion: true
```

## Case 2: strategy_hit_login_timeline

Input:

```yaml
case_id: strategy_hit_login_timeline
task_type: STRATEGY_HIT_QUERY
user_id: "544963630"
time_window: 近 7 天
dry_run: true
max_rows: 1000
goal: 生成策略命中 / RCP / 登录行为 timeline SQL
```

Structured prompt:

```text
Task type: STRATEGY_HIT_QUERY
Business context: strategy hit and login timeline alignment dry-run
Entity: user_id=544963630
Time window: last 7 days, Asia/Shanghai, bounded
dry_run: true
max_rows: 1000

Recommended source tables:
- ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
- ks_rc_arch.antispam_feature_map_default_partitioned
- ks_raw_log_v2.antispam_feature_map_partitioned

Recommended fields:
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

Generate SQL only. Do not execute Hive. Align login op_time and RCP/strategy event time into a bounded timeline.
Return final SQL or dry-run result only in MODEL_ANSWER.
Strategy hit is auxiliary evidence, not final ATO judgement.
No-data boundary: no RCP rows or no login rows under this filter is not no risk.
Sensitive output boundary: do not output phone, cookie, token, session, header, email, id_card or credential plaintext.
```

Conversational API payload:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "Dennis DataAgent readonly contract. Return step-based JSON. MODEL_ANSWER is the only evidence explanation. TOOL_CALL/query_id/generated_sql/trace are provenance only. Do not output sensitive plaintext."
    },
    {
      "role": "user",
      "content": "<structured prompt above>"
    }
  ],
  "stream": false,
  "session_id": "local_dryrun_parity_strategy_hit_login_timeline",
  "user_id": "dennis_full_runtime_local"
}
```

Expected response status:

- preferred: `sql_generated`
- failure states: `permission_denied`, `failed`, `timeout`

Normalization expectation:

- extract `MODEL_ANSWER`
- parse generated SQL
- preserve `TOOL_CALL.query_id` / `generated_sql` / trace as provenance only
- normalize SQL-only output to `status=sql_generated`

Source quality mapping:

```yaml
source_quality:
  dry_run: true
  hive_called: false
  sql_submitted: false
  pending_execution_not_evidence: true
  no_data_not_risk_exclusion: true
```

