# Dennis Risk Agent v2.6 Full Experience-First Manifest v1

## 1. Package Status

```yaml
release_name: dennis_risk_agent_v2_6_full_experience_first_release
release_type: full_cloud_internal_agent_integration_package
base_release: outputs/release/dennis_risk_agent_v2_4_runtime_plus_release
experience_addendum: outputs/release/dennis_risk_agent_v2_6_experience_first_release
status: ready_for_cloud_internal_agent_full_integration
new_platform_hand_added: false
real_platform_read_logic_changed: false
real_platform_query_executed: false
core_skill_modified: false
git_commit_created: false
```

## 2. What This Package Contains

This full package contains both the previous complete runtime release and the v2.6 experience-first addendum.

Core runtime and routing:

- v2.4 runtime-plus manifest, release note, startup loading checklist, integration quick start, query intent schema, and final route regression.
- ATO complete runtime files, including account security expert skill, ATO runtime slim manifest, and ATO short-question entrypoint adaptation.
- Runtime summaries for account security adjacent domains: protocol attack, group control, cracked app, real-user crowdsourcing, anti-crawler, activity anti-cheating, traffic anti-cheating, and traffic diversion.

DataAgent boundary:

- DataAgent provider boundary overlay.
- DataAgent conclusion thresholds.
- DataAgent markdown response parser.
- DataAgent timeout policy review.
- Data join paths and DataAgent sync loop notes.

Computer use and readonly hands:

- Archives center playbook, API inventory, user-analysis API direct POST, browser auth preflight, and readonly safety.
- User login unified log UI/API readonly hand docs.
- Device SDK API-direct playbook, observation contract, error semantics, routing rules, and answer contract.
- Frontend activity profile hand docs.
- Tianshi strategy hit and eventList API-read docs.
- Multi-evidence orchestration and E2E readonly test templates.
- User ↔ Device Entity Resolution Layer v2.6.0.
- Observation contracts and smoke tests.

Experience-first layer:

- `computer_use_poc/user_experience_golden_cases.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/run_logs/user_experience_golden_cases_dry_run_001.md`

## 3. What The Incremental v2.6 Package Lacked

`outputs/release/dennis_risk_agent_v2_6_experience_first_release/` is an incremental experience package. It contains the experience-first docs and a small subset of `computer_use_poc`, but it does not include the full runtime-plus base:

- Missing core Agent runtime package files.
- Missing ATO complete runtime body.
- Missing DataAgent boundary package files.
- Missing most existing platform hand / computer use POC docs.
- Missing the full observation contract set.
- Missing v2.4 runtime integration and route regression assets.

Therefore it should not be used alone for cloud internal Agent integration.

## 4. Version Boundaries

This package does not include:

- New platform hands.
- Changes to real platform read logic.
- Real platform execution results beyond already archived run logs.
- Cookie, token, session, storageState, KIM code, or auth headers.
- `outputs/packages/`.
- Automatic punishment, automatic enforcement, or automatic final risk classification.

## 5. Integration Contract

The cloud internal Agent should treat this package as the complete v2.6 integration bundle:

1. Load v2.4 runtime-plus base first.
2. Load DataAgent boundary before any answer that mentions Hive / offline aggregate data.
3. Load v2.6 experience-first routing and answer templates before user-facing answer generation.
4. Load `computer_use_poc/observation_contract_v2_4_6.md` before consuming browser / API observations.
5. Load specific hand playbooks only when a case routes to that capability.

## 6. Validation State

- v2.4 runtime-plus full package: inherited as base.
- v2.6 User ↔ Device Entity Resolution: text regression 10/10 pass; graphData runtime error semantics documented.
- v2.6 experience-first golden cases: dry run completed; device-risk input completeness corrected.
- This full package itself is assembled for cloud integration and still needs cloud-side integration verification.

## 7. Known Risks

- The package is document-level integration; it does not execute real platform queries.
- Some runtime error semantics are documented but not all have real no-data / auth / permission response validation.
- If cloud integration loads only the v2.6 incremental package, the Agent will miss core runtime, ATO, DataAgent, and platform hand context.
- If answer templates are ignored, the Agent may regress to platform-navigation style answers rather than business-risk explanations.
