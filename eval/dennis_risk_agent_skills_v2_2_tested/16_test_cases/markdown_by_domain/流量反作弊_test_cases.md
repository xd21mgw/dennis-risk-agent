# 流量反作弊 测试案例


## AC-008｜刷粉刷赞刷播放

**问题：** 刷粉/刷赞/刷播放/刷人气如何建立通用评估体系，而不是每个场景单独打？

**黑产/风险本质：** 流量作弊本质影响指标可信和流量分配公平，应沉淀跨场景评估和柔性处置。

**期望触发 Skill：**
- traffic_anti_cheating_expert_skill
- business_domain_map_skill

**必须覆盖：**
- 站外价格
- 漏出量
- 质量指标
- 标准化+场景化
- 柔性处置
- 数据矫正

**不能出现：**
- 只封账号
- 忽略指标口径

**交付类型：** plan  
**难度：** medium


## AC-009｜DAU口径作弊

**问题：** DAU/DNU 反作弊需要 SLA 保障，如何设计查杀和口径稳定机制？

**黑产/风险本质：** 业务决策依赖口径，风控要保证稳定识别且不误伤业务判断。

**期望触发 Skill：**
- traffic_anti_cheating_expert_skill
- risk_governance_design_skill

**必须覆盖：**
- SLA
- 阻断/监控/告警/应急/修复
- 实时离线diff
- 准确率/召回率
- 任务产出时间

**不能出现：**
- 只关注查杀
- 不关注口径稳定

**交付类型：** plan  
**难度：** medium


## AC-013｜内容互动刷量

**问题：** 有内容点赞/关注质量异常，如何区分真人众包、群控、协议刷量？

**黑产/风险本质：** 同一业务结果可能由不同手法造成，需要先判手法再治理。

**期望触发 Skill：**
- traffic_anti_cheating_expert_skill
- attack_type_classification_skill
- group_control_expert_skill
- protocol_attack_expert_skill
- real_user_crowdsourcing_skill

**必须覆盖：**
- 手法分类
- 站内质量
- 行为链
- 设备团组
- 任务化真人
- 柔性处置

**不能出现：**
- 只看结果异常
- 全部封禁

**交付类型：** risk_answer  
**难度：** hard
