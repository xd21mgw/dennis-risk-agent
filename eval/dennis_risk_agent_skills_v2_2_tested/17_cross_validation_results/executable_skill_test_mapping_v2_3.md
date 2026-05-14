# Executable Skill Test Mapping v2.3

## 1. 目标

基于 50 个 v2.2 测试案例，验证 v2.3 executable-deep 是否能稳定完成：

- Skill 触发；
- 主控 / 辅助 Skill 路由；
- 判断规则命中；
- must_have 覆盖；
- must_not 约束；
- 证据不足时降级。

## 2. 六个核心 Skill 绑定 Case

### group_control_expert_skill

| Case | 主控 Skill | 辅助 Skill | 触发原因 | 覆盖结论 |
|---|---|---|---|---|
| AC-004 | group_control_expert_skill | anti_crawler_expert_skill, evidence_decomposition_skill | 真机端行为存在但目标高度一致，需判断统一调度 | 覆盖：群控真机、反证、资产访问 |
| AC-013 | traffic_anti_cheating_expert_skill | group_control_expert_skill, protocol_attack_expert_skill, real_user_crowdsourcing_skill | 内容互动刷量需区分群控、协议、真人众包 | 覆盖：手法边界 |
| ACT-001 | activity_anti_cheating_expert_skill | group_control_expert_skill, protocol_attack_expert_skill | 活动黑产假量常混合群控和协议 | 覆盖：查杀分离、分层治理 |
| ACT-007 | activity_anti_cheating_expert_skill | group_control_expert_skill | 直播红包群控设备抢权益 | 覆盖：设备、账号、行为、收益 |
| BI-003 | group_control_expert_skill | account_security_expert_skill, risk_governance_design_skill | 设备处置连接群控治理 | 覆盖：设备处置、误伤、发版约束 |
| BI-008 | material_delivery_skill | group_control_expert_skill, protocol_attack_expert_skill | 黑灰产基建材料需讲群控能力 | 覆盖：材料化表达 |

### protocol_attack_expert_skill

| Case | 主控 Skill | 辅助 Skill | 触发原因 | 覆盖结论 |
|---|---|---|---|---|
| AC-003 | protocol_attack_expert_skill | attack_type_classification_skill, evidence_decomposition_skill | 明确判断单纯协议 | 覆盖：无端链路、排除群控/破解包/真人 |
| AC-010 | anti_crawler_expert_skill | protocol_attack_expert_skill, risk_governance_design_skill | 未登录态接口获取核心内容 | 覆盖：接口直达、上下文绑定 |
| AS-001 | account_security_expert_skill | protocol_attack_expert_skill, credential_stuffing_ato_skill | token 泄露复用可表现为协议化请求 | 覆盖：token/设备/IP 一致性 |
| AS-007 | account_security_expert_skill | protocol_attack_expert_skill, risk_governance_design_skill | 商家和黑产都捅接口登录 | 覆盖：合法自动化边界 |
| BI-001 | protocol_attack_expert_skill | anti_crawler_expert_skill, material_delivery_skill | 协议降发生但养设备协议变多 | 覆盖：协议迁移、养设备协议 |
| BI-008 | material_delivery_skill | protocol_attack_expert_skill, group_control_expert_skill | 黑灰产基建材料需讲协议能力 | 覆盖：材料化表达 |

### anti_crawler_expert_skill

| Case | 主控 Skill | 辅助 Skill | 触发原因 | 覆盖结论 |
|---|---|---|---|---|
| AC-001 | anti_crawler_expert_skill | risk_chain_reconstruction_skill, evidence_decomposition_skill | 外网跟价定位入口 | 覆盖：资产级溯源 |
| AC-002 | anti_crawler_expert_skill | attack_type_classification_skill, cracked_app_expert_skill | 版权泄漏但后端像真人 | 覆盖：破解包/真人/协议边界 |
| AC-004 | group_control_expert_skill | anti_crawler_expert_skill | 群控真机爬核心资产 | 覆盖：资产保护 + 群控 |
| AC-006 | anti_crawler_expert_skill | business_domain_map_skill, material_delivery_skill | 单点策略升级非常 6+1 | 覆盖：体系建设 |
| AC-007 | anti_crawler_expert_skill | business_domain_map_skill | 高中低价值资产分级 | 覆盖：资产分级 |
| AC-010 | anti_crawler_expert_skill | protocol_attack_expert_skill | 未登录态接口治理 | 覆盖：弱端/未接漏洞 |
| AC-014 | anti_crawler_expert_skill | material_delivery_skill | 版权诉讼支撑 | 覆盖：防控、溯源、取证、诉讼 |
| AC-015 | anti_crawler_expert_skill | executive_summary_skill, material_delivery_skill | 反爬业务价值表达 | 覆盖：指标和材料 |

### account_security_expert_skill

| Case | 主控 Skill | 辅助 Skill | 触发原因 | 覆盖结论 |
|---|---|---|---|---|
| AS-001 | account_security_expert_skill | credential_stuffing_ato_skill, protocol_attack_expert_skill | token 泄露和 ATO | 覆盖：token、环境、踢出 |
| AS-002 | account_security_expert_skill | risk_chain_reconstruction_skill | 欺诈盗号 | 覆盖：本人参与但意图被操控 |
| AS-003 | credential_stuffing_ato_skill | account_security_expert_skill | 撞库导致 ATO | 覆盖：登录序列和下游行为 |
| AS-004 | account_security_expert_skill | business_domain_map_skill | 小号从注册扩全链路 | 覆盖：账号生命周期 |
| AS-005 | account_security_expert_skill | risk_governance_design_skill | 二次放号安全体验平衡 | 覆盖：监管和体验边界 |
| AS-006 | account_security_expert_skill | risk_chain_reconstruction_skill | 交易号识别 | 覆盖：账号流通和下游作恶 |
| AS-008 | account_security_expert_skill | risk_governance_design_skill | 可信体系降低误伤 | 覆盖：安全体验分层 |
| AS-009 | account_security_expert_skill | risk_governance_design_skill | 验无可验 | 覆盖：验证体系 |

### activity_anti_cheating_expert_skill

| Case | 主控 Skill | 辅助 Skill | 触发原因 | 覆盖结论 |
|---|---|---|---|---|
| ACT-001 | activity_anti_cheating_expert_skill | group_control_expert_skill, protocol_attack_expert_skill | 裂变活动黑产假量 | 覆盖：查杀分离 |
| ACT-002 | activity_anti_cheating_expert_skill | evidence_decomposition_skill | 低钱效用户不等于黑产 | 覆盖：低质边界 |
| ACT-003 | activity_anti_cheating_expert_skill | traffic_anti_cheating_expert_skill | 渠道抢量 | 覆盖：RTA、归因、结算 |
| ACT-004 | activity_anti_cheating_expert_skill | risk_chain_reconstruction_skill | 口令劫持 | 覆盖：产品交互、举报、离线处罚 |
| ACT-005 | activity_anti_cheating_expert_skill | plugin_reverse_analysis_skill | 活动风险插件 | 覆盖：插件和业务特征 |
| ACT-006 | activity_anti_cheating_expert_skill | risk_governance_design_skill | 普通用户规则套利 | 覆盖：规则漏洞和业务优化 |
| ACT-007 | activity_anti_cheating_expert_skill | group_control_expert_skill | 直播红包群控 | 覆盖：收益链路 |
| ACT-009 | material_delivery_skill | activity_anti_cheating_expert_skill | 增长反作弊复盘 | 覆盖：黑产/低质/站外投放 |

### traffic_anti_cheating_expert_skill

| Case | 主控 Skill | 辅助 Skill | 触发原因 | 覆盖结论 |
|---|---|---|---|---|
| AC-008 | traffic_anti_cheating_expert_skill | business_domain_map_skill | 刷粉刷赞刷播放通用体系 | 覆盖：指标可信和通用评估 |
| AC-009 | traffic_anti_cheating_expert_skill | risk_governance_design_skill | DAU/DNU SLA 和口径稳定 | 覆盖：SLA、口径、查杀 |
| AC-013 | traffic_anti_cheating_expert_skill | group_control_expert_skill, protocol_attack_expert_skill, real_user_crowdsourcing_skill | 内容点赞/关注质量异常 | 覆盖：手法分型 |
| AC-012 | anti_crawler_expert_skill | traffic_anti_cheating_expert_skill, evidence_decomposition_skill | 黑市报价作为反爬效果指标 | 覆盖：外部价格与内部水位 |
| ACT-003 | activity_anti_cheating_expert_skill | traffic_anti_cheating_expert_skill | 渠道抢量也影响投放流量可信 | 覆盖：点击欺诈和归因质量 |
| AC-015 | anti_crawler_expert_skill | traffic_anti_cheating_expert_skill, material_delivery_skill | 反爬水位业务存在感弱 | 覆盖：业务价值表达 |

## 3. must_have / must_not 覆盖结论

- 6 个核心 Skill 均至少绑定 5 个 case。
- group_control_expert_skill 覆盖“只有高频/聚集不得定群控”的 must_not。
- protocol_attack_expert_skill 覆盖“不得因为高频请求直接判断协议”的 must_not。
- anti_crawler_expert_skill 覆盖“反爬不等于协议”和“不能只讲接口防护”的 must_not。
- account_security_expert_skill 覆盖“账号安全不是登录拦截”和“不能牺牲体验”的 must_not。
- activity_anti_cheating_expert_skill 覆盖“低质不等于黑产”和“不能只拦截不评估”的 must_not。
- traffic_anti_cheating_expert_skill 覆盖“不能只封禁，不考虑数据口径和业务使用”的 must_not。

## 4. 仍需继续修复

- real_user_crowdsourcing_skill、cracked_app_expert_skill、traffic_diversion_interception_skill 仍在 v2.2 backlog 中，未纳入本轮 6 个核心 Skill。
- 工具规划类 case 仍缺真实表名、字段、权限和审计边界，本轮不编造字段。
- 流量反作弊 case 数只有 3 个，traffic_anti_cheating_expert_skill 需要借反爬、活动、渠道 case 做辅助验证。
