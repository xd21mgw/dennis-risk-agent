# ATO 客诉 Data Agent Query Intent 模板 v1

## 0. 通用边界

Data Agent 在本流程中只作为 evidence provider：

- 负责找表、生成 SQL、离线取数、聚合摘要、缺失证据和口径风险说明。
- 不负责最终风控定性。
- 不输出处罚、冻结、封禁、扣除或策略上线建议。
- 结论性文字只能进入 `provider_conclusion_hint`。
- `dennis_final_judgement` 由 Dennis 主 Agent 基于 evidence 单独生成。

所有模板必须带上：

```yaml
safety_boundary:
  - 只读取证，不做处置建议
  - 区分数据发现、模型推测、人工备注
  - 用户申诉不是事实
  - 人工备注不是事实
  - SQL-only 不等于查数结果
```

## 1. ato_ground_promotion_scan_check

### 适用问题

地推扫码 / 线下助力 / 送礼 / 拿手机关注后，用户称账号被盗并发布色情、招嫖、网址类内容。

### 最小输入

```yaml
minimum_inputs:
  - case_id
  - user_id
  - suspicious_event_time 或 用户自述被盗日期
  - time_window
  - user_claim_summary
  - manual_note
```

### required_data_domains

- 用户信息域
- 前端行为域，如离线可查
- 后端数据域
- 设备信息域
- 风险画像域
- 策略引擎域，如离线可查
- 内容 / 发布行为域，如可查

### field_types_needed

- user_id
- login_time
- login_method
- oauth_or_qr_scan_event
- device_id
- device_profile
- ip
- region
- token_id
- session_id
- frontend_event
- backend_api
- publish_time
- publish_device
- publish_ip
- content_status
- strategy_hit
- risk_label

### join_paths_needed

- `user_id → login_event → device/IP/region`
- `login_event → oauth_or_qr_scan_event`
- `login_event → token/session`
- `token/session → publish_event`
- `publish_event → content_status`
- `login_event → strategy_hit/risk_label`

### expected_outputs

- 时间窗口内是否存在扫码 / OAuth / 授权 / Web 新设备登录。
- 是否出现新设备、非历史设备、短时间多设备 / 多 IP。
- 是否有 token/session 生成或切换。
- 登录 / 授权后是否发生发布、删除、隐藏、资料变更等敏感动作。
- 发布设备是否与扫码 / Web 新设备一致。
- 是否命中 stealAccount、扫码盗号、Web扫码无历史设备等策略。
- 哪些字段无权限、哪些数据源未覆盖。

### quality_checks

- 扫码或关注行为不等于账号接管。
- 用户称“睡觉 / 上学 / 不在线”只能作为弱证据。
- “已回捞”必须由数据验证。
- 地名或线下点位必须由数据验证，不能只用人工备注。

### missing_evidence

- 实时扫码流程。
- 二维码内容。
- 实时设备指纹。
- token/session 生命周期。
- 作品内容或 caption。

### provider_conclusion_hint 规则

```text
只有当“扫码/OAuth/授权 → Web新设备/非历史设备 → token/session → 发布/敏感动作”链路闭合时，Data Agent 可提示“数据支持扫码/OAuth 型 ATO 嫌疑”。
如果只看到扫码自述或关注行为，最多提示“证据不足 / 需补授权和发布链路”。
```

### dennis_final_judgement

由 Dennis Agent 生成，不由 Data Agent 生成。

## 2. phishing_web_login_check

### 适用问题

钓鱼网站、任务链接、会员领取、充值链接、第三方平台链接导致 web 端登录或短信验证码泄露。

### 最小输入

- case_id
- user_id
- time_window
- user_claim_summary
- manual_note 中的来源线索，如有

### required_data_domains

- 用户信息域
- 后端数据域
- 设备信息域
- 风险画像域
- 内容 / 发布行为域
- 策略引擎域，如可查

### field_types_needed

- login_time
- login_method
- sms_code_login_flag
- web_login_flag
- device_id
- ip
- region
- ua
- source_page_or_action_type
- token_id
- publish_time
- publish_device
- strategy_hit
- risk_label

### join_paths_needed

- `user_id → web_login_event`
- `web_login_event → sms_code_login`
- `web_login_event → device/IP/UA`
- `web_login_event → token/session`
- `token/session → publish_event`
- `login_event → strategy_hit/risk_label`

### expected_outputs

- 是否存在 web 端短信验证码登录。
- 登录设备 / IP / UA 是否为历史环境。
- 登录后是否发生发布、资料变更、换绑、改密、找回。
- 是否存在钓鱼、风险链接、异常来源、策略命中。
- 是否能关联下游内容作恶。

### quality_checks

- 来源字符串、域名、第三方平台备注不是事实。
- 长期未登录后发现封禁，不能直接证明盗号。
- 只有 web 登录但没有下游作恶链路时，不能强判。

### missing_evidence

- 钓鱼页面内容。
- 实时点击链路。
- 验证码实际发送 / 输入过程。
- token/session 完整生命周期。

### provider_conclusion_hint 规则

```text
web短信验证码登录 + 非历史环境 + 下游发布/敏感动作链路闭合时，可提示“数据支持钓鱼/web登录型 ATO 嫌疑”。
如果只有来源备注或用户说输入验证码，提示“证据不足，需补 web 登录和发布链路”。
```

### dennis_final_judgement

由 Dennis Agent 生成，不由 Data Agent 生成。

## 3. sms_code_leakage_login_check

### 适用问题

短信验证码被电话、熟人、任务或欺诈话术骗取后，账号被登录或会话被置换。

### 最小输入

- case_id
- user_id
- time_window
- suspicious_event_time
- user_claim_summary

### required_data_domains

- 用户信息域
- 后端数据域
- 设备信息域
- 风险画像域
- 策略引擎域
- 发布 / 敏感动作域

### field_types_needed

- sms_code_login_flag
- login_time
- login_method
- device_id
- device_profile
- ip
- region
- token_id
- session_id
- sensitive_action
- publish_event
- strategy_hit
- risk_label

### join_paths_needed

- `user_id → sms_code_login_event`
- `sms_code_login_event → device/IP/region`
- `sms_code_login_event → token/session`
- `token/session → publish_event/sensitive_action`
- `login_event → strategy_hit`

### expected_outputs

- 是否存在短信验证码登录。
- 验证码登录是否发生在异常窗口。
- 登录环境是否为新设备、异地、非常用环境。
- 登录后是否发生发布、换绑、改密、找回、资料变更。
- 是否有 token/session 被踢出、复用、置换。
- 是否命中短信泄露、异常登录、盗号等策略。

### quality_checks

- 用户称“没收到短信”不是事实，需要短信 / 登录日志验证。
- 验证码登录是强线索，但必须看后续接管和作恶链路。
- 登录到作恶间隔较长时，要排查账号交易 / 租借。

### missing_evidence

- 短信实际送达 / 输入详情。
- 实时登录链路。
- token/session 生命周期。
- 账号交易 / 租借反证。

### provider_conclusion_hint 规则

```text
短信验证码登录 + 非历史环境 + token/session 或下游敏感动作链路闭合时，可提示“数据支持短信泄露型 ATO 嫌疑”。
如果登录到作恶间隔较长或缺下游链路，应提示 partial_support 或 insufficient_support。
```

### dennis_final_judgement

由 Dennis Agent 生成，不由 Data Agent 生成。

## 4. token_reuse_or_session_hijack_check

### 适用问题

疑似 token 泄露、登录态复用、token 被置换、风控拦截后 token 仍下发、用户无登录感知但有下游作恶。

### 最小输入

- case_id
- user_id
- time_window
- target_action 或异常作品/处罚时间
- manual_note，如有 token 线索

### required_data_domains

- 用户信息域
- 后端数据域
- 设备信息域
- 策略引擎域
- 风险画像域
- 发布 / 敏感动作域

### field_types_needed

- token_id
- session_id
- login_time
- token_issue_time
- token_use_time
- device_id
- ip
- ua
- region
- gateway_decision
- engine_decision
- disposal_action
- publish_event

### join_paths_needed

- `user_id → token/session`
- `token/session → device/IP/UA/region`
- `token/session → publish_event/sensitive_action`
- `gateway/risk_engine → token_issue_or_block`
- `login_event → token_issue → downstream_action`

### expected_outputs

- 是否存在 token 与设备 / IP / UA / 地区冲突。
- 是否存在拦截后 token 下发或继续有效。
- 是否存在 token/session 被踢、复用、置换、多端冲突。
- 下游作恶是否由异常 token/session 承载。
- 是否存在合法多端 / 授权登录反证。

### quality_checks

- 没有异地登录不等于 token 泄露成立。
- token 泄露标签不是事实，必须有 token/session 证据。
- 租借账号、主动分享、合法授权需要排除。

### missing_evidence

- 实时 token 生命周期。
- 网关 / 风控引擎完整决策链路。
- 端侧设备指纹。
- 合法授权或多端登录解释。

### provider_conclusion_hint 规则

```text
token/session 与设备/IP/UA/地区冲突，且下游作恶由异常登录态承载时，可提示“数据支持 token/session 接管嫌疑”。
只有用户无感知或无异地登录时，不能提示强支持。
```

### dennis_final_judgement

由 Dennis Agent 生成，不由 Data Agent 生成。

## 5. complaint_false_positive_review

### 适用问题

非盗号、历史 case、不确定样本、导流封禁、反诈封禁、实名租借、账号主动分享、历史群控误伤等。

### 最小输入

- case_id
- user_id
- time_window
- complaint_reason 或 manual_note

### required_data_domains

- 用户信息域
- 后端数据域
- 策略引擎域
- 风险画像域
- 发布 / 内容域，如可查
- 账号安全事件域

### field_types_needed

- login_event
- device_id
- ip
- region
- publish_event
- content_status
- strategy_hit
- disposal_action
- risk_label
- sensitive_action
- manual_label

### join_paths_needed

- `user_id → strategy_hit/disposal_action`
- `user_id → login_event → device/IP/region`
- `user_id → publish_event/content_status`
- `strategy_hit → complaint_reason`
- `manual_note → data_findings`

### expected_outputs

- 处罚 / 封禁是否来自账号安全、反诈、导流、内容违规或其他策略。
- 是否存在异常登录、授权、token/session 接管。
- 是否存在本人历史设备持续在线。
- 是否存在发布行为，但缺账号接管链路。
- 历史 case 是否与当前申诉窗口一致。

### quality_checks

- 用户申诉不是事实。
- 无登录记录不能解释为无风险。
- 导流 / 反诈 / 历史处罚不能直接等同 ATO。
- 历史 case 不能证明当前窗口 ATO。

### missing_evidence

- 实时登录链路。
- 处罚策略完整 params。
- 内容审核细节。
- 人工复核结论。

### provider_conclusion_hint 规则

```text
如果数据无法构建“异常登录/授权/token → 账号接管 → 下游作恶”链路，且存在反诈/导流/历史处罚等正常解释，可提示“证据不足或更像非ATO客诉”。
只有正常行为链路充分且关键反证闭合时，才可提示“数据不支持ATO”。
```

### dennis_final_judgement

由 Dennis Agent 生成，不由 Data Agent 生成。
