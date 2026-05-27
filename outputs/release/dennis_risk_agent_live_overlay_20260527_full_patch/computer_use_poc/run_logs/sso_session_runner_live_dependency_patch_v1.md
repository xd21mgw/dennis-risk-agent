# SSO Session Runner Live Dependency Patch v1

## Goal

Patch the mother-body runner contract after live overlay showed that `importlib.import_module("sso_session")` is not a stable live dependency. The live-preferred path is `ks_aimate.sso_login_client.SmartSSOSession`.

## Changes

- Runner now prefers `from ks_aimate.sso_login_client import SmartSSOSession`.
- Removed legacy-only dependency on `importlib.import_module("sso_session")`.
- Added controlled cookie-state fallback:
  - reads only `.ks_sso/sso-state.json`;
  - extracts only `kuaishou.com` domain cookies;
  - requests only the runner-built whitelist URL;
  - never outputs cookie/header/session/token.
- Observation now includes `executor_mode: smart_sso | cookie_state_fallback | unavailable`.
- Preflight now checks for `ks_aimate.sso_login_client`, cookie-state fallback markers, and legacy-only import dependency.
- Preflight warning now states static pass does not prove live auth success.

## Boundaries

- Did not access real platforms.
- Did not call DataAgent.
- Did not change gateway / safeBins / tools.
- Did not rebuild full release.
- Did not read live `.ks_sso/sso-state.json` during this patch.

## Regression Added

- `SSO-RUNNER-LIVE-DEPENDENCY-001`
- `SSO-RUNNER-COOKIE-STATE-FALLBACK-001`
- `PREFLIGHT-RUNTIME-IMPORT-CHECK-001`
