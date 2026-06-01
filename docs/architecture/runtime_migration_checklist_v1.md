# Runtime Migration Checklist v1

Status: migration checklist only. Use this before any physical file move.

## 1. Pre-migration Checks

Run reference scans before moving a path:

```bash
rg -n "<old/path/or/filename>" AGENTS.md TOOLS.md README.md docs computer_use_poc skills bin
rg -n "<old/path/or/filename>" computer_use_poc/runtime_required_file_manifest_v1.yaml
```

Check manifest membership:

- `full_runtime_required.files`
- `full_runtime_required.optional_files`
- `full_runtime_required.globs`
- `full_runtime_required.optional_globs`
- `online_release_overlay_required.files`
- `excluded_files.patterns`

Check hardcoded Python paths:

- `computer_use_poc/runtime_snapshot_builder.py`
- `computer_use_poc/source_orchestration_check.py`
- `computer_use_poc/browser_backed_fixed_actions_text_dryrun.py`
- `computer_use_poc/runtime_preflight_check.py`
- `computer_use_poc/release_preflight_check.py`
- `computer_use_poc/source_runner_health_check.py`
- `computer_use_poc/package_asset_scanner.py`

Check runtime and validation references:

- `AGENTS.md`
- `TOOLS.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/*.md`

Check generated artifact boundaries:

- `outputs/full_runtime` is a generated test/runtime snapshot, not source.
- `outputs/release` is formal release output, not source.
- `outputs/dist` is local transfer/tarball output, not source.

Do not migrate if the old path appears in a command, manifest, validator,
preflight script, or runtime summary and the replacement has not been prepared.

## 2. Migration Execution Principles

- Migrate one theme per change.
- Prefer pure documentation moves before runtime-adjacent moves.
- Do not mix DataAgent, release tooling, browser-backed, and directory migration
  changes in one commit.
- Every move must update references in the same change.
- Keep old-path indexes or redirect notes until references are fully updated.
- Do not move files listed as `do_not_move_without_reference_update` in
  `runtime_path_reference_report_v1.md`.
- Do not move `outputs/**`.
- Do not move `skills/**/11_runtime_summaries/**` until runtime loading and
  manifest behavior are updated together.
- Do not rely on `outputs/full_runtime` as the development source.

## 3. Post-migration Validation

Always run:

```bash
git diff --check
```

If Python changed:

```bash
python3 -m py_compile <changed_python_files>
```

If YAML changed:

```bash
python3 - <<'PY'
import pathlib, yaml
for p in [pathlib.Path("<changed_yaml_file>")]:
    yaml.safe_load(p.read_text())
print("YAML_OK")
PY
```

If orchestration changed:

```bash
python3 computer_use_poc/source_orchestration_check.py --format json
```

If Dennis routing, browser-backed, or answer brain paths changed:

```bash
python3 computer_use_poc/browser_backed_fixed_actions_text_dryrun.py --format json
python3 computer_use_poc/browser_backed_fixed_actions_text_dryrun.py --demo --format json
```

If manifest or full-runtime packaging paths changed:

```bash
python3 computer_use_poc/runtime_snapshot_builder.py --mode full_runtime
```

Only run release/preflight checks in a dedicated release or packaging task:

```bash
python3 computer_use_poc/runtime_preflight_check.py
python3 computer_use_poc/release_preflight_check.py <release_dir>
```

Do not run platform queries, DataAgent, Hive, or live browser-backed service
calls as part of a directory migration check.

## 4. Rollback Strategy

Before commit:

```bash
git restore --staged <files>
git restore <files>
```

For new files:

```bash
git clean -f -- <new_files>
```

After commit:

```bash
git revert <commit>
```

Rollback principles:

- Keep migrations in single-theme commits.
- Revert the whole migration commit if path references break.
- Restore moved files to old paths first; fix references in a separate change.
- Keep old-path index notes until all references are updated and validated.

## 5. First Migration Candidates

Candidates only. Do not execute without a new task.

| priority | candidate | reason | required validation |
|---|---|---|---|
| 1 | Add more `docs/architecture/*.md` governance docs | Already outside runtime mainline. | `git diff --check` |
| 2 | Add missing `INDEX.md` files, such as `batch_risk_clustering/INDEX.md` | Navigation-only, low behavior risk. | `git diff --check`; no manifest edits |
| 3 | Add `question_collection/INDEX.md` | Clarifies case learning vs runtime logging. | `git diff --check`; check manifest exclusions |
| 4 | Add `tool_contracts/INDEX.md` and `strategy_governance/INDEX.md` | Clarifies platform/capability contracts before moving. | `git diff --check`; reference scan |
| 5 | Move one pure architecture doc only after reference scan | Smallest physical migration test. | reference scan, `git diff --check`, smoke keyword check if cited |

## 6. Explicit Non-candidates for Early Migration

Do not move in the first physical migration wave:

- `computer_use_poc/source_orchestration_plan_v1.yaml`
- `computer_use_poc/source_orchestration_check.py`
- `computer_use_poc/runtime_required_file_manifest_v1.yaml`
- `computer_use_poc/runtime_snapshot_builder.py`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/browser_backed_fixed_actions_text_dryrun.py`
- `computer_use_poc/browser_backed_fixed_actions_text_regression_cases_v1.yaml`
- `computer_use_poc/browser_backed_service_client.py`
- `computer_use_poc/runtime_preflight_check.py`
- `computer_use_poc/release_preflight_check.py`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/**`
- `outputs/full_runtime/**`
- `outputs/release/**`
- `outputs/dist/**`

## 7. Boundary

- Directory migration does not authorize platform access.
- Directory migration does not authorize DataAgent/Hive execution.
- Directory migration does not modify release artifacts.
- Directory migration does not change runtime behavior unless explicitly scoped
  and validated.
