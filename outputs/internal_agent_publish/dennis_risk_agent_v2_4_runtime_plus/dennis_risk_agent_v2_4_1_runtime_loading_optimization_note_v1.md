# Dennis Risk Agent v2.4.1 Runtime Loading Optimization Note v1

## 1. 为什么做优化

v2.4 Runtime Plus 已经通过 smoke test 和路由回归，能力边界是对的，但内部 Agent 实测显示：

- ATO 完全体问题的 token 成本仍偏高。
- 非 ATO 场景如果同时加载 system prompt、manifest、startup checklist 和多个 summary，会出现明显重复。
- 运行态的主要成本不在判断能力，而在加载层冗余。

因此本次优化目标不是改能力，而是**收紧默认加载，降低每轮问答 token 成本**。

## 2. 之前 token 高的原因

主要来自三类重复：

1. `system_prompt_runtime_plus_v1.md`、manifest、startup checklist 三层都在讲总定位、DataAgent 边界和加载原则。
2. 非 ATO summary 都带通用边界语句，如默认不调用 DataAgent、高风险动作需人工确认、SQL-only/partial/timeout 降级。
3. 集成说明、release note、route regression、smoke test 等文件不适合作为每轮常驻内容。

## 3. 新的常驻 / 初始化 / 按需加载策略

### 3.1 常驻最小加载

建议常驻：

- `system_prompt_runtime_plus_v1.md`
- `dennis_risk_agent_v2_4_runtime_plus_manifest_v1.md`
- DataAgent 边界摘要 / 规则摘要
- 必要输出格式要求

### 3.2 初始化 / 配置期使用，不建议每轮常驻

建议只在初始化 / 配置 / 上架阶段使用：

- `dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md`
- `internal_agent_publish_guide.md`
- `publish_checklist.md`
- `dennis_risk_agent_v2_4_runtime_plus_release_note_v1.md`
- `dennis_risk_agent_v2_4_runtime_plus_final_route_regression_v1.md`
- `dennis_risk_agent_v2_4_runtime_plus_integration_smoke_test_v1.md`

### 3.3 按需召回

- 8 个 runtime summary：非 ATO 场景默认只加载 1 个，明确跨域时最多 2 个。
- ATO 完全体文件：只有 ATO / 账号安全命中后加载。
- DataAgent parser / interpretation / thresholds：只有已经产生 DataAgent / Hive 结果后加载。

## 4. 不变的能力边界

本次优化不改变：

- ATO 仍进入完全体。
- 非 ATO 仍默认走 runtime summary。
- 默认不调用 DataAgent。
- 用户明确要求查数时才进入 DataAgent / Hive。
- DataAgent 仍只定位为 Hive / 公司数仓取数分析能力。
- SQL-only / partial / timeout / no_permission 仍必须降级。
- 高风险治理动作仍必须人工确认。

## 5. 对 ATO、非 ATO、DataAgent 的影响

### 5.1 ATO

- 不削弱 ATO 完全体。
- 仅减少 ATO 进入前的无效常驻材料。

### 5.2 非 ATO

- 保持轻量但不表面。
- 优先单一 summary。
- 明确跨域时最多加载 2 个 summary。

### 5.3 DataAgent

- 不扩大 DataAgent 权限。
- 不改变 Hive / 公司数仓定位。
- 不改变 evidence provider 边界。

## 6. 回归建议

建议回归顺序：

1. ATO 短问。
2. 单一非 ATO summary 问题。
3. 明确跨域的双 summary 问题。
4. 明确查数请求。

验收点：

- ATO 是否仍进入完全体。
- 非 ATO 是否只加载单一 summary 或最多 2 个 summary。
- startup checklist 是否不再每轮常驻。
- 是否没有误调 DataAgent。
- 回答质量是否保持。

## 7. 结论

v2.4.1 的优化目标是：

**不改能力边界，只收紧默认加载，让 Runtime Plus 更适合真实运行。**

