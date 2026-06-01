# Runtime Directory Consolidation Plan v1

Status: architecture plan only.
Scope: local mother-repo directory governance, inventory, dependency risk, and a minimal migration proposal.
Non-goals: no bulk move, no delete, no runtime behavior change, no packaging, no commit.

Related indexes and gates:

- `docs/architecture/INDEX.md`
- `docs/architecture/runtime_path_reference_report_v1.md`
- `docs/architecture/runtime_migration_checklist_v1.md`
- `computer_use_poc/INDEX.md`
- `computer_use_poc/batch_risk_clustering/INDEX.md`
- `computer_use_poc/question_collection/INDEX.md`
- `computer_use_poc/tool_contracts/INDEX.md`
- `computer_use_poc/strategy_governance/INDEX.md`
- `computer_use_poc/platform_access/INDEX.md`
- `computer_use_poc/bad_cases/INDEX.md`
- `computer_use_poc/run_logs/INDEX.md`
- `docs/archive/INDEX.md`

## 1. Current Directory Inventory

### Top-level inventory

| path | main content | current role | current issue | runtime dependency | historical/temp/artifact | migration recommendation | risk |
|---|---|---|---|---|---|---|---|
| `AGENTS.md` | main Dennis runtime instructions and guard rules | runtime entry contract | high impact, many downstream assumptions | yes | no | keep | high |
| `TOOLS.md` | tool/platform boundary and main-entry guard | tool boundary contract | overlays must not replace it accidentally | yes | no | keep | high |
| `README.md` / `QUICKSTART_PROMPTS.md` | repo usage and prompts | human entry docs | can lag runtime reality | low/unknown | no | index_only | low |
| `bin/` | wrapper commands such as source runners | executable boundary | referenced by manifest/builder/preflight | yes | no | keep | high |
| `computer_use_poc/` | runtime core, orchestration, platform docs, validation, DataAgent, security, run logs, release helpers | overloaded mother-body workspace | mixes runtime mainline, historical logs, platform docs, tests, release tooling, local experiments | yes | yes | split by index first; move later only after grep | high |
| `skills/` | full skill source and runtime summaries | expert knowledge base | runtime summaries are loaded, full skill source is not always packaged | yes for summaries | historical/full source mixed | keep; index summaries | high |
| `eval/` | tested skill templates and historical eval packs | evaluation/history | some capability registry references still point here | unknown | yes | archive/index later | medium |
| `outputs/full_runtime/` | generated full runtime snapshot | test/runtime snapshot | can be mistaken as development source | yes as generated output, not source | artifact | do_not_touch | high |
| `outputs/release/` | formal release/overlay packages | release artifacts | many versions and overlays; should not be edited as source | no for source; yes for release review | artifact | do_not_touch | high |
| `outputs/dist/` | local tarballs / transfer packages | temporary distribution | should not enter source/runtime decisions | no | artifact/temp | do_not_touch | high |
| `outputs/drafts`, `outputs/final`, `outputs/intermediate`, `outputs/packages`, `outputs/reviews` | generated material and review outputs | artifact workspace | mixed lifecycle | no/unknown | artifact | do_not_touch this round | medium |
| `docs/` | goals and new architecture docs | planning docs | currently sparse and untracked in this workspace | no | no | keep for architecture indexes | low |
| `memory/` | local routing trace memory | local runtime observation | should not become source truth | no/unknown | temp/history | archive/index only | medium |
| `internal_risk_platforms/` | internal platform references | platform context | needs separate boundary from runtime core | unknown | no | index later | medium |

### `computer_use_poc/` sub-inventory

| path | main content | current role | issue | runtime dependency | recommendation | risk |
|---|---|---|---|---|---|---|
| `source_orchestration_plan_v1.yaml` | source plan, browser-backed, batch ATO, universal workflow | orchestration core | hardcoded by validator/dry-run | yes | keep | high |
| `source_orchestration_check.py` | local offline validator | orchestration validator | hardcoded `PLAN_PATH` | yes | keep | high |
| `multi_entry_runtime_guard_v1.md` | entry guard | runtime core | referenced by AGENTS/manifest/preflight | yes | keep | high |
| `answer_experience_templates.md` | user-facing output contract | answer contract | referenced by manifest/release/preflight | yes | keep | high |
| `capability_registry.md` | formal capability index | capability core | many docs refer to capability names | yes | keep | high |
| `scene_to_capability_routing.md` | routing map | routing core | referenced by AGENTS/preflight/validation | yes | keep | high |
| `runtime_required_file_manifest_v1.yaml` | full runtime manifest | packaging/runtime snapshot input | contains many exact current paths and exclude globs | yes | keep | high |
| `runtime_snapshot_builder.py` | builds `outputs/full_runtime` | snapshot builder | hardcoded manifest/output path and runtime-local AGENTS block | yes | keep | high |
| `smoke_tests.md` / `runtime_validation_cases_v1.yaml` | validation cases and smoke text gates | regression | large and mixed but heavily referenced | yes | keep; later split index | high |
| `browser_backed_*` | browser-backed client, adapter, text dry-run/demo/regression | source adapter and regression | pure passthrough path is runtime-sensitive | yes | keep | high |
| `platform_access/` | platform access schemas/contracts | platform playbook layer | current docs and schema are referenced by manifest and checks | yes | keep; future platform_access top-level via move_later | high |
| `tianshi_strategy_platform_contracts/`, `strategy_governance/`, `tool_contracts/` | platform capability contracts | platform-specific contracts | belongs conceptually under platform access | yes/unknown | index now; move later | medium/high |
| `batch_risk_clustering/` | batch clustering, ATO lens, DataAgent/Hive registries | batch/capability/offline plan | mixes runtime batch docs and golden/dry-run files | yes | keep; split later by index | high |
| `query_plans/` | offline query plan examples | offline planning | should not be runtime evidence | unknown | index_only | medium |
| `question_collection/` | case learning and logging stubs | case learning | mix of runtime append-only logging and candidate docs | yes/unknown | keep; index later | medium |
| `bad_cases/`, `case_sets/` | bad case docs and case sets | regression/history | should feed validation but not runtime conclusion | no/unknown | archive/index | low/medium |
| `run_logs/` | 177 historical run logs and patch logs | history/audit | largest pollution source inside `computer_use_poc`; often references runtime files | no for runtime; yes as historical context | archive/index only | medium |
| `security_preflight_*`, `release_*`, `package_asset_scanner*`, `runtime_preflight_check.py` | security/release guards | release/security tooling | scripts hardcode paths | yes for release guard | keep | high |
| `dataagent_*`, `setup_dataagent_*` | DataAgent/Hive contracts and local dry-run helpers | offline data boundary | must not be confused with live execution | yes/unknown | keep; index under offline data later | high |

## 2. Current Problem Diagnosis

- `computer_use_poc/` is too broad. It contains runtime core, orchestration, platform playbooks, browser-backed adapter contracts, DataAgent/Hive offline plans, validation cases, release/preflight scripts, security scanners, historical run logs, bad cases, and local experiments.
- Runtime mainline files are mixed with patch history. Core files include `multi_entry_runtime_guard_v1.md`, `source_orchestration_plan_v1.yaml`, `source_orchestration_check.py`, `capability_registry.md`, `scene_to_capability_routing.md`, `answer_experience_templates.md`, `runtime_required_file_manifest_v1.yaml`, `runtime_validation_cases_v1.yaml`, and `smoke_tests.md`.
- Testing/regression files are mixed with runtime contracts. `browser_backed_fixed_actions_text_dryrun.py`, its regression YAML, demo markdown, `runtime_validation_cases_v1.yaml`, and `smoke_tests.md` should be treated as validation, not runtime source behavior.
- Platform access docs are spread across root `computer_use_poc/*.md`, `platform_access/`, `tianshi_strategy_platform_contracts/`, `strategy_governance/`, and `tool_contracts/`.
- Historical run logs and patch notes live inside the main runtime workspace. They should be indexed and marked historical-only so future development does not infer runtime behavior from old patches.
- Release and artifact directories are present in the same repo tree. `outputs/full_runtime` is a generated test snapshot, `outputs/release` is release output, and `outputs/dist` is transfer output. None should be edited as development source.
- Hardcoded paths are significant. `runtime_required_file_manifest_v1.yaml`, `runtime_snapshot_builder.py`, `source_orchestration_check.py`, `browser_backed_fixed_actions_text_dryrun.py`, `runtime_preflight_check.py`, `release_preflight_check.py`, and `source_runner_health_check.py` all reference exact current paths.
- High-risk files cannot be moved first. Any path used by manifest, builder, preflight, validator, dry-run, or AGENTS/TOOLS must remain in place until references are updated and validated.

## 3. Recommended First-level Directory Scheme

This is a target model, not an immediate migration.

| target directory | responsibility | should contain | should not contain | current mapping | migrate now? |
|---|---|---|---|---|---|
| `runtime_core/` | entry guards, field/output policy, answer contract, core runtime manifest | `multi_entry_runtime_guard`, `answer_experience_templates`, field policy, runtime user guide | platform playbooks, run logs, release artifacts | mostly `computer_use_poc/*.md` | no; index first |
| `orchestration/` | source plans and validators | `source_orchestration_plan`, `source_orchestration_check`, source readiness and runner registry | historical patches, platform API details | `computer_use_poc/source_*`, `runner_registry` | no; high hardcoded risk |
| `capabilities/` | capability registry and scene routing | `capability_registry`, `scene_to_capability_routing`, capability architecture docs | platform schemas, run logs | `computer_use_poc/capability_*`, routing docs | no; index first |
| `platform_access/` | platform playbooks, API contracts, HAR-derived docs | `platform_access/`, Tianshi contracts, Archives/Device/Track/Login playbooks | runtime answer templates, release scripts | mixed under `computer_use_poc/` | move_later |
| `browser_backed/` | browser-backed fixed action adapter, pure passthrough, controlled batch, local text dry-runs | browser-backed adapter/client/regression/demo | unrelated platform docs | `computer_use_poc/browser_backed_*` | move_later after path sweep |
| `offline_data/` | DataAgent/Hive contracts, query plan templates, offline registries | DataAgent schemas, Hive source registries, query plans | runtime execution claims, raw results | `computer_use_poc/dataagent_*`, `batch_risk_clustering/account_security_hive_*`, `query_plans/` | move_later |
| `validation/` | smoke tests, runtime cases, text dry-runs, fixtures | validation YAML, smoke markdown, fixtures, demo outputs | runtime source contracts | `smoke_tests`, `runtime_validation`, `test_fixtures`, dry-run files | move_later |
| `cases/` | bad cases, case sets, learning notes | `bad_cases`, `case_sets`, curated case-learning notes | live runtime rules | `computer_use_poc/bad_cases`, `case_sets`, `question_collection` parts | move_later/index |
| `docs/` | architecture and planning docs | architecture plans, indexes, design notes | runtime-loaded rules unless explicitly referenced | existing `docs/` plus this plan | yes for new docs only |
| `run_logs/` | historical run logs | indexed historical logs | runtime mainline rules | `computer_use_poc/run_logs` | index_only; do not bulk move |
| `security/` | preflight, asset scanner, release guard, redaction policy | security preflight, package scanner, release security checklist | platform playbooks, runtime summaries | `computer_use_poc/security_*`, `release_*`, `package_asset_*` | move_later |
| `release/` | release recipes and packaging guidance | release checklists, manifests, generated release metadata references | actual release outputs | `computer_use_poc/release_*`, `outputs/release` as artifact | index only |
| `skills/` | full skill source and runtime summaries | existing skill tree | runtime-generated output | `skills/` | keep |
| `outputs/` | generated artifacts | `full_runtime`, `release`, `dist`, drafts/reviews | development source | existing `outputs/` | do_not_touch |

## 4. Key Module Ownership Table

| module | current_path | recommended_path | action | reason | runtime_dependency | migration_risk | validation_needed |
|---|---|---|---|---|---|---|---|
| runtime core / guard | `computer_use_poc/multi_entry_runtime_guard_v1.md` | `runtime_core/multi_entry_runtime_guard_v1.md` | move_later | hardcoded in AGENTS, manifest, preflight | yes | high | manifest, preflight, grep, dry-run |
| answer contract | `computer_use_poc/answer_experience_templates.md` | `runtime_core/answer_experience_templates.md` | move_later | core user-visible output | yes | high | smoke, dry-run, manifest |
| field/output policy | `computer_use_poc/field_output_classification_policy_v1.md` | `runtime_core/field_output_classification_policy_v1.md` | move_later | loaded by manifest and guard | yes | high | manifest, grep |
| source orchestration plan | `computer_use_poc/source_orchestration_plan_v1.yaml` | `orchestration/source_orchestration_plan_v1.yaml` | keep | `source_orchestration_check.py` hardcodes path | yes | high | source_orchestration_check |
| source orchestration check | `computer_use_poc/source_orchestration_check.py` | `orchestration/source_orchestration_check.py` | keep | invoked by AGENTS/TOOLS/preflight | yes | high | py_compile, validator |
| capability registry | `computer_use_poc/capability_registry.md` | `capabilities/capability_registry.md` | move_later | many references and formal names | yes | high | grep, dry-run |
| scene routing | `computer_use_poc/scene_to_capability_routing.md` | `capabilities/scene_to_capability_routing.md` | move_later | AGENTS and validation reference | yes | high | grep, dry-run |
| platform playbook index | `computer_use_poc/platform_call_playbook_index.md` | `platform_access/platform_call_playbook_index.md` | move_later | AGENTS/preflight/runtime depend on exact path | yes | high | preflight, grep |
| platform API/HAR docs | `computer_use_poc/platform_access/**`, `tianshi_strategy_platform_contracts/**`, platform root docs | `platform_access/**` | move_later | good conceptual target, but manifest globs and docs reference current path | yes/unknown | medium/high | manifest, grep |
| browser-backed adapter | `computer_use_poc/browser_backed_service_adapter_v1.md` | `browser_backed/browser_backed_service_adapter_v1.md` | move_later | manifest and source plan reference path | yes | high | dry-run, manifest |
| browser-backed client | `computer_use_poc/browser_backed_service_client.py` | `browser_backed/browser_backed_service_client.py` | move_later | approved command paths and manifest likely assume current path | yes | high | py_compile, self-test |
| controlled parallel batch contract | `source_orchestration_plan_v1.yaml`, `browser_backed_service_adapter_v1.md` | `orchestration/` + `browser_backed/` | keep | split only after index | yes | high | source check and text dry-run |
| DataAgent contracts | `computer_use_poc/dataagent_*` | `offline_data/dataagent/` | move_later | runtime manifest includes several files | yes/unknown | high | manifest, py_compile |
| Hive/offline registries | `computer_use_poc/batch_risk_clustering/account_security_hive_*`, `query_plans/` | `offline_data/hive_registry/` | move_later | source plan and capability docs reference exact paths | yes | high | grep, validation |
| validation cases | `computer_use_poc/runtime_validation_cases_v1.yaml` | `validation/runtime_validation_cases_v1.yaml` | keep | widely referenced | yes | high | YAML parse, grep |
| smoke tests | `computer_use_poc/smoke_tests.md` | `validation/smoke_tests.md` | keep | manifest and AGENTS reference exact path | yes | high | grep |
| text dry-run/demo | `computer_use_poc/browser_backed_fixed_actions_text_*` | `validation/browser_backed/` | move_later | dry-run hardcodes current paths | yes | high | py_compile, dry-run |
| full simulation fixtures | `outputs/full_runtime`, `computer_use_poc/full_runtime_inference_contract_v1.md` | `outputs/full_runtime`, `runtime_core/full_runtime_inference_contract_v1.md` | do_not_touch for output; move_later for contract | generated snapshot boundary | yes | high | snapshot builder |
| runtime summaries | `skills/.../11_runtime_summaries/*.md` | keep under `skills/.../11_runtime_summaries/` | keep | AGENTS and manifest load this glob | yes | high | manifest |
| run logs | `computer_use_poc/run_logs/**` | `run_logs/` or `docs/history/run_logs/` | index_only | historical audit; excluded from runtime manifest | no | medium | grep before moving |
| bad cases | `computer_use_poc/bad_cases/**` | `cases/bad_cases/` | move_later/index | useful regression history, not runtime mainline | unknown | medium | grep |
| case learning notes | `computer_use_poc/question_collection/**` | `cases/question_collection/` | move_later/index | some files in manifest, some excluded | yes/unknown | medium/high | manifest, grep |
| security/preflight | `computer_use_poc/security_*`, `runtime_preflight_check.py`, `release_preflight_check.py`, `package_asset_scanner*` | `security/` | move_later | scripts hardcode paths | yes for release guard | high | py_compile, preflight |
| `AGENTS.md` | `AGENTS.md` | root | keep | entry instruction file | yes | high | manual review |
| `TOOLS.md` | `TOOLS.md` | root | keep | tool boundary file | yes | high | manual review |
| `outputs/full_runtime` | `outputs/full_runtime` | same | do_not_touch | generated runtime snapshot/test package | artifact | high | rebuild only in dedicated task |
| `outputs/release` | `outputs/release` | same | do_not_touch | formal release outputs | artifact | high | release preflight only |
| `outputs/dist` | `outputs/dist` | same | do_not_touch | local tar.gz/upload packages | artifact/temp | high | package scanner only |

## 5. Keep-in-place List

Do not move in the next migration unless all references are updated and checked:

- `AGENTS.md`, `TOOLS.md`.
- `computer_use_poc/runtime_required_file_manifest_v1.yaml`.
- `computer_use_poc/runtime_snapshot_builder.py`.
- `computer_use_poc/source_orchestration_plan_v1.yaml`.
- `computer_use_poc/source_orchestration_check.py`.
- `computer_use_poc/browser_backed_fixed_actions_text_dryrun.py`.
- `computer_use_poc/browser_backed_fixed_actions_text_regression_cases_v1.yaml`.
- `computer_use_poc/browser_backed_fixed_actions_text_demo_v1.md`.
- `computer_use_poc/runtime_validation_cases_v1.yaml`.
- `computer_use_poc/smoke_tests.md`.
- `computer_use_poc/runtime_preflight_check.py`.
- `computer_use_poc/release_preflight_check.py`.
- `computer_use_poc/package_asset_scanner.py` and `package_asset_scanner_rules.json`.
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/*.md`.
- `outputs/full_runtime/**`, `outputs/release/**`, `outputs/dist/**`.

Reason: these are referenced by manifest, builder, tests, runtime instructions, or release/security scripts. Moving first would create path drift.

## 6. Historical Archive and Indexing Plan

- `computer_use_poc/run_logs/**`: keep historical-only. Add an index before moving anything. Suggested metadata: date, theme, files touched, validation commands, runtime relevance, historical-only flag.
- Old overlays / historical patches: keep under release/run-log history, not runtime core. If they mention old defaults or legacy paths, mark them `historical_only_not_runtime_dependency`.
- `computer_use_poc/bad_cases/**`: keep as curated regression source. Index by risk domain, bad-case root cause, regression IDs, and current runtime rule that addresses it.
- `computer_use_poc/question_collection/**`: split conceptually into case learning templates, runtime logging stubs, sample records, and candidate queues. Some files are in runtime manifest, so only index first.
- Any historical document that conflicts with current pure passthrough, no default routing metadata, DataAgent authorization, or full-runtime boundary should be downgraded in index rather than silently used as runtime source.

## 7. Outputs Boundary

- `outputs/full_runtime`: generated test/runtime snapshot. It is useful for local user-experience simulation and validation, but it is not the development source of truth. Rebuild only via `runtime_snapshot_builder.py` in a dedicated task.
- `outputs/release`: formal release and overlay artifacts. Treat as versioned output that can be reviewed and rolled back, not as editable source.
- `outputs/dist`: local tar.gz/upload/transfer package directory. Default is not to commit and not to use as runtime input.
- This round does not modify any `outputs/**` path.

## 8. Minimal Executable Migration Plan

Limit the next round to at most five low-risk actions:

| action | purpose | files | risk | validation | rollback |
|---|---|---|---|---|---|
| 1. Add `docs/architecture/INDEX.md` | make architecture plans discoverable | new markdown only | low | `git diff --check` | delete the new file |
| 2. Add `computer_use_poc/INDEX.md` | label current subareas without moving files | new markdown only | low | `git diff --check`; grep no path changes | delete the new file |
| 3. Add `computer_use_poc/run_logs/INDEX.md` | stop historical logs from polluting runtime interpretation | new markdown only | low/medium because run_logs may be ignored | `git diff --check`; if ignored, note `git add -f` need | delete the new file |
| 4. Add `computer_use_poc/bad_cases/INDEX.md` | map bad cases to active regression IDs | new markdown only | low | `git diff --check` | delete the new file |
| 5. Add `computer_use_poc/platform_access/INDEX.md` | group platform contracts/playbooks before any move | new markdown only | low | `git diff --check`; confirm no manifest edits | delete the new file |

Do not perform file moves in the next round unless these indexes are accepted.

## 9. Migration Risk and Rollback Strategy

Before any move:

1. Run `rg -n "<old/path/or/filename>" AGENTS.md TOOLS.md README.md computer_use_poc skills eval bin`.
2. Check `computer_use_poc/runtime_required_file_manifest_v1.yaml` for `files`, `globs`, `optional_files`, and `excluded_files`.
3. Check scripts with hardcoded paths:
   - `computer_use_poc/runtime_snapshot_builder.py`
   - `computer_use_poc/source_orchestration_check.py`
   - `computer_use_poc/browser_backed_fixed_actions_text_dryrun.py`
   - `computer_use_poc/runtime_preflight_check.py`
   - `computer_use_poc/release_preflight_check.py`
   - `computer_use_poc/source_runner_health_check.py`
4. Update references and run validation:
   - `python3 -m py_compile <changed_python_files>`
   - YAML parse for changed manifests/cases.
   - `python3 computer_use_poc/source_orchestration_check.py --format json`
   - relevant text dry-run/demo if browser-backed paths change.
   - `git diff --check`.
5. Split commits by theme: indexes only, runtime path move, validation path move, platform docs move, release/security tooling move. Do not mix with unrelated dirty files.

Rollback:

- Before commit: `git restore --staged <files>` and `git restore <files>` for tracked files; remove newly added index files if needed.
- After commit: use `git revert <commit>` rather than manual partial rollback when path moves affect multiple references.
- If a move fails validation, restore moved files to old paths first, then fix references separately.

## 10. This Round Boundary

Confirmed scope for this document:

- No real platform access.
- No DataAgent/Hive call.
- No bulk file move.
- No file deletion.
- No runtime behavior change.
- No release build.
- No modification to `outputs/full_runtime`, `outputs/release`, or `outputs/dist`.
- No handling of unrelated dirty/untracked files except noting them in inventory.
- No git commit.
