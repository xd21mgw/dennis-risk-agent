# v2.3 其他 Skill 自我进化交叉检查汇总

## 本轮目标

基于强对抗回归和 ADV-003/ADV-008 定点回写经验，对其他核心 Skill 自生成交叉 case，检查是否会误判、过度自信或路由错误，并做轻量回写。

## 修改文件

本轮新增轻量回写 3 个文件：

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/03_attack_skills/protocol_attack_expert_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/account_security_expert_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/traffic_anti_cheating_expert_skill.md`

沿用上一轮已修改的 3 个文件：

- `traffic_diversion_interception_skill.md`
- `real_user_crowdsourcing_skill.md`
- `skill_execution_contract_v2_3.md`

未修改：

- `group_control_expert_skill.md`
- `anti_crawler_expert_skill.md`
- `activity_anti_cheating_expert_skill.md`

## 自生成交叉 Case 结果

| Case | 对抗点 | 主控 Skill | 是否回写 | 回写后分数 |
|---|---|---|---|---:|
| SE-001 | 前端无日志但可能采集/版本问题 | protocol_attack_expert_skill | 是 | 90 |
| SE-002 | 商家/达人/机构接口化运营 | account_security_expert_skill | 是 | 91 |
| SE-003 | DAU/DNU 异常但缺攻击证据 | traffic_anti_cheating_expert_skill | 是 | 91 |
| SE-004 | 高频目标一致但无调度/协议证据 | evidence_decomposition_skill | 否 | 89 |
| SE-005 | 外网跟价但无接口异常 | anti_crawler_expert_skill | 否 | 90 |
| SE-006 | 活动低质但无黑产证据 | activity_anti_cheating_expert_skill | 否 | 91 |

平均分：90.3/100。

## 回写内容摘要

### protocol_attack_expert_skill

收紧高置信单纯协议条件：不能因为“服务端有请求、前端无日志”单点强判协议。必须同时有无端链路、接口序列异常、强目标直达和参数/签名/token/设备链路冲突。补充 SDK、网关采样、版本灰度、破解包绕采集和合法自动化反证。

### account_security_expert_skill

新增商家、达人、机构、ISV、客服工具批量登录/接口化运营的合法自动化分支。先做授权主体、调用范围、审计、配额和敏感动作边界校验，不直接按盗号或协议攻击处置。

### traffic_anti_cheating_expert_skill

新增 DAU/DNU 缺攻击证据时的数据治理分支。指标异常先做口径定义、去重逻辑、端版本、埋点变更、任务依赖、实时/离线 diff 和回补记录校验，不直接定黑产污染。

## 仍需注意的边界

- protocol 的强判仍依赖前后端 join、签名/token/设备链路完整性；日志缺失时只能保持链路冲突判断。
- account 的合法自动化需要授权台账和操作审计，否则只能给审计方案，不能替业务兜底白名单。
- traffic 的 DAU/DNU 分支依赖数据平台任务链路和业务口径 owner，不能由风控单方改核心口径。
- group_control、anti_crawler、activity 本轮未改，是因为自生成 case 未暴露新的结构缺口；后续若出现“合法矩阵群控”“合作方缓存外泄”“普通用户规则套利大规模化”等更细 case，可再定点补。

## 结论

本轮完成了其他核心 Skill 的轻量自我进化：重点补齐 protocol、account、traffic 三个容易过度自信的边界。结合上一轮对真人众包和导流截流的升级，v2.3 executable-deep 在弱证据、合法自动化、口径异常、真人任务化和导流截流上的路由稳定性明显增强。
