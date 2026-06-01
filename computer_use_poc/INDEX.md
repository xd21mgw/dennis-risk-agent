# computer_use_poc Index

Status: temporary navigation for the current repository layout. This index does
not move files and does not change runtime behavior.

`computer_use_poc/` is currently an overloaded workspace. It contains runtime
core rules, orchestration, capability routing, platform access contracts,
browser-backed adapters, DataAgent/Hive planning, validation, security tooling,
release support, bad cases, and historical run logs.

## Module Map

| group | key paths | purpose | runtime role | future action | risk note |
|---|---|---|---|---|---|
| runtime core / guard / answer contract | `multi_entry_runtime_guard_v1.md`, `answer_experience_templates.md`, `field_output_classification_policy_v1.md`, `runtime_semi_open_user_guide_v1.md`, `observation_contract_v2_4_6.md` | Entry guard, user-facing answer boundary, field classification, and observation contract. | runtime mainline | keep now; move_later only after reference checks | `do_not_move_without_reference_check` |
| source orchestration | `source_orchestration_plan_v1.yaml`, `source_orchestration_check.py`, `source_readiness_matrix_v1.yaml`, `source_executability_inventory_v1.yaml`, `runner_registry_v1.yaml`, `source_runner_health_check.py` | Source plan, controlled parallel groups, validator, runner inventory, readiness gates. | runtime mainline and validation | keep now | `source_orchestration_check.py` and dry-runs assume current paths |
| capability / scene routing | `capability_registry.md`, `scene_to_capability_routing.md`, `dennis_agent_capability_*.md`, `plan_mode_capability_v1.md` | Formal capability names, scene routing, and high-level capability architecture. | runtime mainline | keep now; index before any split | capability names are referenced by validation and answer gates |
| browser-backed / passthrough / controlled parallel | `browser_backed_service_adapter_v1.md`, `browser_backed_service_client.py`, `browser_backed_fixed_actions_text_dryrun.py`, `browser_backed_fixed_actions_text_regression_cases_v1.yaml`, `browser_backed_fixed_actions_text_demo_v1.md`, `browser_backed_fixed_actions_v1_integration_closure.md` | Browser-backed fixed actions contract, pure passthrough boundary, text regression and demo. | runtime adapter plus validation | move_later after path sweep | approved command paths and regression scripts assume current paths |
| platform access / playbooks / HAR / API direct | `platform_call_playbook_index.md`, `platform_access/`, `har_platform_interface_inventory_v1.md`, `archives_*`, `user_login_log_*`, `track_analysis_*`, `device_sdk_*`, `tianshi_*`, `tool_contracts/`, `tianshi_strategy_platform_contracts/` | Platform source contracts, playbooks, API direct notes, HAR-derived inventory, source-specific semantics. | platform access support; some files are runtime referenced | keep now; future platform_access consolidation | do not treat playbooks as runtime brain by themselves |
| DataAgent / Hive / offline data | `dataagent_*`, `setup_dataagent_*`, `query_plans/`, `batch_risk_clustering/account_security_hive_*`, `dataagent_sql_quality_gate.py` | Offline query plans, connector contracts, Hive registry-first guidance, local dry-run helpers. | offline planning; execution requires explicit authorization | keep now; move_later to offline data only after manifest check | do not imply DataAgent/Hive was executed |
| batch risk clustering | `batch_risk_clustering/INDEX.md`, `batch_risk_clustering/` | Batch clustering, ATO cluster lens, representative sampling, Hive/offline query planning, and batch regressions. | runtime/capability plus validation | keep now | selected files are manifest entries; golden/dry-run files are historical/regression |
| question collection | `question_collection/INDEX.md`, `question_collection/` | Runtime logging contracts, feedback capture, learning policy, templates, samples. | runtime support plus historical samples | keep now | selected files are manifest entries; sample CSV/JSONL must not be overwritten as runtime output |
| validation / smoke tests / dry-run / demo | `runtime_validation_cases_v1.yaml`, `smoke_tests.md`, `browser_backed_fixed_actions_text_*`, `test_fixtures/`, `user_experience_golden_cases.md`, `entity_resolution_*_test_cases*` | Regression cases, smoke gates, dry-run scripts, demo docs, fixtures. | validation / regression | keep now; split later only with test updates | path drift can break local checks |
| security / preflight / asset scanner | `security_preflight_*`, `readonly_safety_rules.md`, `capability_security_policy.md`, `asset_extraction_*`, `package_asset_scanner.py`, `package_asset_scanner_rules.json`, `runtime_preflight_check.py`, `release_preflight_check.py`, `release_*` | Security gates, preflight scripts, asset scanning, release readiness. | release support and guard validation | keep now | scripts contain hardcoded path assumptions |
| full simulation / snapshot / release support | `runtime_required_file_manifest_v1.yaml`, `runtime_snapshot_builder.py`, `full_runtime_inference_contract_v1.md`, `runtime_integration_validation_checklist_v1.md` | Runtime snapshot manifest, builder, full-runtime simulation contract. | packaging and validation support | keep now | `outputs/full_runtime` is generated, not source |
| run logs / historical notes | `run_logs/` | Historical patch logs, validation summaries, run evidence. | historical_only | index_only | not runtime mainline |
| bad cases / case learning | `bad_cases/`, `case_sets/`, `question_collection/` | Bad cases, curated case sets, learning notes, candidate queues. | regression_source or historical_only, depending on file | index_only now | do not infer runtime behavior from stale cases |

## Archived Legacy Notes

- `integration_notes.md` moved to `docs/archive/computer_use_poc_legacy/integration_notes.md`.
- `failure_modes.md` moved to `docs/archive/computer_use_poc_legacy/failure_modes.md`.

Both are `historical_only`; current runtime boundaries live in the active guard,
source orchestration, platform access contracts, and validation files.

## Outputs Boundary

- `outputs/full_runtime`: generated test/runtime snapshot, not a development source.
- `outputs/release`: formal release artifact area, versioned and reviewable.
- `outputs/dist`: local transfer/tarball package area, default not to commit.

This index does not modify any `outputs/**` path.

## Subdirectory Indexes

- `batch_risk_clustering/INDEX.md`: batch clustering, ATO lens, offline plan,
  validation, and historical/golden assets.
- `question_collection/INDEX.md`: runtime logging contracts, learning policy,
  templates, samples, and historical validation records.
- `tool_contracts/INDEX.md`: source/tool contract boundary.
- `strategy_governance/INDEX.md`: strategy governance readonly capability
  contracts and validation assets.
- `platform_access/INDEX.md`: platform access contracts and observation
  boundary.
- `bad_cases/INDEX.md`: bad cases as regression source, not runtime mainline.
- `run_logs/INDEX.md`: historical run logs index. This file may require
  `git add -f` because `run_logs/**` is ignored.

## Migration Checkpoint

Before moving any path out of `computer_use_poc/`, check:

- `runtime_required_file_manifest_v1.yaml`
- `runtime_snapshot_builder.py`
- `source_orchestration_check.py`
- `browser_backed_fixed_actions_text_dryrun.py`
- `runtime_preflight_check.py`
- `release_preflight_check.py`
- `source_runner_health_check.py`
- references from `AGENTS.md`, `TOOLS.md`, `skills/**/11_runtime_summaries/**`, and validation cases

Files marked `do_not_move_without_reference_check` must remain in place until
the references and validation commands are updated together.
