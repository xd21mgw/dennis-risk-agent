# Release Notes

## Release

`dennis_risk_agent_runtime_canonical_release_v1`

This release is a clean runtime canonical release. It replaces the mental model of stacking temporary overlays with a single baseline for Dennis Risk Agent runtime validation.

## Problems Addressed

- Runtime drift after multiple overlay patches.
- Readonly runtime config template existed but was not applied live.
- dennis-risk-agent could inherit full-profile defaults.
- Wrapper-first existed as text guidance rather than runtime enforcement.
- Browser fallback could be overused or misrepresented.
- Main agent could attempt to take over platform querying after dennis timeout.
- ATO single case and small-batch paths lacked reliable checkpoint and partial fallback behavior.

## Included Capabilities

- Runtime config apply checklist.
- Canonical runtime baseline.
- ATO single source checkpoint.
- ATO deadline partial fallback.
- 2-9 user `small_batch_execution_with_checkpoint`.
- Unified login auth bridge boundary.
- Login log approximate 7-day reliable window.
- APP login source gap boundary.
- Standard YAML `routing_metadata` schema.
- Smoke tests and runtime validation cases.

## Not Included

- Live `openclaw.json` modification.
- Real platform query.
- DataAgent call.
- Auth or gateway change.
- Full deep Skill source.
- Full historical run logs.
- Real case raw samples.
- Risky fixtures.
- Historical `outputs/dist` or `outputs/packages`.

## Internal Agent Next Steps

1. Overlay this release into live workspace.
2. Apply live `openclaw.json` dedicated `dennis-risk-agent` entry.
3. Validate `safeBins`, `tools.deny`, `workspaceOnly`, and `loopDetection`.
4. Validate main agent can spawn dennis-risk-agent.
5. Run single ATO and 2-9 user small-batch smoke tests.
6. Confirm feedback writer and pilot log paths.
