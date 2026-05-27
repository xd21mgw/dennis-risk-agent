# Runtime Live-Fix Consolidation Patch v1

## Purpose

Consolidate the live stop-the-bleeding fixes back into the Dennis Risk Agent mother-body so future overlays do not regress the runtime entry guard, runner entrypoint, exec allowlist contract, or Weapon API path.

## Live Fixes Captured

- `TOOLS.md` must keep the main entry guard marker and must not be replaced by a focused overlay stub.
- `AGENTS.md` first 200 lines must expose the source orchestration guard, business-case no-auth-repair rule, main fallback direct-bypass ban, and no free URL guessing rule.
- `dennis-risk-agent` runtime config must use `exec.security=allowlist`, not `full`.
- `bin/sso_session_runner` is the safeBin entrypoint and delegates to `computer_use_poc/sso_session_runner.py`.
- `exec-approvals.json` must contain a non-empty `dennis-risk-agent` allowlist including the runner wrapper and `python3`.
- `sso_session_runner.py` remains the single canonical runner implementation.
- Weapon runner actions are added as controlled readonly actions:
  - `--platform weapon --action graph_data --user-id <user_id>`
  - `--platform weapon --action risk_data --device-id <device_id>`
- Weapon runner actions only use:
  - `/apiv2/graphData`
  - `/apiv2/riskData`

## Files Changed

- `AGENTS.md`
- `TOOLS.md`
- `bin/sso_session_runner`
- `computer_use_poc/sso_session_runner.py`
- `computer_use_poc/runtime_preflight_check.py`
- `computer_use_poc/release_overlay_readiness_checklist.md`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## Regression Added

- `TOOLS-RESTORE-MARKER-001`
- `FOCUSED-OVERLAY-NO-AGENTS-TOOLS-001`
- `AGENTS-ENTRY-GUARD-FIRST-200-001`
- `SAFEBIN-RUNNER-WRAPPER-001`
- `EXEC-ALLOWLIST-CONTRACT-001`
- `WEAPON-RUNNER-ACTION-001`
- `MAIN-FALLBACK-DIRECT-BYPASS-FORBIDDEN-001`

## Boundaries

- Did not access any real platform.
- Did not call DataAgent or Hive.
- Did not modify live gateway, safeBins, tools, or approvals.
- Did not add track-analysis, archives, or generic multi-platform runner actions.
- Did not repackage a full release.
- Did not output cookie, token, session, header, or auth state.

## Validation Plan

- `python3 -m py_compile computer_use_poc/sso_session_runner.py computer_use_poc/runtime_preflight_check.py`
- YAML parse for `computer_use_poc/runtime_validation_cases_v1.yaml`
- `python3 computer_use_poc/runtime_preflight_check.py`
- `git diff --check`
