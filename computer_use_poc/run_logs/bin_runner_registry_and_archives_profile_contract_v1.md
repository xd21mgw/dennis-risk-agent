# Bin Runner Registry and Archives Profile Contract v1

## Background

The controlled runner path for `sso_session_runner` has restored the login log and Weapon graphData/riskData sources, but Dennis Risk Agent's original source plan is broader. Archives Center, Tianshi/RCP, track-analysis, and DataAgent/Hive remain core sources for ATO, abnormal publish, punishment-chain, strategy-hit, and frontend-activity cases.

Only restoring login_log + Weapon is insufficient because:

- ATO needs Archives Center user analysis as P0 account-baseline evidence.
- Abnormal publish / traffic-diversion content needs publish chain and publish-device evidence.
- Explicit strategy-hit questions need Tianshi strategy-hit evidence as target source.
- Frontend activity alignment needs track-analysis once a controlled runner is available.

## Why Bin Runner Registry

The registry makes platform execution explicit and bounded:

- child agent calls `bin/<runner_name>`;
- no `uv run` or direct implementation-file execution;
- no curl + cookie;
- no arbitrary URL/header/cookie inputs;
- fixed actions and input schemas;
- unified `source_card`, `source_quality`, `source_checkpoint_private`, and `redaction` output;
- main agent does not execute platform runners.

## Files Added / Updated

- `computer_use_poc/runner_registry_v1.yaml`
- `computer_use_poc/bin_runner_contract_v1.md`
- `computer_use_poc/archives_profile_runner.py`
- `bin/archives_profile_runner`
- `computer_use_poc/source_readiness_matrix_v1.yaml`
- `computer_use_poc/source_orchestration_plan_v1.yaml`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## Runner Status

- `sso_session_runner`: `runner_ready`; supports login log and Weapon graph/risk actions.
- `archives_profile_runner`: `planned_or_minimal_stub`; validates input and returns structured source gap without platform access.
- `tianshi_rcp_runner`: `playbook_ready_not_runner_ready`; contract only.
- `track_analysis_runner`: `endpoint_verified_not_runner_ready`; contract only.

## Archives Profile Runner Scope

This patch creates a minimal stub, not a live Archives Center connector.

Supported CLI shape:

```text
bin/archives_profile_runner --action archives.profile_home_info --user-id <uid> --timeout <sec> --format json
```

It returns:

- `archives_profile_source_status`
- `same_origin_fetch_ready`
- `available_fields`
- `account_status_summary`
- `ban_info_summary`
- `demote_info_summary`
- `login_device_summary`
- `register_device_summary`
- `missing_fields`
- `source_card`
- `source_quality`
- `source_checkpoint_private`
- `redaction`

Boundary:

- readonly only;
- no auth repair;
- no publish-device judgement;
- no real platform call in this patch;
- no cookie/token/session/header output.

## Not Implemented

- Full Archives Center same-origin fetch implementation.
- Publish-device trace runner.
- Tianshi/RCP runner implementation.
- Track-analysis runner implementation.
- DataAgent/Hive execution.

## Safety Boundary

- Did not access real platforms.
- Did not call DataAgent/Hive.
- Did not modify live config.
- Did not modify gateway/safeBins/tools.
- Did not modify `TOOLS.md`.
- Did not repackage.
