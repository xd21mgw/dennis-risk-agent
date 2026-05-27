# Runtime Config Apply Canonical Baseline Patch v1

## Background

Recent live investigation found that the readonly runtime config template was not actually applied to live `openclaw.json`:

- live `agents.list` only had `main`
- there was no dedicated `dennis-risk-agent` entry
- `safeBins`, `tools.deny`, exec allowlist, workspace-only, and loop detection were not enforced for dennis-risk-agent
- dennis-risk-agent effectively inherited full-profile defaults
- wrapper-first / browser-fallback rules existed as text guidance, not runtime hard constraints

This can make dennis fall back to browser same-origin fetch, manual curl/cookie patterns, or unmanaged browser access. It also increases the risk that main agent takes over platform querying after dennis timeout.

## Root Cause

`dennis_agent_readonly_runtime_config_template.json` or equivalent readonly runtime template is a design artifact. It is not effective until live `openclaw.json` contains a dedicated `dennis-risk-agent` entry and main spawns that entry.

## Relationship to Previous ATO Patch

The previous ATO single / small-batch / auth bridge / source boundary patch is not reverted.

That patch fixed:

- per-source checkpoint
- deadline fallback
- partial evidence card
- 2-9 user `small_batch_execution_with_checkpoint`
- login log reliable-window boundary
- APP-login-only source gap
- auth bridge direct exec guard
- routing metadata YAML schema

This run fixes a different layer:

- runtime config apply checklist
- canonical runtime baseline
- live apply precondition
- bad case `BC-RUNTIME-CONFIG-NOT-APPLIED-001`

The two patches are complementary. Live effectiveness requires both rule-layer closure and runtime config enforcement.

## Added Files

- `computer_use_poc/runtime_config_apply_checklist_v1.md`
- `computer_use_poc/runtime_canonical_baseline_v1.md`

## Modified Files

- `AGENTS.md`
- `computer_use_poc/README.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/runtime_integration_validation_checklist_v1.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`

## Bad Case

`BC-RUNTIME-CONFIG-NOT-APPLIED-001`:

- readonly runtime template exists
- live `openclaw.json` does not contain a dedicated `dennis-risk-agent` entry
- dennis inherits full-profile runtime defaults
- `safeBins`, `tools.deny`, exec allowlist, workspace-only, and loop detection are not active for dennis
- wrapper-first becomes text-only guidance
- browser fallback / manual cookie/curl use increases
- main agent may take over querying after dennis timeout

Correct repair: apply runtime config. Do not treat another routing document as a substitute for live enforcement.

## Live Apply Order

1. Apply dedicated dennis-risk-agent readonly runtime config to live `openclaw.json`.
2. Validate `safeBins`, `tools.deny`, `workspaceOnly`, and `loopDetection`.
3. Validate main spawn target resolves to dennis-risk-agent entry.
4. Overlay ATO checkpoint / small-batch / auth-bridge rules.
5. Run single ATO and small-batch regressions.

## Boundaries

- Did not access real internal platforms.
- Did not call DataAgent.
- Did not modify live workspace.
- Did not modify real `openclaw.json`.
- Did not modify auth or gateway config.
- Did not rebuild release packages.
- Did not commit git changes.

## Next Owner Action

Internal runtime owner should apply the live `openclaw.json` dennis-risk-agent entry and rerun runtime config validation before claiming semi-open safety boundaries are active.
