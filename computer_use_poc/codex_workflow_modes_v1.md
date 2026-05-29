# Codex Workflow Modes v1

本文说明 Codex 在 Dennis Agent 协作模式下如何启动、提问和验收。当前推荐的本地上线体感模拟入口是 `full_runtime`，不是 `runtime_preview_snapshot` / `minimal_guard_preview`。

## 1. development_mode

启动方式：

```bash
cd /Users/pengcheng/dennis-risk-agent
codex
```

适用问题：

- 开发模式 / 修改文件。
- 补规则、补模板、补 regression、改 validator。
- 汇总 bad case 并沉淀本地 contract。

Codex 行为：

- 可以读取完整 repo。
- 必须先理解当前 runtime summaries、routing、capability、answer template、observation contract 和 smoke tests。
- 默认不访问真实平台。
- 默认不调用 DataAgent / Hive。
- 不修改云端配置、auth、gateway、safeBins、TOOLS。
- 输出必须说明改了什么、验证了什么、还有什么未覆盖。

验收方式：

- 日常小修跑 `git diff --check` 和 YAML parse。
- Python / runner / builder 改动跑 `python3 -m py_compile` 和 self-test。
- release 前再跑 scanner / preflight / full_runtime 本地验证。

## 2. full_runtime_mode

启动方式：

```bash
python3 computer_use_poc/runtime_snapshot_builder.py --mode full_runtime
cd outputs/full_runtime
codex
```

定位：

- `full_runtime` 是本地完整 dennis-risk-agent 运行态，用于模拟线上真实用户体感。
- 它不是 preview harness，也不是 contract checker。
- 用户日常想看“上线后 Dennis 怎么答”，应使用 `outputs/full_runtime`。

Codex 行为：

- Codex 启动后会加载 `outputs/full_runtime/AGENTS.md`。
- 裸问单 case 风控问题默认按 dennis-risk-agent runtime 执行。
- 纯数字 ID + case / ATO / 账号安全 / 策略命中上下文，默认推断为 `user_id_candidate`，并在 `routing_metadata` 标 `entity_type_inferred=true`。
- 用户未给时间窗时，按 source playbook/default window 做 bounded_time_range inference，并标 `time_window_inferred=true`。
- 不要因缺少实体类型或时间窗就机械 blocked。
- 策略命中问题属于 explicit source，不能静默跳过。
- 输出顺序应用户友好：先结论 / 判断，再 evidence card，再 source_completion_matrix/source_quality，最后 routing_metadata。

full_runtime 安全边界：

- 不读取 source repo 的 `run_logs/**`、历史 `outputs/**`、`.ks_sso/**`、`TOOLS.md`、old patch、local-file-in-chat。
- 不主动搜索 `skills/**` 或旧 runtime summaries，除非 full_runtime manifest 明确包含并已经复制进 `outputs/full_runtime`。
- 不 debug 认证 / SmartSSOSession / sso_session_runner。
- 不手拼 Cookie / Header。
- 不访问未登记 source。
- source 失败进入 `source_quality`。
- `no_data` / `blocked` / `timeout` / `auth_failed` / `parse_error` / `tool_gap` 不能当无风险反证。
- DataAgent / Hive 仍需逐次授权。

验收方式：

```bash
python3 -m py_compile computer_use_poc/runtime_snapshot_builder.py
python3 computer_use_poc/runtime_snapshot_builder.py --mode full_runtime
```

然后检查 `outputs/full_runtime/AGENTS.md`、`outputs/full_runtime/RUNTIME_MANIFEST.md` 和核心 runtime 文件是否存在，且不包含 excluded files。

## 3. release_mode

启动方式：

```bash
cd /Users/pengcheng/dennis-risk-agent
codex
```

适用问题：

- 阶段性稳定点打包。
- 生成 safe delta / runtime overlay。
- release readiness 验证。

Codex 行为：

- 先跑 asset scanner / release preflight / full_runtime 本地验证。
- 不按每个 patch 打包。
- 不把 repository template 误称为 live runtime 已生效。
- `online_release_overlay` 是线上发布包；`full_runtime` 是本地完整运行态。

验收方式：

- package scanner pass。
- release preflight pass。
- `outputs/full_runtime` 可生成且核心 contract 完整。
- release run log 完整记录。

## 4. cloud_acceptance_mode

适用问题：

- 云端 KIM / webchat 隔离验收。
- 验证 main agent 路由、spawn dennis-risk-agent、真实认证态、小样本只读 source 和日志回流。

Codex 行为：

- 云端只验收，不现场修规则。
- main agent 是路由器，不直接查平台。
- dennis-risk-agent 是执行者，按 source plan 隔离执行。
- 子 agent timeout 后 main agent 不接管平台查询，只记录 source_quality、partial evidence 或 retry plan。
- bad case 回流本地 `development_mode` 修复。

云端调度低频原则：

- 只有入口、权限、工具、channel mapping 变化才调整云端。
- 普通规则、模板、回归和 builder 修复先回本地母体。

## 5. Deprecated Preview Harness

`runtime_preview_snapshot` / `minimal_guard_preview` 已废弃为历史机制，不再作为推荐入口。

原因：

- 它过于偏 contract 校验和保守 blocked。
- 不能代表用户想看的线上 Dennis 真实体感。
- 后续安全边界迁移到 `full_runtime`，不再保留 preview harness 作为主流程。
