# Weapon /apiv2 Capability Recheck v2.6

## 1. Run Status

```yaml
test_stage: v2.6_semi_open
run_type: weapon_apiv2_capability_recheck
real_platform_query_by_codex: false
source_of_result: internal_agent_semi_open_validation
new_platform_hand_added: false
real_read_logic_changed: false
```

## 2. Path Correction

```yaml
previous_incorrect_interpretation: weapon_permission_blocked
corrected_interpretation: UI path blocked / path_error
ui_path:
  - /anti-device/*
api_path:
  - /apiv2/*
notes:
  - /anti-device/* is a frontend UI path and may be blocked by AMC permission middleware.
  - /anti-device/* blocked by AMC must not be generalized to Weapon API permission_blocked.
  - Weapon core readonly API should prefer /apiv2/*.
```

## 3. Verified API Paths

### user_to_device graphData

```yaml
endpoint: /apiv2/graphData
method: GET
query_template: "/apiv2/graphData?product=KUAISHOU&productName=KUAISHOU&groupValue={userId}&groupKey=USER_ID&dimKey=DEVICE_ID&searchLevel=2"
status: api_pass_but_test_user_no_data
interpretation:
  - The API path is reachable.
  - The tested userId returned no_data.
  - no_data means current graph source has no related entity under this query condition.
  - no_data is not permission_blocked.
  - no_data must not be written as user has no devices.
fallback_candidates:
  - unified login log device distribution
  - archives center recent login device
```

### device_to_user graphData

```yaml
endpoint: /apiv2/graphData
method: GET
query_template: "/apiv2/graphData?product=KUAISHOU&productName=KUAISHOU&groupValue={deviceId}&groupKey=DEVICE_ID&dimKey=USER_ID&searchLevel=2"
status: pass
validated_input_example: ANDROID_c1ab0d1eb0a0d1c0
response_summary:
  code: 0
  nodes: 3
  edges: 2
  related_user_count: 2
interpretation:
  - Related users are candidate associated users.
  - Social-ban / risk-tag signals on related users are follow-up leads.
  - Association is not a final risk conclusion.
```

### Device SDK riskData

```yaml
endpoint: /apiv2/riskData
method: GET
query_template: "/apiv2/riskData?product=KUAISHOU&deviceIds={deviceId}"
status: pass
recommended_input: mobile did such as ANDROID_xxx
not_recommended_input: web_ prefixed device id
sample_device_side_findings:
  - no SIM card
  - APK launch count less than 10
  - phone system service Hook
  - frida=0
severity_note:
  hook_level_50: high_severity_device_side_evidence
interpretation:
  - Hook / root / frida / simulator / proxy / repack are device-side evidence.
  - High-severity Hook evidence cannot alone classify the user as cheating or ATO.
```

## 4. Guardrails

- Do not call `/anti-device/*` as the canonical API path.
- Do not convert UI path blocked into Weapon API permission_blocked.
- Do not use `web_` prefixed device ids as primary Device SDK test objects.
- Do not treat graphData no_data as no relationship fact.
- Do not treat device relation as risk conclusion.
- Do not treat Device SDK risk tags as final user-level risk classification.
