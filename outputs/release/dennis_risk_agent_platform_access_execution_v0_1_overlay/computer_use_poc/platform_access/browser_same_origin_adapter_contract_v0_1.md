# Browser Same-Origin Adapter Contract v0.1

Some platform APIs are confirmed only when the browser is already on the correct origin and the user's environment has a valid platform state. This adapter contract keeps those cases structured without turning business execution into auth repair or URL exploration.

## Scope

- Applies to Archives Center, RCP/eventList, track-analysis, and other registered same-origin APIs.
- The project does not carry auth state. It only defines how to execute if the user's browser/profile/state is ready.
- Same-origin access is an `access_method`, not proof that a source is lower priority.

## Allowed

- Use a registered entry domain and registered API path.
- Verify current origin before fetch.
- Perform readonly same-origin API requests for registered contracts.
- Return `platform_access_observation` with `invocation_method=browser_same_origin`.
- Classify HTML/login page, redirect, AccessProxy, path block, or parse errors as structured source states.

## Forbidden

- Guess domains or paths.
- Click login pages in business cases.
- Type username, password, SMS, QR, or MFA in business cases.
- Debug cookie/session/header material.
- Treat same-origin failure as no-data.
- Treat one blocked path as whole-platform unavailable.

## Failure Mapping

- Wrong origin: `same_origin_mismatch`.
- API requires browser origin but runner/direct call was attempted: `same_origin_required`.
- Registered path permission blocked: `api_path_permission_blocked`.
- Some paths work while others fail: `platform_partial_available`.
- HTML/login page after valid same-origin setup: `auth_failed` or `accessproxy_session_invalid`.
