# Dennis Runtime Validator + SSO Refresh Merged Overlay 20260527

## Purpose

Focused live overlay patch that merges:

1. Source drift validator / endpoint hardening.
2. SSO runner auth refresh + retry patch.

This is not a full runtime release and does not include historical release directories, dist packages, auth state, cookies, tokens, sessions, headers, or gateway / safeBins / tools config changes.

## Included Files

- `computer_use_poc/sso_session_runner.py`
- `computer_use_poc/runtime_preflight_check.py`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/release_overlay_readiness_checklist.md`
- `computer_use_poc/source_orchestration_plan_v1.yaml`
- `computer_use_poc/source_orchestration_check.py`
- `computer_use_poc/internal_agent_drift_audit_v1.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/run_logs/sso_runner_auth_refresh_retry_patch_v1.md`
- `computer_use_poc/run_logs/internal_agent_drift_audit_patch_v1.md`
- `computer_use_poc/run_logs/myflicker_weapon_track_analysis_endpoint_validation_v1.md`

## Capability Deltas

- `sso_session_runner.py` includes controlled SSO auth refresh + one retry for unified login log.
- `source_orchestration_check.py` validates required P0 source execution, Weapon `/apiv2/*` paths, track-analysis `/dp/platform/app/analytics/v2/sequence/*` endpoints, source status semantics, stale evidence, and capability overtrust.
- `source_orchestration_plan_v1.yaml` defines required P0 sources for single-user account security / ATO.
- `runtime_preflight_check.py` verifies the runner refresh contract and source orchestration validator.

## Excluded

- No `outputs/dist` contents.
- No old release directories.
- No auth state, cookie, token, session, header, API key, or gateway config.
- No real platform response data.
- No DataAgent result data.

## Live Overlay Notes

After overlaying these files into live workspace, run `OVERLAY_CHECKLIST.md`. Static preflight passing does not prove live SSO auth success; live runner validation still needs to be executed in the live environment.
