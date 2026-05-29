# Collaboration Mode Contract v1

本契约用于把 Dennis Agent 后续协作方式收口为本地母体开发、full_runtime 本地完整运行态、阶段性 release/overlay、云端隔离验收和 bad case 回流修复。

核心定位：

- 本地 Codex 是研发母体，负责开发、规则修复、模板补齐、regression 与 builder / validator 沉淀。
- `full_runtime` 是本地完整 dennis-risk-agent 运行态，用于模拟线上真实用户体感。
- `online_release_overlay` 是线上发布包，不等同于本地 full_runtime。
- 云端是验收环境，只验证入口、权限、工具、认证态、spawn 和小样本真实链路。
- main agent 是路由器，只做意图识别、任务拆分、spawn 和日志回流。
- dennis-risk-agent 是执行者，只在明确 execution slice 内按 source plan 做只读证据采集。
- `runtime_preview_snapshot` / `minimal_guard_preview` 已废弃为历史机制，不再作为推荐入口。

## 1. development_mode

职责：

- 在本地 Codex 母体内开发、修规则、补模板、补 regression、改 builder / validator。
- 读取完整 repo，理解 runtime summaries、routing、capability、answer contract 和 smoke tests。
- 将 bad case 回流为本地可验证的文档、规则、测试或脚本。

允许动作：

- 读取完整 repo 内文件。
- 新增或更新本地文档、脚本、YAML contract、smoke tests、run log。
- 运行本地静态校验、Python 编译、YAML parse、full_runtime 生成和 git diff check。
- 在任务明确要求 `platform contract` 或 live readonly contract 设计时，按已登记只读 source contract 做计划。

禁止动作：

- 默认访问真实平台。
- 默认调用 DataAgent / Hive。
- 修改云端配置、auth、gateway、safeBins、TOOLS。
- 频繁为小 patch 打包 release。
- 使用平台失败作为低风险或无风险反证。

输出：

- 本地文件改动。
- 本地验证结果。
- 未覆盖风险与后续建议。
- 必要时追加 run log。

验证方式：

- 日常小修：`git diff --check`、YAML parse。
- Python / runner / builder：`python3 -m py_compile` 和 self-test。
- release 前：package scanner、release preflight、full_runtime 本地验证。

## 2. full_runtime_mode

职责：

- 用本地完整 runtime 文件集合模拟上线后 dennis-risk-agent 的真实用户体感。
- 验证裸问 case 时，Dennis 是否能合理推断实体类型 / 时间窗、执行 explicit source、输出 evidence card 和 source_quality。
- 承接 preview harness 中必要的安全边界，但不再做 minimal contract checker。

启动方式：

```bash
python3 computer_use_poc/runtime_snapshot_builder.py --mode full_runtime
cd outputs/full_runtime
codex
```

允许动作：

- 读取 `outputs/full_runtime` 内由 `runtime_required_file_manifest_v1.yaml` 复制的 runtime 文件。
- 按 dennis-risk-agent runtime 进行路由、source plan、只读 source execution 或 partial evidence fallback。
- 对纯数字 ID 在 case / ATO / 账号安全 / 策略命中上下文中推断 `user_id_candidate`。
- 对缺失时间窗的问题按 source playbook default window 做 bounded_time_range inference。

禁止动作：

- 读取 source repo 的 `run_logs/**`、历史 `outputs/**`、`.ks_sso/**`、`TOOLS.md`、old patch、local-file-in-chat。
- 主动搜索 `skills/**` 或旧 runtime summaries，除非 manifest 明确包含并复制进 full_runtime。
- debug 认证 / SmartSSOSession / sso_session_runner。
- 手拼 Cookie / Header。
- 访问未登记 source。
- 把 no_data / blocked / timeout / auth_failed / parse_error / tool_gap 当无风险反证。
- 未经逐次授权调用 DataAgent / Hive。

输出：

- 先给用户可读结论 / 判断。
- 再给 evidence card。
- 再给 source_completion_matrix / source_quality。
- 最后给 routing_metadata。

## 3. release_mode

职责：

- 只在阶段性稳定点打包 safe delta / runtime overlay。
- 在 release 前确认 full_runtime、package 边界和 release preflight 通过。
- 将低频发布和日常开发拆开，避免每个 patch 都打包。

允许动作：

- 跑 asset scanner。
- 跑 release preflight。
- 跑 full_runtime 生成与本地检查。
- 生成阶段性 safe delta 或 runtime overlay。

禁止动作：

- 小 patch 立即打包。
- 未跑本地门禁就发布。
- 把 template / overlay 文档误称为 live runtime 已生效。
- 借 release 任务修改 auth / gateway / safeBins / TOOLS，除非任务明确要求并完成对应审批。

## 4. cloud_acceptance_mode

职责：

- 云端只做隔离验收，不做现场开发。
- 验证 KIM / webchat 入口、main agent 路由、spawn dennis-risk-agent、真实认证态、小样本 source execution 和日志回流。
- 将 bad case、source gap、auth gap 和 output gap 回流到本地修复。

允许动作：

- 小样本验收。
- 验证入口、权限、工具、channel mapping。
- 验证 main agent 是否只路由，不直接查平台。
- 验证 dennis-risk-agent 是否隔离执行。

禁止动作：

- 云端现场修规则。
- 云端临场绕认证。
- dennis timeout 后让 main agent 接管平台查询。
- main agent 使用 curl、cookie、browser 或 same-origin fetch 补查平台。
- 将云端 failed source 当作低风险或无风险反证。

## 5. 三类核心验证

### 单 case ATO

- 验证查数路径、source checkpoint、partial evidence card 和 `source_quality`。
- 明确或推断 `user_id` / 时间窗口 / 异常动作。
- 登录日志、Weapon、档案中心、策略命中等 source plan。
- completed / no_data / auth_failed / blocked / timeout / parse_error / tool_gap 分层。
- `no_data`、`timeout`、`blocked` 不作为低风险反证。

### 策略命中 / 原因归因

- 用户显式要求的 source 不被跳过。
- 策略命中不能直接作为最终 ATO 或作弊定性。
- 缺 `eventId` / `eventType` / `queryTime` / `policyCode` 时输出缺口或 query plan。
- explicit source blocked / timeout 时必须进入 source_quality。

### 批量 / 举一返三

- 验证 plan_mode、batch boundary 和 DataAgent/Hive 逐次授权。
- 10+ 实体不得默认逐个 online execution。
- ATO 举一返三只输出扩展锚点、query plan、scope control 和人工复核边界。
- DataAgent / Hive 只作为计划，逐次授权后才可能执行。

## 6. 安全检查分层

日常小修：

- `git diff --check`
- YAML parse

Python / runner / builder：

- `python3 -m py_compile`
- 轻量 self-test

release：

- package scanner
- release preflight
- full_runtime 本地验证

## 7. 打包低频原则

- 小 patch 不打包。
- 多个 local fix 在阶段性稳定点合并验证。
- 阶段性稳定点再打 safe delta / runtime overlay。
- 打包前必须确认 full_runtime、asset scanner 和 release preflight。

## 8. 云端调度低频原则

只有以下变化才调整云端调度：

- 入口变化。
- 权限变化。
- 工具注册变化。
- channel mapping 变化。
- dennis-risk-agent 隔离执行边界变化。

普通规则、模板、回归和 builder 修复先在本地母体完成，再通过阶段性 release/overlay 进入云端验收。
