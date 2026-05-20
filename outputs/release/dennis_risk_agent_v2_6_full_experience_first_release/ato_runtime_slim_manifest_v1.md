# ATO Runtime Slim Manifest v1

## 1. 目的

本 manifest 定义 ATO 场景运行态的最小加载集合，用于降低 Dennis 子 Agent 在 ATO POC / 试用中的 token 和耗时成本。

原则：

- 默认只加载最小闭环。
- 深度文件按需读取。
- review / walkthrough / history 不默认加载。
- 不削弱 ATO 判断、短问入口、DataAgent 边界和降级能力。

## 2. ATO runtime 必备文件

| 文件 | 用途 | 为什么默认加载 |
|---|---|---|
| `AGENTS.md` / `SOUL.md` 最小规则 | 总控约束 | 决定整体风控定位和输出边界 |
| `scenario_intent_router_contract_v1.md` | 通用场景路由 | 维持 ATO 入口与其他场景的一致路由逻辑 |
| `scenario_workflow_contract_v1.md` 摘要 | 通用 workflow | 维持单 case / 批量 / DataAgent / 回捞 / 治理的标准流程 |
| `scenario_response_contract_v1.md` 摘要 | 通用输出协议 | 维持短答、解释、沉淀、治理输出结构 |
| `ato_intent_router_v1.md` | ATO 入口路由 | 让短问、批量、解释、回捞等 ATO 入口稳定工作 |
| `ato_agent_response_contract_v1.md` | ATO 输出协议 | 维持 ATO 的单 case / 批量 / DataAgent 返回解释格式 |
| `dataagent_provider_boundary_overlay_v1.md` 摘要 | DataAgent 边界 | 保证 evidence provider 与 final judgement 分离 |
| `dataagent_timeout_policy_review_v1.md` 摘要 | timeout 规则 | 保证 timeout / SQL-only / partial 降级一致 |
| `ato_short_question_entrypoint_adaptation_v1.md` 摘要 | 短问适配 | 支撑高频短问入口 |

## 3. ATO 按需文件

| 文件 | 用途 | 何时读取 |
|---|---|---|
| `account_security_expert_skill.md` | 账号安全专项规则 | 单 case 研判、治理、回写建议时读取 |
| `dataagent_markdown_response_parser_v1.md` | DataAgent 返回解析 | 用户贴回 DataAgent 内容或需要解释返回时读取 |
| `query_intent_schema_v2.md` | 取证问题 schema | 生成 / 校准 DataAgent 问题时读取 |
| `data_join_paths_v1.md` | join path | 需要解释关联链路或补证路径时读取 |
| `dataagent_result_interpretation_rules_v1.md` | 返回解释规则 | 用户问“这个结果够不够”时读取 |
| `dataagent_conclusion_thresholds_v1.md` | 结论阈值 | 需要判断能否下结论时读取 |

## 4. 边界场景按需文件

| 文件 | 用途 | 何时读取 |
|---|---|---|
| `protocol_attack_expert_skill.md` | 协议边界 | ATO 与协议证据纠缠时读取 |
| `group_control_expert_skill.md` | 群控边界 | ATO 与多设备统一调度纠缠时读取 |
| `real_user_crowdsourcing_skill.md` | 真人众包边界 | ATO 与任务化真人执行纠缠时读取 |

## 5. 离线参考文件

| 文件 | 用途 | 默认加载态度 |
|---|---|---|
| `outputs/reviews/ato_end_to_end_usage_walkthrough_ATO-S2-004.md` | POC 闭环参考 | 不默认加载 |
| `outputs/reviews/ato_short_question_live_test_review_v1.md` | 短问回归参考 | 不默认加载 |
| `outputs/reviews/ato_public_industry_question_set_v1.md` | 公开行业问法参考 | 不默认加载 |
| `outputs/reviews/ato_real_user_question_trial_v1.md` | 内部真实问法参考 | 不默认加载 |
| `outputs/reviews/*regression*` | 历史回归明细 | 不默认加载 |
| `outputs/reviews/*walkthrough*` | 长篇说明 | 不默认加载 |

## 6. 不建议默认注入文件

以下文件不建议默认注入：

- 所有 `outputs/reviews` 全量。
- 所有 `eval` 全量。
- 历史 case 大集合。
- 旧版本 parser / boundary / workflow 的全文。
- 过往 POC / walkthrough 全文。

原因：

- 这些文件会显著增加 token。
- 多数内容只用于离线复盘。
- 默认注入容易让 ATO 入口过拟合具体 case。

## 7. 预计降低的 token 成本

预计可降低的成本来源：

- 不再默认加载大批量 review。
- 不再默认加载历史 walkthrough 全文。
- 不再把旧版 parser / boundary 全文塞入运行态。
- 不再把具体样本统计、具体策略名、具体时间窗带进默认上下文。

主要收益：

- 更短的运行上下文。
- 更稳定的路由。
- 更少的重复解释。
- 更低的 POC token 成本。

## 8. 为什么这么分

### 必备文件

必须默认加载的是“能让 Agent 工作”的最小闭环，而不是“所有知识”。

### 按需文件

只在需要细化判断、生成 DataAgent 问题、解释结果、做边界判断时读取。

### 边界场景文件

只有当 ATO 证据与协议 / 群控 / 真人众包纠缠时才读取，避免日常污染。

### 离线参考文件

只用于复盘和回顾，不适合做 runtime 常驻。

## 9. 风险检查

- **会削弱 ATO 判断能力吗？**
  不会，只要保留入口、response、DataAgent boundary、timeout 摘要和按需读取机制。

- **会破坏 DataAgent evidence provider 边界吗？**
  不会，边界来自 contract / policy，不来自全量注入。

- **会影响短问入口吗？**
  不会，短问入口应保留在默认加载里。

- **会影响 timeout / SQL-only / partial 降级吗？**
  不会，只要 parser / timeout 摘要能按需读取。

- **会导致无法解释 DataAgent 返回吗？**
  不会，只要 parser / response contract / boundary 仍在按需读取列表。

- **会误删账号安全核心判断吗？**
  不会，`account_security_expert_skill` 仍是按需文件，不是移除。

## 10. 未来全局 runtime slimming 的迁移建议

ATO slim 是第一个样板。未来如果要做 Dennis global runtime slimming，建议统一采用：

1. 场景 router / response contract 默认加载。
2. 深度 Skill 按需读取。
3. review / eval / history 默认不加载。
4. 场景 walkthrough 只作离线参考。
5. 只对当前场景加载 overlay，不把其他场景的细节默认注入。

适用扩展场景：

- 反爬。
- 群控。
- 活动反作弊。
- 导流截流。

## 11. 结论

ATO runtime slim 的目标是“保留闭环，移除默认重资产”。

如果按本 manifest 执行，ATO 子 Agent 默认成本应明显下降，同时保留：

- 短问入口；
- ATO 单 case 判断；
- DataAgent 解释；
- timeout / SQL-only / partial / no_permission 降级；
- `dennis_final_judgement` 独立输出。

