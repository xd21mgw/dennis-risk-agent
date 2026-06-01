# Runtime Path Reference Report v1

Status: migration pre-check only.
Scope: hardcoded path and runtime dependency scan for local mother-repo
directory governance.
Non-goals: no file move, no delete, no runtime behavior change, no packaging,
no platform access, no DataAgent/Hive execution.

## Scan Inputs

Scanned paths:

- `AGENTS.md`
- `TOOLS.md`
- `README.md`
- `docs/**/*.md`
- `computer_use_poc/**/*.py`
- `computer_use_poc/**/*.md`
- `computer_use_poc/**/*.yaml`
- `skills/**/*.md`

Primary keywords:

- `computer_use_poc/`
- `source_orchestration_plan_v1.yaml`
- `source_orchestration_check.py`
- `runtime_required_file_manifest_v1.yaml`
- `runtime_snapshot_builder.py`
- `smoke_tests.md`
- `runtime_validation_cases_v1.yaml`
- `browser_backed_service_client.py`
- `browser_backed_fixed_actions_text_dryrun.py`
- `capability_registry.md`
- `scene_to_capability_routing.md`
- `platform_call_playbook_index.md`
- `answer_experience_templates.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep`
- `outputs/full_runtime`
- `outputs/release`
- `outputs/dist`
- `run_logs`
- `batch_risk_clustering`
- `question_collection`
- `platform_access`

## Summary

The repository still has substantial exact-path coupling. The highest-risk
couplings are not only documentation references; several Python scripts and the
runtime manifest directly load current paths. Moving runtime-adjacent files
before updating references would break source orchestration, full-runtime
snapshot generation, preflight checks, and text dry-run validation.

## High-risk References

Mark all paths in this section as `do_not_move_without_reference_update`.

| referenced_path | referenced_by | reference_type | migration_risk | recommended_action | notes |
|---|---|---|---|---|---|
| `computer_use_poc/runtime_required_file_manifest_v1.yaml` | `runtime_snapshot_builder.py`, manifest self-reference, architecture docs | runtime / release | high | keep | Builder hardcodes this manifest path as `DEFAULT_MANIFEST`. |
| `computer_use_poc/runtime_snapshot_builder.py` | architecture docs, approved workflow, full-runtime process | runtime / release | high | keep | Owns `outputs/full_runtime` generation; do not move before manifest and command updates. |
| `computer_use_poc/source_orchestration_plan_v1.yaml` | `source_orchestration_check.py`, `browser_backed_fixed_actions_text_dryrun.py`, `runtime_preflight_check.py`, manifest, AGENTS | runtime / validation | high | keep | Core source plan; validator and dry-run hardcode this path. |
| `computer_use_poc/source_orchestration_check.py` | AGENTS, `runtime_preflight_check.py`, manifest, architecture docs | runtime / validation | high | keep | Required before platform source execution; invoked by preflight. |
| `computer_use_poc/browser_backed_fixed_actions_text_dryrun.py` | manifest, architecture docs, local validation commands | validation | high | keep | Hardcodes source plan, regression YAML, and demo doc paths. |
| `computer_use_poc/browser_backed_fixed_actions_text_regression_cases_v1.yaml` | dry-run script, manifest, smoke tests | validation | high | keep | Moving requires dry-run path update and YAML validation. |
| `computer_use_poc/browser_backed_fixed_actions_text_demo_v1.md` | dry-run script, manifest | validation / demo | high | keep | Demo writer path is hardcoded. |
| `computer_use_poc/runtime_validation_cases_v1.yaml` | AGENTS, manifest, `runtime_preflight_check.py`, smoke tests | validation / runtime gate | high | keep | Broad regression dependency. |
| `computer_use_poc/smoke_tests.md` | AGENTS, manifest, README, many docs | validation | high | keep | Contains many exact file and command checks. |
| `computer_use_poc/multi_entry_runtime_guard_v1.md` | AGENTS, manifest, preflight checks | runtime | high | keep | Entry guard; moving requires AGENTS and manifest update. |
| `computer_use_poc/answer_experience_templates.md` | AGENTS, manifest, README, smoke tests | runtime | high | keep | User-facing answer contract. |
| `computer_use_poc/capability_registry.md` | AGENTS, manifest, README, smoke tests, routing docs | runtime | high | keep | Capability names are treated as canonical. |
| `computer_use_poc/scene_to_capability_routing.md` | AGENTS, manifest, README, smoke tests | runtime | high | keep | Route names are treated as canonical. |
| `computer_use_poc/platform_call_playbook_index.md` | AGENTS, manifest, preflight references | runtime support | high | keep | Platform call preflight depends on this current path. |
| `computer_use_poc/field_output_classification_policy_v1.md` | AGENTS, manifest, smoke tests | runtime | high | keep | Output safety and redaction policy. |
| `computer_use_poc/security_preflight_policy.yaml` | AGENTS, manifest, security checks | runtime / security | high | keep | Security policy input. |
| `computer_use_poc/runtime_preflight_check.py` | AGENTS, manifest, README, smoke tests | release / runtime guard | high | keep | Reads several hardcoded runtime files and runs orchestration validator. |
| `computer_use_poc/release_preflight_check.py` | manifest, README, smoke tests | release | high | keep | Has required path checks for release packages. |
| `computer_use_poc/package_asset_scanner.py` and rules | manifest, README, smoke tests | release / security | high | keep | Release security gate with hardcoded expected assets. |
| `computer_use_poc/browser_backed_service_client.py` | manifest, approved command paths, browser-backed docs | runtime adapter | high | keep | Not only a doc reference; command paths assume current location. |
| `computer_use_poc/browser_backed_service_adapter_v1.md` | manifest, source plan, browser-backed docs | runtime adapter contract | high | keep | Pure passthrough contract. |
| `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/*.md` | AGENTS, manifest glob | runtime | high | keep | Loaded as runtime summaries; do not move before loader/manifest update. |
| `computer_use_poc/platform_access/**` | manifest glob, platform docs, run logs | runtime support / platform contract | high | keep | Whole directory is included by manifest glob. |
| `computer_use_poc/tool_contracts/**` | manifest glob | runtime support | high | keep | Whole directory included by manifest. |
| `computer_use_poc/tianshi_strategy_platform_contracts/**` | manifest glob, README, smoke tests | runtime support | high | keep | Whole directory included by manifest. |
| `computer_use_poc/strategy_governance/**` | manifest glob, README, smoke tests | runtime support | high | keep | Whole directory included by manifest. |
| `computer_use_poc/multi_evidence_orchestration_contracts/**` | manifest glob, README | runtime support | high | keep | Whole directory included by manifest. |
| `computer_use_poc/batch_risk_clustering/*` selected runtime files | manifest explicit entries, README, smoke tests | runtime / capability | high | keep | Some batch files are included, while golden/text-dry-run files are excluded. |
| `computer_use_poc/question_collection/*` selected runtime files | manifest explicit entries, README, smoke tests | runtime support / learning contract | high | keep | Some templates/logs are excluded, but collector and contract files are included. |
| `bin/archives_profile_runner` and `bin/tianshi_rcp_runner` | manifest explicit entries | runtime runner | high | keep | Runner paths must not drift from manifest. |
| `outputs/full_runtime` | builder output, docs, run logs | generated artifact | high | do_not_touch | Test/runtime snapshot, not development source. |
| `outputs/release` | manifest exclusion, release docs, smoke tests | release artifact | high | do_not_touch | Formal release output; do not edit as source. |
| `outputs/dist` | README, smoke tests, architecture docs | temp artifact | high | do_not_touch | Local transfer/tarball output; default not to commit. |

## Medium-risk References

These references are mostly docs, README entries, indexes, and playbooks. They
can move later, but only with bulk reference replacement and validation.

| referenced_path | referenced_by | reference_type | migration_risk | recommended_action | notes |
|---|---|---|---|---|---|
| `computer_use_poc/README.md` | README, project structure index, smoke tests | doc | medium | move_later | Human entry doc; may lag runtime reality. |
| `computer_use_poc/project_structure_index.md` | README, smoke tests, architecture docs | doc / validation | medium | move_later | Existing navigation doc; keep until new indexes are accepted. |
| `computer_use_poc/dennis_agent_capability_overview_v1.md` | README and docs | doc | medium | move_later | Candidate for future docs/capability archive after reference check. |
| `computer_use_poc/dennis_agent_capability_architecture_v1.md` | README and docs | doc | medium | move_later | Architecture-adjacent but currently referenced. |
| `computer_use_poc/dennis_agent_expert_capability_view_v1.md` | README and docs | doc | medium | move_later | Expert capability view; can be indexed first. |
| `computer_use_poc/archives_*`, `user_login_log_*`, `track_analysis_*`, `device_sdk_*`, `tianshi_*` root docs | manifest, README, smoke tests, run logs | platform playbook / doc | medium | move_later | Conceptually belongs under platform access, but many direct references exist. |
| `computer_use_poc/dataagent_*` | manifest, README, smoke tests, run logs | offline data contract | medium/high | move_later | Move only with DataAgent boundary validation; no execution implied. |
| `computer_use_poc/query_plans/**` | docs and planning materials | offline plan | medium | index_only | Not runtime evidence; can be indexed under offline data. |
| `computer_use_poc/bad_cases/**` | architecture docs, bad case index, possible validation references | regression_source | medium | archive_later | Current bad cases are useful but not runtime mainline. |
| `docs/architecture/**` | architecture docs and indexes | doc | medium | keep | New governance docs; easy to move only within docs if needed. |
| `README.md` references to `skills/**` and `computer_use_poc/**` | root README | doc | medium | move_later | Update after physical migration, not before. |

## Low-risk References

These are historical references and can be archived later. Some still feed
regression understanding, so avoid bulk deletion.

| referenced_path | referenced_by | reference_type | migration_risk | recommended_action | notes |
|---|---|---|---|---|---|
| `computer_use_poc/run_logs/**` | run log files, README, smoke tests, architecture docs | historical | low/medium | index_only / archive_later | Excluded from manifest. Some smoke tests cite selected logs as evidence. |
| `computer_use_poc/run_logs/INDEX.md` | ignored by `.gitignore` currently | historical index | low | index_only | If committed later, use `git add -f` for this INDEX only. |
| `computer_use_poc/batch_risk_clustering/*golden*` | manifest excluded patterns, docs | regression / historical | low | archive_later | Excluded from full-runtime manifest. |
| `computer_use_poc/batch_risk_clustering/*text_dry_run*` | manifest excluded patterns, run logs | validation history | low | archive_later | Excluded from full-runtime manifest. |
| `computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv` | manifest excluded patterns, README, smoke tests | template/history | low | archive_later | Do not treat as runtime write target. |
| `computer_use_poc/question_collection/runtime_question_record_sample_v1.jsonl` | manifest excluded patterns, README, smoke tests | sample | low | archive_later | Sample only. |
| `computer_use_poc/test_fixtures/**` selected excluded paths | manifest exclusions, smoke tests | fixture | low/medium | keep or archive_later | Fixtures must stay until tests are updated. |

## Do-not-move List

Do not move these without a coordinated reference update and validation run:

- `AGENTS.md`
- `TOOLS.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/*.md`
- `computer_use_poc/runtime_required_file_manifest_v1.yaml`
- `computer_use_poc/runtime_snapshot_builder.py`
- `computer_use_poc/source_orchestration_plan_v1.yaml`
- `computer_use_poc/source_orchestration_check.py`
- `computer_use_poc/browser_backed_fixed_actions_text_dryrun.py`
- `computer_use_poc/browser_backed_fixed_actions_text_regression_cases_v1.yaml`
- `computer_use_poc/browser_backed_fixed_actions_text_demo_v1.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/runtime_preflight_check.py`
- `computer_use_poc/release_preflight_check.py`
- `computer_use_poc/package_asset_scanner.py`
- `computer_use_poc/package_asset_scanner_rules.json`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/platform_access/**`
- `computer_use_poc/tool_contracts/**`
- `computer_use_poc/tianshi_strategy_platform_contracts/**`
- `computer_use_poc/strategy_governance/**`
- `computer_use_poc/multi_evidence_orchestration_contracts/**`
- `bin/archives_profile_runner`
- `bin/tianshi_rcp_runner`
- `outputs/full_runtime/**`
- `outputs/release/**`
- `outputs/dist/**`

## First Migration Candidates

Candidates only; no migration is executed in this round.

| candidate | why first | condition before move |
|---|---|---|
| Additional `docs/architecture/*.md` docs | Already in `docs/`; low runtime coupling. | `git diff --check` only if docs-only. |
| `computer_use_poc/INDEX.md` family | Index docs are navigation-only. | Keep in place until accepted; do not move runtime files. |
| `computer_use_poc/bad_cases/INDEX.md` and future bad case index metadata | Regression-source only. | Check exact filename references in validation and smoke tests. |
| `computer_use_poc/run_logs/INDEX.md` | Historical index only. | If committed, use `git add -f`; do not stage historical logs. |
| Architecture-adjacent docs such as `dennis_agent_capability_architecture_v1.md` | Mostly explanatory docs. | First replace README/smoke references and run doc checks. |

## Third-step Applied Low-risk Archive

The following files were moved after active-reference scans found no AGENTS,
manifest, builder, Python/YAML, smoke-test, or skills runtime references. The
only remaining references were historical run logs, which are intentionally not
rewritten.

| old_path | new_path | decision | notes |
|---|---|---|---|
| `computer_use_poc/integration_notes.md` | `docs/archive/computer_use_poc_legacy/integration_notes.md` | safe_to_move_archive | Early Archives/computer-use POC note; historical-only. |
| `computer_use_poc/failure_modes.md` | `docs/archive/computer_use_poc_legacy/failure_modes.md` | safe_to_move_archive | Early Archives/computer-use POC failure-mode note; historical-only. |

## Current Boundary

- No real platform access was performed.
- No DataAgent/Hive call was performed.
- No file move or deletion was performed.
- No `outputs/full_runtime`, `outputs/release`, or `outputs/dist` modification.
- No package or release build.
- No runtime behavior change.
