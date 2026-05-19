# ATO 客诉回归 Case v1

## 说明

本文件从 Excel 内容抽象 25 个匿名回归 case。所有 case 仅使用 `case_id`，不暴露完整 user_id。

字段中的“manual_label / attack_category / attack_subcategory / abuse_type”来自人工表格，不代表最终事实。最终结论必须由数据证据、Dennis Agent 解释和人工复核共同完成。

## Case 列表

### ATO_XLSX_001

```yaml
case_id: ATO_XLSX_001
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider, human_review]
user_complaint_summary: 用户称街头陌生人要求扫码给直播间涨人气，后续账号异常。
manual_label: 是
attack_category: 欺诈
attack_subcategory: 地推欺诈
abuse_type: 视频标题
evidence_from_manual_review: 盗号具体原因记录为已回捞。
strong_evidence: [线下扫码诱导线索, 后续账号异常]
medium_evidence: [用户自述与地推扫码路径一致]
weak_evidence: [用户自述]
counter_evidence: [未见数据层登录/授权/token/发布链路]
missing_evidence: [扫码授权记录, Web新设备登录, token生成, 发布行为, 回扫记录]
expected_conclusion: data_supports_ato_suspicion_if_data_chain_closes
must_have: [扫码/OAuth或Web登录, 新设备, 登录态生成, 后续敏感动作]
must_not: [不得仅凭用户称扫码直接强判ATO]
dataagent_query_intent_needed: ato_ground_promotion_scan_check
next_evidence_to_collect: [登录授权全景, 设备/IP, token/session, 发布链路, 回扫记录]
human_review_required: true
```

### ATO_XLSX_002

```yaml
case_id: ATO_XLSX_002
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider, content_review_provider, human_review]
user_complaint_summary: 用户和朋友外出遇到扫码送零食，次日发现账号发布招嫖/涉黄内容并封禁。
manual_label: 是
attack_category: 欺诈
attack_subcategory: 地推欺诈
abuse_type: 视频招嫖-金额
evidence_from_manual_review: 盗号具体原因记录为已回捞。
strong_evidence: [扫码诱导, 后续异常发布, 账号封禁]
medium_evidence: [作恶类型明确为招嫖金额类]
weak_evidence: [用户回忆时间可能不精确]
counter_evidence: [缺少发布设备与登录设备一致性]
missing_evidence: [作品发布时间, 内容审核结论, 登录发布链路]
expected_conclusion: data_supports_ato_suspicion_if_publish_chain_matches
must_have: [扫码后新设备登录, 发布设备一致, 发布时间落在异常窗口]
must_not: [不得把“已回捞”当数据事实]
dataagent_query_intent_needed: ato_ground_promotion_scan_check
next_evidence_to_collect: [登录/授权, 发布行为, 删除/隐藏状态, 内容违规类型]
human_review_required: true
```

### ATO_XLSX_003

```yaml
case_id: ATO_XLSX_003
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider, risk_engine_provider]
user_complaint_summary: 用户称在商场扫码关注/助力，短暂交出手机，后续发现账号被登录并发布视频。
manual_label: 是
attack_category: 欺诈
attack_subcategory: 地推欺诈
abuse_type: 色情视频-网址
evidence_from_manual_review: 已回捞。
strong_evidence: [线下地推, 交出手机, 后续发布]
medium_evidence: [地点和时间描述较清晰]
weak_evidence: [无法确认操作主体]
counter_evidence: [可能是用户本人授权操作但未理解风险]
missing_evidence: [授权页面, OAuth/扫码日志, Web新设备, 作品设备]
expected_conclusion: partial_support_until_authorization_chain_verified
must_have: [授权/扫码事件, 新设备登录, 发布链路]
must_not: [不得只因交出手机就认定盗号]
dataagent_query_intent_needed: ato_ground_promotion_scan_check
next_evidence_to_collect: [授权记录, 登录方式, 设备环境, 发布链路]
human_review_required: true
```

### ATO_XLSX_004

```yaml
case_id: ATO_XLSX_004
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider, relation_graph_provider]
user_complaint_summary: 用户称陌生人助力后，晚上睡觉期间账号发布多个涉黄作品。
manual_label: 是
attack_category: 欺诈
attack_subcategory: 地推欺诈
abuse_type: 色情视频-网址
evidence_from_manual_review: 已回捞。
strong_evidence: [睡眠时段发布, 地推助力, 多作品发布]
medium_evidence: [同一场景可能存在多人同批扫码]
weak_evidence: [睡眠时段来自用户自述]
counter_evidence: [无法排除本人设备定时发布或主动分享]
missing_evidence: [批量地推团伙关联, 发布设备/IP, 授权日志]
expected_conclusion: data_supports_ato_suspicion_if_group_scan_and_publish_verified
must_have: [同批扫码/授权, 发布链路, 新设备或token异常]
must_not: [不得把“睡觉”作为强证据]
dataagent_query_intent_needed: ato_ground_promotion_scan_check
next_evidence_to_collect: [同时间段同地点同类case聚集, 设备/IP团组, 发布链路]
human_review_required: true
```

### ATO_XLSX_005

```yaml
case_id: ATO_XLSX_005
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider]
user_complaint_summary: 用户称地推送扇子，让其帮忙关注，之后账号因传播色情被封。
manual_label: 是
attack_category: 欺诈
attack_subcategory: 地推欺诈
abuse_type: 色情视频-网址
evidence_from_manual_review: 已回捞。
strong_evidence: [地推物料诱导, 关注/扫码动作, 后续涉黄发布]
medium_evidence: [典型线下地推模式]
weak_evidence: [用户未确认对方具体操作]
counter_evidence: [可能是正常关注行为，未必完成登录授权]
missing_evidence: [是否触发授权, 是否生成token, 是否有Web新设备]
expected_conclusion: partial_support_until_login_authorization_verified
must_have: [登录/授权/Token证据]
must_not: [不得把关注动作直接等同账号接管]
dataagent_query_intent_needed: ato_ground_promotion_scan_check
next_evidence_to_collect: [授权记录, 关注行为与登录行为区分, 后续发布]
human_review_required: true
```

### ATO_XLSX_006

```yaml
case_id: ATO_XLSX_006
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider]
user_complaint_summary: 用户称拿手机扫码后，次日凌晨账号发布色情视频并封禁。
manual_label: 是
attack_category: 欺诈
attack_subcategory: 地推欺诈
abuse_type: 色情视频-网址
evidence_from_manual_review: 已回捞。
strong_evidence: [扫码后异常发布, 账号封禁]
medium_evidence: [发布时间与用户自述不在线相符]
weak_evidence: [用户自述]
counter_evidence: [缺数据证明扫码与发布相关]
missing_evidence: [扫码授权, 新设备登录, 发布设备一致性]
expected_conclusion: data_supports_ato_suspicion_if_scan_to_publish_chain_closes
must_have: [扫码/OAuth, Web新设备, 发布链路]
must_not: [不得只凭封禁结果判断ATO]
dataagent_query_intent_needed: ato_ground_promotion_scan_check
next_evidence_to_collect: [登录/授权全景, 发布行为, 策略命中]
human_review_required: true
```

### ATO_XLSX_007

```yaml
case_id: ATO_XLSX_007
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider]
user_complaint_summary: 用户在任务/助力场景打开链接，后续发现账号出现异常作品。
manual_label: 是
attack_category: 欺诈
attack_subcategory: 钓鱼欺诈
abuse_type: 招嫖视频-钱
evidence_from_manual_review: 未回扫，web端短信验证码登录，来源线索为任务/链接类。
strong_evidence: [web端短信验证码登录线索, 下游招嫖内容]
medium_evidence: [钓鱼任务链路]
weak_evidence: [来源线索未由数据验证]
counter_evidence: [未回扫，缺批量验证]
missing_evidence: [web登录数据, 验证码登录, 来源落地页, token/session]
expected_conclusion: partial_support_until_web_login_verified
must_have: [web短信验证码登录, 新设备/IP, 发布链路]
must_not: [不得把来源字符串当事实]
dataagent_query_intent_needed: phishing_web_login_check
next_evidence_to_collect: [web登录, 短信验证码登录, 发布链路, 回扫匹量]
human_review_required: true
```

### ATO_XLSX_008

```yaml
case_id: ATO_XLSX_008
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider]
user_complaint_summary: 用户在二手平台购买会员，进入链接并输入手机号/验证码，后续账号封禁。
manual_label: 是
attack_category: 欺诈
attack_subcategory: 钓鱼欺诈
abuse_type: 色情视频-网址单人
evidence_from_manual_review: 未回扫，web端短信验证码登录，充值/会员类来源线索。
strong_evidence: [输入手机号/验证码, web端登录线索, 后续封禁]
medium_evidence: [会员领取/充值类钓鱼场景]
weak_evidence: [平台来源和链接未验证]
counter_evidence: [可能是用户主动授权领取服务]
missing_evidence: [短信验证码登录记录, web新设备, 发布内容, 来源链接]
expected_conclusion: data_supports_ato_suspicion_if_sms_web_chain_closes
must_have: [短信验证码登录, 登录后发布, 非历史设备]
must_not: [不得只因购买会员经历判断钓鱼]
dataagent_query_intent_needed: phishing_web_login_check
next_evidence_to_collect: [web登录, 验证码登录, 发布行为, 设备/IP]
human_review_required: true
```

### ATO_XLSX_009

```yaml
case_id: ATO_XLSX_009
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider, content_review_provider]
user_complaint_summary: 用户长期未登录，发现昵称/资料变化并有低俗作品。
manual_label: 是
attack_category: 欺诈
attack_subcategory: 钓鱼欺诈
abuse_type: 招嫖视频-微信
evidence_from_manual_review: 未回扫，web端短信验证码登录。
strong_evidence: [资料变化线索, web短信验证码登录线索, 招嫖内容]
medium_evidence: [长期未登录后发现异常]
weak_evidence: [用户记忆与发现时间]
counter_evidence: [长期未登录导致时间窗口难定位]
missing_evidence: [资料变更记录, web登录, 作品内容, 发布时间]
expected_conclusion: partial_support
must_have: [资料变更或发布动作与异常登录链路一致]
must_not: [不得因长期未登录直接判盗号]
dataagent_query_intent_needed: phishing_web_login_check
next_evidence_to_collect: [账号资料变更, 登录全景, 发布链路]
human_review_required: true
```

### ATO_XLSX_010

```yaml
case_id: ATO_XLSX_010
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider]
user_complaint_summary: 用户称网上朋友或链接相关操作后，账号在休息时段发布色情视频。
manual_label: 是
attack_category: 欺诈
attack_subcategory: 钓鱼欺诈
abuse_type: 色情视频-网址
evidence_from_manual_review: 未回扫，web端短信验证码登录，疑似 shop 类来源。
strong_evidence: [web短信验证码登录线索, 下游色情视频]
medium_evidence: [用户描述存在第三方诱导]
weak_evidence: [具体来源未验证]
counter_evidence: [可能缺少准确异常时间]
missing_evidence: [web登录, 来源域/页面, 验证码, 发布设备]
expected_conclusion: partial_support_until_data_verified
must_have: [web端验证码登录, 发布链路]
must_not: [不得把“shop类来源”当已验证事实]
dataagent_query_intent_needed: phishing_web_login_check
next_evidence_to_collect: [登录方式, 设备/IP, 发布行为, 来源线索匹量]
human_review_required: true
```

### ATO_XLSX_011

```yaml
case_id: ATO_XLSX_011
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider]
user_complaint_summary: 用户称长期未使用，重新打开发现账号被封且 IP/作品异常。
manual_label: 是
attack_category: 欺诈
attack_subcategory: 钓鱼欺诈
abuse_type: 色情视频-网址单人
evidence_from_manual_review: 未回扫，web端短信验证码登录，疑似 recharge 类来源。
strong_evidence: [长期未使用后异常, web短信登录线索]
medium_evidence: [IP/作品异常来自用户感知]
weak_evidence: [用户感知不可替代数据]
counter_evidence: [长期未使用导致历史基线和窗口不稳定]
missing_evidence: [登录时间, 登录方式, 发布行为, IP归属]
expected_conclusion: partial_support
must_have: [web登录 + 发布链路]
must_not: [不得把用户看到的IP当平台取证事实]
dataagent_query_intent_needed: phishing_web_login_check
next_evidence_to_collect: [登录全景, IP/设备, 发布链路]
human_review_required: true
```

### ATO_XLSX_012

```yaml
case_id: ATO_XLSX_012
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider]
user_complaint_summary: 用户称扫码自助领取会员，链接失效后晚间发现因违规视频封禁。
manual_label: 是
attack_category: 欺诈
attack_subcategory: 钓鱼欺诈
abuse_type: 招嫖视频-微信
evidence_from_manual_review: 未回扫，web端短信验证码登录。
strong_evidence: [扫码/链接诱导, web短信验证码登录线索, 下游违规]
medium_evidence: [自助领取会员是典型钓鱼入口]
weak_evidence: [来源和链接未验证]
counter_evidence: [可能是用户主动授权第三方服务]
missing_evidence: [登录/授权全景, token/session, 发布链路]
expected_conclusion: data_supports_ato_suspicion_if_web_sms_publish_chain_closes
must_have: [短信验证码登录, 新设备, 发布行为]
must_not: [不得把第三方服务纠纷直接判ATO]
dataagent_query_intent_needed: phishing_web_login_check
next_evidence_to_collect: [web登录, 短信验证, 发布链路, 来源匹量]
human_review_required: true
```

### ATO_XLSX_013

```yaml
case_id: ATO_XLSX_013
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider]
user_complaint_summary: 用户称账号在不知情情况下发布色情作品，表内原因提示 app 端短信验证码登录。
manual_label: 是
attack_category: 登录信息泄露
attack_subcategory: 短信泄露
abuse_type: 空值
evidence_from_manual_review: app端短信验证码登录，登录到作恶间隔较长，可能存在账号交易风险。
strong_evidence: [短信验证码登录线索]
medium_evidence: [登录到作恶时间间隔较长，存在账号交易/租借边界]
weak_evidence: [用户称不知情]
counter_evidence: [时间间隔长，不一定是即时盗号]
missing_evidence: [登录后行为链路, 账号交易/租借反证, token/session]
expected_conclusion: partial_support_or_insufficient_support
must_have: [短信登录与下游作恶时间链路]
must_not: [不得忽略账号交易风险]
dataagent_query_intent_needed: sms_code_leakage_login_check
next_evidence_to_collect: [短信登录, 设备/IP, 发布行为, 收益/交易线索]
human_review_required: true
```

### ATO_XLSX_014

```yaml
case_id: ATO_XLSX_014
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider]
user_complaint_summary: 用户长期不使用极速版，清理手机时发现账号违规封禁。
manual_label: 是
attack_category: 登录信息泄露
attack_subcategory: 短信泄露
abuse_type: 空值
evidence_from_manual_review: 未回扫，web端短信验证码登录。
strong_evidence: [web端短信验证码登录线索]
medium_evidence: [长期未使用后发现异常]
weak_evidence: [用户发现滞后]
counter_evidence: [窗口定位可能偏差]
missing_evidence: [短信登录记录, 发布链路, 作品类型]
expected_conclusion: partial_support_until_chain_verified
must_have: [短信登录 + 发布/敏感动作]
must_not: [不得因长期未使用直接判盗号]
dataagent_query_intent_needed: sms_code_leakage_login_check
next_evidence_to_collect: [登录全景, 发布行为, 策略命中]
human_review_required: true
```

### ATO_XLSX_015

```yaml
case_id: ATO_XLSX_015
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider]
user_complaint_summary: 用户称老人接到陌生电话并泄露验证码，账号后续出现不良作品。
manual_label: 是
attack_category: 登录信息泄露
attack_subcategory: 短信泄露
abuse_type: 空值
evidence_from_manual_review: 未回扫，app短信验证码登录成功。
strong_evidence: [验证码泄露自述, app短信验证码登录线索, 下游不良作品]
medium_evidence: [老年用户被骗场景]
weak_evidence: [亲属代述]
counter_evidence: [需确认验证码是否用于快手登录]
missing_evidence: [验证码登录时间, 登录设备, 发布链路]
expected_conclusion: data_supports_ato_suspicion_if_sms_login_and_publish_verified
must_have: [短信验证码登录, 非历史设备或异常IP, 发布链路]
must_not: [不得只凭亲属代述强判]
dataagent_query_intent_needed: sms_code_leakage_login_check
next_evidence_to_collect: [验证码登录, 设备/IP, 发布行为]
human_review_required: true
```

### ATO_XLSX_016

```yaml
case_id: ATO_XLSX_016
source_sheet: 工作表1
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider]
user_complaint_summary: 用户称未收到验证码提示，但表内原因指向短信泄露后登录小程序并置换 web token。
manual_label: 是
attack_category: 登录信息泄露
attack_subcategory: 短信泄露
abuse_type: 空值
evidence_from_manual_review: 短信泄露后登录微信小程序，之后置换web端token作恶。
strong_evidence: [短信泄露, 小程序登录, web token置换线索]
medium_evidence: [用户无感知]
weak_evidence: [用户称未收到验证码]
counter_evidence: [需确认验证码链路和token置换是否真实发生]
missing_evidence: [小程序登录, token/session生命周期, 下游作恶链路]
expected_conclusion: data_supports_ato_suspicion_if_token_replacement_verified
must_have: [短信登录, token置换, 下游作恶]
must_not: [不得把备注中的token置换当事实]
dataagent_query_intent_needed: sms_code_leakage_login_check
next_evidence_to_collect: [登录方式, token/session, 发布/敏感动作]
human_review_required: true
```

### ATO_XLSX_017

```yaml
case_id: ATO_XLSX_017
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider]
user_complaint_summary: 用户称不常看快手，未发现异地登录但出现异常作品。
manual_label: 是
attack_category: token泄露
attack_subcategory: 租借账号
abuse_type: 空值
evidence_from_manual_review: 已回捞。
strong_evidence: [疑似登录态链路问题]
medium_evidence: [无明显异地登录但下游作恶]
weak_evidence: [不常使用导致发现滞后]
counter_evidence: [租借账号可能是主动授权/账号交易边界]
missing_evidence: [token使用记录, 设备/IP/UA冲突, 租借/交易线索]
expected_conclusion: partial_support_or_boundary_to_account_rental
must_have: [token/session异常或账号交易证据]
must_not: [不得把租借账号直接等同被盗]
dataagent_query_intent_needed: token_reuse_or_session_hijack_check
next_evidence_to_collect: [token/session, 登录态设备环境, 发布链路, 账号租借反证]
human_review_required: true
```

### ATO_XLSX_018

```yaml
case_id: ATO_XLSX_018
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider]
user_complaint_summary: 用户称长时间未登录，某日出现非本人作品并封禁。
manual_label: 是
attack_category: token泄露
attack_subcategory: token泄露
abuse_type: 视频招嫖
evidence_from_manual_review: 未回扫。
strong_evidence: [疑似token泄露标签, 下游招嫖作品]
medium_evidence: [长期未登录后出现作品]
weak_evidence: [用户自述]
counter_evidence: [未回扫，缺token证据]
missing_evidence: [token/session复用, 登录态生成, 发布设备, 策略命中]
expected_conclusion: partial_support_until_token_evidence_verified
must_have: [token与设备/IP/UA冲突, 发布链路]
must_not: [不得把token泄露标签当数据事实]
dataagent_query_intent_needed: token_reuse_or_session_hijack_check
next_evidence_to_collect: [token/session, 设备/IP/UA, 发布链路]
human_review_required: true
```

### ATO_XLSX_019

```yaml
case_id: ATO_XLSX_019
source_sheet: 工作表1
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider, risk_engine_provider]
user_complaint_summary: 表内原因指向风控拦截后 token 仍下发，盗号已处理且问题修复。
manual_label: 空值
attack_category: 空值
attack_subcategory: token泄露线索
abuse_type: 空值
evidence_from_manual_review: CP平台风控拦截token仍然下发。
strong_evidence: [平台侧token下发漏洞线索]
medium_evidence: [已处理/已修复备注]
weak_evidence: [缺用户自述和结构标签]
counter_evidence: [人工备注不能替代执行日志]
missing_evidence: [风控拦截日志, token下发日志, 修复前后对比]
expected_conclusion: not_evaluated_until_platform_logs_verified
must_have: [拦截后token下发证据]
must_not: [不得把“问题已修复”当事实]
dataagent_query_intent_needed: token_reuse_or_session_hijack_check
next_evidence_to_collect: [策略引擎, token发放, 下游作恶, 修复前后指标]
human_review_required: true
```

### ATO_XLSX_020

```yaml
case_id: ATO_XLSX_020
source_sheet: 工作表1
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [human_review, dataagent_provider]
user_complaint_summary: 表内原因记录为历史 case，早期盗号。
manual_label: 空值
attack_category: 空值
attack_subcategory: 历史case
abuse_type: 空值
evidence_from_manual_review: 历史case，年份较早。
strong_evidence: []
medium_evidence: [历史盗号备注]
weak_evidence: [缺当前窗口用户自述]
counter_evidence: [历史case不能证明当前盗号]
missing_evidence: [当前申诉窗口, 当前登录/发布链路]
expected_conclusion: historical_case_not_current_ato
must_have: [当前窗口证据才能判断当前ATO]
must_not: [不得把历史case当当前事实]
dataagent_query_intent_needed: complaint_false_positive_review
next_evidence_to_collect: [历史记录, 当前申诉时间, 当前处罚原因]
human_review_required: true
```

### ATO_XLSX_021

```yaml
case_id: ATO_XLSX_021
source_sheet: 工作表1
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider]
user_complaint_summary: 历史地推盗号 case，备注称不清楚为何未回捞干净，需要二次回捞。
manual_label: 是
attack_category: 欺诈
attack_subcategory: 地推欺诈
abuse_type: 空值
evidence_from_manual_review: 历史case，需要二次回捞。
strong_evidence: [历史地推盗号线索]
medium_evidence: [需二次回捞]
weak_evidence: [用户称异地登录]
counter_evidence: [历史case与当前窗口可能不一致]
missing_evidence: [回捞规则, 当前剩余量, 新增样本链路]
expected_conclusion: resweep_needed_not_final_conclusion
must_have: [回捞匹量结果]
must_not: [不得把需回捞当已回捞]
dataagent_query_intent_needed: ato_ground_promotion_scan_check
next_evidence_to_collect: [同规则匹量, 漏召回样本, 当前窗口链路]
human_review_required: true
```

### ATO_XLSX_022

```yaml
case_id: ATO_XLSX_022
source_sheet: 工作表1
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [human_review]
user_complaint_summary: 表内原因记录为非被盗。
manual_label: 空值
attack_category: 非盗号
attack_subcategory: 非被盗
abuse_type: 空值
evidence_from_manual_review: 非被盗。
strong_evidence: []
medium_evidence: [人工核查否定盗号]
weak_evidence: []
counter_evidence: [人工备注指向非被盗]
missing_evidence: [具体否定依据, 登录/发布链路]
expected_conclusion: insufficient_support_or_data_does_not_support_ato
must_have: [完整正常行为链路才能data_does_not_support_ato]
must_not: [不得因表格空标签忽略反例价值]
dataagent_query_intent_needed: complaint_false_positive_review
next_evidence_to_collect: [处罚原因, 登录设备, 作品来源]
human_review_required: true
```

### ATO_XLSX_023

```yaml
case_id: ATO_XLSX_023
source_sheet: 工作表1
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [human_review]
user_complaint_summary: 表内原因记录为反诈封禁导致客诉，没有发现被盗痕迹。
manual_label: 空值
attack_category: 非盗号
attack_subcategory: 反诈封禁误报
abuse_type: 空值
evidence_from_manual_review: 反诈封禁导致客诉，没有发现被盗痕迹。
strong_evidence: []
medium_evidence: [非ATO处罚原因线索]
weak_evidence: [缺结构化策略证据]
counter_evidence: [反诈封禁可能解释客诉]
missing_evidence: [策略命中, 登录链路, 申诉动作]
expected_conclusion: complaint_false_positive_review
must_have: [策略命中与行为链路]
must_not: [不得把所有封禁客诉归为盗号]
dataagent_query_intent_needed: complaint_false_positive_review
next_evidence_to_collect: [策略命中, 处罚原因, 登录/发布行为]
human_review_required: true
```

### ATO_XLSX_024

```yaml
case_id: ATO_XLSX_024
source_sheet: 工作表1
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [traffic_diversion_interception_skill, human_review]
user_complaint_summary: 表内原因记录为非被盗，导流封禁。
manual_label: 空值
attack_category: 非盗号
attack_subcategory: 导流封禁
abuse_type: 空值
evidence_from_manual_review: 非被盗，导流封禁。
strong_evidence: []
medium_evidence: [导流处罚原因线索]
weak_evidence: []
counter_evidence: [导流违规可解释封禁，不必然是ATO]
missing_evidence: [导流证据, 登录链路, 发布主体]
expected_conclusion: not_ato_route_to_traffic_diversion_if_verified
must_have: [导流链路证据]
must_not: [不得把导流封禁误归盗号]
dataagent_query_intent_needed: complaint_false_positive_review
next_evidence_to_collect: [处罚规则, 导流内容, 登录设备]
human_review_required: true
```

### ATO_XLSX_025

```yaml
case_id: ATO_XLSX_025
source_sheet: 工作表1
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider, human_review]
user_complaint_summary: 用户称凌晨发现开播黄色内容，但登录设备看起来都是常用设备。
manual_label: 不确定
attack_category: 不确定
attack_subcategory: 不确定
abuse_type: 直播/色情内容线索
evidence_from_manual_review: 是否盗号=不确定。
strong_evidence: []
medium_evidence: [直播/色情内容异常, 用户称非本人]
weak_evidence: [用户自述睡觉或未操作]
counter_evidence: [登录设备均为常用设备]
missing_evidence: [开播设备, 实时登录链路, 直播操作主体]
expected_conclusion: insufficient_support
must_have: [异常登录或账号接管证据]
must_not: [不得因色情直播直接强判ATO]
dataagent_query_intent_needed: complaint_false_positive_review
next_evidence_to_collect: [开播日志, 登录设备, 设备指纹, 策略命中]
human_review_required: true
```

### ATO_XLSX_026

```yaml
case_id: ATO_XLSX_026
source_sheet: 工作表1
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider]
user_complaint_summary: 用户发现昵称变化和封号，但缺明确异常链路。
manual_label: 不确定
attack_category: 不确定
attack_subcategory: 不确定
abuse_type: 空值
evidence_from_manual_review: 是否盗号=不确定。
strong_evidence: []
medium_evidence: [资料变化线索]
weak_evidence: [用户困惑描述]
counter_evidence: [缺登录、token、发布链路]
missing_evidence: [资料变更记录, 登录全景, 发布行为]
expected_conclusion: insufficient_support
must_have: [资料变更与异常登录链路]
must_not: [不得因昵称变化直接判盗号]
dataagent_query_intent_needed: complaint_false_positive_review
next_evidence_to_collect: [资料变更, 登录设备, 敏感动作]
human_review_required: true
```

### ATO_XLSX_027

```yaml
case_id: ATO_XLSX_027
source_sheet: 工作表2
risk_domain: account_security
primary_skill: account_security_expert_skill
auxiliary_skills: [dataagent_provider, human_review]
user_complaint_summary: 用户称很少登录，发现解绑、资料异常和封禁，表内分类缺失。
manual_label: 是
attack_category: 空值
attack_subcategory: 空值
abuse_type: 低俗视频
evidence_from_manual_review: 历史盗号。
strong_evidence: [历史盗号线索, 资料/关系变化线索]
medium_evidence: [低俗视频作恶类型]
weak_evidence: [分类缺失]
counter_evidence: [历史盗号不能直接证明当前窗口]
missing_evidence: [登录链路, 解绑记录, 发布时间, 分类补全]
expected_conclusion: needs_label_cleanup_and_data_verification
must_have: [数据验证后才能补分类]
must_not: [不得自动补成某一类盗号]
dataagent_query_intent_needed: complaint_false_positive_review
next_evidence_to_collect: [登录/资料变更/解绑/发布链路]
human_review_required: true
```

## 覆盖性总结

| 类型 | 覆盖 case |
|---|---|
| 地推欺诈正例 | 001-006, 021 |
| 钓鱼欺诈正例 | 007-012 |
| 短信泄露正例 | 013-016 |
| token 泄露 / 登录态复用 | 017-019 |
| 历史 case | 020-021, 027 |
| 非盗号反例 | 022-024 |
| 不确定样本 | 025-026 |
| 标签缺失样本 | 027 |
| 需要回捞样本 | 007-012, 018, 021 |
| 已回捞样本 | 001-006, 017 |
