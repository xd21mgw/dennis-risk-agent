# Dennis Agent 运行态瘦身建议

## 1. 当前 token 成本来源分析

本次 POC 约 139k token，主要消耗来源通常有四类：

1. 运行态自动加载的 MD 过多；
2. 重复的 review / walkthrough / regression 材料过多；
3. DataAgent 相关 contract、parser、boundary 文档层数太厚；
4. 同一问题被多层解释，导致上下文反复叠加。

其中最需要瘦身的不是“能力本身”，而是**默认注入范围**。

## 2. 哪些 MD 应继续保留在 runtime

建议默认保留的只有最小闭环文件：

1. `AGENTS.md`
2. 总控规则 / 核心 system prompt
3. `scenario_intent_router_contract_v1.md`
4. `scenario_workflow_contract_v1.md`
5. `scenario_response_contract_v1.md`
6. 当前生效的 scenario overlay，例如 ATO overlay
7. DataAgent 最小 contract / boundary / parser
8. 最近一版真实 POC / 运行态校准说明

原则：

- 保持“能路由、能解释、能降级、能结论”即可；
- 不把历史大批量 review 默认塞进 runtime。

## 3. 哪些 MD 可以改为按需 read

建议按需读取，不默认加载：

- 所有大批量 regression report；
- 所有历史 case 大集合；
- 所有 walkthrough / demo / 长链路解释材料；
- 所有 batch management / label taxonomy / feature layering 的历史扩展；
- 过往多个版本的 parser / overlay 交叉说明。

这些材料适合“需要时查”，不适合“每次都注入”。

## 4. 哪些 review / walkthrough 不应默认加载

以下类型不应进入默认 runtime：

- 端到端闭环大篇幅 walkthrough；
- 大量 case 的解析 summary；
- 历史修订对照；
- POC 以外的扩展推演文档；
- 已被新版本覆盖的旧版评审。

这些文档的价值在于复盘，不在于日常路由。

## 5. ATO-only runtime slim 包建议

建议拆成一个极小运行包：

1. 总控约束；
2. scenario contract；
3. ATO overlay；
4. DataAgent 最小 contract；
5. DataAgent parser；
6. DataAgent provider boundary；
7. 最近 1 个真实 POC 结果；
8. 最近 1 个降级 / 反例样例。

不建议把所有 ATO 历史 review 一次性塞进去。

## 6. 后续扩反爬 / 群控时如何避免主 Agent 上下文污染

建议采用“场景包分离”：

- 主 Agent 保留通用风控能力；
- 每个场景只加载自己的 overlay / workflow / response contract；
- 不同场景之间只共享最小通用 contract；
- 不把 ATO 的 case 细节带到反爬 / 群控的运行态。

这样可以避免：

- 路由偏置；
- 规则串味；
- 过拟合 ATO 样本；
- 上下文过载导致判断不稳定。

## 7. 子 Agent vs Skill 的最终建议

### 当前推荐

继续用子 Agent。

### 原因

1. 能隔离风控上下文；
2. 不污染主 Agent 的日常任务；
3. 便于把 DataAgent 作为 evidence provider 接入；
4. 便于以后扩展到反爬、群控、活动反作弊；
5. 更适合做最小 POC 和受控试用。

如果直接把所有逻辑压到主 Agent，成本会更高，且更容易引入长期上下文污染。

## 8. 下一轮优化建议

1. 建立“runtime minimal set”清单，严格控制默认注入文件；
2. review / walkthrough 改成按需 read；
3. 将最近 POC 结果压缩成单页摘要；
4. 将扩展场景保留在 overlay，不进主运行态；
5. 继续观测 token 成本是否能降到更稳定的区间；
6. 对 DataAgent 同步闭环优先优化提示和路由，而不是继续扩文档。

