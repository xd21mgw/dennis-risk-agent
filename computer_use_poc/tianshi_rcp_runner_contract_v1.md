# Tianshi RCP Runner Contract v1

## Purpose

`bin/tianshi_rcp_runner` is the controlled readonly entrypoint for Tianshi strategy-hit and RCP event-list source calls in full_runtime.

Current implementation status:

- dry-run / contract-check: available.
- future live readonly mode: declared but disabled by default.
- live platform verification: not done in this patch.

The runner exists to eliminate runner-missing `tool_gap` for explicit Tianshi/RCP source routing. It must not pretend that dry-run output is live platform evidence.

## Supported Actions

```yaml
supported_actions:
  - strategy_hit_overview_lookup
  - rcp_event_list_readonly
```

Action mapping:

| action | source_name | intended readonly source |
|---|---|---|
| `strategy_hit_overview_lookup` | `tianshi_strategy_hit` | fastQueryHbase strategy-hit overview |
| `rcp_event_list_readonly` | `rcp_event_list` | RCP eventList request-level readonly evidence |

## Invocation

Contract check, no platform access:

```bash
bin/tianshi_rcp_runner --mode contract-check
```

Strategy-hit dry-run for the 544963630 style case:

```bash
bin/tianshi_rcp_runner \
  --mode dry-run \
  --action strategy_hit_overview_lookup \
  --entity-type user_id_candidate \
  --entity-id 544963630 \
  --from-timestamp 1710000000000 \
  --to-timestamp 1710086400000 \
  --time-window-inferred \
  --entity-type-inferred \
  --product KUAISHOU \
  --app-name KUAISHOU
```

RCP event-list dry-run:

```bash
bin/tianshi_rcp_runner \
  --mode dry-run \
  --action rcp_event_list_readonly \
  --entity-type user_id_candidate \
  --entity-id 544963630 \
  --from-timestamp 1710000000000 \
  --to-timestamp 1710086400000 \
  --time-window-inferred \
  --entity-type-inferred \
  --product KUAISHOU \
  --app-name KUAISHOU
```

## Required Inputs

```yaml
required_inputs:
  entity_type:
    allowed:
      - user_id_candidate
      - source_id
      - source_id_candidate
      - event_id
      - event_id_candidate
      - device_id
  entity_id:
    rule: bounded opaque identifier; user_id_candidate must be numeric
  bounded_time_range:
    from_timestamp: epoch milliseconds
    to_timestamp: epoch milliseconds
    rule: from_timestamp < to_timestamp
  product_or_app:
    product: default KUAISHOU
    app_name: default KUAISHOU
optional_inputs:
  event_type:
    applies_to: rcp_event_list_readonly
```

## Inference Support

```yaml
inference_support:
  entity_type_user_id_candidate:
    rule: pure numeric id + case/ATO/strategy-hit/account-security context may be treated as user_id_candidate
    must_mark:
      - entity_type_inferred=true
      - confidence
      - caveat
  time_window_inferred:
    rule: if user omitted a time window, runtime may use bounded default window from source playbook
    must_mark:
      - time_window_inferred=true
      - default_window_not_full_history=true
```

For the case:

```text
544963630 这个 case 有没有策略命中能辅助判断？
```

full_runtime should infer:

```yaml
entity_type: user_id_candidate
entity_id: "544963630"
time_window_inferred: true
explicit_target_source:
  - tianshi_strategy_hit
  - rcp_event_list
```

Dry-run output means the runner contract is present; it does not mean any strategy hit was or was not found.

## Output Schema

Required top-level fields:

```yaml
source_status:
records_count:
hit_summary:
policy_code_summary:
risk_decision_summary:
time_range:
source_quality:
redaction_applied:
```

Additional standard fields:

```yaml
schema_version: tianshi_rcp_runner_observation_v1
source_name:
action:
source_card:
source_checkpoint_private:
redaction:
sensitive_output: false
real_platform_request_executed: false
platform_write_action: false
dataagent_called: false
readonly: true
collected_at:
```

`hit_summary`:

```yaml
dry_run_only:
has_strategy_hit:
production_policy_hit_count:
interpretation:
```

`policy_code_summary`:

```yaml
policy_codes:
raw_policy_payload_output: false
```

`risk_decision_summary`:

```yaml
distribution:
dry_run_only:
```

`source_quality`:

```yaml
permission_status:
auth_status:
response_type:
reliability_level:
failure_reason:
no_data_not_risk_exclusion: true
tool_gap: false
runner_present: true
live_readonly_verified:
explicit_source_not_silently_skipped:
```

## Source Status

Allowed statuses:

```yaml
failure_statuses:
  - completed
  - no_data
  - auth_failed
  - blocked
  - timeout
  - parse_error
  - tool_gap
  - dry_run_only
```

Current local contract behavior:

- `--mode contract-check`: `source_status=dry_run_only`
- `--mode dry-run`: `source_status=dry_run_only`
- `--mode live`: `source_status=dry_run_only`, `failure_reason=live_mode_not_enabled`
- invalid invocation: `source_status=blocked`

## Failure And Evidence Boundary

- `dry_run_only` is not platform evidence.
- `dry_run_only` must not be interpreted as `no_data`.
- `tool_gap=false` only means the runner entry exists; it does not mean live execution is verified.
- `no_data`, `blocked`, `timeout`, `auth_failed`, `parse_error`, `tool_gap`, and `dry_run_only` cannot be used as low-risk or no-risk evidence.
- Strategy hit, when live-verified in the future, is auxiliary source evidence, not final ATO judgement.
- RCP event-list, when live-verified in the future, is request-level evidence, not a full user-history query.

## Forbidden

```yaml
forbidden:
  - arbitrary_url
  - raw_cookie
  - raw_header
  - write_operation
  - auth_debug
  - SmartSSOSession_debug
  - sso_state_file_read
  - raw_platform_response_dump
  - credential_material_output
```

The runner must not output cookie, token, session, header, authorization, password, or equivalent credential material.

