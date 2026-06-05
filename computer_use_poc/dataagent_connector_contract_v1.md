# DataAgent Connector Contract v1

## Current Channel

Current usable DataAgent entrypoint:

```text
POST https://video-data.corp.kuaishou.com/v1/chat/completions/full
```

This is the Conversational API MVP channel. Dennis must construct a structured natural-language prompt, send it through the Conversational API only after per-call user authorization, then normalize DataAgent's step-based response into source observation and evidence-card fields.

## Cloud Skill Verified Contract

Status: `cloud_skill_verified_contract`.

The cloud Dennis/DataAgent Skill has already successfully interacted with DataAgent through the Conversational API. The known entry parameters and payload structure are aligned with this local connector design:

- endpoint: `POST /v1/chat/completions/full`
- payload: `messages`, `stream=false`, `session_id`, `user_id`
- response: step-based JSON with `MODEL_THINKING`, `TOOL_CALL`, `MODEL_ANSWER`, and `AGENT_END`

The local full_runtime connector target is therefore parity with the cloud Skill contract, not redefining the DataAgent API from scratch. Local work should focus on:

- request parity check
- prompt dry-run generation
- mock step-response normalization
- later explicitly authorized live API smoke test

Boundary:

- cloud Skill verified does not mean local live verified.
- Before a local live readonly check succeeds, do not mark `local_live_verified`.
- The local status is `cloud_skill_verified_contract + local_connector_contract_ready`.
- Plan B local live parity dry-run status is `local_live_parity_dryrun_pending`.
- Real execution still requires per-call user authorization.
- Readonly, sensitive-field interception, and `no_data_not_risk_exclusion` remain mandatory.

## Currently Unavailable

The following interfaces are not available in the current runtime contract:

- SDK
- CLI
- RPC
- MCP
- structured-query API

Structured-query schema may be used as a mid-term design direction only. It must not be described as an available live interface.

## Dennis Boundary

- Default mode is `dry_run_sql_generation`: generate a query plan / prompt / SQL candidate without calling DataAgent.
- `dry_run=true` only means SQL generation / dry-run response. It does not mean data was queried, Hive ran, or evidence completed.
- `sql_generated` must not enter completed evidence. It is pending execution / provenance only.
- Real execution requires explicit user authorization for each query, including table, entity set, time window, fields, and business reason.
- Any future `dry_run=false` execution requires per-call authorization before the request is sent.
- DataAgent is readonly for Dennis runtime. Write operations, mutation, table creation, table overwrite, policy operation, account operation, and enforcement are forbidden.
- Do not output cookie, token, session, header, phone, email, id card, password, or equivalent sensitive plaintext.
- `no_data` is not no-risk evidence.
- `pending`, `running`, `failed`, `timeout`, and `permission_denied` must enter `source_quality`; none can be used as low-risk or no-risk proof.
- Pending DataAgent execution is not evidence. It can only be reported as `missing_hive_result` / `dataagent_query_pending`.
- DataAgent/Hive remains a follow-up source for offline history, aggregation, long-window gaps, cross-table validation, and batch clustering; it does not replace online P0 readonly sources.

## Local Network Readiness Boundary

`computer_use_poc/dataagent_network_readiness_check.py` is a local connectivity preflight only. It is not a DataAgent business query runner.

Supported command:

```text
python3 computer_use_poc/dataagent_network_readiness_check.py --json
```

Configuration:

- `DATAAGENT_BASE_URL`: required unless `DATAAGENT_ENDPOINT_URL` is set.
- `DATAAGENT_ENDPOINT_URL`: optional full endpoint override.
- `DATAAGENT_ENDPOINT_PATH`: optional path override, default `/v1/chat/completions/full`.
- `DATAAGENT_HTTP_TIMEOUT_SECONDS`: optional timeout override.

Readiness checks:

- env configured
- DNS resolution
- TCP connection
- TLS handshake for HTTPS
- HTTP endpoint reachability
- read timeout classification

Allowed `network_status` values:

- `env_missing`
- `dns_failed`
- `tcp_failed`
- `tls_failed`
- `http_reachable`
- `auth_required`
- `permission_denied`
- `read_timeout`
- `unknown`

Boundary:

- No business DataAgent payload is sent.
- No Hive SQL is submitted.
- No `.ks_sso` file is read.
- No cookie/token/session/header is printed.
- No manual authentication header is constructed.
- `401` / `403` are permission boundaries, not connector contract failures.

## Supported Modes

```yaml
supported_modes:
  dry_run_sql_generation:
    live_api_call: false
    default: true
    output: query_plan, conversational_prompt, generated_sql_candidate
  authorized_live_query:
    live_api_call: true
    requires_per_call_user_authorization: true
    current_contract_status: connector_contract_ready_not_live_executable
  async_status_polling_future:
    live_api_call: future
    current_contract_status: design_only
```

## Conversational API Payload Boundary

Dennis-side request builder should produce:

```yaml
endpoint: https://video-data.corp.kuaishou.com/v1/chat/completions/full
method: POST
payload:
  messages:
    - role: system
      content: Dennis DataAgent connector boundary and output requirements
    - role: user
      content: structured prompt with task, tables, fields, filters, time window, max rows, no-data boundary
  stream: false
  session_id: runtime-generated safe id
  user_id: Dennis requester safe id or approved requester id
```

Network readiness probing is separated from business dry-run invocation. Connectivity checks must not send the Conversational API business payload, and business dry-run invocation remains gated by explicit `--allow-live-dry-run`.

## Step-Based Response Handling

DataAgent returns step-based JSON. Dennis must inspect step type and extract evidence only from `MODEL_ANSWER`.

Known raw step types:

- `MODEL_THINKING`
- `TOOL_CALL`
- `MODEL_ANSWER`
- `AGENT_END`

Rules:

- `MODEL_THINKING` is not evidence.
- `TOOL_CALL` is not evidence unless reflected in `MODEL_ANSWER` and normalized.
- `MODEL_ANSWER` is the only primary source for generated SQL, Markdown/table result, error, no-data, or permission outcome.
- `AGENT_END` can provide terminal metadata only.
- Raw step JSON must not be pasted into user-visible evidence.

## Normalized Output Boundary

Normalized DataAgent output must map to:

- `dataagent_response_schema_v1.yaml`
- source observation compatible fields:
  - `source_card`
  - `source_quality`
  - `source_checkpoint_private`
  - `redaction`

If only SQL is generated and no query result is returned:

```yaml
status: sql_generated
real_dataagent_query_executed: false
result_rows: []
row_count: 0
source_quality:
  pending_execution_not_evidence: true
```

Before any future `dry_run=false` request, Dennis must run the local SQL
quality gate against `generated_sql`. The gate does not execute SQL. It checks:

- table names are in the Dennis recommended / registered source set;
- required partition filters such as `p_date` are present;
- referenced fields are whitelisted for the requested account-security scope;
- credential secrets and strict PII fields are absent;
- scan scope is bounded by partition, entity filter, and `LIMIT`;
- DataAgent caveats do not require manual table / partition verification.

If DataAgent returns a caveat such as:

```text
Table not found in metadata catalog; verify table name & partition column before execution
```

then `dry_run_false_eligible=false` and Dennis must not proceed to
`dry_run=false`.

Field classification boundary:

- IP / device_id / DID / user_id / eventId / sourceId are
  `risk_entity_identifier` fields for risk analysis, not privacy fields by
  default.
- cookie / token secret / session / header / authorization / password, full
  phone, ID card, email, and raw real-name fields remain blocked.

If DataAgent returns a no-data result:

```yaml
status: no_data
no_data_reason:
source_quality:
  no_data_not_risk_exclusion: true
```

If permission or runtime fails:

```yaml
status: permission_denied | failed | timeout
source_quality:
  permission_status:
  failure_reason:
```

## Table Source Layering

DataAgent 提示词s may recommend tables, but Dennis must preserve the existing Hive registry layers:

- `recommended_source`: tables selected from Dennis registry / playbook.
- `candidate_source`: DataAgent-suggested table or additional table requiring review.

DataAgent output must not overwrite Dennis registry source selection when names conflict. Conflicts must be reported as source selection metadata.

## Forbidden

```yaml
forbidden:
  - live_call_without_per_call_authorization
  - structured_query_api_as_currently_available
  - SDK_CLI_RPC_MCP_claimed_available
  - write_operation
  - table_mutation
  - policy_or_account_operation
  - raw_cookie_output
  - raw_token_output
  - raw_session_output
  - raw_header_output
  - phone_plaintext_output
  - id_card_plaintext_output
  - MODEL_THINKING_as_evidence
  - TOOL_CALL_as_evidence_without_MODEL_ANSWER_normalization
  - no_data_as_no_risk
  - pending_or_failed_as_completed_evidence
```
