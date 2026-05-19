# ATO Agent Entrypoint Design Review v1

## 1. 本轮新增文件

| 文件 | 作用 |
|---|---|
| `skills/dennis_risk_agent_skills_v2_1_focused_deep/09_scenario_workflows/ato_account_takeover_workflows_v1.md` | 定义 ATO 场景 7 类 Agent 自动调度 workflow |
| `skills/dennis_risk_agent_skills_v2_1_focused_deep/10_agent_entrypoints/ato_intent_router_v1.md` | 定义用户自然语言问题到 ATO workflow 的路由规则 |
| `skills/dennis_risk_agent_skills_v2_1_focused_deep/10_agent_entrypoints/ato_agent_response_contract_v1.md` | 定义 Agent 面向用户的稳定输出协议 |
| `outputs/reviews/ato_agent_entrypoint_design_review_v1.md` | 本次入口层设计自检 |

## 2. 核心摘要

### 2.1 workflow

新增 7 类 ATO 场景 workflow：

1. `single_case_judgement`
2. `batch_case_clustering`
3. `dataagent_question_generation`
4. `dataagent_result_interpretation`
5. `generalization_and_recall`
6. `governance_design`
7. `review_and_skill_distillation`

这些 workflow 不是给同学直接读 MD，而是给 Agent 自动调度。

### 2.2 intent router

router 支持：
- 盗号 / 被盗 / ATO / 登录异常。
- 扫码 / 钓鱼 / 验证码 / token / session。
- 客诉 / 解封 / 回捞 / 批量样本。
- Data Agent 返回解释。

并支持多意图串联，例如：
- 批量分层 → Data Agent 问题生成。
- Data Agent 解释 → 举一反三。
- 单 case 判断 → 治理方案。

### 2.3 response contract

定义了 7 类稳定输出协议：
- 单 case。
- 批量 case。
- Data Agent 问题。
- Data Agent 返回解释。
- 举一反三。
- 治理方案。
- 复盘沉淀。

## 3. 其他同学可以怎么问

示例：

| 用户问法 | 自动触发 workflow |
|---|---|
| “这个用户是不是被盗？” | `single_case_judgement` |
| “这批样本帮我分一下扫码、钓鱼、token。” | `batch_case_clustering` |
| “帮我生成 Data Agent 查询问题。” | `dataagent_question_generation` |
| “这是 Data Agent 返回，帮我解释够不够判断盗号。” | `dataagent_result_interpretation` |
| “怎么回捞同类盗号？” | `generalization_and_recall` |
| “这类盗号怎么治理？” | `governance_design` |
| “这批 case 要不要回写 Skill？” | `review_and_skill_distillation` |

## 4. 哪些问题需要 Data Agent

需要：
- 要查登录、授权、token/session、设备、发布、策略、活动等证据。
- 要做批量样本共性分析。
- 要验证人工备注或用户申诉。
- 要生成回捞候选特征。

不需要：
- 解释 ATO 概念或边界。
- 对已有 Data Agent 返回做解释。
- 做治理打法框架。
- 做 review / eval / Skill 沉淀判断。

## 5. 自检项

| 检查项 | 结果 |
|---|---|
| 是否不是面向同学阅读 MD，而是面向 Agent 调度 | 通过 |
| 是否覆盖单 case、批量 case、Data Agent、回捞、治理、复盘 | 通过 |
| 是否保持 Data Agent evidence provider 边界 | 通过 |
| 是否避免过拟合单批样本 | 通过 |
| 是否能支持内部盗号同学自然语言使用 | 通过 |
| 是否未修改核心 Skill | 通过 |
| 是否保持 Dennis Risk Agent 通用风控专家定位 | 通过 |

## 6. 防过拟合检查

本次入口层没有把以下内容写成长期规则：

- 单批样本比例。
- 具体时间窗。
- 具体策略名。
- 完整 user_id。
- 具体表名、字段名、SQL、API。
- 发布色情 / 招嫖作为 ATO 必要路径。

入口层保留的原则是：

```text
ATO 发生方式与下游作恶方式拆开；
Data Agent 提供 evidence provider 级发现；
Dennis Agent 做最终解释；
人工做最终确认。
```

## 7. 是否需要接入 account_security_expert_skill

需要，但不是本轮修改。

后续建议：
- 入口层触发后，默认调用 `account_security_expert_skill` 作为主控 Skill。
- ATO workflow 负责场景编排。
- account_security Skill 负责账号安全专业判断。
- Data Agent 工具层负责取证。

## 8. 是否需要更新 AGENTS.md 或 routing rules

建议后续更新，但本轮不改。

可选更新方向：
- 在 AGENTS.md 中增加“场景入口层优先触发”说明。
- 在 Skill registry 或 routing rules 中挂载 `ato_intent_router_v1.md`。
- 保持 ATO 只是第一个 scenario workflow，不把 Agent 变成盗号专用 Agent。

## 9. 是否修改核心 Skill

未修改核心 Skill。

本轮只新增 scenario workflow、agent entrypoint、response contract 和 review 文件。
