# Source Runner Health Check Plan v1

## Scope

This plan covers only runners that already exist in the mother repo and are included in `outputs/full_runtime`:

- `user_login_log`
- `weapon_graphData`
- `weapon_riskData`
- `archives_center_profile`

It does not create new runners, access unregistered sources, debug SSO/auth, read `.ks_sso`, call DataAgent/Hive, or query real platforms.

## Status Boundary

`runner_present_not_verified` means the runner file exists and is present in full_runtime, but live source execution has not been verified in the current local run.

It must not be reported as:

- live executable
- source completed
- no_data
- low risk / no risk
- strategy or ATO evidence

Until a runner has either safe dry-run support or an explicitly authorized live readonly acceptance run, it remains `runner_present_not_verified`.

## Minimal Local Validator

Run from repo root:

```bash
python3 computer_use_poc/source_runner_health_check.py
```

Machine-readable output:

```bash
python3 computer_use_poc/source_runner_health_check.py --json
```

The validator is a local contract checker, not a source runner. It uses only no-platform paths:

- `sso_session_runner`: missing-required-argument invocations, so execution stops before SmartSSOSession or cookie fallback.
- `archives_profile_runner`: safe local stub invocation, which returns source gap / blocked without platform access.

## Source Matrix

| Source | Runner Entry | Required Inputs | Local Health Check Mode | Current Status |
|---|---|---|---|---|
| `user_login_log` | `bin/sso_session_runner` | `--platform login_log --action query_user_login_log --user-id <numeric> [--from_timestamp <ms> --to_timestamp <ms>] [--timeout 1-120] --format json` | Invocation contract only; missing `--user-id` path must return JSON `blocked` with `real_platform_request_executed=false`. | `runner_present_not_verified` |
| `weapon_graphData` | `bin/sso_session_runner` | `--platform weapon --action graph_data --user-id <numeric> [--timeout 1-120] --format json` | Invocation contract only; missing `--user-id` path must return JSON `blocked` with `real_platform_request_executed=false`. | `runner_present_not_verified` |
| `weapon_riskData` | `bin/sso_session_runner` | `--platform weapon --action risk_data --device-id <opaque_device_id> [--timeout 1-120] --format json` | Invocation contract only; missing `--device-id` path must return JSON `blocked` with `real_platform_request_executed=false`. | `runner_present_not_verified` |
| `archives_center_profile` | `bin/archives_profile_runner` | `--action archives.profile_home_info --user-id <numeric> [--timeout 1-60] --format json` | Safe local stub; valid input returns JSON `blocked` / `source_gap` with `real_platform_request_executed=false`. | `runner_present_not_verified` because stub is not live-connected |

## Expected Output Fields

All checked runners must emit one parseable JSON object on stdout.

Common required fields:

- `source_quality`
- `redaction`
- `real_platform_request_executed`

Status and sensitive-output resolution:

- `sso_session_runner` uses top-level `source_status` and `sensitive_output`.
- `archives_profile_runner` currently uses `archives_profile_source_status` plus `source_card.source_status`; sensitive-output state is read from `redaction.sensitive_output`.
- Health check treats the Archives status alias as a current runner contract difference, not as proof of live executability.

`sso_session_runner` additionally exposes:

- `schema_version`
- `source_name`
- `user_id`
- `records_count`
- `evidence_time_range`
- `evidence_summary`
- `raw_references`
- `source_card`
- `source_checkpoint_private`
- `redaction_applied`
- `dataagent_called`
- `platform_write_action`

`archives_profile_runner` additionally exposes:

- `archives_profile_source_status`
- `same_origin_fetch_ready`
- `available_fields`
- `account_status_summary`
- `ban_info_summary`
- `demote_info_summary`
- `login_device_summary`
- `register_device_summary`
- `missing_fields`
- `source_checkpoint_private`
- `runner_readiness_status`
- `remaining_gap`

## Source Status Enum

For the four scoped sources, health check and runtime output may use:

- `completed`
- `no_data`
- `blocked`
- `auth_failed`
- `timeout`
- `parse_error`
- `tool_gap`

Local no-platform health checks should only observe:

- `blocked`

`blocked` in local health check means the invocation contract or local stub boundary worked. It is not platform evidence.

## Sensitive Output Filter

All checked output must satisfy:

- `sensitive_output=false`
- `redaction.redaction_applied=true`
- no cookie / token / session / header / authorization / password plaintext
- no raw platform response dump
- no raw device fingerprint in user-visible fields
- raw references only in private checkpoint fields when needed for same-task chaining

The local validator scans stdout/stderr for credential-like patterns and fails closed if any are detected.

## Live Verification Boundary

Do not perform live verification in this plan.

Live readonly acceptance is a separate mode and requires:

- explicit task authorization
- registered source and runner
- no manual cookie/header
- no auth debug
- source failure recorded in `source_quality`
- `no_data` / `blocked` / `timeout` / `auth_failed` / `parse_error` not used as no-risk evidence
