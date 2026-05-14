# v2.3 20 个混合攻击 Case 回归

## 评分口径

本轮目标是验证混合攻击下的主控路由、证据降级、反证和误伤控制，不因格式完整给高分。

- 90+：主控稳定、混合手法拆分清楚、有反证和降级。
- 85-89：可用，但依赖补证或存在轻微主控摇摆。
- 80-84：边界可识别，但需要 Skill 或契约补强。
- <80：容易误判或过度自信，需要回写。

## Case 矩阵

| Case | 混合攻击输入 | 主控 Skill | 辅助 Skill | 易错点 | 期望稳定判断 | 分数 |
|---|---|---|---|---|---|---:|
| MIX-001 | 活动红包领取：有真实端行为，设备路径高度一致，领奖接口后段疑似接口化 | activity_anti_cheating_expert_skill | group_control, protocol | 只按协议打，忽略活动收益链 | 活动主控，拆成群控前置 + 协议领奖后段，补收益闭环 | 89 |
| MIX-002 | 外网跟价：部分账号真实访问，部分接口无端链路，另有合作方缓存 | anti_crawler_expert_skill | protocol, group_control | 直接判协议 | 价格资产主控，按协议/群控/合作方缓存多分支溯源 | 90 |
| MIX-003 | 直播间用户被站外添加：账号矩阵私信，同时部分粉丝列表访问高频 | traffic_diversion_interception_skill | group_control, anti_crawler | 误归反爬 | 导流截流主控；只有批量关系链获取闭合才组合反爬 | 90 |
| MIX-004 | DAU 暴涨：新版本埋点变更，同时有少量低质账号刷启动 | traffic_anti_cheating_expert_skill | evidence, group_control | 直接剔除 DAU | 口径/SLA 主控；攻击证据不足先双轨口径和 diff | 89 |
| MIX-005 | 商家工具批量登录，同时个别敏感动作异常 | account_security_expert_skill | protocol, governance | 一刀切拦截商家 | 合法自动化审计主控；敏感动作 step-up，非授权接口收紧 | 91 |
| MIX-006 | 大量真人完成同一拉新任务，设备离散，奖励提现有小规模聚集 | real_user_crowdsourcing_skill | activity | 判自然用户或群控 | 真人众包嫌疑；补任务平台、教程、收益链，低准延迟结算 | 90 |
| MIX-007 | 内容点赞异常：设备离散、站外任务教程明确、部分账号后续接口化点赞 | traffic_anti_cheating_expert_skill | real_user_crowdsourcing, protocol | 只判真人众包或协议 | 流量主控，拆真人众包前置 + 协议化后段，做数据矫正 | 88 |
| MIX-008 | 账号无登录但 token 跨环境调用私信接口，私信内容导流站外 | account_security_expert_skill | protocol, diversion | 只治理私信导流 | 账号安全主控，token 泄露/复用 + 导流扩散，先踢风险 token 和限敏感动作 | 90 |
| MIX-009 | 群控真机爬关系链后站外添加用户 | traffic_diversion_interception_skill | group_control, anti_crawler | 只按群控或反爬 | 若核心损伤是站外承接，导流主控；补关系链批量获取后组合反爬/群控 | 86 |
| MIX-010 | 破解包绕 SDK 导致前端无日志，服务端强目标接口直达 | protocol_attack_expert_skill | cracked_app | 把破解包采集缺失当单纯协议 | 协议/破解包多分支；先证明包签名/SDK/hook，再定混合协议 | 84 |
| MIX-011 | 渠道买量 RTA 抢量，同时低质用户参与活动领奖 | activity_anti_cheating_expert_skill | traffic_anti_cheating | 把低质用户当黑产 | 活动/渠道主控，拆归因抢量与后验低质，先沙盒评估和结算扣除 | 88 |
| MIX-012 | 旧版本弱端未登录价格接口泄漏，外部竞品同步，账号访问频率不高 | anti_crawler_expert_skill | protocol | 因低频忽略风险 | 反爬主控，弱端/未登录态资产泄漏，频率不是必要条件 | 91 |
| MIX-013 | 活动规则漏洞被普通用户大规模利用，无群控/协议证据 | activity_anti_cheating_expert_skill | governance | 把普通用户套利当黑产 | 规则漏洞主控，产品机制修复和收益上限，不默认封禁 | 90 |
| MIX-014 | 私信导流账号疑似交易号：登录环境突变后开始批量私信 | account_security_expert_skill | diversion | 只按导流封私信 | 账号安全主控，交易号/盗号后导流扩散，补登录环境和下游行为 | 88 |
| MIX-015 | 直播人气异常：主播活动预告带来自然流量，同时站外刷人气报价出现 | traffic_anti_cheating_expert_skill | real_user_crowdsourcing | 把热点直接判刷量 | 流量主控，中置信；必须补质量、站外任务与账号设备关系 | 87 |
| MIX-016 | 核心内容盗版站同步，内部访问看似真人低频，多地设备离散 | anti_crawler_expert_skill | real_user_crowdsourcing | 因真人低频放过 | 反爬主控，真人众包采集候选，补水印/蜜罐/外部同步时延 | 88 |
| MIX-017 | 账号小号参与活动领奖，又参与刷赞刷播放 | account_security_expert_skill | activity, traffic | 活动和流量各打各的 | 账号生命周期主控，存量小号跨场景复用，活动/流量做下游证据 | 86 |
| MIX-018 | 合法 MCN 矩阵批量运营账号，同时有少量导流话术违规 | traffic_diversion_interception_skill | account, governance | 把 MCN 矩阵当黑产群控 | 导流主控处理违规触达；合法矩阵走授权审计，不一刀切封矩阵 | 85 |
| MIX-019 | 站外任务平台组织真人搜索用户昵称并添加微信 | traffic_diversion_interception_skill | real_user_crowdsourcing | 只按真人众包，忽略信息暴露 | 导流主控 + 真人众包辅助，补目标获取、搜索触达、站外承接和任务收益 | 90 |
| MIX-020 | 服务端接口高频、IP 聚集、但同时业务上线新推荐策略 | evidence_decomposition_skill | protocol, traffic | 高频直接判协议/刷量 | 弱信号主控，先排推荐策略和口径变化，只监控加采 | 89 |

平均分：88.5/100。

## 主要观察

1. 主控路由总体稳定  
领域损伤明确时，主控能优先落在业务领域：活动资损归活动、资产泄漏归反爬、指标污染归流量、站外承接归导流、账号接管归账号安全。

2. 混合手法拆分能力可用  
多数 case 能拆成“前置手法 + 后段变现/扩散”，例如群控前置 + 协议领奖、token 复用 + 私信导流、真人众包 + 协议化点赞。

3. 低分集中在未完全 v2.3 化或辅助薄弱 Skill  
MIX-010 依赖 cracked_app_expert_skill，MIX-017 依赖账号生命周期跨活动/流量复用，MIX-018 依赖合法矩阵/MCN 运营边界。

4. 证据不足降级整体有效  
高频、低质、前端无日志、指标异常、外网报价、站外添加等弱信号没有直接触发强结论。

## 暴露的主要问题

### 1. cracked_app_expert_skill 需要升级

MIX-010 暴露：破解包绕 SDK 会让协议 Skill 看到“前端无日志”，但本质可能是客户端完整性问题。当前 protocol 已能降级，但 cracked_app 需要成为更强的承接 Skill。

建议补：
- 包签名、SDK 缺失、hook/root、抓包代理、运行环境异常；
- 破解包 vs 协议 vs 群控边界；
- “像协议但其实是采集被绕”的判断规则；
- 客户端完整性治理、灰度、误伤和版本兼容。

### 2. credential_stuffing_ato_skill 仍需独立强测

本轮账号 case 更多覆盖 token、交易号、合法自动化。撞库/ATO 的登录失败/成功序列、代理多账号尝试、成功后行为突变还没有做 20 case 同等级压测。

建议补：
- 撞库 vs 密码爆破 vs 正常登录失败；
- ATO 后下游行为突变；
- 被攻击账号库、泄漏凭证库、条件 MFA；
- 安全体验和登录打扰率。

### 3. 合法矩阵 / MCN / 商家运营边界需要更细

MIX-018 暴露：合法矩阵和黑产群控、导流违规会混在一起。当前执行契约和 account 已补授权矩阵，但缺一套统一的“合法矩阵治理 playbook”。

建议补：
- 授权主体、工具、账号范围、操作人、调用接口、敏感动作；
- 合法矩阵内违规账号的局部处置；
- 不因矩阵身份豁免导流/欺诈；
- 不因批量运营默认黑产。

### 4. 账号生命周期跨场景复用还可加强

MIX-017 暴露：小号可能先活动套利，再刷量，再导流/爬取。当前 account 能做全链路，但缺跨业务复用的策略树。

建议补：
- 注册、登录、活跃、回扫、任务、刷量、导流、交易的统一账号风险分；
- 账号风险标签如何被活动/流量/导流消费；
- 风险回流和误伤隔离。

### 5. 真实数据落地仍是最大短板

多数 case 都能说清“查什么”，但缺字段级模板：
- 前后端 join 字段；
- token 签发/刷新/踢出链路字段；
- 搜索/私信/站外承接链路字段；
- DAU/DNU 口径 diff 字段；
- 活动发奖/提现/后验质量字段。

## 下一步改进建议

### P0：升级 cracked_app_expert_skill

原因：它是 protocol 误判的重要反证承接，当前混合攻击下最容易造成“前端无日志 = 协议”的错误归因。

目标：
- 升级为 v2.3 executable-deep；
- 补判断规则、证据体系、反证、治理闭环；
- 专门覆盖破解包绕 SDK、改包、hook/root、抓包代理、客户端完整性。

### P0：补合法矩阵治理 playbook

原因：商家、达人、MCN、客服工具、ISV 与黑产批量运营表象相似，误伤业务损伤大。

目标：
- 可放在 account_security 或独立 business_domain_map / governance 小节；
- 明确授权登记、调用范围、账号边界、敏感动作、审计、灰度、违规局部处置。

### P1：做账号生命周期跨场景策略树

原因：小号/交易号会跨活动、流量、导流、反爬复用，单领域治理容易烟囱化。

目标：
- 输出账号全链路策略树；
- 定义账号风险分如何被各业务消费；
- 明确误伤隔离和标签回流。

### P1：补 5 类字段级查数模板

优先模板：
1. 协议前后端 join；
2. token 复用链路；
3. 导流截流链路；
4. DAU/DNU 口径 diff；
5. 活动收益/后验质量。

### P2：建立自动化回归 lint

检查每个 case 输出是否包含：
- 主控 / 辅助 Skill；
- 强/中/弱证据；
- 反证；
- 当前最多能下什么结论；
- 降级策略；
- 业务损伤；
- 是否需要回写。

## 总体结论

20 个混合攻击 case 下，v2.3 当前平均 88.5/100，已经可用于复杂风险研判和评审辅助。下一步不建议继续大面积改所有 Skill，而是优先补三个高价值缺口：cracked_app 承接、合法矩阵 playbook、账号跨场景生命周期策略树。
