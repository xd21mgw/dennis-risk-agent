# ATO Real DataAgent Pilot Case Set v1

## 0. 使用边界

本 case set 用于 v2.4 Data Agent-only 真实只读试点。样本中的人工备注和人工标签只作为 `golden hint / human label`，不作为最终事实。Data Agent 只做取数、找表、SQL、数据摘要；Dennis Agent 负责证据解释和最终风险研判。

## Case 001：ATO_CASE_001_PASSWORD_KPN_RESWEEP

- case_id: `ATO_CASE_001_PASSWORD_KPN_RESWEEP`
- case_name: 密码泄露 / 电商 KPN 站点 / 已回扫
- user_id: `788438474`
- sample_date: `2026-04-24`
- suspicious_event_time: `2026-04-17 06:35:00`
- user_claim_summary: 用户称自己平常仅签到领现金，被盗号时未收到短信提示，4 月 17 发生异常登录，盗号者发布违规视频；用户称平常使用微信或验证码登录。
- manual_label: 是
- risk_category: 登录信息泄露
- risk_subcategory: 密码泄露
- manual_note: 电商 kpn 站点密码盗号，已回扫
- business_scene: 账号安全 / 盗号申诉 / ATO
- target_api_or_action: 登录行为、登录方式变化、设备/IP/地区变化、token/session 变化、发布作品行为、账号资料变更、换绑/改密/找回、策略命中/风险画像/回扫记录
- recommended_time_window: `2026-04-16 06:35:00 ~ 2026-04-18 06:35:00`
- why_selected: 密码泄露正例，且有“已回扫”人工线索，适合作为 ATO 只读取证的正例校准。
- expected_skill: `account_security_expert_skill`、`dataagent_provider`、`human_review`
- dataagent_minimum_inputs: user_id、recommended_time_window、business_scene、target_api_or_action
- evidence_to_collect:
  - 登录方式变化，尤其历史微信/验证码登录 vs 可疑密码登录。
  - 新设备、异地、非常用 IP/地区。
  - 登录后违规发布作品时间链路。
  - token/session 被踢、复用、异常切换。
  - 密码泄露、盗号策略命中、风险画像和回扫记录。
- expected_boundaries:
  - 用户声称未收到短信不能单独证明盗号。
  - 人工备注“已回扫”只是 golden hint，需 Data Agent 返回数据支撑。
  - Data Agent-only 缺实时设备指纹和实时登录链路时必须标记 provider_limitations。
- should_not_conclude:
  - 不因申诉文本直接确认盗号。
  - 不因存在违规发布直接确认盗号。
  - 不输出处罚、冻结、扣除、封禁或策略上线建议。
- parser_focus: 密码登录、异常设备、违规发布链路、回扫记录、登录方式历史差异。
- human_review_focus: 违规发布是否发生在异常登录之后；登录方式是否明显违背历史习惯；回扫记录是否与人工备注一致。

## Case 002：ATO_CASE_002_PHISHING_SHOP_NO_RESWEEP

- case_id: `ATO_CASE_002_PHISHING_SHOP_NO_RESWEEP`
- case_name: 钓鱼网站欺诈 / 未回扫
- user_id: `3322351127`
- sample_date: `2026-04-24`
- suspicious_event_time: `2026-04-22 02:17:00`
- user_claim_summary: 用户称当时没有上线快手，使用其他软件，后续发现账号被封禁。
- manual_label: 是
- risk_category: 欺诈
- risk_subcategory: 钓鱼欺诈
- manual_note: 未回扫，疑似钓鱼网站欺诈，kuaishou.shop.b
- business_scene: 账号安全 / 盗号申诉 / ATO
- target_api_or_action: 登录行为、登录方式变化、设备/IP/地区变化、token/session 变化、发布作品行为、账号资料变更、换绑/改密/找回、策略命中/风险画像/回扫记录
- recommended_time_window: `2026-04-21 02:17:00 ~ 2026-04-23 02:17:00`
- why_selected: 钓鱼欺诈正例但未回扫，适合验证证据不足边界和钓鱼风险画像缺失时的降级。
- expected_skill: `account_security_expert_skill`、`dataagent_provider`、`human_review`
- dataagent_minimum_inputs: user_id、recommended_time_window、business_scene、target_api_or_action
- evidence_to_collect:
  - 可疑时间窗内登录环境变化。
  - 是否出现钓鱼风险画像、钓鱼策略命中或异常登录链路。
  - 封禁前是否发生违规发布或资料变更。
  - 是否缺回扫记录。
- expected_boundaries:
  - “未回扫”意味着不能把人工备注当已验证事实。
  - 外部钓鱼域名线索 Data Agent 可能无法直接取证，只能作为人工备注。
- should_not_conclude:
  - 不因用户称未上线直接确认盗号。
  - 不因钓鱼备注直接确认钓鱼。
- parser_focus: 钓鱼风险画像、异常登录、未回扫状态、证据不足边界。
- human_review_focus: 是否有数据支持钓鱼路径；封禁行为是否与异常登录链路闭合。

## Case 003：ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP

- case_id: `ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP`
- case_name: 扫码欺诈 / 地推 / 已回扫
- user_id: `2861890219`
- sample_date: `2026-04-24`
- suspicious_event_time: `2026-04-20`
- user_claim_summary: 用户称不知情时被盗。
- manual_label: 是
- risk_category: 欺诈
- risk_subcategory: 扫码欺诈
- manual_note: 山东德州扫码地推，已回扫，河南濮阳，kuaishou.server.webday7
- business_scene: 账号安全 / 盗号申诉 / ATO
- target_api_or_action: 登录行为、扫码/OAuth 授权、设备/IP/地区变化、token/session 变化、发布作品行为、策略命中/风险画像/回扫记录
- recommended_time_window: `2026-04-19 00:00:00 ~ 2026-04-21 23:59:59`
- why_selected: 扫码/OAuth/地推链路样本，适合测试授权行为、异地和 token/session 变化。
- expected_skill: `account_security_expert_skill`、`dataagent_provider`、`human_review`
- dataagent_minimum_inputs: user_id、recommended_time_window、business_scene、target_api_or_action
- evidence_to_collect:
  - 扫码/OAuth 授权行为。
  - 异地登录和设备变化。
  - token/session 变化、被踢或多端冲突。
  - 地推相关风险画像或回扫记录。
- expected_boundaries:
  - 地名和域名备注只作为人工线索。
  - Data Agent 无法直接验证线下地推，需要看平台内行为链路。
- should_not_conclude:
  - 不因“扫码地推”备注直接确认盗号。
  - 不因异地单点登录直接确认 ATO。
- parser_focus: 扫码/OAuth/授权行为、异地、token/session 变化、地推线索。
- human_review_focus: 授权行为是否与后续异常操作有时间链路；是否有回扫记录支撑。

## Case 004：ATO_CASE_004_SMS_LEAK_OAUTH_TOKEN_KICK

- case_id: `ATO_CASE_004_SMS_LEAK_OAUTH_TOKEN_KICK`
- case_name: 短信泄露 / OAuth 踢 token / 已回扫
- user_id: `792728243`
- sample_date: `2026-04-24`
- suspicious_event_time: `2026-04-14`
- user_claim_summary: 用户称登上去不是本人网名和头像，账号已封禁，验证也不行。
- manual_label: 是
- risk_category: 登录信息泄露
- risk_subcategory: 短信泄露
- manual_note: 短信泄露 kuaishou.oauth 踢 token，已回扫
- business_scene: 账号安全 / 盗号申诉 / ATO
- target_api_or_action: 短信验证码登录、OAuth 授权、token/session 被踢、账号资料变更、封禁前行为、回扫记录
- recommended_time_window: `2026-04-13 00:00:00 ~ 2026-04-15 23:59:59`
- why_selected: 短信泄露 + OAuth token 异常样本，适合验证 token/session 链路和资料变更链路。
- expected_skill: `account_security_expert_skill`、`dataagent_provider`、`human_review`
- dataagent_minimum_inputs: user_id、recommended_time_window、business_scene、target_api_or_action
- evidence_to_collect:
  - 短信验证码登录或验证行为。
  - OAuth 授权链路。
  - token/session 被踢或异常切换。
  - 网名/头像等账号资料变更。
  - 回扫记录。
- expected_boundaries:
  - 用户称资料变化需数据验证。
  - OAuth 踢 token 备注不能直接替代 token/session 数据。
- should_not_conclude:
  - 不因用户说“不是本人头像”直接确认盗号。
- parser_focus: 短信验证码、OAuth、踢 token、账号资料变更。
- human_review_focus: 资料变更是否紧随异常登录；token/session 链路是否闭合。

## Case 005：ATO_CASE_005_MEMBER_PHISHING_SMS_CODE

- case_id: `ATO_CASE_005_MEMBER_PHISHING_SMS_CODE`
- case_name: 会员钓鱼 / 短信验证码
- user_id: `111856532`
- sample_date: `2026-04-24`
- suspicious_event_time: `2026-04-12`
- user_claim_summary: 用户称从别的平台购买会员，领取会员需要输入手机号和短信验证，期间账号被盗用发布违规视频。
- manual_label: 是
- risk_category: 欺诈
- risk_subcategory: 钓鱼欺诈
- manual_note: 未回扫，疑似钓鱼网站欺诈，kuaishou.shop.b
- business_scene: 账号安全 / 盗号申诉 / ATO
- target_api_or_action: 验证码登录、手机号验证、登录环境变化、发布作品行为、钓鱼风险画像、策略命中/回扫记录
- recommended_time_window: `2026-04-11 00:00:00 ~ 2026-04-13 23:59:59`
- why_selected: 用户描述中包含会员钓鱼和验证码输入链路，适合验证“申诉文本强但数据不足”的边界。
- expected_skill: `account_security_expert_skill`、`dataagent_provider`、`human_review`
- dataagent_minimum_inputs: user_id、recommended_time_window、business_scene、target_api_or_action
- evidence_to_collect:
  - 验证码登录或手机号验证行为。
  - 登录后违规发布链路。
  - 钓鱼风险画像或策略命中。
  - 回扫记录是否缺失。
- expected_boundaries:
  - 外部购买会员场景 Data Agent 可能无法直接验证。
  - 用户描述不能直接当作钓鱼事实。
- should_not_conclude:
  - 不因“购买会员输入验证码”申诉直接确认钓鱼盗号。
- parser_focus: 验证码登录、钓鱼会员场景、发布行为链路。
- human_review_focus: 验证码行为和违规发布时间是否闭合；是否存在数据支持钓鱼路径。

## Case 006：ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE

- case_id: `ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE`
- case_name: 不确定 / 反例 / 无明确盗号标签
- user_id: `5224005946`
- sample_date: `2026-04-24`
- suspicious_event_time: `2026-04-21 21:41:00`
- user_claim_summary: 用户申诉称账号被永久封禁，违规内容非本人发布，怀疑异地登录和异常操作，但样本行没有明确盗号标签。
- manual_label: 否
- risk_category: 未明确
- risk_subcategory: 未明确
- manual_note: 无明确回扫/细分类备注
- business_scene: 账号安全 / 盗号申诉 / ATO
- target_api_or_action: 登录行为、设备/IP/地区变化、发布作品行为、账号资料变更、策略命中/风险画像
- recommended_time_window: `2026-04-20 21:41:00 ~ 2026-04-22 21:41:00`
- why_selected: 反例 / 不确定样本，用于验证不因用户申诉直接强判盗号。
- expected_skill: `account_security_expert_skill`、`dataagent_provider`、`human_review`
- dataagent_minimum_inputs: user_id、recommended_time_window、business_scene、target_api_or_action
- evidence_to_collect:
  - 是否存在异常登录链路。
  - 设备/IP/地区是否与历史常用一致。
  - 发布行为前后是否有 token/session 变化。
  - 是否缺盗号风险画像或策略命中。
- expected_boundaries:
  - manual_label 为“否”，但仍需数据解释。
  - 用户申诉是弱证据，不得直接强判。
- should_not_conclude:
  - 不因“非本人发布”申诉直接确认 ATO。
  - 不因封禁结果直接确认盗号。
- parser_focus: 反例，不因用户申诉直接判断盗号。
- human_review_focus: 是否存在反向排除证据；是否更像本人操作或证据不支持。

