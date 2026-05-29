# Collaboration Mode Runtime Preview Consolidation v1

## Summary

本轮把 Dennis Agent 协作模式从“云端边跑边修 / Codex 自由发挥 / 频繁打包”收口为：

1. 本地 Codex 母体开发。
2. runtime_preview snapshot 模拟上线效果。
3. 本地轻量验证。
4. 阶段性 release / overlay。
5. 云端只做隔离验收。
6. bad case 回流本地修复。

## Added / Updated Files

新增或更新：

- `computer_use_poc/collaboration_mode_contract_v1.md`
- `computer_use_poc/codex_workflow_modes_v1.md`
- `runtime_preview/README.md`
- `runtime_preview/AGENTS.md`
- `runtime_preview/runtime_file_allowlist.yaml`
- `runtime_preview/live_source_allowlist.yaml`
- `runtime_preview/expected_output_contract.yaml`
- `runtime_preview/online_effect_preview_cases.yaml`
- `runtime_preview/preview_runner_prompt.md`
- `computer_use_poc/runtime_preview_snapshot_builder.py`
- `computer_use_poc/runtime_preview_validator.py`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/run_logs/collaboration_mode_runtime_preview_consolidation_v1.md`

## Runtime Preview Snapshot Mechanism

新增 `runtime_preview_snapshot_builder.py`：

- 读取 `runtime_preview/runtime_file_allowlist.yaml`。
- 只复制 allowlist 文件与 preview 必需 contract。
- 保留相对路径结构。
- 在 `outputs/runtime_preview_snapshot/` 根目录生成强 `AGENTS.md`。
- 生成 `SNAPSHOT_MANIFEST.md`，记录 copied_files、missing_files、forbidden_sources、created_at、source_repo_root、snapshot_mode。
- allowlist 含 forbidden path 时 fail closed。
- 不复制 run_logs、历史 outputs、archives、`.ks_sso`、`TOOLS.md`。

新增 `runtime_preview_validator.py`：

- 校验 preview report required sections。
- 检查 forbidden behaviors。
- 输出 `PASS_EXPECTED_BEHAVIOR`、`PREVIEW_FAILED_CONTRACT_VIOLATION`、`PREVIEW_BLOCKED_INSUFFICIENT_CONTRACT` 或 `PREVIEW_BLOCKED_CONTRACT_CONFLICT`。

## Live Readonly Preview Boundary

`live_readonly_preview` 允许访问登记的只读平台 source：

- `login_log`
- `weapon_graphData`
- `weapon_riskData`
- `tianshi_strategy_hit`
- `rcp_event_list`
- `track_analysis_profile`
- `track_analysis_use_duration`
- `archives_center_profile`

统一禁止：

- 读取 `.ks_sso`。
- 手拼 cookie / header。
- debug runner / auth bridge。
- 访问未登记 source。
- arbitrary URL probing。
- 写操作。
- 将 source failure 当作低风险或无风险反证。

## This Run Boundaries

- 未访问真实平台。
- 未调用 DataAgent / Hive。
- 未修改 auth / gateway / safeBins / TOOLS。
- 未重新打包。
- 未提交 git。

## Future Usage

1. 运行：

```bash
python3 computer_use_poc/runtime_preview_snapshot_builder.py
```

2. 进入 snapshot：

```bash
cd outputs/runtime_preview_snapshot
```

3. 启动 Codex：

```bash
codex
```

4. 直接裸问 case，或使用前缀：

```text
live_readonly_preview：
<测试问题>
```

5. 输出 preview report 后回到 repo 根目录运行 validator：

```bash
python3 computer_use_poc/runtime_preview_validator.py --report outputs/local_preview/preview_report.md
```
