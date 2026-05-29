# Collaboration Mode Contract v1

本契约用于把 Dennis Agent 后续协作方式收口为本地母体开发、runtime preview、本地轻量验证、阶段性 release/overlay、云端隔离验收和 bad case 回流修复。

核心定位：

- 本地 Codex 是研发母体，负责开发、规则修复、模板补齐、regression 与 validator 沉淀。
- runtime_preview snapshot 是上线体感模拟层，负责隔离回放预期行为，不做开发设计。
- 云端是验收环境，只验证入口、权限、工具、认证态、spawn 和小样本真实链路。
- main agent 是路由器，只做意图识别、任务拆分、spawn 和日志回流。
- dennis-risk-agent 是执行者，只在明确 execution slice 内按 source plan 做只读证据采集。

## 1. development_mode

职责：

- 在本地 Codex 母体内开发、修规则、补模板、补 regression、改 validator。
- 读取完整 repo，理解 runtime summaries、routing、capability、answer contract 和 smoke tests。
- 将 bad case 回流为本地可验证的文档、规则、测试或脚本。

允许动作：

- 读取完整 repo 内文件。
- 新增或更新本地文档、脚本、YAML contract、smoke tests、run log。
- 运行本地静态校验、Python 编译、YAML parse、validator mock 和 git diff check。
- 在任务明确要求 `platform contract` 或 `live readonly preview` 时，按已登记只读 source contract 做计划或受控预览。

禁止动作：

- 默认访问真实平台。
- 默认调用 DataAgent / Hive。
- 修改云端配置、auth、gateway、safeBins、TOOLS。
- 频繁为小 patch 打包 release。
- 使用平台失败作为低风险或无风险反证。

输入：

- 用户的本地开发任务。
- bad case、回归需求、contract gap、smoke test gap。
- repo 内当前 runtime 文件。

输出：

- 本地文件改动。
- 本地验证结果。
- 未覆盖风险与后续建议。
- 必要时追加 run log。

验证方式：

- 日常小修：`git diff --check`、YAML parse。
- Python / runner / validator：`python3 -m py_compile` 和 self-test。
- release 前：package scanner、release preflight、preview validator。

## 2. runtime_preview_mode

职责：

- 用隔离 snapshot 模拟上线后 dennis-risk-agent 的预期用户体感。
- 验证用户裸问 case 时，路由、source plan、source completion matrix、evidence card、source_quality 和最终回答是否符合 contract。
- 区分 offline_preview 与 live_readonly_preview。

允许动作：

- 默认只读取 `outputs/runtime_preview_snapshot/` 内文件。
- offline_preview：不访问平台，只做路由、计划、证据边界和输出 contract 回放。
- live_readonly_preview：只能访问 `runtime_preview/live_source_allowlist.yaml` 中登记的只读 source。
- source 失败时记录 `source_quality`，输出 partial evidence card。

禁止动作：

- 读取完整 repo、`run_logs`、历史 `outputs`、`archives`、old patch、`.ks_sso`、`TOOLS.md`。
- 补规则、新增 source、debug 认证、临场修 runner。
- 手拼 cookie / header，读取 SSO state，猜 URL，探测未登记 source。
- 把 preview 结果包装成正式平台结论。

输入：

- snapshot 内 runtime contract。
- 用户裸问 case 或带前缀的 preview 测试问题。
- live_readonly_preview 的 allowed live source 列表。

输出：

- `route_decision`
- `execution_mode`
- `source_plan`
- `source_completion_matrix`
- `evidence_card`
- `source_quality`
- `routing_metadata`
- `expected_user_answer`
- `contract_compliance_check`

验证方式：

- 运行 `computer_use_poc/runtime_preview_validator.py --report outputs/local_preview/preview_report.md`。
- 输出状态只能为：
  - `PASS_EXPECTED_BEHAVIOR`
  - `PREVIEW_FAILED_CONTRACT_VIOLATION`
  - `PREVIEW_BLOCKED_INSUFFICIENT_CONTRACT`
  - `PREVIEW_BLOCKED_CONTRACT_CONFLICT`

## 3. release_mode

职责：

- 只在阶段性稳定点打包 safe delta / runtime overlay。
- 在 release 前确认 preview 行为、package 边界和 release preflight 通过。
- 将低频发布和日常开发拆开，避免每个 patch 都打包。

允许动作：

- 跑 asset scanner。
- 跑 release preflight。
- 跑 preview validator。
- 生成阶段性 safe delta 或 runtime overlay。

禁止动作：

- 小 patch 立即打包。
- 未跑本地门禁就发布。
- 把 template / overlay 文档误称为 live runtime 已生效。
- 借 release 任务修改 auth / gateway / safeBins / TOOLS，除非任务明确要求并完成对应审批。

输入：

- 已稳定的一组本地 contract、script、template 和 regression。
- release readiness checklist。
- preview validator 结果。

输出：

- release readiness 结果。
- safe delta / runtime overlay。
- release run log。

验证方式：

- `python3 computer_use_poc/package_asset_scanner.py`
- `python3 computer_use_poc/runtime_preflight_check.py`
- release preflight 与 preview validator。

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

输入：

- release / overlay 后的云端环境。
- KIM / webchat 验收样本。
- 已登记 source 和 live auth state。

输出：

- 验收结果。
- source_quality。
- partial evidence card 或 bad case 回流项。
- 不在云端直接修复的本地 backlog。

验证方式：

- KIM / webchat 入口路由验收。
- dennis-risk-agent spawn 验收。
- 小样本只读 source 验收。
- 观测日志回流验收。

## 5. 三类核心验证

### 单 case ATO

目标：

- 验证查数路径、source checkpoint、partial evidence card 和 `source_quality`。

必须覆盖：

- 明确 `user_id` / 时间窗口 / 异常动作。
- 登录日志、Weapon、档案中心、策略命中等 source plan。
- completed / no_data / auth_failed / blocked / timeout / parse_error / tool_gap 的分层。
- `no_data`、`timeout`、`blocked` 不作为低风险反证。

### 策略命中 / 原因归因

目标：

- 验证用户显式要求的 source 不被跳过。
- 验证策略命中不能直接作为最终 ATO 或作弊定性。

必须覆盖：

- `strategy_hit_read`、`tianshi_eventlist_read`、`tianshi_strategy_governance_readonly` 的路由边界。
- 缺 `eventId` / `eventType` / `queryTime` / `policyCode` 时输出缺口或 query plan。
- explicit source 被 blocked / timeout 时必须进入 source_quality。

### 批量 / 举一返三

目标：

- 验证 plan_mode、batch boundary 和 DataAgent/Hive 逐次授权。

必须覆盖：

- 10+ 实体不得默认逐个 online execution。
- ATO 举一返三只输出扩展锚点、query plan、scope control 和人工复核边界。
- DataAgent / Hive 只作为计划，逐次授权后才可能执行。

## 6. 安全检查分层

日常小修：

- `git diff --check`
- YAML parse

Python / runner / validator：

- `python3 -m py_compile`
- 轻量 self-test

release：

- package scanner
- release preflight
- preview validator

## 7. 打包低频原则

- 小 patch 不打包。
- 多个 local fix 在阶段性稳定点合并验证。
- 阶段性稳定点再打 safe delta / runtime overlay。
- 打包前必须确认 preview validator、asset scanner 和 release preflight。

## 8. 云端调度低频原则

只有以下变化才调整云端调度：

- 入口变化。
- 权限变化。
- 工具注册变化。
- channel mapping 变化。
- dennis-risk-agent 隔离执行边界变化。

普通规则、模板、回归和 validator 修复先在本地母体完成，再通过阶段性 release/overlay 进入云端验收。
