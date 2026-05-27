# P0 Multisource Orchestration Gate Patch v1

## Goal

Fix the single-user account security / ATO execution gap where `user_login_unified_log` could return `no_data` and the agent stopped without running the rest of the P0 source sequence.

This is a minimal rules / playbook / regression patch. It does not access live platforms, call DataAgent, change gateway / safeBins / tools, probe track-analysis endpoints, or repackage a release.

## Changes

- Added a P0 multisource orchestration gate for single-user account security / ATO / login anomaly cases.
- Clarified that login log status `completed`, `no_data`, `auth_failed`, `timeout`, or `parse_error` is never terminal by itself.
- Required the default P0 sequence:
  - `user_login_unified_log`
  - Weapon USER_ID to DEVICE_ID graph via `/apiv2/graphData`
  - Weapon device risk via `/apiv2/riskData`
  - Tianshi strategy hit summary when required fields exist
  - Archives profile availability check
- Required every source to checkpoint as completed / no_data / blocked / auth_failed / timeout / parse_error / not_checked.
- Added a Weapon hard rule: do not use `/api/graphData` as default execution guidance; use `/apiv2/graphData` and `/apiv2/riskData`.
- Added a track-analysis execution warning: an API contract does not make a source completed unless the current runtime has a verified executable endpoint.

## Regression Coverage

- `SINGLE-USER-P0-MULTISOURCE-NO-STOP-AFTER-LOGINLOG-001`
- `WEAPON-APIV2-PATH-HARD-RULE-001`
- `LOGINLOG-NODATA-DOES-NOT-END-JUDGEMENT-001`
- `TRACK-ANALYSIS-ENDPOINT-NOT-CONFIRMED-NOT-COMPLETED-001`

## Boundaries

- No real platform access.
- No DataAgent call.
- No gateway / safeBins / tools change.
- No track-analysis endpoint probing.
- No release repackaging.
- No git commit.
