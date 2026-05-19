# ATO Skill Coverage Review After Real Cases

## 1. 当前 ATO 真实试点总体结论

v2.4 第一阶段 Data Agent-only ATO 试点已完成 3 个关键真实 case，覆盖了两类正例和一个反例：

| case_id | 结论 | 验证能力 |
|---|---|---|
| `ATO_CASE_001_PASSWORD_KPN_RESWEEP` | `data_supports_ato_suspicion` | 密码登录、新设备、风控命中、发布行为、登录发布链路闭合 |
| `ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP` | `data_supports_ato_suspicion` | OAuth/扫码授权、Web 新设备、Token 生成、登录态接管、发布行为闭合 |
| `ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE` | `insufficient_support` | 反例 / 证据不足，不因用户申诉直接强判 ATO |

已经稳定的流程：

- 最小输入：`user_id + time_window + business_scene + target_action`。
- Data Agent-only question 能转成表检索、SQL 生成和执行跟进。
- SQL-only / pending_execution 状态机已经跑通。
- SQL ID → execution tracking → aggregate summary → parser evidence 已跑通。
- `provider_conclusion_hint` 与 Dennis Agent evidence judgement 已分离。
- 人工备注 / 用户申诉不进入事实证据。
- 正例和反例都能生成强 / 中 / 弱证据、反证、缺失证据、权限限制和质量风险。

仍依赖人工复核的部分：

- 内容是否违规，依赖内容审核或人工确认。
- `params` 高敏字段被移除后的策略决策流解释。
- token/session 实时生命周期、实时登录链路、设备指纹和在线关系图谱。
- 外部钓鱼、地推、KPN、回扫等人工备注来源验证。
- 最终盗号人工定性。

## 2. account_security_expert_skill 覆盖情况评分

| 维度 | 评分 | 说明 |
|---|---:|---|
| ATO 知识覆盖 | 82 | 已覆盖盗号、欺诈验证、token、登录异常、下游敏感动作，但缺 ATO 专项分型细节。 |
| ATO 取证链路覆盖 | 78 | 已有登录/token/设备/下游补证清单，但未显式写出“异常登录/授权 → 接管 → 发布/敏感动作”闭环。 |
| 强 / 中 / 弱证据边界 | 80 | 有通用强中弱证据，但真实 case 暴露的扫码/OAuth、SQL-only、反例边界还未进入 Skill。 |
| 反证和证据不足处理 | 84 | 已有正常换机、多端、漫游、本人操作等反证；Case 006 反例规则可进一步加强。 |
| Data Agent-only 状态处理 | 55 | Skill 本身没有 SQL-only、pending_execution、execution_result_ready 等工具状态规则。 |
| 人工备注 vs 数据事实边界 | 68 | Skill 有证据不足原则，但未明确“人工备注 / golden hint 不等于数据事实”。 |
| 反例不强判能力 | 78 | 通用禁止证据不足强结论已覆盖，但 ATO 反例专门规则不足。 |

综合判断：`account_security_expert_skill` 能支撑 ATO 基础研判，但缺一节 ATO / 账号接管专项取证规则。当前不建议大改，只建议轻量新增专项章节。

## 3. 6 个 ATO Pilot Case 覆盖矩阵

| case_id | 风险类型 | 是否已真实跑数 | Data Agent 返回状态 | conclusion_support | 覆盖的 ATO 链路 | 暴露的新规则 | 是否适合长期回归 |
|---|---|---|---|---|---|---|---|
| `ATO_CASE_001_PASSWORD_KPN_RESWEEP` | 密码泄露 / KPN / 发布链路 | 是 | `execution_result_ready` | `data_supports_ato_suspicion` | 密码登录 + 非历史设备 + 风控命中 + 发布行为 + 登录发布链路 | SQL-only 不能当证据；人工备注“已回扫/KPN”不能当事实；发布字段权限要记录 | 是 |
| `ATO_CASE_002_PHISHING_SHOP_NO_RESWEEP` | 钓鱼欺诈 / 未回扫 | 否 | 待跑 | 待定 | 钓鱼画像、异常登录、封禁前行为、未回扫边界 | 预计验证钓鱼备注不能当事实、未回扫降级 | 是 |
| `ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP` | 扫码/OAuth / 地推 / 发布链路 | 是 | `execution_result_ready` | `data_supports_ato_suspicion` | OAuth/扫码 → Web 新设备 → Token → 登录态接管 → 发布删除 | stealAccount 策略名是强证据；山东德州备注需按数据修正为山东青岛；已回扫未验证 | 是 |
| `ATO_CASE_004_SMS_LEAK_OAUTH_TOKEN_KICK` | 短信泄露 / OAuth / 踢 token | 否 | 待跑 | 待定 | 短信验证码、OAuth、token 踢出、资料变更 | 预计验证 token/session 证据和资料变更链路 | 是 |
| `ATO_CASE_005_MEMBER_PHISHING_SMS_CODE` | 会员钓鱼 / 验证码 / 发布 | 否 | 待跑 | 待定 | 验证码登录、钓鱼会员、发布链路、未回扫 | 预计验证申诉强但数据弱时的降级 | 是 |
| `ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE` | 反例 / 证据不足 | 是 | `execution_result_ready` | `insufficient_support` | 无异常登录、无 ATO 标签、发布行为但缺接管链路 | 无登录记录不能当无风险；申诉不等于 ATO；疑点可正常解释则降级 | 是 |

## 4. Case 001 暴露的新规则

- SQL-only / pending_execution 不能当证据。
- 只有 SQL 执行结果或明确空结果才能进入 evidence。
- 密码登录 + 新设备 + 风控命中 + 发布链路闭合，才能支持 ATO 嫌疑。
- 人工备注“已回扫 / KPN”不能当数据事实。
- 发布内容、精确时间、`params` 权限缺失必须进入 `permission_notes`。
- “数据支持 ATO 嫌疑”不等于最终人工盗号定性。

## 5. Case 003 暴露的新规则

- 扫码 / OAuth / Web 新设备 / Token 生成可以形成登录态接管链路。
- 策略名包含 `stealAccount` 是强证据，但仍需保留策略 params 缺失边界。
- 发布设备与 Web 新设备一致是强链路证据。
- “山东德州”人工备注未被数据验证时，必须修正为数据发现：山东青岛。
- “已回扫”仍不能当数据事实。
- 登录不异地不代表接管不成立；本 case 异地发生在发布阶段。

## 6. Case 006 暴露的新规则

- 用户申诉不等于盗号事实。
- 发布行为存在不等于 ATO 成立。
- 地区不一致不等于盗号成立。
- 无登录记录不能解释为无风险。
- 疑点可被正常行为解释时，应输出 `insufficient_support`。
- 证据不足反例必须纳入长期回归。

## 7. 是否需要回写 account_security_expert_skill

建议回写，但只做轻量新增，不重写 Skill。

建议新增章节：

```markdown
## ATO / 账号接管专项取证规则

### 适用场景
- 用户申诉账号被盗、内容违规后称非本人操作。
- 异常登录、扫码/OAuth 授权、短信/密码泄露、token/session 异常。
- 登录后发布、资料变更、换绑、改密、找回、注销等敏感动作。

### 最小输入
- user_id。
- time_window。
- suspicious_event_time。
- user_claim_summary。
- target_action：登录、授权、token/session、发布、资料变更、找回/改密/换绑、策略事件。

### 强证据
- 异常登录/授权后发生发布、资料变更、换绑、改密、找回。
- OAuth/扫码授权 → Web 新设备 → Token 生成 → 登录态接管链路。
- 密码登录 + 非历史设备 + 风控命中 + 下游发布链路闭合。
- 策略名或画像明确命中盗号/stealAccount，且与行为链路一致。

### 中证据
- 多设备、多 IP、短时间切换。
- 密码登录与历史习惯或申诉方向冲突，但缺长期基线。
- 风控命中但 params 或策略明细缺失。
- 发布行为存在，但内容或精确时间缺失。

### 弱证据
- 用户申诉。
- 人工备注。
- 单点地区差异。
- 只有发布结果，无异常登录或接管链路。

### 反证
- 历史设备、常用地区、本人设备可能性。
- 无 OAuth/扫码/token/session 异常。
- 无换绑/改密/找回。
- 无盗号/钓鱼/密码泄露标签。
- 疑点存在正常行为解释。

### 证据不足条件
- 无异常登录或授权链路。
- 发布存在但无法和接管链路闭合。
- 无登录记录但离线覆盖不确定。
- 关键字段无权限，无法解释策略或内容。

### 结论等级
- `data_supports_ato_suspicion`
- `local_highly_suspicious_but_overall_insufficient`
- `insufficient_support`
- `reverse_or_not_supported`

### Data Agent-only 边界
- SQL-only / pending_execution 不进入强中证据。
- execution_result_ready 才能进入 evidence。
- provider_conclusion_hint 不等于最终人工定性。

### 人工备注使用规则
- 人工备注是 golden hint，不是数据事实。
- 已回扫、地推、外部域名、KPN 等必须被数据验证或标为未验证。

### 反例不强判规则
- 用户申诉不等于盗号。
- 无登录记录不等于无风险。
- 地区不一致不等于盗号。
- 发布行为存在不等于 ATO。
```

## 8. 哪些内容该放在哪里

| 内容 | 建议位置 |
|---|---|
| ATO 通用判断、强中弱证据、反证、结论等级 | `account_security_expert_skill.md` |
| 具体字段、case 级证据清单、Data Agent-only 权限风险细节 | `ato_expected_evidence_and_boundaries_v1.md` |
| `sql_only`、`pending_execution`、`execution_result_ready`、`partial`、`empty_result` 等状态识别 | `dataagent_markdown_response_parser_v1.md` |
| SQL ID follow-up、聚合摘要、执行状态机模板 | `dataagent_sql_execution_followup_template_v1.md` |
| 发给 Data Agent 的自然语言取数问题 | `ato_dataagent_question_templates_v1.md` |
| 真实 case 选择、长期回归矩阵 | `ato_parser_regression_plan_v1.md` 与 case set |

## 9. 是否需要新增独立 ATO Skill

当前阶段不建议新增独立 `ato_account_takeover_expert_skill.md`，建议先增强 `account_security_expert_skill`。

理由：

- 路由复杂度：ATO 是账号安全核心子领域，单独拆 Skill 会增加路由和边界判断成本。
- 维护成本：目前真实跑数只有 3 个 case，尚未到独立 Skill 的规模。
- 内容膨胀程度：新增一节专项规则即可覆盖当前缺口。
- 后续条件：如果真实 case 扩展到 20+，覆盖撞库、短信、OAuth、token、钓鱼、找回、资料变更、商家账号等多分支，再考虑独立 Skill。

推荐：P0 先在 `account_security_expert_skill` 增加 ATO 专节；P2 观察是否独立拆 Skill。

## 10. Parser / Template 是否需要回写

| 文件 | 是否需要 | 理由 |
|---|---|---|
| `dataagent_markdown_response_parser_v1.md` | 暂不需要 | SQL 状态机、provider hint、permission、quality risk 已覆盖 3 case。 |
| `dataagent_sql_execution_followup_template_v1.md` | P1 可选 | 可补一个 full execution aggregate summary 示例，但不是阻塞。 |
| `ato_dataagent_question_templates_v1.md` | 暂不需要 | 已能驱动 Case 001/003/006 取数闭环。 |
| `ato_expected_evidence_and_boundaries_v1.md` | P1 建议 | 可补 Case 006 反例规则：“无登录记录不能当无风险”“发布存在不等于 ATO”。 |
| `ato_parser_regression_plan_v1.md` | P1 建议 | 将 Case 001/003/006 标为长期回归固定样例。 |

## 11. 覆盖率评分

| 维度 | 分数 |
|---|---:|
| ATO 知识覆盖 | 86 |
| ATO 执行覆盖 | 88 |
| Data Agent 取证覆盖 | 90 |
| SQL 状态机覆盖 | 92 |
| 正例覆盖 | 84 |
| 反例覆盖 | 82 |
| 人工复核边界覆盖 | 90 |
| 总体评分 | 87 |

评分理由：

- 已覆盖密码登录型、扫码/OAuth 型和证据不足反例。
- Data Agent-only 从 question 到 SQL execution 到 parser evidence 已跑通。
- 仍缺短信泄露、钓鱼未回扫、会员验证码钓鱼三类真实执行。
- account_security_expert_skill 尚未沉淀 ATO 专节，因此总体不打 90+。

## 12. 下一步建议

### P0：必须回写

- 在 `account_security_expert_skill.md` 轻量新增 `ATO / 账号接管专项取证规则`。
- 明确人工备注不是事实、申诉不是事实、无登录记录不是无风险。
- 明确 Data Agent-only provider hint 不替代最终判断。

### P1：建议回写

- 在 `ato_expected_evidence_and_boundaries_v1.md` 增补 Case 006 反例规则。
- 在 `ato_parser_regression_plan_v1.md` 将 Case 001/003/006 标为长期回归固定样例。
- 在 `dataagent_sql_execution_followup_template_v1.md` 增加 full execution aggregate summary 示例。

### P2：后续观察

- 跑 Case 002 / 004 / 005，覆盖钓鱼、短信泄露、会员验证码。
- 如果真实 case 增多，再评估是否独立 ATO Skill。

### 暂不做

- 暂不新增 `ato_account_takeover_expert_skill.md`。
- 暂不修改 parser 状态机。
- 暂不把 Data Agent-only 结论升级成自动治理动作。

## 13. 最终建议

- 建议回写 `account_security_expert_skill.md`，只新增 ATO 专项规则，不重写整个 Skill。
- 暂不建议新增独立 ATO Skill。
- 下一步具体让 Codex 做：轻量回写 account_security 的 ATO 专节，并同步更新 ATO evidence boundary / regression plan 的 Case 006 反例规则。

## 14. 是否修改核心 Skill

本轮未修改核心 Skill。只新增 review 文件。
