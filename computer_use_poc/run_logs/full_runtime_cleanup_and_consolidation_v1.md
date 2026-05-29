# Full Runtime Cleanup and Consolidation v1

## Why Clean Up Preview Harness

`runtime_preview_snapshot` / `minimal_guard_preview` 过于偏 contract 校验和保守 blocked，不能满足“上线后真实 dennis-agent 用户体感”的主需求。

本轮将 preview harness 删除或降级为历史机制，不再作为推荐入口。后续日常看上线效果使用 `outputs/full_runtime`。

## Why full_runtime Is The Main Need

full_runtime 更接近真实 Dennis 用户体验：

- 允许基于上下文做合理实体类型推断。
- 允许基于 source playbook/default window 做有界时间窗推断。
- 不因缺少实体类型或时间窗机械 blocked。
- explicit source 不被静默跳过。
- source failure 进入 source_quality，而不是把整轮回答变成 contract blocked。

## 544963630 Case Problem

问题：

```text
544963630 这个 case 有没有策略命中能辅助判断？
```

旧 preview harness 容易因为实体类型 / 时间窗不完整而 blocked，或偏向 contract checker 输出。

full_runtime 规则：

- 默认 `entity_type=user_id_candidate`。
- 标 `entity_type_inferred=true`。
- 未给时间窗时标 `time_window_inferred=true`。
- `strategy_hit` 是 explicit target source。
- 尝试 `tianshi_strategy_hit` / `rcp_event_list` 只读 source。
- source 失败进入 source_quality。
- 结论不能说“没有命中”，只能说本轮 source 状态如何。

## Migrated Safety Boundaries

迁移到 full_runtime 的安全边界：

- 不读取 `run_logs/**`。
- 不读取历史 `outputs/**`。
- 不读取 `.ks_sso/**`。
- 不读取 `TOOLS.md`。
- 不读取 old patch / local-file-in-chat。
- 不追逐未列入 manifest 的旧依赖。
- 不主动搜索 `skills/**` 或旧 runtime summaries，除非 full_runtime manifest 明确包含。
- 不 debug 认证 / SmartSSOSession / sso_session_runner。
- 不手拼 Cookie / Header。
- 不访问未登记 source。
- source 失败进入 source_quality。
- `no_data` / `blocked` / `timeout` / `auth_failed` / `parse_error` / `tool_gap` 不能当无风险反证。
- DataAgent / Hive 仍需逐次授权。

## Added Full Runtime Files

- `computer_use_poc/runtime_required_file_manifest_v1.yaml`
- `computer_use_poc/runtime_snapshot_builder.py`
- `computer_use_poc/full_runtime_inference_contract_v1.md`
- `computer_use_poc/run_logs/full_runtime_mode_v1.md`
- `computer_use_poc/run_logs/full_runtime_cleanup_and_consolidation_v1.md`

## Removed / Deprecated Preview Harness

- Removed local `runtime_preview/` files from the recommended runtime path.
- Removed `computer_use_poc/runtime_preview_snapshot_builder.py`.
- Removed `computer_use_poc/runtime_preview_validator.py`.
- Removed generated local `outputs/runtime_preview_snapshot/` and `outputs/local_preview/` during cleanup.

## Boundaries This Run

- 未访问真实平台。
- 未调用 DataAgent / Hive。
- 未修改 auth / gateway / safeBins / TOOLS。
- 未打包。
- 未提交 git。
- 未处理 `outputs/release`。
- 未读取 `.ks_sso`。
