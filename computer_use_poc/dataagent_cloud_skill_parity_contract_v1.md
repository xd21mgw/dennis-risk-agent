# DataAgent Cloud Skill Parity Contract v1

## Verified Fact

Cloud Dennis/DataAgent Skill has successfully interacted with DataAgent. The local full_runtime connector should align with that cloud Skill contract instead of redefining a new DataAgent API schema from scratch.

Local status:

```yaml
cloud_skill_verified_contract: true
local_connector_contract_ready: true
local_live_verified: false
```

Cloud verification does not prove local live verification. Local live execution still requires an explicit follow-up test with per-call authorization.

## Known Entry

```yaml
channel: Conversational API
method: POST
endpoint: /v1/chat/completions/full
full_url: https://video-data.corp.kuaishou.com/v1/chat/completions/full
```

Current non-goals:

- no SDK
- no CLI
- no RPC
- no MCP
- no available structured-query API

## Request Payload

The cloud Skill request payload shape is:

```yaml
payload:
  messages:
    - role: system
      content: data boundary, readonly, sensitive output, and response formatting instructions
    - role: user
      content: structured prompt with task, tables, fields, filters, time window, max rows, and no-data boundary
  stream: false
  session_id: caller/runtime scoped id
  user_id: requester or approved runtime user id
```

Local parity goal:

- Dennis can construct the same payload shape.
- `stream` defaults to `false`.
- Prompt includes Dennis recommended source tables and candidate-source layering.
- Dry-run mode emits prompt and SQL candidate without API execution.

## Structured Prompt Format

The local prompt must carry:

```yaml
task_type:
business_context:
reason:
entity_type:
entity_ids:
time_window:
data_sources:
  recommended_source:
  candidate_source:
fields:
filters:
group_by:
max_rows:
dry_run:
no_data_boundary:
sensitive_output_boundary:
authorization_scope:
```

Table source layering remains:

- `recommended_source`: Dennis registry / playbook selected table.
- `candidate_source`: DataAgent suggested or unverified source requiring review.

## Step Response Types

Known step types:

- `MODEL_THINKING`
- `TOOL_CALL`
- `MODEL_ANSWER`
- `AGENT_END`

Evidence handling:

- Dennis extracts `MODEL_ANSWER` as the only user-displayable explanation and evidence summary source.
- `MODEL_THINKING` is ignored for evidence.
- `TOOL_CALL` can provide provenance such as `query_id`, generated SQL, table names, and trace handle, but it cannot be used directly as a business conclusion.
- `AGENT_END` is terminal metadata only.

## Local Normalization Contract

The local normalizer must support:

- extract `MODEL_ANSWER`
- parse SQL block from `MODEL_ANSWER`
- parse Markdown table from `MODEL_ANSWER`
- preserve `TOOL_CALL.query_id` / `TOOL_CALL.generated_sql` as provenance only
- output `status=sql_generated` when SQL is present but no table/result rows exist
- output `status=completed` when normalized table rows exist
- output `status=no_data` only when MODEL_ANSWER states no data
- output `permission_denied` / `failed` / `timeout` into `source_quality`
- block or redact sensitive fields

## Parity Check Goal

Local parity check does not call DataAgent. It must prove:

```yaml
same_request_shape_can_be_constructed: true
cloud_skill_mock_response_can_be_normalized: true
MODEL_ANSWER_extracted: true
TOOL_CALL_provenance_preserved_not_evidence: true
local_live_verified: false
```

Passing parity check means `cloud_skill_verified_contract + local_connector_contract_ready`, not local live execution.

