# Architecture Docs Index

Status: navigation only. This directory documents repository governance and
future migration plans. It does not define runtime behavior by itself.

## Current Documents

| document | purpose | status |
|---|---|---|
| `runtime_directory_consolidation_plan_v1.md` | Current directory inventory, dependency risk, target directory model, and minimal migration plan. | active architecture plan |
| `runtime_path_reference_report_v1.md` | Hardcoded path and runtime dependency risk report. | active migration pre-check |
| `runtime_migration_checklist_v1.md` | Checklist for future physical path migrations. | active migration gate |

## Directory Governance Principles

- Index first, migrate later.
- Identify runtime dependencies before moving files.
- Keep hardcoded runtime paths in place until manifest, builder, validators,
  dry-runs, and preflight scripts have been updated and verified.
- `outputs/full_runtime` is a generated test/runtime snapshot, not the
  development source of truth.
- `outputs/release` is formal release output; `outputs/dist` is temporary local
  transfer/package output.
- Release artifacts, dist packages, run logs, overlays, and historical patches
  must not pollute the runtime mainline.

## Dennis Agent Construction Layers Mapping

This mapping is a cognitive aid only. It is not a physical directory migration
plan for this round.

| construction layer | current repository areas | interpretation |
|---|---|---|
| 专家能力层 | `skills/**/11_runtime_summaries`, `computer_use_poc/capability_registry.md`, `computer_use_poc/scene_to_capability_routing.md`, `computer_use_poc/answer_experience_templates.md` | Expert judgment, capability naming, scene routing, and answer contracts. |
| 质量进化层 | `computer_use_poc/runtime_validation_cases_v1.yaml`, `computer_use_poc/smoke_tests.md`, `computer_use_poc/browser_backed_fixed_actions_text_*`, `computer_use_poc/bad_cases`, `computer_use_poc/run_logs` | Regression, smoke checks, bad cases, and historical learning assets. |
| 应用价值层 | `computer_use_poc/batch_risk_clustering`, `computer_use_poc/strategy_governance`, business evidence templates | Batch analysis, cluster lenses, strategy governance, and business-facing outputs. |
| 安全防线 | `AGENTS.md`, `TOOLS.md`, `computer_use_poc/security_preflight_*`, `computer_use_poc/package_asset_scanner*`, field/output policies | Runtime guardrails, security checks, asset scanning, and output boundaries. |
| 工程支撑层 | `computer_use_poc/runtime_required_file_manifest_v1.yaml`, `computer_use_poc/runtime_snapshot_builder.py`, `outputs/**`, release/preflight scripts, browser-backed and DataAgent contracts | Packaging, snapshots, local validation, source adapters, and operational support. |

## Do Not Move Without Reference Check

Before any migration, run reference checks across at least:

- `AGENTS.md`
- `TOOLS.md`
- `computer_use_poc/runtime_required_file_manifest_v1.yaml`
- `computer_use_poc/runtime_snapshot_builder.py`
- `computer_use_poc/source_orchestration_check.py`
- `computer_use_poc/browser_backed_fixed_actions_text_dryrun.py`
- `computer_use_poc/runtime_preflight_check.py`
- `computer_use_poc/release_preflight_check.py`
- `skills/**/11_runtime_summaries/**`

Use `runtime_directory_consolidation_plan_v1.md` as the controlling plan before
performing any file move.
