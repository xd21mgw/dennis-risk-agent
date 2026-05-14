# v2.3 Executable 强对抗回归汇总

## 回归范围

本轮不是检查格式完整性，而是检查 v2.3 executable-deep 在弱证据、反证、合法自动化、真人众包、低质、口径异常和导流截流场景下是否会误判或过度自信。

| Case | 对抗点 | 主控 Skill | 最高可下结论 | 分数 | 是否需回写 |
|---|---|---|---|---:|---|
| ADV-001 | 只有高频访问 | evidence_decomposition_skill | 高频异常，补证/监控 | 88 | 建议补执行契约 |
| ADV-002 | 前端无日志但可能埋点缺失 | protocol_attack_expert_skill | 疑似前后端链路冲突 | 86 | 建议回写 protocol |
| ADV-003 | 大量真实用户同任务且设备离散 | real_user_crowdsourcing_skill | 任务化真人/低质风险 | 82 | 是 |
| ADV-004 | 商家/达人批量登录或接口化运营 | account_security_expert_skill | 合法自动化审计 | 87 | 建议回写 account |
| ADV-005 | 活动低钱效但无黑产证据 | activity_anti_cheating_expert_skill | 低质用户/钱效治理 | 90 | 否 |
| ADV-006 | 外网跟价但内部无接口异常 | anti_crawler_expert_skill | 价格资产外泄待溯源 | 89 | 否 |
| ADV-007 | DAU/DNU 异常但缺攻击证据 | traffic_anti_cheating_expert_skill | 指标口径异常待校验 | 88 | 建议回写 traffic |
| ADV-008 | 直播间用户被站外添加但无爬虫证据 | traffic_diversion_interception_skill | 导流/截流链路风险 | 74 | 是 |

平均分：85.5/100。最低分 ADV-008，原因不是回答格式缺失，而是导流截流 Skill 本身还不是 v2.3 executable-deep，边界规则不足。

## 哪些 Skill 容易误判

1. protocol_attack_expert_skill  
   风险点：使用者可能把“服务端有请求、前端无日志”单点当成协议强证据。实际还必须排除埋点缺失、SDK 采集、破解包绕采集、网关采样和合法自动化。

2. group_control_expert_skill  
   风险点：在“高频、目标一致、任务一致”场景下容易被误触发。当前规则已经写了不得仅凭高频/聚集定群控，但真人众包和活动低质的承接 Skill 较弱。

3. real_user_crowdsourcing_skill  
   风险点：仍是 v2.1，缺少可执行的触发条件、输入格式、判断分支和失败处理。面对“真人但任务化”的 case，需要它作为主控承接，否则容易被群控或活动 Skill 抢主控。

4. traffic_anti_cheating_expert_skill  
   风险点：DAU/DNU 指标异常容易被写成黑产污染，但在缺攻击证据时应先进入口径校验、数据任务和 SLA 保障。

5. traffic_diversion_interception_skill  
   风险点：直播间站外添加容易被误归反爬、协议或账号安全。现有 Skill 对“目标获取、触达、站外承接、变现”的链路有认知，但缺 v2.3 的规则化边界。

## 哪些判断规则需要补充

- skill_execution_contract_v2_3：增加“弱信号统一出口”，明确只有高频、聚集、单指标波动时，默认进入监控/加采/补证，不选择攻击手法主控。
- protocol_attack_expert_skill 第 4 节第 1 条：强调高置信单纯协议必须同时满足“无端链路 + 接口序列异常 + 强目标直达/参数冲突”，单独前端无日志只能算链路冲突。
- account_security_expert_skill 第 4 节：增加商家、达人、机构、ISV、客服工具的合法自动化/授权矩阵审计分支。
- traffic_anti_cheating_expert_skill 第 4 节第 2 条：增加 DAU/DNU 缺攻击证据时的口径事故、数据任务、埋点变更、双轨对账分支。
- real_user_crowdsourcing_skill：升级到 v2.3 executable-deep，补触发、输入、判断规则、强中弱证据、反证、降级和业务损伤。
- traffic_diversion_interception_skill：升级到 v2.3 executable-deep，补导流截流 vs 反爬/协议/账号盗号/正常社交的边界规则。

## 是否需要回写 Skill

需要，但本轮按用户要求不修改 Skill 文件。

必须回写：
- real_user_crowdsourcing_skill：补 v2.3 executable-deep 全结构，尤其是“真实用户 + 设备离散 + 任务化目标”的主控承接。
- traffic_diversion_interception_skill：补 v2.3 executable-deep 全结构，尤其是“直播间信息暴露/站外添加”不得误归反爬或协议。

建议回写：
- protocol_attack_expert_skill：收紧第 1 条强协议判定的并列条件。
- account_security_expert_skill：增加合法自动化/机构账号分支。
- traffic_anti_cheating_expert_skill：增加 DAU/DNU 缺攻击证据时的数据治理分支。
- skill_execution_contract_v2_3：增加弱信号统一降级出口。

## 结论

v2.3 对活动低质、反爬多路径溯源、DAU/DNU 口径保障、合法自动化等方向具备较好的防过拟合能力；主要短板在非核心 v2.3 化 Skill 的承接能力。强对抗下最容易出错的不是输出格式，而是主控路由：真人众包和导流截流如果没有足够强的可执行规则，会被群控、协议或反爬错误吸收。
