# Scenario Entrypoint Framework Review v1

## 1. 本轮新增文件

| 文件 | 作用 |
|---|---|
| `skills/dennis_risk_agent_skills_v2_1_focused_deep/10_agent_entrypoints/scenario_intent_router_contract_v1.md` | 通用场景 intent router contract |
| `skills/dennis_risk_agent_skills_v2_1_focused_deep/09_scenario_workflows/scenario_workflow_contract_v1.md` | 通用场景 workflow contract |
| `skills/dennis_risk_agent_skills_v2_1_focused_deep/10_agent_entrypoints/scenario_response_contract_v1.md` | 通用场景 response contract |
| `outputs/reviews/scenario_entrypoint_framework_review_v1.md` | 本次通用入口层自检 |

## 2. 通用入口层如何工作

通用链路：

```text
用户自然语言问题
→ scenario_intent_router_contract
→ scenario_workflow_contract
→ core Skill / evidence card / Data Agent template
→ scenario_response_contract
→ Dennis final judgement / next action
```

三层职责：

- intent router：识别用户意图和场景。
- workflow：调度已有 Skill、证据卡和工具模板。
- response contract：稳定输出用户可用结果。

## 3. ATO overlay 与通用 contract 的关系

ATO 是第一个 scenario overlay：

```text
scenario_intent_router_contract_v1
→ ato_intent_router_v1

scenario_workflow_contract_v1
→ ato_account_takeover_workflows_v1

scenario_response_contract_v1
→ ato_agent_response_contract_v1
```

当前 ATO 文件应保留为第一个场景落地样板，不需要推翻或重写。

## 4. 是否保持通用风控专家定位

检查通过。

本轮没有把 Agent 改成盗号专用 Agent：

- 通用 contract 不绑定 ATO。
- 明确未来可扩展反爬、群控、活动反作弊、导流、渠道抢量等场景。
- ATO 只是第一个 overlay。
- 核心 Skill 不被复制或重写。

## 5. 未来反爬场景如何扩展

可新增：

```text
anti_crawler_intent_router_v1
anti_crawler_workflows_v1
anti_crawler_response_contract_v1
```

复用通用 intent：
- single_case_judgement：单个爬取 case 是否成立。
- batch_case_clustering：爬虫样本按资产访问、接口路径、账号设备聚集分层。
- evidence_planning：前后端链路、资产访问、接口频率、设备/IP/UA、外部泄漏对齐。
- dataagent_question_generation：生成资产访问离线复盘问题。
- dataagent_result_interpretation：解释 Data Agent 返回，区分外网跟价、缓存、合作方、真人访问等反证。
- generalization_and_recall：回捞相似资产访问路径。
- governance_design：接口限频、挑战、脱敏、缓存治理、合作方排查。

## 6. 未来群控场景如何扩展

可新增：

```text
group_control_intent_router_v1
group_control_workflows_v1
group_control_response_contract_v1
```

复用通用 intent：
- single_case_judgement：单个账号/设备是否群控。
- batch_case_clustering：设备团组、统一调度、行为路径相似分层。
- evidence_planning：设备团组、同批启动/停止、行为路径、收益聚集、合法矩阵反证。
- dataagent_question_generation：生成离线团组和行为聚合问题。
- generalization_and_recall：抽象统一调度机制特征。
- governance_design：设备挑战、账号限权、收益拦截、合法矩阵豁免。

## 7. 未来活动反作弊场景如何扩展

可新增：

```text
activity_anti_cheating_intent_router_v1
activity_anti_cheating_workflows_v1
activity_anti_cheating_response_contract_v1
```

复用通用 intent：
- batch_case_clustering：活动用户按低质、黑产、真人众包、正常用户分层。
- evidence_planning：活动参与、邀请关系、奖励/提现、留存、设备/账号团组。
- dataagent_question_generation：生成活动参与和后验质量取证问题。
- dataagent_result_interpretation：区分低质用户与黑产。
- generalization_and_recall：回捞任务平台、奖励聚集、低留存低付费人群。
- governance_design：奖励延迟、提现验证、任务限权、低质监控。

## 8. 自检

| 检查项 | 结果 |
|---|---|
| 是否保持 Dennis Risk Agent 通用风控专家定位 | 通过 |
| 是否没有把 Agent 改成盗号专用 | 通过 |
| ATO 是否只是第一个 overlay | 通过 |
| 现有 ATO entrypoint 是否可作为样板保留 | 通过 |
| 是否支持反爬扩展 | 通过 |
| 是否支持群控扩展 | 通过 |
| 是否支持活动反作弊扩展 | 通过 |
| 是否没有修改核心 Skill | 通过 |
| 是否没有调用 Data Agent | 通过 |

## 9. 后续建议

P0：
- 保持 ATO overlay 作为第一个落地样板。
- 不急于把通用 contract 写入核心 Skill。

P1：
- 在确认 ATO workflow 稳定后，将 scenario contracts 挂入 Skill registry 或 routing rules。
- 按同样模式新增 anti_crawler / group_control / activity overlay。

P2：
- 后续可更新 AGENTS.md，说明“场景入口层优先路由，但不替代核心 Skill”。

## 10. 是否修改核心 Skill

未修改核心 Skill。

本轮只新增通用 scenario intent router、workflow、response contract 和 review 文件。
