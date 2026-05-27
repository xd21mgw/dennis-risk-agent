# Dennis Risk Agent Runtime Canonical Release v1

This is Dennis Risk Agent Runtime Canonical Release v1.

It is a clean runtime canonical release, not a historical patch stack and not another temporary overlay patch. It is delivered as an overlay directory for internal Agent rollout, but its main role is to define the new runtime baseline for Dennis Risk Agent.

## What This Package Is

- Canonical runtime baseline for Dennis Risk Agent.
- Release-safe overlay source for internal Agent workspace update.
- Unified closure for recent runtime, ATO, auth bridge, source boundary, and runtime config apply fixes.
- A package of distilled runtime files, checklists, schemas, smoke tests, validation cases, and selected safe summaries.

## What This Package Is Not

- It does not automatically modify live `openclaw.json`.
- It does not change auth or gateway config.
- It does not call real platforms.
- It does not call DataAgent.
- It does not include full deep Skill source.
- It does not include full historical run logs.
- It does not include real case raw samples or risky fixtures.

## Live Apply Requirements

After overlay, the internal Agent owner must separately apply and validate a live `dennis-risk-agent` runtime entry.

Live validation must cover:

- `openclaw.json` contains a dedicated `dennis-risk-agent` entry.
- dennis-risk-agent does not inherit full-profile defaults.
- `exec.security=allowlist` is active.
- `safeBins` is active.
- `tools.deny` is active.
- `fs.workspaceOnly=true` is active.
- `loopDetection` is active.
- main agent can spawn dennis-risk-agent.
- main agent does not take over platform querying after dennis timeout.
- ATO single case can output a partial evidence card.
- 2-9 user ATO small batch uses checkpoint mode.
- feedback writer and pilot log paths resolve correctly.

## Key Boundaries

- Runtime config template is not live runtime enforcement.
- Release package or overlay completion is not live apply.
- Browser fallback success is not wrapper-first success.
- Source wrapper failure must be recorded in `source_quality`.
- `no_data`, timeout, blocked, and auth failure are not risk counter-evidence.
- Main agent is routing / logging only for risk-platform access; dennis-risk-agent owns risk source orchestration.

## Recommended Reading Order

1. `computer_use_poc/runtime_config_apply_checklist_v1.md`
2. `computer_use_poc/runtime_canonical_baseline_v1.md`
3. `computer_use_poc/multi_entry_runtime_guard_v1.md`
4. `computer_use_poc/scene_to_capability_routing.md`
5. `computer_use_poc/capability_registry.md`
6. `computer_use_poc/answer_experience_templates.md`
7. `computer_use_poc/runtime_validation_cases_v1.yaml`
8. `computer_use_poc/runtime_integration_validation_checklist_v1.md`
9. `computer_use_poc/smoke_tests.md`
