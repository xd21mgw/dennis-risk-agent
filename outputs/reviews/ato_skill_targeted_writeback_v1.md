# ATO Skill Targeted Writeback v1

## 1. 本轮修改文件

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/account_security_expert_skill.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/18_real_dataagent_ato_pilot_cases/ato_expected_evidence_and_boundaries_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/18_real_dataagent_ato_pilot_cases/ato_parser_regression_plan_v1.md`

## 2. 新增文件

- `outputs/reviews/ato_skill_targeted_writeback_v1.md`

## 3. account_security_expert_skill 新增了哪些 ATO 规则

新增 `## 4.1 ATO / 账号接管专项取证规则`，覆盖：

- ATO 适用场景。
- 最小输入和缺输入处理。
- ATO 强证据、中证据、弱证据。
- ATO 反证。
- ATO 证据不足条件。
- 四档结论等级：`data_supports_ato_suspicion`、`partial_support`、`insufficient_support`、`data_does_not_support_ato`。
- Data Agent-only 边界。
- 人工备注使用规则。
- 反例不强判规则。

## 4. 来自 Case 001 的规则

- SQL-only / pending_execution / running 不是证据。
- 只有 SQL 执行结果才能进入 evidence。
- 密码登录 + 非历史设备 + 风控命中 + 发布链路闭合，才支持 ATO 嫌疑。
- 人工备注“已回扫 / KPN”不是数据事实。
- `caption` / `upload_timestamp` / `params` 权限缺失必须记录。

## 5. 来自 Case 003 的规则

- OAuth / 扫码授权 + Web 新设备 + token 生成，可以形成登录态接管链路。
- `stealAccount` 策略命中是强策略证据，但仍需保留策略明细缺失边界。
- 发布设备与 Web 新设备一致是强链路证据。
- 山东德州人工备注未被数据验证时，必须按数据发现修正。
- 已回扫仍需数据或回扫记录验证。

## 6. 来自 Case 006 的规则

- 用户申诉不等于盗号事实。
- 发布行为存在不等于 ATO 成立。
- 地区不一致不等于 ATO 成立。
- 无登录记录不能解释为无风险，也不能直接支持 ATO。
- 找回 / 密码重置 / 注销尝试需要结合登录链路和设备归属判断。
- 疑点可被正常行为解释时，结论停留 `insufficient_support`。

## 7. 哪些内容没有回写到 Skill

保留在 evidence boundary：

- Case 级字段细节、权限缺失细节、强/中/弱证据扩展解释。
- Case 006 反例规则的细粒度解释。

保留在 parser：

- `sql_only`、`pending_execution`、`execution_in_progress`、`execution_result_ready`、`execution_partial` 等状态识别逻辑。
- `provider_conclusion_hint`、`permission_notes`、`quality_risks` 的结构化映射。

保留在 template：

- Data Agent 自然语言问题模板。
- SQL ID follow-up prompt。

## 8. 是否新增独立 ATO Skill

未新增独立 ATO Skill。

判断：当前阶段继续增强 `account_security_expert_skill` 更合适。ATO 仍是账号安全核心子领域，真实 case 已跑 3 个，尚未到需要单独拆分 Skill 的规模。后续当真实 case 覆盖 20+ 且包含撞库、短信泄露、OAuth、token、钓鱼、找回、资料变更、商家账号等多分支时，再评估独立 `ato_account_takeover_expert_skill.md`。

## 9. 是否修改其他核心 Skill

未修改其他核心 Skill。

本轮只修改 `account_security_expert_skill.md` 一个核心 Skill，且为定点新增 ATO 专节。

## 10. 下一步如何回归验证

建议回归：

1. 跑 `ATO_CASE_001_PASSWORD_KPN_RESWEEP`，预期 `data_supports_ato_suspicion`，不得把已回扫 / KPN 人工备注当事实。
2. 跑 `ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP`，预期 `data_supports_ato_suspicion`，不得把山东德州 / 已回扫当数据事实。
3. 跑 `ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE`，预期 `insufficient_support`，不得因申诉、发布、地区不一致强判 ATO，也不得把无登录记录当无风险。
4. 继续跑 Case 002 / 004 / 005，覆盖钓鱼未回扫、短信泄露 OAuth token、会员验证码钓鱼。

## 11. 回写摘要

本轮将真实 Data Agent-only ATO pilot 的核心经验回写到账号安全主 Skill：

- 正例链路：密码登录型、扫码/OAuth 型。
- 反例链路：证据不足、不强判。
- 工具边界：Data Agent-only 只取数，provider hint 不是最终定性。
- 人工备注边界：备注是 golden hint，不是事实。
- 结论边界：数据支持嫌疑、局部支持、证据不足、数据不支持四档。
