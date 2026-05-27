# SSO Runner Auth Refresh Retry Patch v1

## Goal

Add a minimal auth preflight + refresh + retry loop to `computer_use_poc/sso_session_runner.py` for unified login log only.

## Problem

The runner can execute real HTTP requests, but when the initial cookie / ticket is expired it returns `auth_failed` for 302 / HTML login / access proxy redirect. Manual execution of `skills/kuaishou-sso-login-client/scripts/sso_session.py --target_url <login_log_api_url>` refreshes auth state, after which the runner succeeds.

## Fix

- Detect initial auth failure:
  - HTTP 302.
  - HTML / login page.
  - SSO / access-proxy redirect style response.
- Run one controlled refresh using `skills/kuaishou-sso-login-client/scripts/sso_session.py`.
- Pass only the runner-built whitelist URL to the refresh script.
- Retry the original runner request once.
- If refresh fails or retry still fails, return structured `auth_failed` / `blocked`.

## Output Fields Added

- `auth_refresh_attempted`
- `auth_refresh_status`
- `retry_after_refresh`
- `source_status_before_refresh`

## Safety Boundaries

- No arbitrary URL input.
- No `target_url` CLI parameter on the runner.
- No curl+cookie path.
- No cookie/token/session/header output.
- No main-agent direct bypass.
- No gateway / safeBins / tools change.
- No DataAgent call.
- No real platform validation in this patch.

## Modified Files

- `computer_use_poc/sso_session_runner.py`
- `computer_use_poc/runtime_preflight_check.py`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/release_overlay_readiness_checklist.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## Regression Added

- `SSO-RUNNER-AUTH-REFRESH-RETRY-001`
- `SSO-RUNNER-REFRESH-FAIL-CLOSED-001`
- `SSO-RUNNER-NO-AUTH-LOOP-001`

## Validation

Local validation only:

- Python compile for runner and preflight.
- YAML parse for runtime validation cases.
- Static preflight.
- `git diff --check`.
