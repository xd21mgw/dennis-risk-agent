# Track-analysis API Direct Contract Current

## Positioning

Track-analysis / 用户分析平台 is a frontend behavior, activity, and profile-statistics evidence source. It can supplement account security, protocol attack, group-control, and traffic-abuse investigations, but it does not independently prove ATO, protocol login, group control, or cheating.

This contract records current API-direct coverage based on internal Agent self-test observations and existing local v2.5.x frontend-activity documents. It is not named v2.5.5 because the current checkout does not contain a `track_analysis_api_direct_selftest_v2_5_5.yaml` source file.

This patch does not modify `sso_session_runner.py`, does not add a new runner, and does not turn the SSO runner into a generalized multi-platform HTTP client.

## Supported Inputs

- `userId`
- `deviceId`
- `appName`: `KUAISHOU` or `NEBULA`

`KUAISHOU` and `NEBULA` must be interpreted separately. A `NEBULA` duration of zero means no observed NEBULA activity in the queried coverage; it does not mean the account has no activity in KUAISHOU or other apps.

## Supported API Groups

### getLastestDateTime

Purpose: confirm latest available data timestamp for the selected app and entity scope.

Input parameters:

- `appName`
- `filtersType`: `userId` or `deviceId`
- `filtersValue`

Key output fields:

- latest available datetime / partition indicator
- response status

Source status mapping:

- JSON success with timestamp: `completed`
- JSON success without available timestamp: `no_data`
- HTML / login page / redirect: `auth_failed`
- non-JSON or unexpected shape: `parse_error`
- timeout: `timeout`

Source quality:

- Missing latest timestamp is a source coverage gap, not risk exclusion.
- Stale latest timestamp must be marked `stale_source`.

### getDeviceIds

Purpose: resolve `userId` to track-analysis visible deviceIds for behavior-profile checks.

Input parameters:

- `appName`
- `userId`

Key output fields:

- `deviceIds`
- count / list length

Source status mapping:

- JSON success with deviceIds: `completed`
- JSON success with empty list: `no_data`
- HTML / login page / redirect: `auth_failed`
- non-JSON or unexpected shape: `parse_error`
- timeout: `timeout`

Source quality:

- Empty device list is not evidence that the user has no devices.
- Use as entity-resolution support only; do not use it as final risk judgement.

### getUseDuration

Purpose: read activity duration by day for `userId` or `deviceId`.

Input parameters:

- `appName`
- `filtersType`: `userId` or `deviceId`
- `filtersValue`
- time range / recent-day window when supported

Key output fields:

- `rows`
- date field
- duration field
- total duration when computed locally

Important shape rule:

- `getUseDuration.rows` is an array of objects / dicts.
- It is not a two-dimensional array.
- Parsers must address fields by object keys, not fixed column offsets.

Observed interpretation examples:

- `KUAISHOU + deviceId` can return 30-day daily duration.
- `KUAISHOU + userId` can aggregate multiple-device duration.
- `NEBULA` duration of `0` should be interpreted as no NEBULA activity under the query, not account inactivity.

Source status mapping:

- JSON success with rows: `completed`
- JSON success with empty rows or all zero duration: `no_data` or `completed` with zero-activity summary, depending on app scope
- HTML / login page / redirect: `auth_failed`
- row shape mismatch: `parse_error`
- timeout: `timeout`

Source quality:

- Duration is behavior-supporting evidence.
- Activity spikes, long inactivity followed by activation, or user/device duration mismatch can raise suspicion but require cross-validation.

Day-level alignment:

- `getUseDuration` is not only for monthly active days, total duration, and peak duration.
- It must support day-level alignment against login success date, scan-login date, device-switch date, abnormal-device-login date, and strategy-hit date.
- If backend login / scan / abnormal-device login / strategy hit exists on a day, but track-analysis `userId` or `deviceId` duration is `0` or no frontend activity, record `front_backend_activity_mismatch`.
- `front_backend_activity_mismatch` is a medium/high-value lead for protocol login, token/session use, or non-real-client behavior.
- It is not standalone final judgement; it must be cross-validated with login chain, device risk tags, strategy hits, publish / request / interaction behavior, and follow-up raw evidence.
- If the event day is outside track-analysis source window, mark `source_window_boundary` / `missing_evidence`, not no risk.

### profile

Purpose: read profile card and behavior-profile statistics for `userId` or `deviceId`.

Input parameters:

- `appName`
- `filtersType`: `userId` or `deviceId`
- `filtersValue`

Key output field paths:

- `firstLevelProfile`
  - `userId`
  - `gender`
  - `age`
  - `country`
  - `province`
  - `city`
  - `userType30d`
  - `channelType`
  - `refluxPTag`
  - `headUrl`
- `secondLevelProfile`
  - label-value pairs
  - register time
  - fan distribution
  - monthly active days / active-days bucket

Important field-path rule:

- `register_time`, `fan_distribution`, and `active_days_bucket` live in `secondLevelProfile` label-value pairs.
- Do not search only `firstLevelProfile` for these fields.
- `userId` profile may return `deviceIds`.

Source status mapping:

- JSON success with profile fields: `completed`
- JSON success with missing key labels: `partial_source`
- JSON empty profile: `no_data`
- HTML / login page / redirect: `auth_failed`
- unexpected field shape: `parse_error`
- timeout: `timeout`

Source quality:

- Profile-card fields are behavior/profile support only.
- Missing label-value pairs reduce coverage; they do not prove normal behavior.

## Coverage Summary

Covered:

- `profile_card`
- `usage_duration`
- `register_time`
- `fan_distribution`
- `active_days_bucket`
- `userId` API path
- `deviceId` API path
- `KUAISHOU` / `NEBULA` app split

Current default:

- Use API direct first.
- DOM / SPA / selector fallback is not the default for these covered fields.
- Browser fallback should only be used for auth activation, response-shape investigation, or fields not covered by API direct.

Capability status:

- `api_direct_confirmed` for `profile`, `getUseDuration`, `getDeviceIds`, and `getLastestDateTime`.
- Do not route these covered fields to SPA DOM by default.
- If API direct returns `auth_failed`, `timeout`, or `parse_error`, record source quality and consider scoped fallback; do not convert the failure into a risk conclusion.

## Evidence Boundary

Track-analysis activity evidence can support:

- long inactivity followed by sudden activation
- abnormal activity on a specific day
- userId vs deviceId activity inconsistency
- backend login / scan / strategy-hit day with frontend duration=0 as `front_backend_activity_mismatch`
- KUAISHOU vs NEBULA app-scope differences
- profile-statistics mismatch with other sources

It cannot independently conclude:

- ATO
- protocol login
- group control
- real user operation
- no risk

Required cross-validation examples:

- login chain / token / OAuth / scan evidence
- device risk and device consistency
- strategy hit and policy attribution
- publish / interaction / request behavior chain
- other raw platform evidence

## Security and Redaction

- Do not output raw profile JSON.
- Do not output full media / avatar URLs.
- Do not output sensitive user attributes as final judgement.
- Summarize counts, buckets, distributions, activity windows, and consistency signals.
