# Runtime Preview

`runtime_preview` 用于模拟上线后的 dennis-risk-agent 用户体感，不是开发设计目录。

## 1. 两种 preview

offline_preview：

- 不访问平台。
- 用 snapshot 内 contract 回放路由、source plan、输出结构和边界。
- 批量、举一返三、策略推荐、DataAgent/Hive 计划类问题默认走 offline_preview / plan_mode。

live_readonly_preview：

- 可访问已登记只读 source。
- 只能使用 `runtime_preview/live_source_allowlist.yaml` 中允许的 source。
- 不新增 source，不补规则，不 debug 认证。
- source 失败只进入 `source_quality`，输出 partial evidence card。

## 2. 生成 snapshot

在 repo 根目录运行：

```bash
python3 computer_use_poc/runtime_preview_snapshot_builder.py
```

生成目录：

```text
outputs/runtime_preview_snapshot/
```

snapshot 会复制 allowlist 内 runtime 文件，并在根目录生成强 `AGENTS.md`。

## 3. 从 snapshot 启动 Codex

```bash
cd outputs/runtime_preview_snapshot
codex
```

Codex 启动后会加载当前目录 `AGENTS.md`，因此 snapshot 根目录必须有强约束。

## 4. 裸问 case

在 snapshot 中，直接提风控 case：

```text
帮我看这个 user_id 是否疑似 ATO，时间是 2026-05-27 晚上，用户反馈非本人登录。
```

默认按 `live_readonly_preview` 执行，只能访问 allowlist source。

也可以加短前缀：

```text
live_readonly_preview：
帮我看这个 user_id 是否疑似 ATO，时间是 2026-05-27 晚上，用户反馈非本人登录。
```

批量、举一返三、策略推荐、方法论问题默认按 offline_preview / plan_mode。

## 5. 运行 validator

preview 输出写入：

```text
outputs/local_preview/preview_report.md
```

回到 repo 根目录运行：

```bash
python3 computer_use_poc/runtime_preview_validator.py --report outputs/local_preview/preview_report.md
```

## 6. preview 结果状态

- `PASS_EXPECTED_BEHAVIOR`
- `PREVIEW_FAILED_CONTRACT_VIOLATION`
- `PREVIEW_BLOCKED_INSUFFICIENT_CONTRACT`
- `PREVIEW_BLOCKED_CONTRACT_CONFLICT`

## 7. 关键边界

- preview 结果不是正式平台结论。
- `no_data`、`blocked`、`timeout`、`auth_failed`、`parse_error`、`tool_gap` 不等于无风险。
- live_readonly_preview 不读取完整 repo、不读取历史输出、不读取认证态、不修 runner。
