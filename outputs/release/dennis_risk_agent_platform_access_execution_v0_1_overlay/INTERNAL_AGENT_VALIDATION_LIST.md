# Internal Agent Validation List

After applying this overlay, run the following minimum smoke checks.

## 1. WEAPON-GRAPHDATA-WRAPPER-SMOKE-001

Expected:

- Use `computer_use_poc/bin/sso_session_runner`.
- Do not directly call `python3 computer_use_poc/sso_session_runner.py`.
- Wrapper failure maps to `runner_invocation_error` or `runner_dependency_error`.
- Do not label wrapper/dependency failures as `auth_failed`.

## 2. WEAPON-RISKDATA-DIRECT-DEVICEID-001

Expected:

- When `deviceId` is known, `riskData` can be called directly.
- `graphData` is only the discovery source when `deviceId` is missing.
- Do not use `userId` as `deviceId`.

## 3. RCP_EVENTLIST_STRATEGY_HIT_SMOKE_001

Expected:

- RCP `eventList` is the strategy-hit main entry.
- `fastQueryHbase` is fallback.
- `rcpEventDetail`, `FeatureList`, `policyVersion`, and `nodePolicyAttribution` trigger only when upstream fields are present.
- Missing fields output `missing_upstream_id`.
- Missing upstream fields must not be reported as `auth_failed`.

## 4. TRACK-ANALYSIS-EVENT-DAY-ACTIVITY-001

Expected:

- Validate event-day frontend activity alignment.
- Follow the contract for `userId`, `deviceId`, `appName`, and date-level fields.
- `front_backend_activity_mismatch` is auxiliary evidence, not final judgement.

## 5. ARCHIVES-CENTER-PUBLISH-CHAIN-P0-001

Expected:

- Archives Center user analysis is ATO P0.
- Abnormal publish makes publish chain P0-conditional.
- Auth or same-origin gaps are source gaps and do not downgrade source priority.
