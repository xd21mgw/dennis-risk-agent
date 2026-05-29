# Full Runtime Mode v1

## Positioning

`full_runtime` 是本地完整 dennis-risk-agent 运行态，用于模拟线上真实用户体感。它不是 `runtime_preview_snapshot`，不是 `minimal_guard_preview`，也不是 contract checker。

用户日常想看“上线后 Dennis 怎么答”时，应使用：

```bash
python3 computer_use_poc/runtime_snapshot_builder.py --mode full_runtime
cd outputs/full_runtime
codex
```

## Core Behavior

- 裸问单 case 风控问题默认按 dennis-risk-agent runtime 执行。
- 纯数字 ID + case / ATO / 账号安全 / 策略命中上下文，默认推断为 `user_id_candidate`。
- 实体类型推断必须标 `entity_type_inferred=true`。
- 用户未给时间窗时，按 source playbook/default window 做 bounded_time_range inference。
- 时间窗推断必须标 `time_window_inferred=true`。
- 不因缺少实体类型或时间窗就机械 blocked。
- 策略命中问题属于 explicit source，不得静默跳过。

## User-facing Answer

full_runtime 输出顺序：

1. 先给用户可读结论 / 当前状态。
2. 再给 evidence card。
3. 再给 source_completion_matrix / source_quality。
4. 最后给 routing_metadata。

## Safety Boundary

- 不读取 source repo 的 `run_logs/**`。
- 不读取 source repo 的历史 `outputs/**`。
- 不读取 `.ks_sso/**`。
- 不读取 `TOOLS.md`。
- 不读取 old patch / local-file-in-chat。
- 不追逐未列入 `RUNTIME_MANIFEST.md` 的旧依赖。
- 不主动搜索 `skills/**` 或旧 runtime summaries，除非 full_runtime manifest 明确包含。
- 不 debug 认证 / SmartSSOSession / sso_session_runner。
- 不手拼 Cookie / Header。
- 不访问未登记 source。
- source 失败进入 source_quality。
- `no_data` / `blocked` / `timeout` / `auth_failed` / `parse_error` / `tool_gap` 不能当无风险反证。
- DataAgent / Hive 仍需逐次授权。

## Relationship To Release

- `full_runtime` 是本地完整运行态。
- `online_release_overlay` 是线上发布包。
- release 前应先确认 full_runtime 可生成且核心文件完整，再进入 release preflight / package scanner。
