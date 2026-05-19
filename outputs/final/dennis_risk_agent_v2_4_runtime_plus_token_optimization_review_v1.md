# Dennis Risk Agent v2.4 Runtime Plus Token Optimization Review v1

## 0. 结论

本轮评估结论：**功能通过，存在可优化的加载重叠，但不需要改动能力边界。**

当前 smoke test 全部通过，说明 Runtime Plus 已满足可集成要求。  
token 成本偏高的主要原因不是能力缺失，而是 **启动加载层和运行态 summary 之间存在较多重复表达**，尤其集中在：

1. `system_prompt_runtime_plus_v1.md`
2. `dennis_risk_agent_v2_4_runtime_plus_manifest_v1.md`
3. `dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md`
4. 各 runtime summary 的共用边界段落

当前不建议大改架构。最小优化建议是：

- 常驻文件收紧到最小。
- 启动 checklist 改成初始化期加载，而不是每次对话都进入运行态。
- runtime summary 保留，但尽量做到“一个场景一份 summary”，不要交叉加载无关 summary。

## 1. 评估范围

本次重点检查以下文件：

- `system_prompt_runtime_plus_v1.md`
- `dennis_risk_agent_v2_4_runtime_plus_manifest_v1.md`
- `dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md`
- 8 个 runtime summary

结论基线：

- ATO 作为深度完全体样板，不能削弱。
- 非 ATO 仍应默认走 runtime summary。
- 默认不调用 DataAgent。
- 只有用户明确要求查数时才进入 DataAgent / Hive。

## 2. 重复内容分析

### 2.1 system_prompt 与 manifest 的重复

`system_prompt_runtime_plus_v1.md` 和 `manifest` 都在重复说明：

- Dennis 是通用业务风控专家。
- ATO 是深度完全体样板。
- 非 ATO 默认走 runtime summary。
- 默认不调用 DataAgent。
- DataAgent 只定位为 Hive / 公司数仓取数分析能力。

这部分重复是**合理但可压缩**的。

#### 影响

- 对功能无损。
- 对 token 有轻微重复消耗。

#### 建议

- system prompt 保留简洁定位。
- manifest 保留文件清单和加载规则。
- 避免在其他运行态文件里再重复写“默认不调用 DataAgent / 高风险动作必须人工确认”这类总控语句。

### 2.2 manifest 与 startup checklist 的重复

`manifest` 和 `startup_loading_order_checklist` 都在讲：

- 默认加载什么。
- ATO 怎么加载。
- 非 ATO 怎么加载。
- 不建议默认注入什么。
- DataAgent 边界。

其中 `startup_loading_order_checklist` 的重复度最高，而且篇幅也最大。

#### 影响

- 它是 token 成本的主要来源之一。
- 如果每次运行都完整加载，性价比不高。

#### 建议

- 把 `startup_loading_order_checklist` 从“每次运行态默认加载”降级为“初始化 / 集成期加载”。
- 在实际对话运行时只保留 manifest + 当前场景 summary / ATO 完全体。

### 2.3 runtime summaries 的重复

8 个 runtime summary 的共性结构基本一致：

- 场景定位。
- 核心判断问题。
- 场景本质。
- 典型攻击路径。
- 强 / 中 / 弱证据。
- 反证边界。
- 低成本取证方向。
- 治理方法。
- 短问回复。
- DataAgent 边界。
- 默认输出结构 / 升级条件 / 当前边界。
- 禁止行为。

这类重复是**结构性重复**，但不是无效重复，因为每个 summary 需要独立支撑短问回答。

#### 影响

- 单份 summary 成本可控。
- 但一旦多场景同时加载，就会出现结构性重复叠加。

#### 建议

- 保持“按场景单独加载”。
- 不要在一个问题里同时加载多个无关 summary。
- 对必须比较的场景（如群控 vs 真人众包）只加载必要的 2 份 summary。

## 3. 哪些文件适合常驻

### 3.1 建议常驻

以下文件适合作为默认常驻的最小集合：

1. `system_prompt_runtime_plus_v1.md`
2. `dennis_risk_agent_v2_4_runtime_plus_manifest_v1.md`
3. `scenario_intent_router_contract_v1.md` 摘要
4. `scenario_response_contract_v1.md` 摘要
5. `dataagent_provider_boundary_overlay_v1.md` 摘要
6. `dataagent_timeout_policy_review_v1.md` 摘要

#### 原因

- 这些文件体量小。
- 提供全局定位、路由、边界、降级和默认行为。
- 对所有场景都需要。

### 3.2 建议仅集成期 / 初始化期加载

以下文件建议只在初始化、发布、验收或集成阶段加载，不作为每次运行的默认常驻：

- `dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md`
- `dennis_risk_agent_v2_4_runtime_plus_final_route_regression_v1.md`
- `dennis_risk_agent_v2_4_runtime_plus_integration_smoke_test_v1.md`
- `dennis_risk_agent_v2_4_runtime_plus_release_note_v1.md`

#### 原因

- 这些文件更多是集成说明、回归报告和发布说明。
- 它们对回答质量帮助有限，但对 token 有明显成本。

### 3.3 建议按需召回

以下文件建议按需召回：

- 8 个 runtime summary
- ATO 完全体相关解释文件
- DataAgent parser / schema / join / threshold / interpretation 文件
- review / eval / walkthrough / history 全文

#### 原因

- 它们是能力载体，但不是所有问题都需要。
- 只在对应场景或需要深答时读取。

## 4. 哪些文件应改成更强的按需召回

### 4.1 startup checklist

这是目前最建议降级的文件。

#### 原因

- 它和 manifest 的内容高度重叠。
- 它更适合“集成前检查”而不是每次自然语言问答都加载。

#### 最小优化建议

- 常驻时只保留 manifest。
- startup checklist 变成“初始化校验清单”。

### 4.2 runtime summaries 中的共用边界段落

每份 summary 都写了：

- 默认不调用 DataAgent。
- 高成本查询必须用户确认。
- SQL-only / partial / timeout 不能强结论。
- 不自动处罚 / 封禁 / 冻结 / 上线策略。

#### 原因

- 这部分属于通用边界，重复成本较高。

#### 最小优化建议

- 后续可抽成一个共享边界块。
- 当前不建议改大结构，避免引入新架构。

## 5. ATO 是否被削弱

结论：**没有**。

原因：

- manifest 仍明确列出 ATO 完全体。
- startup checklist 明确要求 ATO 命中后进入完全体。
- ATO 短问已做回归。
- ATO POC 已验证 DataAgent 闭环和 `provider_conclusion_hint` / `dennis_final_judgement` 分离。

当前 token 优化建议不会影响 ATO 能力，只是建议把**启动检查文件**从每次对话默认加载中剥离出去。

## 6. DataAgent 是否被泛化

结论：**没有明显泛化，但仍有边界重复风险。**

表现为：

- 各 summary 都会讲 DataAgent 边界。
- manifest 也讲一次。
- system prompt 再讲一次。

这不会导致能力失真，但会造成重复 token。

### 最小建议

- system prompt 保留一句总边界即可。
- manifest 保留正式边界定义。
- summary 只保留与本场景相关的查数边界。

## 7. 文件常驻 / 按需建议表

| 类别 | 建议 | 文件 |
|---|---|---|
| 常驻 | 必须 | system prompt、manifest、场景 router 摘要、response contract 摘要、DataAgent boundary 摘要、timeout 摘要 |
| 集成期加载 | 建议 | startup checklist、release note、route regression、smoke test |
| ATO 按需 | 建议 | ATO 完全体 parser/schema/join/threshold/interpretation 文件 |
| 非 ATO 按需 | 建议 | 8 个 runtime summary、对应深度 Skill |
| 不默认注入 | 建议 | review / eval / history / walkthrough 全量材料 |

## 8. 最小 token 优化建议

### 建议 1：startup checklist 降级

把 `dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md` 从默认常驻降为初始化期文件。

### 建议 2：非 ATO 只带单一 summary

只加载与当前问题匹配的 runtime summary，不做多 summary 叠加。

### 建议 3：ATO 只在命中后加载完全体

ATO 问题不要一开始就把所有 summary 和历史材料混进来。

### 建议 4：不要默认加载 release note / regression / smoke test

这些文件用于集成验收，不用于每轮问答。

### 建议 5：把通用边界收敛成一段短规则

如果后续要继续压 token，优先压缩的是：

- DataAgent 默认边界。
- 高成本查询边界。
- 手工确认边界。

## 9. 当前结论

当前 Runtime Plus 可以继续作为可用发布态，不需要重构。

最值得做的优化不是改能力，而是：

1. 收紧默认加载。
2. 把 startup checklist 移出每轮常驻。
3. 非 ATO 只加载一份 summary。
4. ATO 只在命中后加载完全体。

这样可以在不改边界的前提下，进一步压缩 token 成本。

