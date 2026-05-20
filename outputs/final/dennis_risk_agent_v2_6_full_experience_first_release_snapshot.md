# Dennis Risk Agent v2.6 Full Experience-First Release Snapshot

## 1. Snapshot Status

```yaml
release_name: dennis_risk_agent_v2_6_full_experience_first_release
release_path: outputs/release/dennis_risk_agent_v2_6_full_experience_first_release/
base_release: outputs/release/dennis_risk_agent_v2_4_runtime_plus_release/
incremental_experience_package: outputs/release/dennis_risk_agent_v2_6_experience_first_release/
status: full_package_generated
cloud_internal_agent_integration_ready: true
platform_hand_added: false
real_platform_read_logic_changed: false
real_platform_query_executed: false
git_committed: false
```

## 2. Package Type Decision

The existing package `outputs/release/dennis_risk_agent_v2_6_experience_first_release/` is an incremental experience addendum. It is useful as a focused experience layer, but it is not sufficient as an independent cloud internal Agent integration package because it lacks the complete runtime base, ATO body, DataAgent boundaries, and full computer-use contracts.

The new package `outputs/release/dennis_risk_agent_v2_6_full_experience_first_release/` is the independent full package. It is built by layering v2.6 experience-first files and key `computer_use_poc` contracts on top of the v2.4 runtime-plus full release.

## 3. Included Capability Blocks

- Core Agent runtime / startup / routing from v2.4 runtime-plus.
- ATO complete runtime and account-security skill material.
- DataAgent boundary, parser, timeout, and conclusion threshold docs.
- Existing readonly platform hand docs for archives center, user login unified log, Device SDK, frontend activity profile, and Tianshi.
- Observation contract and observation schema.
- User ↔ Device Entity Resolution v2.6.0.
- Experience-first golden cases, answer templates, scene-to-capability routing, smoke tests, and dry run.

## 4. Integration Boundary

This package does not:

- Add new platform hands.
- Change real platform read logic.
- Execute real platform queries.
- Include cookie / token / session / storageState / KIM code.
- Include `outputs/packages/`.
- Introduce automatic enforcement or automatic final risk classification.

## 5. Recommended Cloud Verification

P0:

- ATO user judgment with real readonly observation flow.
- Login failure / verification reason explanation with real readonly observation flow.

P1:

- Device-risk userId input branch: user-to-device entity resolution before Device SDK.
- Strategy-hit explanation boundary.
- Permission / auth / no-data blockers in observation contract.
