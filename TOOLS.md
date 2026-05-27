# Dennis Risk Agent Tool / Platform Call Gate

Guard marker: `DENNIS_ROUTING_GUARD_V1`.

TOOLS restore marker: `TOOLS_MAIN_ENTRY_GUARD_FULL`.

This file is the lightweight platform-call preflight entry for release / overlay / live runtime validation. It does not contain credentials, auth state, cookies, tokens, sessions, headers, or raw platform responses.

## Overlay Protection

- Focused overlays must not include or overwrite top-level `AGENTS.md` or `TOOLS.md` by default.
- Only an explicit `main-entry patch` may include top-level `AGENTS.md` / `TOOLS.md`.
- Any overlay that includes top-level `AGENTS.md` or `TOOLS.md` must state why the main entry guard is intentionally changing, and must pass `runtime_preflight_check.py`.
- A short focused overlay that replaces this file with a stub is a release blocker.
- If `TOOLS_MAIN_ENTRY_GUARD_FULL` is missing after overlay, treat it as `tools_entry_guard_drift`.

## Source Orchestration Gate

- Business execution cases must select a source plan before platform source calls.
- `source_orchestration_check.py` is the canonical local validator for source plan and source completion matrix drift.
- Login-log-only execution is not sufficient for a final account security / ATO judgement.
- Weapon source calls must use `/apiv2/graphData` and `/apiv2/riskData`; `/api/graphData` is not a default path.

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
