# DataAgent Local Dry-Run Parity Plan v1

## Goal

Plan B: DataAgent local live parity dry-run.

The goal is to verify that local full_runtime can construct the same Conversational API payload shape used by the cloud Dennis/DataAgent Skill, then parse step-based JSON and `MODEL_ANSWER` through the local normalizer.

This plan validates:

- local request builder
- API payload shape
- `MODEL_ANSWER` parser
- `source_quality` mapping
- provenance mapping for `TOOL_CALL` / generated SQL / query id / trace handle

## Non-Goals

- Do not query real business data in this round.
- Do not submit SQL.
- Do not call Hive.
- Do not mark `local_live_verified`.
- Do not use SDK / CLI / RPC / MCP.
- Do not use structured-query API as a current interface.

## Execution Boundary

```yaml
mode: local_live_parity_dryrun
dry_run: true
default_real_http_call: false
real_dataagent_api_called_by_default: false
hive_called: false
sql_submitted: false
```

Real HTTP dry-run is only allowed in a future step with both:

- explicit user authorization for this one dry-run call
- `--allow-live-dry-run`

## Conversational API

```yaml
method: POST
endpoint: /v1/chat/completions/full
full_url: https://video-data.corp.kuaishou.com/v1/chat/completions/full
payload:
  messages:
    - role: system
      content: readonly and sensitive-output contract
    - role: user
      content: structured prompt
  stream: false
  session_id: local parity safe id
  user_id: requester safe id
```

## Response Handling

DataAgent response is step-based JSON.

Known step types:

- `MODEL_THINKING`
- `TOOL_CALL`
- `MODEL_ANSWER`
- `AGENT_END`

Evidence boundary:

- Only `MODEL_ANSWER` may enter evidence explanation.
- `TOOL_CALL`, generated SQL, `query_id`, and trace handle are provenance only.
- `MODEL_THINKING` is ignored for evidence.
- `AGENT_END` is terminal metadata only.

## Source Quality Mapping

```yaml
source_quality_mapping:
  completed:
    meaning: MODEL_ANSWER contains normalized result rows
  sql_generated:
    meaning: SQL generated but not executed
    evidence_allowed: false
  pending:
    evidence_allowed: false
    source_quality: pending_execution_not_evidence
  failed:
    evidence_allowed: false
    source_quality: failed_not_no_risk
  timeout:
    evidence_allowed: false
    source_quality: timeout_not_no_risk
  no_data:
    evidence_allowed: false
    source_quality: no_data_not_risk_exclusion
  permission_denied:
    evidence_allowed: false
    source_quality: permission_denied_not_no_risk
```

`no_data` is not no-risk evidence.

## Acceptance Criteria

Local dry-run parity is ready when:

- `--mock` parses cloud Skill mock successfully.
- `--print-payload --case single_user_ato` emits Conversational API payload without HTTP call.
- `--print-payload --case strategy_hit_login_timeline` emits Conversational API payload without HTTP call.
- payload contains `messages`, `stream=false`, `session_id`, and `user_id`.
- `dry_run=true` is present in the structured prompt.
- output explicitly reports `real_dataagent_api_called=false`, `hive_called=false`, and `sql_submitted=false`.

