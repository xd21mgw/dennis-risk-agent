# 活动反作弊 测试案例


## ACT-001｜黑产假量

**问题：** 裂变活动资损率高，怀疑黑产假量，如何建立查杀分离能力？

**黑产/风险本质：** 黑产通过账号、设备、协议、群控、插件等批量薅奖励，查侧要独立评估，杀侧分层处置。

**期望触发 Skill：**
- activity_anti_cheating_expert_skill
- group_control_expert_skill
- protocol_attack_expert_skill
- risk_governance_design_skill

**必须覆盖：**
- 查杀分离
- 资损率
- 账号/设备/行为/收益链路
- 高准/中准/低准
- 误伤/客诉

**不能出现：**
- 只堆拦截策略
- 没有评估

**交付类型：** plan  
**难度：** hard


## ACT-002｜低质真人

**问题：** 活动低钱效用户很多，但未必是黑产，如何治理？

**黑产/风险本质：** 低质风险不等于黑产，需要监控赋能业务而非全部打击。

**期望触发 Skill：**
- activity_anti_cheating_expert_skill
- evidence_decomposition_skill

**必须覆盖：**
- 黑产vs低质
- 业务钱效
- 留存/付费
- 监控赋能
- 活动规则优化
- 灰度

**不能出现：**
- 把低质都封禁
- 只看设备风险

**交付类型：** risk_answer  
**难度：** hard


## ACT-003｜渠道抢量

**问题：** 站外投放存在抢量作弊，只有点击数据，如何从0到1建设识别和评估？

**黑产/风险本质：** 渠道通过曝光/点击/归因链路抢量，风险识别要前置并能进入结算/归因评估。

**期望触发 Skill：**
- activity_anti_cheating_expert_skill
- traffic_anti_cheating_expert_skill

**必须覆盖：**
- 点击数据
- 抢量设备召回/准确率
- 内外双策略评估
- 自然量/付费量误伤
- 结算应用

**不能出现：**
- 没有评估直接处罚
- 只看激活

**交付类型：** plan  
**难度：** hard


## ACT-004｜口令劫持

**问题：** 口令劫持从无感助力到有感知助力，怎么治理和评估？

**黑产/风险本质：** 黑产利用产品交互和用户无感知机制获益，需要产品交互+举报证据+策略+离线处罚。

**期望触发 Skill：**
- activity_anti_cheating_expert_skill
- risk_chain_reconstruction_skill

**必须覆盖：**
- 产品交互改造
- 举报证据
- 内容/行为/意图
- 分享回流风控
- 冻结打款

**不能出现：**
- 只加策略不改产品
- 忽略用户感知

**交付类型：** risk_answer  
**难度：** medium


## ACT-005｜插件脚本活动

**问题：** 活动激励场景发现风险插件，如何判断和沉淀策略？

**黑产/风险本质：** 插件辅助自动完成任务，既要逆向证据，也要业务特征保准确。

**期望触发 Skill：**
- plugin_reverse_analysis_skill
- activity_anti_cheating_expert_skill
- evidence_decomposition_skill

**必须覆盖：**
- 插件证据
- 业务特征
- 设备风险保召回
- 场景内增量拦截
- 样本库

**不能出现：**
- 只有逆向没有业务验证
- 只有业务异常没有插件证据

**交付类型：** risk_answer  
**难度：** medium


## ACT-006｜规则漏洞

**问题：** 活动规则被普通用户套利，不一定是黑产，如何处理？

**黑产/风险本质：** 平台规则设计被利用，重点是规则修复、收益限制和后验评估。

**期望触发 Skill：**
- activity_anti_cheating_expert_skill
- risk_governance_design_skill

**必须覆盖：**
- 规则漏洞
- 收益上限
- 冷却期
- 延迟结算
- 异常收益回收
- 用户体验

**不能出现：**
- 直接定义黑产
- 只靠封禁

**交付类型：** risk_answer  
**难度：** medium


## ACT-007｜直播红包群控

**问题：** 直播红包被大量群控设备抢，如何查和打？

**黑产/风险本质：** 群控设备批量参与实时权益分发，收益链路和设备团组是关键。

**期望触发 Skill：**
- activity_anti_cheating_expert_skill
- group_control_expert_skill

**必须覆盖：**
- 设备团组
- 同批启动
- 收益聚集
- 限额/延迟/验证
- 抢红包漏出量/金额

**不能出现：**
- 只按频控
- 忽略收益链路

**交付类型：** risk_answer  
**难度：** hard


## ACT-008｜活动策略体系

**问题：** 活动策略数过多、难维护，如何从打地鼠升级为结构化策略体系？

**黑产/风险本质：** 长期应急策略导致熵增，需要大问题小解、小问题根解，沉淀策略包。

**期望触发 Skill：**
- activity_anti_cheating_expert_skill
- material_delivery_skill

**必须覆盖：**
- 结构化策略体系
- 场景分类/手法分类
- 策略数压缩
- 迭代效率
- 策略包

**不能出现：**
- 只继续加规则
- 没有治理逻辑

**交付类型：** plan  
**难度：** medium


## ACT-009｜活动年度复盘

**问题：** 帮我复盘增长反作弊：黑产、真人低质、站外投放三个方向怎么讲？

**黑产/风险本质：** 需要材料级表达，不只是技术分析。

**期望触发 Skill：**
- material_delivery_skill
- activity_anti_cheating_expert_skill
- executive_summary_skill

**必须覆盖：**
- 业务情况
- 核心思考
- 站内黑产/真人低质/站外投放
- 核心进展+一句话总结
- 做得好/可提升

**不能出现：**
- 流水账
- 没有业务钱效

**交付类型：** material  
**难度：** hard


## ACT-010｜渠道结算扣除

**问题：** 渠道推广作弊已经能识别，但业务落地推广困难，如何推进？

**黑产/风险本质：** 能力建成不等于业务价值落地，需要 BP 机制、归因沙盒、误伤边界和结算策略。

**期望触发 Skill：**
- activity_anti_cheating_expert_skill
- executive_summary_skill
- risk_governance_design_skill

**必须覆盖：**
- 落地应用不足
- BP机制
- 归因沙盒
- 误伤<阈值
- 结算扣除
- 业务协同

**不能出现：**
- 只说模型准确率
- 不讲落地阻力

**交付类型：** plan  
**难度：** hard
