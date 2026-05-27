# Dennis Risk Agent Tool / Platform Call Gate

Guard marker: `DENNIS_ROUTING_GUARD_V1`.

This file is the lightweight platform-call preflight entry for release / overlay / live runtime validation. It does not contain credentials, auth state, cookies, tokens, sessions, headers, or raw platform responses.

Before any Dennis Risk Agent realtime platform source call, read:

1. `computer_use_poc/platform_call_playbook_index.md`
2. The platform-specific playbook referenced by that index.
3. `computer_use_poc/release_overlay_readiness_checklist.md` before release / overlay.
4. `computer_use_poc/runtime_config_apply_checklist_v1.md` before live apply.

## Hard Boundaries

- Realtime readonly API queries do not require user confirmation when required fields are present.
- DataAgent / Hive / big batch / write / high-risk operations require query plan or explicit confirmation.
- Do not use historical observation as a no-cache realtime result.
- Do not use curl+cookie, manual header injection, or arbitrary URL runner input.
- Do not let main agent take over platform querying after `dennis-risk-agent` timeout.
- Every source must emit checkpoint and `source_quality`.
- `no_data`, `blocked`, `timeout`, and `auth_failed` are not no-risk counter evidence.

## Required Platform Preflight

```yaml
platform_call_preflight:
  playbook_read: true
  selected_platform:
  selected_source:
  input_fields:
  required_fields_missing: []
  access_method: readonly_wrapper_api | browser_same_origin_fetch | browser_ui_observation
  fallback_allowed:
  no_data_boundary:
```

## Platform Index

- Unified login log: runner first, no arbitrary URL.
- Weapon: `USER_ID -> DEVICE_ID` uses graphData; device risk uses riskData only after device id is available.
- Tianshi: strategy hit inventory uses sourceId / eventId / time window and fastQueryHbase; not simple userId direct lookup.
- Archives Center: SPA profile activation and same-origin API direct read before declaring unavailable.
- Track-analysis: stats-first; no SPA loop.
