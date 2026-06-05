# Raw Reference Retention & Redaction Layering Contract v1

## Purpose

Prevent display-layer redaction from corrupting internal source chaining. Risk entities may need to be retained as raw references inside the current task execution context, while user-visible answers, run logs, and release artifacts remain redacted.

This contract is generic. It is not limited to `device_id`.

## Layers

| Layer | Raw reference allowed | Purpose |
|---|---:|---|
| `tool_call_internal` | conditional | Build the next approved readonly platform request. |
| `source_checkpoint_private` | conditional | Preserve current-task evidence provenance and downstream source inputs. |
| `source_chaining` | conditional | Pass exact identifiers to approved next sources. |
| `evidence_card_user_visible` | no | Show alias, masked id, counts, summaries, or safe references only. |
| `final_answer` | no | Show conclusion, evidence summary, source quality, and boundaries. |
| `run_log` | no | Record behavior, rules, validation status, and redacted examples only. |

Credential-like material is never retained in any layer.

## Reference Types

| ref_type | raw_allowed_in_internal_checkpoint | raw_allowed_in_tool_call | raw_allowed_in_run_log | raw_allowed_in_final_answer | masking_format | alias_format | allowed_downstream_sources |
|---|---:|---:|---:|---:|---|---|---|
| `user_id` | true | true | false | false | `user_***<last4>` | `user_ref_<n>` | login log, Archives, Weapon graphData, Tianshi source/event lookup, DataAgent query plan |
| `device_id` | true | true | false | false | `<prefix>_***<last4>` | `device_ref_<n>` | Weapon riskData, track-analysis device queries, Device SDK query plan |
| `event_id` | true | true | false | false | `event_***<last4>` | `event_ref_<n>` | rcpEventDetail, Tianshi attribution, event detail query plan |
| `source_id` | true | true | false | false | `source_***<last4>` | `source_ref_<n>` | fastQueryHbase, eventList, DataAgent query plan |
| `policy_code` | true | true | true_if_business_code_only | true_if_business_code_only | keep code or `policy_ref_<n>` if sensitive context | `policy_ref_<n>` | policy detail, policy tree, policy attribution, release records |
| `ip` | true | true | false | false | `<a>.<b>.*.*` or `ip_hash_<n>` | `ip_ref_<n>` | IP cluster query plan, Hive query plan, risk relation summary |
| `phone` | false_by_default | false_by_default | false | false | `phone_masked` | `phone_ref_<n>` | none unless explicit approved identity workflow |
| `real_name` | false | false | false | false | `real_name_redacted` | `real_name_ref_<n>` | none |
| `id_card` | false | false | false | false | `id_card_redacted` | `id_ref_<n>` | none |
| `token/session/cookie/header/password` | false | false | false | false | `credential_redacted` | none | none |

## Required Source Checkpoint Schema

```yaml
source_checkpoint:
  source_name:
  source_status:
  raw_references:
    - ref_type:
      raw_reference_safe_id:
      alias:
      masked_value:
      allowed_downstream_sources:
      retention_scope: current_task_only
  redaction:
    redaction_applied: true
    raw_reference_retained_for_followup: true
    sensitive_output: false
  provenance:
    executor_agent:
    source_observation_id:
    current_task_only: true
```

`raw_reference_safe_id` means the internal checkpoint has a safe handle to the raw value for the current task. The handle must not be the masked value. The raw value itself must not be printed in final answers or run logs.

Every `source_quality` must include:

```yaml
source_quality:
  redaction_applied: true
  raw_reference_retained_for_followup: true | false
  sensitive_output: false
  provenance: current_task_observation
```

## Source Chaining Examples

- Weapon `graphData` raw `device_id` -> Weapon `riskData`.
- Tianshi `fastQueryHbase` raw `event_id` + occur time -> `rcpEventDetail`.
- `rcpEventDetail` raw `policy_code` -> policy detail / policy attribution.
- Login log raw `ip` -> IP clustering / Hive query plan.
- Archives raw publish event id -> publish device trace.
- `user_id` -> login log / Archives / Weapon graphData / DataAgent query plan.

### Weapon graphData -> riskData

For Weapon graphData, extract candidate device ids from `payload.data.pointInfoMap`.

Rules:

- Treat pure numeric nodes as `user_id` nodes and filter them out before riskData chaining.
- Retain raw device ids only in `source_checkpoint_private.raw_device_ids_for_chaining`.
- Publish `masked_device_ids` for evidence card / final answer display.
- Set `device_id_redaction_policy=raw_in_chaining_field_masked_in_display`.
- `riskData` must use the retained raw reference safe handle / current-task raw value, not `masked_device_ids`.
- If no raw device id is retained, `riskData` must be `missing_required_fields` or `not_checked`.

## Forbidden Patterns

- `masked_device_id` used as Weapon `riskData` input.
- `masked_event_id` used as `rcpEventDetail` input.
- `redacted_ip` used for IP cluster query.
- Full raw id printed in final answer.
- token / session / cookie / header / password saved to checkpoint.
- main direct bypass result treated as strong business evidence.
- `api_direct_confirmed` capability status treated as completed without current-task observation.

## Validation Rules

- Downstream source input must use a raw reference retained in `tool_call_internal` / `source_checkpoint_private` / `source_chaining`, not `masked_value`.
- If a source uses a cross-source entity, mark `cross_source_entity=true`, `entity_source`, and retain a current-task raw reference safe id.
- If raw reference is not retained, the downstream source must be `missing_required_fields` or `not_checked`; it must not be marked `completed`.
- Credential-like material must fail closed if it appears in `raw_references`.
- Run logs may mention reference type, alias, masking format, and validation result, but not raw values.
