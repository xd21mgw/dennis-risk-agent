# ATO Runtime Slimming Plan v1

## 1. 目标

本方案只针对 ATO / 盗号场景的运行态瘦身，不重构全局 Dennis Risk Agent。

目的：

- 降低 ATO 子 Agent 默认加载成本。
- 保持 ATO 短问入口可用。
- 保持 DataAgent evidence provider 边界。
- 保持 `timeout / SQL-only / partial / no_permission` 降级。
- 保持 `dennis_final_judgement` 独立输出。
- 保持 ATO 单 case / DataAgent 返回解释能力。

## 2. ATO runtime slim 原则

### 2.1 本轮只瘦 ATO 运行态

- 只针对 ATO / 盗号场景。
- 不改反爬、群控、活动反作弊、导流、破解包等其他场景 Skill 内容。
- 不把 ATO 的样板直接扩成全局 runtime 规则。

### 2.2 默认运行态只保留最小闭环

默认只保留：

- ATO 路由。
- ATO 短问入口。
- ATO response contract。
- DataAgent 边界摘要。
- timeout policy 摘要。
- 通用 scenario contract 摘要。

### 2.3 深度 Skill 按需读取

以下内容默认不注入全文，只有在问题需要时再读：

- `account_security_expert_skill.md`
- `dataagent_markdown_response_parser_v1.md`
- `query_intent_schema_v2.md`
- `data_join_paths_v1.md`
- `dataagent_result_interpretation_rules_v1.md`
- `dataagent_conclusion_thresholds_v1.md`

### 2.4 review / eval / walkthrough 默认不加载

不默认加载：

- `outputs/reviews` 全量历史。
- `eval` 全量历史。
- 长篇 case walkthrough。
- 大批量 regression 细节。

### 2.5 POC / walkthrough 只作离线参考

- `ATO-S2-004` walkthrough 只作为离线参考，不默认注入。
- 具体策略名、样本统计、历史 case 不进入默认运行态。

## 3. ATO 默认加载文件建议

### 3.1 必须默认加载

#### A. 总控最小规则

- `AGENTS.md` / `SOUL.md` 或同等总控文件的最小规则。

#### B. ATO 入口层

- `ato_intent_router_v1.md`
- `ato_short_question_entrypoint_adaptation_v1.md` 的摘要

#### C. ATO 输出协议

- `ato_agent_response_contract_v1.md`

#### D. 通用 scenario 规则摘要

- `scenario_intent_router_contract_v1.md` 的摘要
- `scenario_workflow_contract_v1.md` 的摘要
- `scenario_response_contract_v1.md` 的摘要

#### E. DataAgent 边界摘要

- `dataagent_provider_boundary_overlay_v1.md` 的摘要

#### F. timeout 摘要

- `dataagent_timeout_policy_review_v1.md` 的摘要

### 3.2 ATO 按需读取

在需要更细判断时再读取：

- `account_security_expert_skill.md`
- `dataagent_markdown_response_parser_v1.md`
- `query_intent_schema_v2.md`
- `data_join_paths_v1.md`
- `dataagent_result_interpretation_rules_v1.md`
- `dataagent_conclusion_thresholds_v1.md`

### 3.3 特殊边界按需读取

只有当 ATO case 涉及边界判断时才读取：

- `protocol_attack_expert_skill.md`
- `group_control_expert_skill.md`
- `real_user_crowdsourcing_skill.md`

典型触发：

- ATO 与协议边界纠缠。
- ATO 与群控真机 / 统一调度纠缠。
- ATO 与账号租借 / 共享 / 众包纠缠。

### 3.4 不默认加载

不默认加载：

- `outputs/reviews` 全量。
- `eval` 全量。
- 历史材料。
- `ATO-S2-004` walkthrough 全文。
- public industry question set 全文。
- regression 明细全文。

## 4. ATO slim manifest 设计思路

### 4.1 必备文件

只保留能支撑“识别 -> 解释 -> 降级 -> 结论 -> 下一步”闭环的文件。

### 4.2 按需文件

与单 case 判断、DataAgent 解释、回捞、治理相关，但不是每次都必须的深度文件。

### 4.3 边界场景文件

当出现协议 / 群控 / 真人众包 / 租借共享等交叉风险时再读。

### 4.4 离线参考文件

只在离线复盘、写材料、做回归时使用。

## 5. 风险检查

### 5.1 是否会削弱 ATO 判断能力

不会，前提是：

- 入口层保留。
- response contract 保留。
- DataAgent 边界和 timeout 摘要保留。
- 需要时再按需读深层 Skill。

### 5.2 是否会破坏 DataAgent evidence provider 边界

不会。边界靠 prompt / contract / workflow 维持，默认瘦身只减少上下文，不改变角色分工。

### 5.3 是否会影响短问入口

不会。短问入口反而更应该默认加载，因为它是高频入口能力。

### 5.4 是否会影响 timeout / SQL-only / partial 降级

不会，只要 timeout policy 摘要和 parser 摘要仍可按需读取。

### 5.5 是否会导致无法解释 DataAgent 返回

不会，只要保留：

- ATO response contract 摘要；
- DataAgent boundary 摘要；
- parser 按需读取入口。

### 5.6 是否会误删账号安全核心判断

不会。`account_security_expert_skill` 仍然保留为按需读取文件，而不是默认删除。

## 6. ATO runtime slim manifest 推荐策略

### 6.1 默认加载

只加载最小闭环：

- 总控规则最小集合。
- ATO intent router。
- ATO short question 规则摘要。
- ATO response contract。
- 通用 scenario contract 摘要。
- DataAgent boundary 摘要。
- timeout policy 摘要。

### 6.2 按需加载

问题涉及具体 ATO 单 case、DataAgent 结果解释、query intent、join path、结论阈值时，再加载对应深度文件。

### 6.3 离线参考

POC walkthrough、长篇 regression、历史 case 只离线参考，不默认进 runtime。

## 7. 从 ATO runtime slimming 迁移到 Dennis global runtime slimming

ATO slim 是第一个场景样板，未来可以迁移成全局规范：

1. 通用场景 router / response contract 默认加载。
2. 场景 overlay 默认只加载当前场景。
3. 深度 Skill 按需读取。
4. review / eval / history 默认不加载。
5. POC / walkthrough 只作为离线参考。

未来反爬、群控、活动反作弊、导流截流也应采用同样模式：

- 场景 router / response contract 默认加载；
- 深度 Skill 按需读取；
- review / eval / history 默认不加载；
- 场景 POC 只做离线参考。

## 8. 结论

ATO runtime slimming 的目标不是削弱能力，而是把默认注入从“全量知识库”收敛到“最小闭环 + 按需展开”。

建议优先落地：

- 默认加载最小闭环文件；
- review / walkthrough 改为按需 read；
- ATO 细节能力按需展开；
- 先保证短问入口和 DataAgent 降级不受影响。

