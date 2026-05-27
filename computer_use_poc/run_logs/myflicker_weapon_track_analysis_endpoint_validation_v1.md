# Myflicker Weapon / Track-Analysis Endpoint Validation v1

## Goal

Persist the two myflicker live experiment findings into local playbook, source orchestration plan, validator, regression, and smoke tests so future internal agents do not guess URLs at execution time.

This patch is offline-only. It does not access real platforms, call DataAgent, change gateway / safeBins / tools, repackage a release, or commit git changes.

## Weapon Findings Solidified

- Default graph path:
  `/apiv2/graphData?product=KUAISHOU&productName=KUAISHOU&groupValue={userId}&groupKey=USER_ID&dimKey=DEVICE_ID&searchLevel=2`
- Default device risk path:
  `/apiv2/riskData?product=KUAISHOU&deviceIds={deviceId}`
- `/api/graphData` is not a default execution path and should fail validator checks.
- Mobile device id prefixes such as `ANDROID_` and `IOS_` must be preserved.
- Weapon `graphData=0` means no relation edge from the Weapon graph source, not proof that the user has no devices.
- If track-analysis `getDeviceIds` supplies a device id used for Weapon riskData, mark `cross_source_device_id=true`.

## Track-Analysis Findings Solidified

- `GET /dp/platform/app/analytics/v2/sequence/getLastestDateTime`
- `POST /dp/platform/app/analytics/v2/sequence/getDeviceIds`
- `POST /dp/platform/app/analytics/v2/sequence/getUseDuration`
- `POST /dp/platform/app/analytics/v2/sequence/profile`
- `profile` uses millisecond `startTime` / `endTime`, not `startDate` / `endDate`.
- `getUseDuration.rows` is a `{date, duration}` object array / dict structure, not a two-dimensional array.
- Do not guess `/api/profile`, `/rest/profile`, or `/api/user/profile`.
- Capability status is recorded as `api_direct_confirmed_with_cookie_state_fallback` in the playbook.

## Updated Files

- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/source_orchestration_plan_v1.yaml`
- `computer_use_poc/source_orchestration_check.py`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## Regression Added

- `WEAPON-APIV2-CONFIRMED-PATH-001`
- `WEAPON-DEVICE-ID-PREFIX-PRESERVED-001`
- `WEAPON-GRAPHDATA-EMPTY-NOT-NO-DEVICE-001`
- `TRACK-ANALYSIS-DP-ENDPOINTS-001`
- `TRACK-ANALYSIS-NO-GUESSED-ENDPOINTS-001`
- `TRACK-USE-DURATION-ROWS-OBJECT-ARRAY-001`
- `CROSS-SOURCE-DEVICE-ID-RISKDATA-001`

## Not Done

- No real platform validation in this patch.
- No DataAgent call.
- No gateway / safeBins / tools change.
- No release packaging.
