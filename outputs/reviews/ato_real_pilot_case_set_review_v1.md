# ATO Real Pilot Case Set Review v1

## 1. 当前判断

v2.4 第一阶段真实 Data Agent-only 只读试点建议从“协议攻击补证”切到“账号盗号 / ATO 判定”。协议攻击试点保留为第二优先级。

核心原因：这批 ATO 申诉样本已经具备 `user_id`、异常时间、申诉背景、人工备注和风险类型，满足 Data Agent 取数前的最小输入；而协议攻击首个真实 case 暴露出缺 case 标识、缺时间窗口、业务范围不清的问题，更适合作为后续补齐输入后的第二批试点。

## 2. 为什么这 6 个 Case 适合作为 ATO 第一批真实试点

- 输入充分：每个 case 都有 user_id、sample_date、suspicious_event_time、用户描述和人工备注。
- 风险链路多样：覆盖密码泄露、钓鱼欺诈、扫码欺诈、短信泄露、OAuth token 异常、会员钓鱼和不确定反例。
- 取证路径适合 Data Agent：登录、设备/IP、token/session、发布、资料变更、换绑/改密/找回、风险画像、策略命中和回扫记录，都适合先做离线数据发现。
- 边界清晰：人工备注只作为 golden hint，不作为事实；Data Agent 只输出 provider_conclusion_hint；Dennis Agent 再做 evidence-based judgement。
- 有反例：Case 006 能测试“用户申诉不等于盗号”的防过拟合能力。

## 3. 为什么暂时优先于协议攻击

协议攻击补证依赖前后端实时链路、NG 明细、SDK、设备指纹、策略引擎和授权工具排除。Data Agent-only 阶段只能覆盖离线/Hive/BI，容易停留在 evidence gap。

ATO 申诉样本的第一轮目标更贴近 Data Agent 能力：基于明确 user_id 和时间窗口，做离线登录链路、账号生命周期、风险画像、策略命中摘要和敏感动作时间链路取证。即使缺实时 provider，也能产出更可用的初步 evidence object。

## 4. 正例、链路覆盖和反例分布

| case_id | 类型 | 作用 |
|---|---|---|
| ATO_CASE_001_PASSWORD_KPN_RESWEEP | 正例，密码泄露 + 已回扫 | 验证密码登录、异常设备、发布链路、回扫记录 |
| ATO_CASE_002_PHISHING_SHOP_NO_RESWEEP | 正例倾向，钓鱼 + 未回扫 | 验证钓鱼画像和证据不足边界 |
| ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP | 正例，扫码 / OAuth / 地推 + 已回扫 | 验证扫码授权、token/session 和异地链路 |
| ATO_CASE_004_SMS_LEAK_OAUTH_TOKEN_KICK | 正例，短信泄露 + OAuth token | 验证验证码、OAuth、踢 token、资料变更 |
| ATO_CASE_005_MEMBER_PHISHING_SMS_CODE | 正例倾向，会员钓鱼 + 验证码 | 验证验证码钓鱼和违规发布链路 |
| ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE | 反例 / 不确定 | 验证不因用户申诉直接强判 |

## 5. 第一轮建议先跑哪 3 个

建议第一轮优先跑：

1. `ATO_CASE_001_PASSWORD_KPN_RESWEEP`
2. `ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP`
3. `ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE`

原因：

- Case 001：密码泄露 + 已回扫，适合正例，能验证登录方式变化、异常设备和违规发布链路。
- Case 003：扫码欺诈 + 地推，测试 OAuth / 扫码 / token / 异地链路。
- Case 006：反例 / 不确定，测试不强判和反向排除能力。

## 6. 每个 Case 的风险点和解析重点

### ATO_CASE_001_PASSWORD_KPN_RESWEEP

风险点：密码泄露、异常登录、违规发布、回扫记录。

解析重点：密码登录是否偏离历史习惯；异常设备/IP/地区是否出现；登录后是否短时间违规发布；回扫记录是否与链路一致。

### ATO_CASE_002_PHISHING_SHOP_NO_RESWEEP

风险点：钓鱼欺诈、未回扫、封禁后申诉。

解析重点：钓鱼风险画像、异常登录、封禁前行为链路；未回扫导致的证据不足边界。

### ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP

风险点：扫码欺诈、地推诱导、OAuth/token/session 异常。

解析重点：扫码或 OAuth 授权行为；异地和非常用环境；token/session 切换；地推备注不能当作事实。

### ATO_CASE_004_SMS_LEAK_OAUTH_TOKEN_KICK

风险点：短信泄露、OAuth 踢 token、资料变更。

解析重点：短信验证码链路、OAuth 授权、token/session 被踢、多端冲突、昵称头像等资料变更。

### ATO_CASE_005_MEMBER_PHISHING_SMS_CODE

风险点：会员钓鱼、短信验证码泄露、违规发布。

解析重点：验证码登录是否出现；异常登录到违规发布链路；外部会员钓鱼描述只能作为用户陈述。

### ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE

风险点：用户申诉称被盗，但样本行无明确盗号标签。

解析重点：常用设备 / 常用地区 / 历史一致登录方式等反证；如无异常链路，应输出证据不足或反向排除。

## 7. 是否需要修改核心 Skill

不需要。本轮只新增 ATO 真实只读试点样例、问题模板、证据边界、parser 回归计划、real_pilot runbook 和 review 文件。

核心 Skill 未修改。
