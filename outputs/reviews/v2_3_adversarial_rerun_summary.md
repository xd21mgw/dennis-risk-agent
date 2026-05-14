# v2.3 强对抗定点回写后复跑汇总

## 修改范围

本轮按要求只做定点回写，修改 3 个文件：

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/traffic_diversion_interception_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/03_attack_skills/real_user_crowdsourcing_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/00_agent_core/skill_execution_contract_v2_3.md`

未修改可选文件。

## 分数对比

| Case | 修改前 | 修改后 | 提升 | 结论 |
|---|---:|---:|---:|---|
| ADV-003 | 82 | 90 | +8 | 真人众包主控承接稳定，能区分群控、低质、自然用户 |
| ADV-008 | 74 | 89 | +15 | 导流截流主控承接稳定，不再误归反爬或协议 |

## ADV-003 复跑结论

修改后 real_user_crowdsourcing_skill 已能明确承接“行为真实、目标一致、设备离散、任务化完成”场景。它不会因为设备离散就判自然用户，也不会因为目标一致就判群控；证据不足时会降级为“真人众包嫌疑或活动低质”，要求补任务平台、收益链、教程话术、后验质量和提现/奖励聚集。

仍有边界：如果拿不到站外任务平台或收益链，只能保持中置信，不能强打黑产。

## ADV-008 复跑结论

修改后 traffic_diversion_interception_skill 已具备执行型结构，能把“直播间用户被站外添加”优先归为导流截流链路，而不是默认反爬或协议。输出字段也补齐了信息暴露入口、目标获取路径、触达方式、站外承接证据、黑产账号矩阵和治理动作。

ADV-008 修改后为 89/100，高于 85；不需要继续回写。未打到 95+ 是因为真实场景仍依赖站外承接证据和平台内搜索/私信日志闭合。

## 回写效果

- traffic_diversion_interception_skill：从 v2.1 短结构升级到 v2.3 executable-deep，重点补了导流截流 vs 反爬/协议/正常社交的边界。
- real_user_crowdsourcing_skill：从 v2.1 短结构升级到 v2.3 executable-deep，重点补了真人众包 vs 群控/活动低质/正常自然用户的边界。
- skill_execution_contract_v2_3：新增全局转交规则，覆盖导流截流、真人众包、埋点缺失下的协议降级、合法自动化/授权矩阵。

## 是否还需回写

本轮目标内不需要继续修改。

后续可选优化仍包括：

- protocol_attack_expert_skill：收紧“前端无日志”不得单点触发协议强结论。
- account_security_expert_skill：增加商家/达人/机构批量运营的合法自动化分支。
- traffic_anti_cheating_expert_skill：增加 DAU/DNU 缺攻击证据时的数据治理分支。
