# SSO Session Runner Real Executor Patch v1

## Goal

Persist the live hotfix direction back into the Dennis Risk Agent mother-body: upgrade `computer_use_poc/sso_session_runner.py` from URL construction / dry-run behavior into a controlled readonly real HTTP executor for the unified login log P0 source.

## Scope

- Only supports unified login log P0 query.
- Does not add arbitrary HTTP client behavior.
- Does not add write/edit permissions.
- Does not modify gateway, auth state, safeBins, tools allow/deny, or live config.
- Does not call DataAgent.

## Runtime CLI

```bash
python3 computer_use_poc/sso_session_runner.py \
  --platform login_log \
  --action query_user_login_log \
  --user-id 62950989 \
  --timeout 30 \
  --format json
```

Legacy compatibility:

- `--platform_key user_login_unified_log`
- `--user_id`
- `--from_timestamp`
- `--to_timestamp`

## Behavior

- Builds URL only from fixed platform/action mapping.
- Calls live `sso_session.SmartSSOSession.get()` when available.
- Parses JSON and returns a redacted observation summary.
- Detects redirect / HTML login page as `auth_failed`.
- Marks timeout as `timeout`.
- Marks JSON parse failure as `parse_error`.
- If `sso_session` / `SmartSSOSession` is unavailable locally, fail closed as `blocked`.

## Observation Fields

- `source_name`
- `source_status`
- `user_id`
- `records_count`
- `evidence_time_range`
- `evidence_summary`
- `source_quality`
- `raw_reference_safe_id`
- `collected_at`
- `redaction_applied`
- `real_platform_request_executed`

## Safety

- No cookie/token/session/header output.
- No `target_url` / arbitrary URL parameter.
- Non-digit user id fails closed.
- Unknown platform/action fails closed.
- No curl/cookie path.
- No main-agent URL/cookie handoff.

## Validation

Local validation may return `blocked` when `sso_session.SmartSSOSession` is not available. That is expected locally and does not fall back to dry-run success. Live validation should return `completed`, `no_data`, `auth_failed`, `timeout`, or `parse_error` depending on real SSO/API state.
