# Track-Analysis Contract Correction v0.1

## Purpose

Fix the Platform Access Execution v0.1 track-analysis parameter contract after `TRACK-ANALYSIS-EVENT-DAY-ACTIVITY-001` exposed `getLastestDateTime` code `603`.

## Files Updated

- `computer_use_poc/platform_access/track_analysis_api_contract_v0_1.yaml`
- `computer_use_poc/platform_access/platform_access_inventory_v0_1.yaml`
- `computer_use_poc/platform_access/source_orchestration_examples_v0_1.md`
- `computer_use_poc/platform_access/failure_taxonomy_v0_1.yaml`
- `computer_use_poc/platform_access/observation_schema_v0_1.yaml`
- `computer_use_poc/source_orchestration_plan_v1.yaml`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## Contract Extracted From HAR / Run Logs

- `getLastestDateTime`: `GET /dp/platform/app/analytics/v2/sequence/getLastestDateTime`
  - Required query params: `product`, `type`, `funcType`, `_t`
  - `product`: `KUAISHOU | NEBULA`
  - `type`: `userId | deviceId`
  - `funcType`: `USER_PROFILE_QUERY`
- `getDeviceIds`: `POST /dp/platform/app/analytics/v2/sequence/getDeviceIds`
  - Required body: `appName`, `funcType`, `_t`, entity value
  - HAR confirms `deviceId` body key; userId mode is supported by run logs but exact body-key variant remains `needs_har_confirmation` if not present in observed HAR.
- `getUseDuration`: `POST /dp/platform/app/analytics/v2/sequence/getUseDuration`
  - `rows` is an object array with `date` and `duration`
  - Output supports `total_duration`, `peak_day`, and `event_day_duration`
- `profile`: `POST /dp/platform/app/analytics/v2/sequence/profile`
  - Required body includes `appName`, millisecond `startTime/endTime`, `include=1`, `pageSize=100`, `funcType`, `_t`, and entity value
  - `register_time`, `fan_distribution`, and `active_days_bucket` are parsed from `secondLevelProfile` label-value pairs

## getLastestDateTime code=603 Correction

`code=603` should be treated as `invalid_parameter`, `missing_required_param`, or `parameter_contract_missing` before considering auth. It likely indicates missing or invalid `product`, `type`, `funcType`, or cache-buster query contract. It must not be reported as `auth_failed`.

## Event-Day Activity Alignment

Track-analysis supports event-day alignment for:

- login success day
- scan / OAuth day
- device switch day
- strategy hit day
- publish work day
- abnormal behavior day

If backend login / publish / strategy-hit evidence exists but the matching userId/deviceId has `duration=0` or no frontend activity on that day, record `front_backend_activity_mismatch`. This is a medium/high-value lead, not standalone final judgement.

## Regression Cases

- `TRACK-ANALYSIS-EVENT-DAY-ACTIVITY-001`
- `TRACK-GETLATESTDATETIME-PARAM-CONTRACT-001`
- `TRACK-GETUSEDURATION-ROWS-OBJECT-ARRAY-001`
- `TRACK-PROFILE-SECOND-LEVEL-FIELDS-001`
- `TRACK-USERID-DEVICEID-DUAL-MODE-001`
- `TRACK-FRONT-BACKEND-ACTIVITY-MISMATCH-001`

## Boundaries

- Did not access real platforms.
- Did not call DataAgent/Hive.
- Did not modify auth/gateway/safeBins/TOOLS.
- Did not output or save cookie/token/session/header/password.
- Did not copy raw HAR sensitive material.
- Did not rebuild an overlay or full runtime release.
- Did not submit git.
