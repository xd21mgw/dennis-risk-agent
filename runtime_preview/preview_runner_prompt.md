# Runtime Preview Runner Prompt

使用本 prompt 执行一次本地 runtime preview。

## 固定流程

1. 在 repo 根目录运行 snapshot builder：

```bash
python3 computer_use_poc/runtime_preview_snapshot_builder.py
```

2. 从 snapshot 目录启动，或在回答中严格只读取该目录：

```bash
cd outputs/runtime_preview_snapshot
codex
```

3. Codex 启动后只读取 snapshot 内文件，优先读取：

- `runtime_preview/preview_runner_prompt.md`
- `runtime_preview/live_source_allowlist.yaml`
- `runtime_preview/expected_output_contract.yaml`

4. 裸问风控 case 默认 `live_readonly_preview`。

5. `offline_preview` 不访问平台。

6. `live_readonly_preview` 只访问 allowed live sources。

7. 不读取完整 repo。

8. 不读取 `run_logs`、历史 `outputs`、`.ks_sso`、`TOOLS.md`。

9. 不新增 source。

10. 不补规则。

11. 不 debug 认证。

12. 不打包。

13. 不提交 git。

14. 输出 preview report：

```text
outputs/local_preview/preview_report.md
```

15. 回到 repo 根目录运行 validator：

```bash
python3 computer_use_poc/runtime_preview_validator.py --report outputs/local_preview/preview_report.md
```

## 输出 contract

preview report 必须包含：

- `route_decision`
- `execution_mode`
- `source_plan`
- `source_completion_matrix`
- `evidence_card`
- `source_quality`
- `routing_metadata`
- `expected_user_answer`
- `uncertainty_due_to_missing_runtime_info`
- `contract_compliance_check`

如果 allowed files 不足，输出 `PREVIEW_BLOCKED_INSUFFICIENT_CONTRACT`，不许编。

如果 contract 冲突，输出 `PREVIEW_BLOCKED_CONTRACT_CONFLICT`。

如果发现 contract 违反，输出 `PREVIEW_FAILED_CONTRACT_VIOLATION`。
