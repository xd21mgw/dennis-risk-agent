# Internal Agent Drift Audit Patch v1

## Goal

Systematically audit execution drift risks in Dennis Risk Agent and turn the stable parts into local validators, regression cases, and smoke tests. This avoids relying on model memory during live execution.

## Drift Classes Covered

1. Routing drift.
2. Source orchestration drift.
3. Platform path drift.
4. Auth / session drift.
5. Tool boundary drift.
6. Evidence semantic drift.
7. Stale data drift.
8. Capability status drift.

## Files Added

- `computer_use_poc/internal_agent_drift_audit_v1.md`
- `computer_use_poc/run_logs/internal_agent_drift_audit_patch_v1.md`

## Files Updated

- `computer_use_poc/source_orchestration_plan_v1.yaml`
- `computer_use_poc/source_orchestration_check.py`
- `computer_use_poc/runtime_preflight_check.py`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## Validator Additions

`source_orchestration_check.py` now checks:

- source plan / source completion matrix presence.
- login-log-only cannot conclude.
- Weapon `/apiv2/graphData` and `/apiv2/riskData` path / parameter shape.
- forbidden access methods such as `curl_cookie`, `manual_cookie`, `main_agent_direct_exec`, and `arbitrary_url`.
- write/edit attempts during readonly source execution.
- stale / cached provenance during `--no-cache`.
- completed source HTTP / response type consistency when present.
- auth failure before refresh requires controlled refresh attempt.
- no_data / timeout / blocked / auth_failed cannot support low-risk or no-risk final conclusion.
- track-analysis cannot be `completed` without executable endpoint verification.

## Preflight Additions

`runtime_preflight_check.py` now checks:

- drift audit document coverage.
- source orchestration validator drift markers.
- login-log-only negative case fails as expected.

## Boundaries

- No real platform access.
- No DataAgent call.
- No gateway / safeBins / tools change.
- No track-analysis endpoint handling.
- No release repackaging.
- No git commit.
