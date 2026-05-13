# 账号安全 测试案例


## AS-001｜盗号-token泄露

**问题：** 怀疑一批账号不是重新登录被盗，而是 token 泄露后被黑产直接复用。如何判断、补证和治理？

**黑产/风险本质：** 黑产绕过登录环节，复用存量登录态完成下游作恶，核心是 token 与设备/环境/行为链冲突。

**期望触发 Skill：**
- account_security_expert_skill
- credential_stuffing_ato_skill
- evidence_decomposition_skill
- risk_governance_design_skill

**必须覆盖：**
- token 与设备/IP/地理/UA 冲突
- 登录态与下游行为突变
- 风险 token 柔性踢出
- 下游扩散限制
- 快速找回/解封
- 误伤和体验控制

**不能出现：**
- 直接要求全量踢出所有 token
- 只说加强登录风控
- 把 token 泄露简单等同撞库

**交付类型：** risk_answer  
**难度：** hard


## AS-002｜欺诈盗号

**问题：** 用户被诱导扫码/人脸/验证码，黑产绕过平台限制完成盗号，如何还原链路和治理？

**黑产/风险本质：** 黑产利用号主本人完成关键验证，平台看到的是本人动作，但意图被外部操控。

**期望触发 Skill：**
- account_security_expert_skill
- risk_chain_reconstruction_skill
- evidence_decomposition_skill

**必须覆盖：**
- 号主本人参与但非真实意愿
- 站外诱导链路
- 验证状态流转
- 下游扩散
- 用户教育
- Step-up/授权验证

**不能出现：**
- 把所有本人验证都当安全
- 只拦扫码不处理下游扩散

**交付类型：** risk_answer  
**难度：** hard


## AS-003｜撞库/ATO

**问题：** 登录失败量和成功登录量同时上升，如何判断是不是撞库导致 ATO？

**黑产/风险本质：** 泄漏凭证批量测试，成功后账号被接管并进入下游作恶。

**期望触发 Skill：**
- credential_stuffing_ato_skill
- account_security_expert_skill
- evidence_decomposition_skill

**必须覆盖：**
- 失败/成功序列
- 同 IP/代理多账号尝试
- 成功后行为突变
- 条件 MFA/Step-up
- 速率限制
- 泄漏凭证库

**不能出现：**
- 把撞库等同密码爆破
- 只看失败次数不看成功后行为

**交付类型：** risk_answer  
**难度：** medium


## AS-004｜机器小号

**问题：** 注册小号发生量下降但活跃/回扫阶段仍有大量黑产号，账号安全怎么从注册扩到全链路？

**黑产/风险本质：** 黑产不只在注册作恶，存量小号会在登录、活跃、回扫、任务、交易中复用。

**期望触发 Skill：**
- account_security_expert_skill
- business_domain_map_skill
- risk_governance_design_skill

**必须覆盖：**
- 注册+登录+token刷新+活跃+回扫
- 存量小号回捞
- 黑市报价/发生量/漏过量
- 账号安全分
- 分层治理

**不能出现：**
- 只优化注册策略
- 只封新号不管存量

**交付类型：** plan  
**难度：** medium


## AS-005｜二次放号

**问题：** 二次放号场景如何在满足监管要求基础上降低风险和体验损伤？

**黑产/风险本质：** 老号主和新号主权益冲突，既要合规解绑，又要防止旧身份资产造成风险。

**期望触发 Skill：**
- account_security_expert_skill
- risk_governance_design_skill

**必须覆盖：**
- 发生前提醒
- 发生后解绑
- 快速找回
- 客诉量
- 新旧号主体验
- 监管边界

**不能出现：**
- 只站平台安全视角
- 强行阻断正常换号

**交付类型：** risk_answer  
**难度：** medium


## AS-006｜交易号

**问题：** 如何识别养号后交易给黑灰产的交易号，并阻断下游作恶？

**黑产/风险本质：** 账号像商品一样被养成、交易、换绑并进入欺诈/导流/刷量等下游。

**期望触发 Skill：**
- account_security_expert_skill
- risk_chain_reconstruction_skill

**必须覆盖：**
- 画风突变
- 登录环境突变
- 交易链路
- 下游行为
- 社交封禁/强实名/限权
- 关系网络

**不能出现：**
- 只看注册风险
- 只看单账号不看交易链

**交付类型：** risk_answer  
**难度：** medium


## AS-007｜登录接口合法自动化

**问题：** 商家和黑产都会捅接口登录，现有策略对商家站点登录豁免，如何设计更合理方案？

**黑产/风险本质：** 合法自动化需求与黑产接口滥用混在一起，需要白化通道+非法收紧。

**期望触发 Skill：**
- account_security_expert_skill
- protocol_attack_expert_skill
- risk_governance_design_skill

**必须覆盖：**
- 官方工具/授权登记
- 调用范围绑定
- 非授权接口收紧
- 高风险动作验证
- 审计
- 业务合理性

**不能出现：**
- 一刀切拦截商家
- 继续无条件豁免

**交付类型：** plan  
**难度：** hard


## AS-008｜可信体系

**问题：** 登录风控误伤高，如何用可信体系平衡安全和体验？

**黑产/风险本质：** 通过可信环境/可信用户/可信设备降低正常号主打扰，集中火力打高危风险。

**期望触发 Skill：**
- account_security_expert_skill
- risk_governance_design_skill

**必须覆盖：**
- 可信环境
- 账号价值
- 风险类型
- 决策体系
- 登录打扰率
- 验证量下降

**不能出现：**
- 只提高阈值
- 只讲风控拦截

**交付类型：** plan  
**难度：** medium


## AS-009｜验无可验

**问题：** 大量高风险登录没有合适验证方式，如何建设验证体系？

**黑产/风险本质：** 风险识别有结论但缺少可用验证手段，导致只能放过或重伤体验。

**期望触发 Skill：**
- account_security_expert_skill
- risk_governance_design_skill

**必须覆盖：**
- 验证覆盖率
- 特色验证
- 授权验证
- 兜底验证
- Step-up
- 体验/通过率

**不能出现：**
- 默认所有风险都强拦
- 忽略用户体验

**交付类型：** plan  
**难度：** medium


## AS-010｜账号安全年度述职

**问题：** 帮我把账号安全方向整理成年度述职材料，突出历史负债、盗号、小号、token、验证和下一步。

**黑产/风险本质：** 材料交付要求体现从还债到体系化治理，不能只是列工作。

**期望触发 Skill：**
- material_delivery_skill
- account_security_expert_skill
- executive_summary_skill

**必须覆盖：**
- 业务情况
- 核心思考
- 策略打法
- 核心进展+一句话总结
- 做得好的/可提升的
- 下一步方向

**不能出现：**
- 流水账
- 没有指标
- 没有问题反思

**交付类型：** material  
**难度：** hard
