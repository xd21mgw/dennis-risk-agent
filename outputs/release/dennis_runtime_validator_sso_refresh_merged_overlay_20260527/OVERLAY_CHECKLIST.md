# Overlay Checklist

Run these checks after copying the overlay into live workspace.

## Static Preflight

```bash
python3 computer_use_poc/runtime_preflight_check.py
```

Expected:

- `preflight_pass=true`
- `critical_count=0`

## Runner Auth Refresh / Retry Validation

```bash
python3 computer_use_poc/sso_session_runner.py --platform login_log --action query_user_login_log --user-id 62950989 --timeout 30 --format json
```

Expected:

- Structured JSON observation.
- `source_status` is one of `completed`, `no_data`, `auth_failed`, `timeout`, `parse_error`, or `blocked`.
- If first request is auth failed, output includes `auth_refresh_attempted`, `auth_refresh_status`, `retry_after_refresh`, and `source_status_before_refresh`.
- No cookie / token / session / header output.

## Source Orchestration Validator Positive Case

Use a source completion matrix containing:

- `user_login_unified_log`
- `weapon_user_to_device_graph` with `/apiv2/graphData`
- `weapon_device_risk_if_device_id_available` with `/apiv2/riskData`
- `track_analysis_getDeviceIds` with `/dp/platform/app/analytics/v2/sequence/getDeviceIds`
- `track_analysis_getUseDuration` with `/dp/platform/app/analytics/v2/sequence/getUseDuration`
- `track_analysis_profile` with `/dp/platform/app/analytics/v2/sequence/profile`

Expected:

- `validation_pass=true`

## Source Orchestration Validator Negative Cases

Validate that each returns `validation_pass=false`:

- login-log only source matrix.
- Weapon `/api/graphData`.
- track-analysis guessed endpoint such as `/api/profile`, `/rest/profile`, or `/api/user/profile`.

## Runtime Behavior Smoke

- Single-user account security / ATO must not stop after login log only.
- Weapon graph and risk paths must stay on `/apiv2/*`.
- Track-analysis profile must use `startTime` / `endTime`, not `startDate` / `endDate`.
- `getUseDuration.rows` must be treated as object array `{date, duration}`.
- Completed source must come from current execution observation, not capability registry status alone.
