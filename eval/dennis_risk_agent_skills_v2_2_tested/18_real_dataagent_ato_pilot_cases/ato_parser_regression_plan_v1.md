# ATO Parser Regression Plan v1

## 0. 目标

定义 6 个 ATO 真实只读试点 case 后续如何用于 Data Agent markdown parser、`unified_normalized_evidence` 和 Dennis Agent 人工复核闭环回归。

## 1. 通用回归检查项

每个 case 都需要验证：

- Data Agent 是否理解 ATO 问题。
- 是否返回登录 / 设备 / IP / token / 发布 / 策略 / 画像相关数据。
- 是否能区分数据发现和模型推测。
- 是否能识别 `sql_only` / `partial` / `no_permission` / `empty_result` / `failed`。
- 是否能识别 `sql_only / pending_execution`：表检索 + SQL 生成已完成，但没有执行结果。
- 是否能生成 `unified_normalized_evidence`。
- 是否能区分强 / 中 / 弱证据。
- 是否能记录反证和缺失证据。
- 是否能避免“用户申诉 = 盗号”的强判。
- 是否支持人工复核。

## 2. 统一 Parser 输出要求

每次解析 Data Agent 返回后，至少输出：

- `provider: dataagent_provider`
- `provider_response_id`
- `status`
- `execution_state`，如 `pending_execution`
- `returned_type`
- `evidence_plan`
- `data_findings`
- `provider_conclusion_hint`
- `key_findings`
- `strong_evidence`
- `medium_evidence`
- `weak_evidence`
- `counter_evidence`
- `missing_evidence`
- `quality_risks`
- `provider_limitations`
- `permission_notes`
- `manual_review_required`
- `raw_result_reference`

`dennis_final_judgement` 不得由 parser 或 Data Agent 填充，必须由 Dennis 主 Agent 单独生成。

## 2.1 SQL-only / pending_execution 回归规则

定义：

- `sql_only`：Data Agent 只返回 SQL、查询逻辑、表检索结果或查询计划，没有执行结果。
- `pending_execution`：Data Agent 明确等待授权执行，或要求人工下载 SQL 后执行。

回归要求：

- `status` 必须为 `sql_only`。
- `execution_state` 必须为 `pending_execution`。
- `strong_evidence` 必须为空。
- `medium_evidence` 必须为空。
- SQL 取证计划只能进入 `weak_evidence` 或 `evidence_plan`。
- `conclusion_support.level` 必须为 `insufficient_support`。
- 必须生成 `next_action: execute_sql_or_request_execution`。
- `manual_review_required` 必须为 `true`。
- 只有拿到 SQL 执行结果后，才能重新进入 parser evidence 阶段。

ATO 第一阶段如果连续返回 SQL-only，应优先复盘流程问题：

- Data Agent 是否支持授权后执行 SQL。
- 是否需要人工执行 SQL。
- 执行结果如何回填到 case 记录。
- 是否需要把“授权执行 / 人工执行”做成试点前置操作。

## 3. Case 级 Parser Focus

### ATO_CASE_001_PASSWORD_KPN_RESWEEP

重点看：
- 密码登录是否出现。
- 登录方式是否偏离历史习惯。
- 异常设备 / IP / 地区是否出现。
- 异常登录与违规发布是否存在时间链路。
- 回扫记录是否与时间窗口和链路一致。

预期边界：
- 如果只看到人工备注“已回扫”，但没有登录和发布链路，不能强判。
- 如果 Data Agent 返回 SQL-only / pending_execution，强 / 中证据必须为空，SQL 计划只能进入 `evidence_plan` 或弱证据，下一步为 `execute_sql_or_request_execution`。

### ATO_CASE_002_PHISHING_SHOP_NO_RESWEEP

重点看：
- 钓鱼风险画像或策略命中是否存在。
- 异常登录是否和用户声称不在线时段接近。
- 未回扫状态是否导致证据不足。
- 是否有违规发布或封禁前链路。

预期边界：
- 疑似钓鱼域名备注不能直接当作外部来源事实。
- 未回扫不等于未盗号，只说明证据缺口更大。

### ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP

重点看：
- 扫码 / OAuth / 授权行为是否出现。
- 异地或非常用环境是否出现。
- token/session 是否发生踢出、复用、异常切换。
- 地推线索是否只能作为人工备注，还是有数据侧链路支撑。

预期边界：
- 本人扫码可能是被诱导，但平台看到的可能是本人动作，需要识别“本人参与但非真实意愿”的边界。
- 缺外部地推来源数据时不能把地推备注当事实。

### ATO_CASE_004_SMS_LEAK_OAUTH_TOKEN_KICK

重点看：
- 短信验证码登录或短信验证链路。
- OAuth 授权变化。
- token/session 被踢或多端冲突。
- 账号资料变更、昵称头像变化、验证失败链路。

预期边界：
- 用户称昵称头像变化是弱证据，需要数据侧资料变更记录。
- token 踢出如果只有人工备注，不能进入强证据。

### ATO_CASE_005_MEMBER_PHISHING_SMS_CODE

重点看：
- 验证码登录是否出现。
- 会员钓鱼场景是否只能作为用户描述和人工备注。
- 异常登录与违规发布是否存在闭合时间链路。
- 未回扫状态下如何降级。

预期边界：
- “从别的平台购买会员”是用户描述，不是外部钓鱼来源事实。
- 若只看到违规发布，没有登录环境突变，则只能证据不足。

### ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE

重点看：
- 反例 / 不确定样本。
- 是否能避免因用户申诉直接判断盗号。
- 是否存在常用设备、常用 IP、历史一致登录方式等反证。
- 是否缺少明确回扫、风险细分类和链路证据。

预期边界：
- 若数据链路正常，应支持“反向排除 / 更像本人操作或证据不支持”。
- 若数据缺失，应输出证据不足，而不是为了贴合申诉强判。

## 4. 回归通过标准

- 6 个 case 都能生成结构化 parser 输出。
- SQL-only 不进入强 / 中证据链。
- SQL-only / pending_execution 必须生成 `evidence_plan`、`next_action: execute_sql_or_request_execution` 和 `manual_review_required=true`。
- no_permission / partial / failed 必须降级。
- 用户申诉和人工备注不会进入强证据。
- Data Agent 结论性文字只进入 `provider_conclusion_hint`。
- Dennis Agent 单独生成最终研判，并保留人工复核入口。

## 5. 长期固定回归样例

### ATO_CASE_001_PASSWORD_KPN_RESWEEP

```yaml
regression_type: positive_password_takeover
expected_conclusion: data_supports_ato_suspicion
core_chain:
  - 密码登录
  - 新设备 / 非历史设备
  - 风控命中
  - 发布行为
  - 登录发布链路闭合
must_not:
  - 不得把已回扫人工备注当事实
  - 不得把 KPN 人工备注当事实
  - 不得把 Data Agent provider_conclusion_hint 当最终人工定性
  - 不得忽略 caption / upload_timestamp / params 权限限制
```

### ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP

```yaml
regression_type: positive_qr_oauth_takeover
expected_conclusion: data_supports_ato_suspicion
core_chain:
  - OAuth / 扫码授权
  - Web 新设备
  - Token 生成
  - 登录态接管
  - 发布行为闭环
must_not:
  - 不得把山东德州当已验证数据事实
  - 不得把已回扫当数据事实
  - 不得把地推场景当直接数据事实
  - 不得忽略 params / caption / upload_timestamp 权限限制
```

### ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE

```yaml
regression_type: negative_or_insufficient_support
expected_conclusion: insufficient_support
core_chain:
  - 无异常登录记录
  - 无 OAuth / 扫码授权
  - 无 token/session 接管证据
  - 有发布行为但缺接管链路
  - 疑点存在正常解释
must_not:
  - 不得因用户申诉强判 ATO
  - 不得因发布行为强判 ATO
  - 不得因地区不一致强判 ATO
  - 不得把无登录记录解释为无风险
  - 不得把证据不足样本关闭为最终无风险
```
