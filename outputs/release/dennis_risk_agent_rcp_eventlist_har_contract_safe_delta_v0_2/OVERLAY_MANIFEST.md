# Overlay Manifest

Package: `dennis_risk_agent_rcp_eventlist_har_contract_safe_delta_v0_2`

Included files:

- `README.md`
- `OVERLAY_MANIFEST.md`
- `SAFE_DELTA_SUMMARY.md`
- `INTERNAL_AGENT_SYNC_INSTRUCTIONS.md`
- `VALIDATION_TODO.md`
- `computer_use_poc/platform_access/tianshi_rcp_api_contract_v0_1.yaml`
- `computer_use_poc/platform_access/failure_taxonomy_v0_1.yaml`

Included capability changes:

- RCP eventList request body contract.
- tableHeaderList object-array contract.
- string time field contract for startTime, endTime, and currentTime.
- eventV2 full query object contract.
- conditionList nested query-group contract.
- HTTP direct wording corrected to needs exact HAR-body replay.
- Failure taxonomy entries for request body shape and time format errors.

Excluded by design:

- Network-capture payloads.
- Transient runtime memory.
- Original pilot logs.
- Workspace-only TOOLS notes.
- Full runtime release assets.
- Auth-bearing material.
