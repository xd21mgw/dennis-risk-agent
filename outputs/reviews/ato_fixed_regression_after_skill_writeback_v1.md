# ATO Fixed Regression After Skill Writeback v1

## 0. 回归范围

本轮基于已完成的 full parse 输出和回写后的规则做离线固定回归，不调用真实 Data Agent，不修改核心 Skill，不编造新数据。

参考输入：

- `outputs/reviews/ato_real_case_001_password_kpn_full_execution_parse.md`
- `outputs/reviews/ato_real_case_003_qr_scan_full_execution_parse.md`
- `outputs/reviews/ato_real_case_006_uncertain_no_clear_evidence_full_parse.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/account_security_expert_skill.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/18_real_dataagent_ato_pilot_cases/ato_expected_evidence_and_boundaries_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/18_real_dataagent_ato_pilot_cases/ato_parser_regression_plan_v1.md`

## 1. Case 001 固定回归

### 1.1 基本信息

```yaml
case_id: ATO_CASE_001_PASSWORD_KPN_RESWEEP
regression_type: positive_password_takeover
expected_conclusion: data_supports_ato_suspicion
actual_conclusion: data_supports_ato_suspicion
pass: true
```

### 1.2 ATO 专节规则命中

命中 `account_security_expert_skill.md` 的 ATO 专节：

- 适用场景：用户申诉账号被盗、异常登录后发布。
- 强证据：密码登录、非历史设备、风控命中、发布行为、登录发布链路闭合。
- Data Agent-only 边界：provider hint 不等于最终人工定性。
- 人工备注规则：KPN / 已回扫未被当作事实。
- 权限缺失规则：caption / upload_timestamp / params 进入缺失证据和质量风险。

### 1.3 证据校验

| 检查项 | 结果 | 说明 |
|---|---|---|
| strong_evidence 是否正确 | 通过 | 密码登录、非历史设备、风控命中、发布行为、登录发布链路均进入强证据。 |
| medium_evidence 是否正确 | 通过 | 多设备多 IP、策略命中但 params 缺失等被放在中证据。 |
| weak_evidence 是否正确 | 通过 | 用户申诉、人工备注、内容违规原因未验证保留为弱证据。 |
| counter_evidence 是否保留 | 通过 | 注册地一致、无换绑/改密/找回、无直接标签、无 token/session 线索均保留。 |
| missing_evidence 是否保留 | 通过 | 作品精确时间、caption、params、回扫记录、KPN 来源缺失均保留。 |
| provider_limitations 是否保留 | 通过 | Data Agent-only 离线取证和实时链路缺失保留。 |
| 人工备注是否未被当作事实 | 通过 | “已回扫 / KPN”仅为 golden hint，未作为数据事实。 |
| 用户申诉是否未被当作事实 | 通过 | 申诉只作为背景。 |
| provider_conclusion_hint 是否未被当作最终人工定性 | 通过 | 输出为数据层支持 ATO 嫌疑，不等同最终人工定性。 |
| 是否存在强判 / 误判 / 降级不足 | 未发现 | 结论强度与 evidence 闭合程度匹配。 |

### 1.4 结论

Case 001 通过。回写后的 ATO 专节能稳定支持密码登录型账号接管正例，同时保留人工备注、权限缺口和最终人工定性边界。

## 2. Case 003 固定回归

### 2.1 基本信息

```yaml
case_id: ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP
regression_type: positive_qr_oauth_takeover
expected_conclusion: data_supports_ato_suspicion
actual_conclusion: data_supports_ato_suspicion
pass: true
```

### 2.2 ATO 专节规则命中

命中 `account_security_expert_skill.md` 的 ATO 专节：

- 适用场景：扫码 / OAuth 授权异常、Web 新设备登录、内容违规封禁后申诉。
- 强证据：OAuth / 扫码授权后 Web 新设备登录并生成 token。
- 强证据：策略名包含 `stealAccount`。
- 强证据：登录 / 授权 → token 生成 → 发布动作链路闭合。
- 人工备注规则：山东德州、已回扫、地推均未当作数据事实。
- 反证保留：登录河南濮阳与注册地一致，不支持登录阶段异地。

### 2.3 证据校验

| 检查项 | 结果 | 说明 |
|---|---|---|
| strong_evidence 是否正确 | 通过 | OAuth/扫码、Web 新设备、Token、stealAccount、发布链路均进入强证据。 |
| medium_evidence 是否正确 | 通过 | 4 分钟多次扫码、多设备多 IP、多 token、密码重置被拦截进入中证据。 |
| weak_evidence 是否正确 | 通过 | 用户申诉、扫码地推/已回扫备注、山东德州线索作为弱证据或未验证线索。 |
| counter_evidence 是否保留 | 通过 | 登录地区等于注册地、无换绑/改密/找回、山东德州未命中、回扫未验证均保留。 |
| missing_evidence 是否保留 | 通过 | 作品精确时间、caption、params、实时扫码流程、回扫记录等均保留。 |
| provider_limitations 是否保留 | 通过 | Data Agent-only 无法覆盖实时扫码、二维码内容、token 生命周期、在线图谱。 |
| 人工备注是否未被当作事实 | 通过 | 山东德州被修正为山东青岛；已回扫未被当作事实。 |
| 用户申诉是否未被当作事实 | 通过 | 申诉只作为背景。 |
| provider_conclusion_hint 是否未被当作最终人工定性 | 通过 | 数据支持盗号嫌疑保留为数据层结论，不替代人工定性。 |
| 是否存在强判 / 误判 / 降级不足 | 未发现 | 结论与完整 OAuth/扫码接管链路匹配。 |

### 2.4 结论

Case 003 通过。回写后的 ATO 专节能稳定支持扫码/OAuth 型账号接管正例，并正确修正人工备注中的山东德州偏差。

## 3. Case 006 固定回归

### 3.1 基本信息

```yaml
case_id: ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE
regression_type: negative_or_insufficient_support
expected_conclusion: insufficient_support
actual_conclusion: insufficient_support
pass: true
```

### 3.2 ATO 专节规则命中

命中 `account_security_expert_skill.md` 的 ATO 专节：

- 证据不足条件：用户申诉但数据无法验证异常登录。
- 证据不足条件：有发布行为但没有异常登录或登录态接管链路。
- 反例不强判：用户申诉 + 发布行为不等于 ATO。
- 反例不强判：地区不一致不等于 ATO。
- 反例不强判：无登录记录不等于无风险，也不等于 ATO。
- 反证：疑点可被本人设备、跨省移动、正常找回或正常注销解释。

### 3.3 证据校验

| 检查项 | 结果 | 说明 |
|---|---|---|
| strong_evidence 是否正确 | 通过 | strong_evidence 为空，没有强行构造 ATO 证据。 |
| medium_evidence 是否正确 | 通过 | 密码重置后新设备找回、广东到浙江发布、注销尝试主体不明作为中等疑点。 |
| weak_evidence 是否正确 | 通过 | 申诉文本、发布行为但缺链路、地区不一致但有正常解释作为弱证据。 |
| counter_evidence 是否保留 | 通过 | 无登录、历史设备、无 OAuth/扫码、无 ATO 标签、无 token/session、无换绑/改密均保留。 |
| missing_evidence 是否保留 | 通过 | 实时登录链路、设备指纹、token/session、找回详情、注销主体、caption 等缺失保留。 |
| provider_limitations 是否保留 | 通过 | Data Agent-only 离线覆盖限制和“无登录记录不等于实时无登录”保留。 |
| 人工备注是否未被当作事实 | 通过 | manual_label 否和无细分类备注仅作为背景，未直接替代证据。 |
| 用户申诉是否未被当作事实 | 通过 | 未因申诉称被盗而强判 ATO。 |
| provider_conclusion_hint 是否未被当作最终人工定性 | 通过 | `证据不足` 是数据层支持程度，不关闭为最终无风险。 |
| 是否存在强判 / 误判 / 降级不足 | 未发现 | 正确停留 `insufficient_support`。 |

### 3.4 结论

Case 006 通过。回写后的 ATO 专节能稳定处理反例，不因申诉、发布行为、地区不一致强判 ATO，也不把无登录记录解释为无风险。

## 4. 汇总

| case_id | expected_conclusion | actual_conclusion | 是否通过 |
|---|---|---|---|
| `ATO_CASE_001_PASSWORD_KPN_RESWEEP` | `data_supports_ato_suspicion` | `data_supports_ato_suspicion` | 通过 |
| `ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP` | `data_supports_ato_suspicion` | `data_supports_ato_suspicion` | 通过 |
| `ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE` | `insufficient_support` | `insufficient_support` | 通过 |

```yaml
pass_rate: 3/3
pass_rate_percent: 100
```

## 5. 是否有规则回写不生效

未发现。ATO 专节中的以下规则均被验证命中：

- 强证据链路：密码登录型、扫码/OAuth 型。
- 人工备注不是事实。
- 用户申诉不是事实。
- Data Agent provider hint 不等于最终人工定性。
- SQL / provider 状态和权限缺口需保留。
- 反例不强判。
- 无登录记录不等于无风险。

## 6. 是否需要继续回写

### account_security_expert_skill

暂不需要继续回写。当前 ATO 专节已能覆盖 3 个固定回归样例。

后续如跑完 Case 002 / 004 / 005，再根据钓鱼、短信泄露、会员验证码链路补充细节。

### parser / evidence boundary / question template

- `dataagent_markdown_response_parser_v1.md`：暂不需要。
- `ato_expected_evidence_and_boundaries_v1.md`：暂不需要。
- `ato_dataagent_question_templates_v1.md`：暂不需要。
- `ato_parser_regression_plan_v1.md`：暂不需要。

## 7. 是否可以进入 Case 002 / 004 / 005 扩展回归

可以。

建议顺序：

1. `ATO_CASE_004_SMS_LEAK_OAUTH_TOKEN_KICK`：补短信泄露 + OAuth/token 链路。
2. `ATO_CASE_002_PHISHING_SHOP_NO_RESWEEP`：补钓鱼欺诈 + 未回扫降级边界。
3. `ATO_CASE_005_MEMBER_PHISHING_SMS_CODE`：补会员验证码钓鱼 + 发布链路。

## 8. 是否修改核心 Skill

本轮未修改核心 Skill。仅新增离线回归输出文件。
