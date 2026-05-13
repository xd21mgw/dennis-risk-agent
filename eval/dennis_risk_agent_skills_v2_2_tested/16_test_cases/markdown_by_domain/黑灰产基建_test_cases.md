# 黑灰产基建 测试案例


## BI-001｜协议降发生

**问题：** 协议发生量下降但养设备协议变多，如何做认知迭代和下一步？

**黑产/风险本质：** 黑产从低成本纯协议迁移到更接近端行为的养设备协议，需要升级证据和策略。

**期望触发 Skill：**
- protocol_attack_expert_skill
- anti_crawler_expert_skill
- material_delivery_skill

**必须覆盖：**
- 纯协议 vs 养设备协议
- 迁移路径
- 前后端冲突
- 强目的接口
- 下一步策略

**不能出现：**
- 只庆祝发生量下降
- 不看迁移

**交付类型：** material  
**难度：** medium


## BI-002｜小号通用能力

**问题：** 黑产小号只在注册场景有策略，如何扩成通用基建？

**黑产/风险本质：** 小号资源贯穿注册、登录、活跃、任务、交易和回扫，不能只在注册打。

**期望触发 Skill：**
- account_security_expert_skill
- business_domain_map_skill

**必须覆盖：**
- 授权号/接码号/转生号/双参号
- 注册+登录+活跃+回扫
- 标签库
- 业务复用

**不能出现：**
- 只做注册拦截
- 不做全链路

**交付类型：** plan  
**难度：** medium


## BI-003｜设备处置

**问题：** 设备处置从无感验证、强制登录到强制升级，如何定位价值？

**黑产/风险本质：** 设备处置是连接协议、群控、设备基建和验证体系的通用治理能力。

**期望触发 Skill：**
- group_control_expert_skill
- account_security_expert_skill
- risk_governance_design_skill

**必须覆盖：**
- 无感验证
- 强制登录
- 强制升级
- 长链接下发
- 设备层处置
- 体验和发版约束

**不能出现：**
- 只当单点处罚
- 不讲通用基建价值

**交付类型：** plan  
**难度：** medium


## BI-004｜设备同步上报

**问题：** 实时指纹同步上报为什么重要，如何和网络库/风控联动？

**黑产/风险本质：** 端侧设备数据时效是准实时防控基础，影响协议、群控、反爬、账号。

**期望触发 Skill：**
- account_security_expert_skill
- anti_crawler_expert_skill
- tool_call_planning_skill

**必须覆盖：**
- 统一网络库
- 拦截器
- 设备指纹
- 端云联动
- 实时/准实时
- 接口覆盖

**不能出现：**
- 只讲采集字段
- 不讲防控闭环

**交付类型：** plan  
**难度：** medium


## BI-005｜插件能力复用

**问题：** 风险 APP 取证如何服务活动、爬虫、注册等多个场景？

**黑产/风险本质：** 逆向取证不是孤立能力，应反哺风险认知、特征、策略和样本库。

**期望触发 Skill：**
- plugin_reverse_analysis_skill
- material_delivery_skill

**必须覆盖：**
- 情报还原
- 攻击路径
- 可复用特征
- 多场景复用
- 证据完整度

**不能出现：**
- 只做逆向报告
- 不回流策略

**交付类型：** plan  
**难度：** medium


## BI-006｜黑产产业链

**问题：** 一个风险 case 如何拆作恶方、上游资源、中游执行、下游变现？

**黑产/风险本质：** 黑产本质是资源、工具、任务、收益的产业链协作。

**期望触发 Skill：**
- risk_chain_reconstruction_skill
- evidence_decomposition_skill
- risk_governance_design_skill

**必须覆盖：**
- 上游账号/设备/IP/工具
- 中游接单/群控/任务平台
- 下游导流/套利/诈骗
- 治理断点

**不能出现：**
- 只看单账号异常
- 不讲收益链路

**交付类型：** risk_answer  
**难度：** medium


## BI-007｜业务安全监控

**问题：** 如何建立黑灰产通用监控，而不是等业务反馈？

**黑产/风险本质：** 从被动问题驱动变成主动发现，需要业务监控、外部情报、异常检测、看板运营。

**期望触发 Skill：**
- business_domain_map_skill
- risk_governance_design_skill
- material_delivery_skill

**必须覆盖：**
- 业务监控
- 外部情报
- 异常检测
- 客诉举报
- 监控运营
- 告警接手

**不能出现：**
- 只做离线报表
- 没有运营机制

**交付类型：** plan  
**难度：** medium


## BI-008｜专家材料复盘

**问题：** 把协议、群控、小号、插件四类黑灰产基建写成述职材料，怎么组织？

**黑产/风险本质：** 材料要体现通能能力沉淀、业务复用、指标进展和短板，不是列标签。

**期望触发 Skill：**
- material_delivery_skill
- executive_summary_skill
- protocol_attack_expert_skill
- group_control_expert_skill
- account_security_expert_skill
- plugin_reverse_analysis_skill

**必须覆盖：**
- 核心进展+一句话总结+策略打法
- 协议/群控/小号/插件
- 做得好/可提升
- 下一步方向

**不能出现：**
- 只列项目名
- 没有认知迭代

**交付类型：** material  
**难度：** hard
