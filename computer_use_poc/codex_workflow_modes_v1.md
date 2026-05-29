# Codex Workflow Modes v1

本文说明 Codex 在 Dennis Agent 四种协作模式下如何启动、提问和验收。

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
- Python / runner / validator 改动跑 `python3 -m py_compile` 和 self-test。
- release 前再跑 scanner / preflight / preview validator。

## 2. runtime_preview_mode

启动方式：

```bash
python3 computer_use_poc/runtime_preview_snapshot_builder.py
cd outputs/runtime_preview_snapshot
codex
```

关键原则：

- Codex 启动后会加载当前目录 `AGENTS.md`。
- 因此 snapshot 根目录必须有强 `AGENTS.md`。
- preview 默认只读取当前 snapshot 内文件。
- preview 不知道就 blocked，不许编。
- preview 输出不是正式平台结论。

用户裸问风控 case：

- snapshot `AGENTS.md` 应默认按 `live_readonly_preview` 执行。
- 仅允许访问 `runtime_preview/live_source_allowlist.yaml` 中登记的只读 source。
- source 失败必须区分 `completed`、`no_data`、`auth_failed`、`blocked`、`timeout`、`parse_error`、`tool_gap`。

用户问批量、举一返三、策略推荐、方法论：

- 默认 `offline_preview` / `plan_mode`。
- 不访问平台。
- 不逐个扩量查数。
- DataAgent / Hive 只输出 query plan 和逐次授权边界。

用户明确说“开发模式 / 修改文件”：

- 不在 snapshot 里直接改母体。
- 回到 repo 根目录进入 `development_mode`。

验收方式：

```bash
python3 computer_use_poc/runtime_preview_validator.py --report outputs/local_preview/preview_report.md
```

preview 结果状态：

- `PASS_EXPECTED_BEHAVIOR`
- `PREVIEW_FAILED_CONTRACT_VIOLATION`
- `PREVIEW_BLOCKED_INSUFFICIENT_CONTRACT`
- `PREVIEW_BLOCKED_CONTRACT_CONFLICT`

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

- 先跑 asset scanner / release preflight / preview validator。
- 不按每个 patch 打包。
- 不把 repository template 误称为 live runtime 已生效。

验收方式：

- package scanner pass。
- release preflight pass。
- preview validator pass 或明确 blocked 原因。
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
- 普通规则、模板、回归和 validator 修复先回本地母体。

## 5. preview 输出边界

preview 必须区分：

- `completed`
- `no_data`
- `auth_failed`
- `blocked`
- `timeout`
- `parse_error`
- `tool_gap`

preview 禁止：

- 把 `no_data` 当无风险。
- 把策略命中当最终 ATO 结论。
- 把 stale data 当实时查询。
- 把 mock 当真实平台查询。
- 把 partial 包装成 final。
- source failed 后 debug auth、手拼 cookie/header 或猜 URL。
