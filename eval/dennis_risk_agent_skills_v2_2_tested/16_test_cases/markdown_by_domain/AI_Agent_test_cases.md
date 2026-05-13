# AI Agent 测试案例


## AG-001｜风控RAG问答

**问题：** 风控 RAG 助手回答风险问题时，如何避免编造结论？

**黑产/风险本质：** RAG 管检索和引用，风险 Skill 管专业判断，证据不足必须显式降级。

**期望触发 Skill：**
- risk_rag_answering_skill
- evidence_decomposition_skill
- ai_agent_orchestration_skill

**必须覆盖：**
- 引用依据
- 确定/推测/不足
- 下一步查证
- Skill路由
- 不编造

**不能出现：**
- 检索到一句就强结论
- 不标注不确定性

**交付类型：** plan  
**难度：** medium


## AG-002｜策略算法化

**问题：** 历史策略命中作为标签，如何避免模型只是复制老策略？

**黑产/风险本质：** 策略算法化要拆规则背后的风险认知，并加入人工样本、弱标签、特征和评估。

**期望触发 Skill：**
- strategy_to_model_distillation_skill
- evidence_decomposition_skill

**必须覆盖：**
- 规则拆解
- 标签偏差
- 特征设计
- 人工复核
- 灰度评估
- 蒸馏

**不能出现：**
- 直接用策略命中训练上线
- 不评估偏差

**交付类型：** plan  
**难度：** hard


## AG-003｜Agent工具规划

**问题：** 未来 AI 风控 Agent 想读用户画像、设备画像、行为日志，工具规划怎么做？

**黑产/风险本质：** Agent 需要工具化读数和证据链，而不是只聊天。

**期望触发 Skill：**
- tool_call_planning_skill
- ai_agent_orchestration_skill

**必须覆盖：**
- 用户画像
- 设备画像
- 行为日志
- 接口日志
- 关系网络
- 支付/提现
- 权限和审计

**不能出现：**
- 只做自然语言问答
- 没有工具边界

**交付类型：** plan  
**难度：** medium
