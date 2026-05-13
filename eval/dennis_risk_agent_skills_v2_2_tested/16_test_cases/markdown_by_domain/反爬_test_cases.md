# 反爬 测试案例


## AC-001｜外网跟价

**问题：** 外网实时跟价我们产品，但内部没发现明显攻击。如何定位外网是怎么拿到价格的？

**黑产/风险本质：** 核心资产被外部低成本获取，可能是协议、群控、真人、缓存、合作方或内部泄漏。

**期望触发 Skill：**
- anti_crawler_expert_skill
- risk_chain_reconstruction_skill
- evidence_decomposition_skill
- attack_type_classification_skill

**必须覆盖：**
- 资产分级
- 泄漏入口
- 协议/群控/真人/合作方/缓存/内部
- 外部报价/同步延迟
- 补证动作

**不能出现：**
- 直接断定协议攻击
- 只看接口频率

**交付类型：** risk_answer  
**难度：** hard


## AC-002｜版权内容泄漏

**问题：** 版权内容被竞品拿到，后端流量都是真人访问，但用户没有前端操作，可能是什么路径？

**黑产/风险本质：** 真人/端行为/服务端日志出现矛盾，可能是破解包、协议后拉、埋点缺失、授权后脚本化。

**期望触发 Skill：**
- anti_crawler_expert_skill
- attack_type_classification_skill
- cracked_app_expert_skill
- real_user_crowdsourcing_skill

**必须覆盖：**
- 解释真人访问和无前端操作矛盾
- 端日志/SDK/埋点补证
- 破解包/协议/真人众包/口径差异
- 版权资产保护

**不能出现：**
- 因为是真人就放过
- 直接认定协议

**交付类型：** risk_answer  
**难度：** hard


## AC-003｜单纯协议判定

**问题：** 如何明确一个攻击是单纯协议类攻击，而不是群控、破解包或真人众包？

**黑产/风险本质：** 必须证明请求脱离端侧执行链，同时排除端行为缺失的其他原因。

**期望触发 Skill：**
- protocol_attack_expert_skill
- attack_type_classification_skill
- evidence_decomposition_skill

**必须覆盖：**
- 无端行为
- 接口序列异常
- 签名/token/设备冲突
- 排除群控/破解包/埋点缺失
- 补证动作

**不能出现：**
- 只有高频就判协议
- 不做排除项

**交付类型：** risk_answer  
**难度：** hard


## AC-004｜群控真机爬取

**问题：** 核心资产访问看起来都有真实设备和端行为，但目标高度一致，如何判断是不是群控真机爬取？

**黑产/风险本质：** 真机/端行为存在不代表安全，关键看是否被统一调度完成资产访问。

**期望触发 Skill：**
- group_control_expert_skill
- anti_crawler_expert_skill
- evidence_decomposition_skill

**必须覆盖：**
- 统一调度
- 设备团组
- 访问路径一致
- 资产命中
- 收益/目标一致
- 协议反证

**不能出现：**
- 有端行为就判正常
- 只按协议治理

**交付类型：** risk_answer  
**难度：** hard


## AC-005｜破解包反爬

**问题：** 怀疑破解包绕过 SDK 采集爬核心资产，如何确认和治理？

**黑产/风险本质：** 客户端被改造导致端侧证据缺失或采集失真，进而低成本获取资产。

**期望触发 Skill：**
- cracked_app_expert_skill
- anti_crawler_expert_skill
- evidence_decomposition_skill

**必须覆盖：**
- 包签名/版本/渠道异常
- SDK日志缺失
- 关键接口上下文
- 强制升级/完整性校验
- 样本库

**不能出现：**
- 只看服务端请求
- 忽略端包证据

**交付类型：** risk_answer  
**难度：** medium


## AC-006｜6+1飞轮

**问题：** 如何把一个反爬专项从单点策略升级成“非常6+1”体系？

**黑产/风险本质：** 从策略对抗升级到未接漏洞、产品改造、实时发现、处置、评估和引擎体系。

**期望触发 Skill：**
- anti_crawler_expert_skill
- business_domain_map_skill
- material_delivery_skill

**必须覆盖：**
- 未接漏洞
- 产品改造
- 实时发现
- 策略对抗
- 风险处置
- 水位评估
- 引擎

**不能出现：**
- 只罗列接口策略
- 没有评估指标

**交付类型：** plan  
**难度：** medium


## AC-007｜资产分级

**问题：** 高价值/中价值/低价值资产如何分级治理？

**黑产/风险本质：** 不同资产价值不同，治理态度不同，不能全量强防造成业务成本过高。

**期望触发 Skill：**
- anti_crawler_expert_skill
- business_domain_map_skill

**必须覆盖：**
- 价格/库存/版权/关系链/普通页面
- 治理态度
- 观测指标
- 轻重边界

**不能出现：**
- 所有资产同等防护
- 没有成本收益

**交付类型：** plan  
**难度：** medium


## AC-010｜未登录态爬取

**问题：** 未登录态接口能拿到核心内容，如何治理？

**黑产/风险本质：** 弱端/无登录态入口降低资产获取成本，是反爬未接漏洞和产品改造问题。

**期望触发 Skill：**
- anti_crawler_expert_skill
- protocol_attack_expert_skill
- risk_governance_design_skill

**必须覆盖：**
- 未接漏洞
- 弱端入口
- 登录/权限门槛
- 字段最小化
- 敏感接口接入风控

**不能出现：**
- 只加频控
- 不改产品入口

**交付类型：** risk_answer  
**难度：** medium


## AC-011｜真人众包爬取

**问题：** 如果爬取流量都是真人完成，怎么防？

**黑产/风险本质：** 真人执行不代表正常，背后可能被任务化组织，治理要抬收益成本而不是只技术拦截。

**期望触发 Skill：**
- real_user_crowdsourcing_skill
- anti_crawler_expert_skill

**必须覆盖：**
- 任务化组织
- 收益链路
- 低价值行为
- 任务随机化
- 后验质量
- 外部情报

**不能出现：**
- 真人就不治理
- 按协议处理

**交付类型：** risk_answer  
**难度：** medium


## AC-012｜外部黑市报价

**问题：** 黑市报价从很低涨到很高，如何作为反爬效果指标使用？

**黑产/风险本质：** 外部价格体现黑产成本和供需，但需结合内部水位和漏出验证。

**期望触发 Skill：**
- anti_crawler_expert_skill
- evidence_decomposition_skill

**必须覆盖：**
- 报价作为外部指标
- 内部TOP请求账号量
- 投诉/漏出
- 供需变化反证
- 不能单独证明

**不能出现：**
- 只看报价就认定成功
- 忽略样本偏差

**交付类型：** risk_answer  
**难度：** medium


## AC-014｜版权诉讼支撑

**问题：** 版权反爬如何同时支撑防控、溯源、内容清理和法律诉讼？

**黑产/风险本质：** 版权反爬不是只拦爬虫，还要形成取证和诉讼支撑能力。

**期望触发 Skill：**
- anti_crawler_expert_skill
- material_delivery_skill

**必须覆盖：**
- 防控+溯源
- 取证召回/准确率
- 内容清理
- 案件素材
- 投诉指标
- 法务协同

**不能出现：**
- 只讲技术防护
- 不讲取证和诉讼

**交付类型：** material  
**难度：** medium


## AC-015｜反爬业务存在感弱

**问题：** 反爬水位提升但业务价值存在感弱，如何汇报和规划下一步？

**黑产/风险本质：** 技术水位不等于业务价值，需要把资产保护、投诉、报价、诉讼、业务反馈串起来。

**期望触发 Skill：**
- anti_crawler_expert_skill
- executive_summary_skill
- material_delivery_skill

**必须覆盖：**
- 业务情况
- 核心思考
- 资产保护价值
- 核心指标
- 做得好/可提升
- 下一步方向

**不能出现：**
- 只讲策略命中
- 没有业务价值

**交付类型：** material  
**难度：** hard
