# Release / Overlay Readiness Gate v1

## Reason

Recent live self-tests exposed repeated drift between mother-body docs, overlays, live runtime config, source wrappers, routing guard, platform playbooks, and actual platform call order.

Observed failure classes:

- `sso_session_runner` previously returned dry-run URL construction instead of real controlled SSO observation.
- Live / mother-body / overlay could diverge on runner behavior, safeBins, tools, exec host, and routing guard.
- Realtime readonly API execution sometimes asked users for confirmation even when required fields were present.
- Platform call knowledge existed in playbooks but was not always read before execution.
- Archives, Tianshi, Weapon, unified login log, and track-analysis source order could regress.
- `no_data`, `blocked`, `timeout`, and `auth_failed` needed consistent source_quality treatment.
- Single-user realtime case `user_id=62950989` needed an end-to-end regression gate.

## Files Added

- `computer_use_poc/release_overlay_readiness_checklist.md`
- `computer_use_poc/runtime_preflight_check.py`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/run_logs/release_overlay_readiness_gate_v1.md`

## Files Updated

- `AGENTS.md`
- `computer_use_poc/README.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## Gate Summary

- Release / overlay readiness checklist now separates package-time checks, overlay-time checks, live apply checks, rollback checks, forbidden states, and required runtime behaviors.
- Runtime preflight script performs local static checks and outputs JSON.
- Platform call playbook index records execution order and fallback rules for unified login log, Weapon, Tianshi, Archives Center, and track-analysis.
- Runtime guard now requires platform playbook preflight before source calls.
- Realtime readonly API requires no user confirmation when fields are complete; DataAgent / Hive / big batch / write / high-risk operations require plan or confirmation.
- Validation and smoke tests include release/overlay readiness cases.

## Not Done

- No real platform access.
- No DataAgent call.
- No gateway / auth / safeBins / tools live config change.
- No release package rebuild.
- No git commit.

## Required Follow-up

Before the next live overlay:

1. Run `python3 computer_use_poc/runtime_preflight_check.py`.
2. Verify live `openclaw.json` independently.
3. Run package scanner / release preflight for the actual release directory.
4. Run the `62950989` single-user realtime regression through internal Agent.
5. Verify source checkpoints and partial evidence card behavior.
