# Platform Access Execution v0.1 Answer Template Overlay

This focused runtime overlay replaces the full mother-body answer template for smoke validation. It only contains Platform Access Execution v0.1 output requirements.

## Required Blocks

Execution answers that use platform sources must include:

- `platform_access_observations`
- `evidence_card`
- `source_quality`
- `routing_metadata`
- `missing_evidence`
- `next_action`

## Platform Access Observation

```yaml
platform_access_observation:
  platform_key:
  source_name:
  api_name:
  invocation_method:
  input_entity_type:
  required_params: []
  upstream_source:
  params_valid:
  source_status:
  records_count:
  schema_valid:
  output_fields_observed: []
  failure_layer:
  source_quality:
    response_type:
    http_status:
    no_data_not_risk_exclusion: true
    no_hit_not_risk_exclusion: true
  raw_reference_retained_for_followup:
  redaction_applied: true
  next_action:
```

## Interpretation Rules

- Classify invocation chain before auth.
- Classify parameter contract before permission.
- Classify local API/path availability before platform availability.
- `completed_no_data`, `completed_no_hit`, `timeout`, `blocked`, and `auth_failed` are source states, not no-risk evidence.
- `missing_upstream_id` means downstream execution is not triggered until upstream fields are available.
- RCP `eventList` is primary for strategy-hit event list; `fastQueryHbase` is fallback.
- Weapon `riskData` is direct device-level evidence when `deviceId` is available.
- Archives user analysis remains ATO P0; abnormal publish makes publish chain P0-conditional.
- Track-analysis event-day activity mismatch is auxiliary evidence, not final judgement.

## Routing Metadata

Every formal answer must end with YAML `routing_metadata` and set:

```yaml
routing_metadata:
  platform_called:
  dataagent_called: false
  direct_tool_bypass: false
  sensitive_output: false
  redaction_applied: true
  final_status:
```
