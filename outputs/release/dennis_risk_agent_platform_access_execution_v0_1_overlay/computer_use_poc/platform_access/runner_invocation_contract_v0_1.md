# Runner Invocation Contract v0.1

This contract defines how dennis-risk-agent invokes controlled platform runners. It is an execution contract, not an auth-state package. Each user environment owns its own SSO state, cookie state, browser profile, and permissions.

## Rules

- The child agent invokes registered runner binaries. The main agent does not run platform tools directly.
- The preferred SSO runner entry is `computer_use_poc/bin/sso_session_runner`.
- The wrapper may call implementation details such as `uv run --with requests python3 computer_use_poc/sso_session_runner.py "$@"`, but the agent should call the wrapper.
- Runners must expose fixed `platform/action` allowlists and reject arbitrary URL, arbitrary header, arbitrary cookie, or arbitrary target input.
- Runners must return JSON observations using `platform_access_observation` or the platform-specific source card schema.
- Runners must map pre-request failures to `runner_invocation_error`, `runner_dependency_error`, or `runner_platform_not_supported` before claiming auth failure.
- Runners must not output cookie, token, session, header, password, or full credential material.
- Failed runner invocation is not platform evidence and cannot become low-risk or no-risk evidence.

## Current Wrapper

```sh
computer_use_poc/bin/sso_session_runner --platform weapon --action graph_data --user-id <user_id> --format json
computer_use_poc/bin/sso_session_runner --platform weapon --action risk_data --device-id <device_id> --format json
computer_use_poc/bin/sso_session_runner --platform login_log --action query_user_login_log --user-id <user_id> --format json
```

## Failure Mapping

- Wrong binary, cwd, or argument names: `runner_invocation_error`.
- Missing runtime dependency, such as `requests` not available to direct Python invocation: `runner_dependency_error`.
- Unsupported platform/action: `runner_platform_not_supported`.
- HTTP redirect after valid invocation: classify as auth/session only after invocation, dependency, domain, and parameter checks pass.
