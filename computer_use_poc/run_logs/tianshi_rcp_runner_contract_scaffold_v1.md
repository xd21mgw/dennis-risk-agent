# Tianshi RCP Runner Contract Scaffold v1

## Summary

本轮基于 `computer_use_poc/source_executability_inventory_v1.yaml`，推进 `tianshi_strategy_hit` / `rcp_event_list` 从 `playbook_ready_not_runner_ready` 到最小可执行 runner scaffold。

目标是解决 `544963630 这个 case 有没有策略命中能辅助判断？` 在 full_runtime 中只能返回 runner-missing `tool_gap` 的问题。

## Added / Updated

- 新增 `bin/tianshi_rcp_runner`。
- 新增 `computer_use_poc/tianshi_rcp_runner.py`。
- 新增 `computer_use_poc/tianshi_rcp_runner_contract_v1.md`。
- 更新 `computer_use_poc/source_executability_inventory_v1.yaml`：
  - `tianshi_strategy_hit` -> `dry_run_contract_ready`。
  - `rcp_event_list` -> `dry_run_contract_ready`。
  - 从当前 P0/P1 runner-missing tool_gap 列表移除天师/RCP。
- 更新 `computer_use_poc/runtime_required_file_manifest_v1.yaml`，将 runner 与 contract 纳入 full_runtime。
- 更新 `computer_use_poc/runner_registry_v1.yaml` 和 `computer_use_poc/source_readiness_matrix_v1.yaml`，避免 registry/readiness 仍声称缺 runner。
- 更新 `computer_use_poc/smoke_tests.md`，增加 dry-run contract、runner-present-not-completed、544963630 no runner-missing tool_gap 检查。

## Runner Boundary

- 当前 runner 支持 `--mode contract-check` 和 `--mode dry-run`。
- `--mode live` 已声明但默认关闭，返回 `dry_run_only` / `live_mode_not_enabled`，不访问平台。
- runner readonly。
- 不接受 arbitrary URL。
- 不读取 `.ks_sso`。
- 不手拼 cookie/header。
- 不 debug SSO / SmartSSOSession。
- 不输出 cookie/token/session/header。
- 不调用 DataAgent / Hive。

## Current Status

- `tianshi_strategy_hit`: `dry_run_contract_ready`，非 live executable。
- `rcp_event_list`: `dry_run_contract_ready`，非 live executable。
- 544963630 类策略命中问题应路由到 runner contract，输出 `dry_run_only` / `source_quality`；不得再因为缺 `bin/tianshi_rcp_runner` 输出 `tool_gap`。
- dry-run 不能说明有无策略命中，不能当 `no_data`、低风险或无风险。

## Boundaries This Run

- 未访问真实平台。
- 未调用 DataAgent / Hive。
- 未手拼 cookie/header。
- 未 debug SSO / runner。
- 未修改 auth / gateway / safeBins / TOOLS。
- 未打包。
- 未提交 git。

## Validation

- `PYTHONPYCACHEPREFIX=/private/tmp/codex_pycache python3 -m py_compile computer_use_poc/tianshi_rcp_runner.py`: passed.
- `bin/tianshi_rcp_runner --mode contract-check`: passed, `source_status=dry_run_only`, `real_platform_request_executed=false`.
- `bin/tianshi_rcp_runner --mode dry-run --action strategy_hit_overview_lookup --entity-type user_id_candidate --entity-id 544963630 ...`: passed, `source_name=tianshi_strategy_hit`, `source_status=dry_run_only`, `tool_gap=false`.
- `bin/tianshi_rcp_runner --mode dry-run --action rcp_event_list_readonly --entity-type user_id_candidate --entity-id 544963630 ...`: passed, `source_name=rcp_event_list`, `source_status=dry_run_only`, `tool_gap=false`.
- YAML parse passed for:
  - `computer_use_poc/source_executability_inventory_v1.yaml`
  - `computer_use_poc/runtime_required_file_manifest_v1.yaml`
  - `computer_use_poc/runner_registry_v1.yaml`
  - `computer_use_poc/source_readiness_matrix_v1.yaml`
- `python3 computer_use_poc/runtime_snapshot_builder.py --mode full_runtime`: passed, `status=created`, `copied_files_count=91`, `missing_required=[]`.
- `outputs/full_runtime/RUNTIME_MANIFEST.md` contains:
  - `bin/tianshi_rcp_runner`
  - `computer_use_poc/tianshi_rcp_runner.py`
  - `computer_use_poc/tianshi_rcp_runner_contract_v1.md`
- forbidden path check passed for `outputs/full_runtime`.
- `git diff --check`: passed.
