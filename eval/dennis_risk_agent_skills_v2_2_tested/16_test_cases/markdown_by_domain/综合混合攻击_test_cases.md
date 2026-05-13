# 综合混合攻击 测试案例


## MIX-001｜直播间截流+账号搜索+私信导流

**问题：** 直播间公开展示/口播用户信息后，黑产搜索用户 ID 定向添加并私信导流，怎么还原证据链和治理？

**黑产/风险本质：** 公开信息暴露被结构化利用，黑产通过人工/半自动搜索目标、触达并站外承接。

**期望触发 Skill：**
- traffic_diversion_interception_skill
- risk_chain_reconstruction_skill
- evidence_decomposition_skill
- account_security_expert_skill

**必须覆盖：**
- 信息暴露入口
- 目标获取
- 搜索手误/时间相关
- 关注/私信承接
- 站外导流
- 脱敏/搜索限制/私信风控/主播教育

**不能出现：**
- 当成反爬
- 只封单个账号不治理暴露入口

**交付类型：** risk_answer  
**难度：** hard
