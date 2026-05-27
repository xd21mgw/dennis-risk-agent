# Track-analysis API Direct Contract Current Run Log

## Goal

Record current track-analysis / 用户分析平台 API direct coverage as a local contract, playbook update, validation cases, and smoke tests.

## Source

The user provided internal Agent self-test conclusions for track-analysis API direct coverage. The current checkout does not contain `computer_use_poc/track_analysis_api_direct_selftest_v2_5_5.yaml`; existing local track-analysis assets are v2.5.2 / v2.5.3 / v2.5.4 frontend-activity documents. Therefore this patch uses `current` naming instead of v2.5.5.

## Coverage Recorded

- `getLastestDateTime`
- `getDeviceIds`
- `getUseDuration`
- `profile`

The self-test conclusion recorded here says API direct works after SSO auth state for KUAISHOU / NEBULA and userId / deviceId combinations.

## Field Findings

- `getUseDuration.rows` is an object-array / dict structure, not a two-dimensional array.
- `profile.firstLevelProfile` contains high-level profile-card fields.
- `profile.secondLevelProfile` contains label-value pairs such as register time, fan distribution, and active-days bucket.
- userId profile can return deviceIds.
- KUAISHOU / NEBULA must be interpreted separately.
- NEBULA duration `0` means no NEBULA activity in the queried app scope, not account inactivity.

## Boundary

- Track-analysis is behavior / activity / profile-statistics supporting evidence.
- It does not independently prove ATO, protocol login, group control, or no risk.
- It must be cross-validated with login chain, device risk, strategy hit, publish / request / interaction behavior, and other raw evidence.

## Not Done

- Did not access real platforms.
- Did not call DataAgent.
- Did not modify gateway / safeBins / tools.
- Did not modify `sso_session_runner.py`.
- Did not add a new runner.
- Did not repackage release.

## Follow-up Option

After runtime requirements are stable, evaluate whether a dedicated `track_analysis_runner` is needed. Do not expand `sso_session_runner.py` into a generalized multi-platform HTTP client.
