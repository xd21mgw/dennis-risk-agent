# ATO Account Takeover Real Pilot Runbook v1

## 0. 试点定位

v2.4 第一优先级从“协议攻击补证”调整为“ATO / 账号盗号判定只读试点”。协议攻击 Data Agent-only 试点保留，但降为第二优先级。

当前阶段仍是 Data Agent-only，只做离线 / Hive / BI / 数据平台取证。Data Agent 负责取数、找表、SQL 生成、数据摘要、覆盖范围、缺失证据和口径风险；Dennis Agent 负责证据解释、结论等级、边界降级和治理建议；人工复核负责最终确认。

## 1. 适用问题

- 用户申诉账号被盗。
- 异常登录后发生违规发布。
- 钓鱼 / 扫码 / 短信泄露 / 密码泄露 / OAuth token 异常。
- 内容违规封禁后申诉称非本人操作。
- 账号资料变化、token/session 异常、换绑、改密、找回与异常登录链路排查。

## 2. 不适用问题

- 实时拦截。
- 自动解封。
- 自动处罚。
- 自动冻结、扣除或封禁。
- 自动策略上线。
- 只凭申诉文本判断是否盗号。
- 需要实时登录链路、实时设备指纹、实时策略引擎决策明细才能闭合的强结论。

## 3. 最小输入

真实只读 case 启动前必须具备：

- `user_id`：必填。
- `time_window`：必填，建议不超过 7 天。
- `suspicious_event_time`：建议提供，用于收敛时间窗口。
- `user_claim_summary`：建议提供，用于理解用户申诉，不作为事实。
- `manual_note`：可作为人工备注 / golden hint，不作为事实。
- `business_scene`：账号安全 / 盗号申诉 / ATO。
- `target_api_or_action`：登录行为、登录方式变化、设备/IP/地区变化、token/session、发布、资料变更、换绑、改密、找回、策略命中、风险画像、回扫记录。

缺少 `user_id` 或 `time_window` 时，case 标记为 `blocked_by_missing_minimum_inputs`，不得调用 Data Agent，不得生成风险结论。

## 4. 取证流程

1. Case 输入：读取 case_id、user_id、time_window、用户描述、人工备注。
2. Data Agent question：根据 `ato_dataagent_question_templates_v1.md` 生成自然语言取数问题。
3. Data Agent markdown response：人工把真实返回粘贴进 case 记录。
4. Parser：按 Data Agent-only markdown parser 解析为 `unified_normalized_evidence`。
5. Evidence：抽取数据发现、强 / 中 / 弱证据、反证、缺失证据、质量风险、provider limitation。
6. Dennis Agent 解释：基于证据输出 evidence-based judgement，不复述 Data Agent 结论为最终判断。
7. 人工复核：人工确认最终标签、误读点、回写位置。
8. 回写沉淀：必要时回写 parser、question template、evidence boundaries 或 case set。

## 4.1 SQL-only / pending_execution 中间状态

ATO Data Agent-only 真实试点中，Data Agent 可能只完成表检索和 SQL 生成，尚未执行查询。这类返回统一标记为：

```yaml
status: sql_only
execution_state: pending_execution
```

定义：

- Data Agent 已识别候选数据范围或生成一组 / 多组只读 SQL。
- Data Agent 未返回执行结果、样本统计、表格摘要或数据发现。
- Data Agent 正在等待授权执行，或要求人工下载 SQL 后执行。

处理规则：

- SQL-only 不得进入 `strong_evidence`。
- SQL-only 不得进入 `medium_evidence`。
- SQL 取证计划只能进入 `weak_evidence` 或 `evidence_plan`。
- 必须生成 `next_action: execute_sql_or_request_execution`。
- 必须标记 `manual_review_required: true`。
- 只有拿到 SQL 执行结果后，才能重新进入 parser evidence 阶段。
- 不得基于“已回扫”“人工备注”或“SQL 覆盖完整”直接判断明确盗号或高度疑似盗号。

第一阶段如果连续返回 `sql_only / pending_execution`，优先解决流程问题：

- Data Agent 是否支持用户授权后直接执行 SQL。
- 是否需要人工下载 SQL 到数据平台执行。
- 执行结果如何回填到 case 记录。
- SQL 执行前是否需要人工确认只读、时间窗口、user_id 和业务动作范围。

## 4.2 SQL execution follow-up 状态机

ATO Data Agent-only 试点采用以下 SQL 执行状态机：

| 状态 | 含义 | 允许动作 | 禁止动作 |
|---|---|---|---|
| `sql_only` | 只有 SQL / 查询计划 | 记录 evidence_plan | 进入强/中证据 |
| `pending_execution` | 等待授权或人工执行 | 生成执行请求 | 风险判断 |
| `execution_in_progress` | SQL 已提交，任务 running | 记录 SQL ID 和执行进度 | 将 running 当证据 |
| `execution_result_ready` | 单个 SQL 完成并返回聚合摘要 | 进入候选数据发现解析 | 跳过质量风险 |
| `execution_partial` | 部分完成、部分 running / failed / no_permission | 局部解析已完成结果，整体降级 | 最终判断 |
| `execution_failed` | 执行失败 | 记录失败和重试动作 | 当作无风险 |
| `execution_no_permission` | 无权限或字段裁剪影响结果 | 记录 permission_notes 和缺口 | 强结论 |
| `execution_timeout` | 执行超时 | 收窄窗口/拆分查询 | 当作空结果 |
| `evidence_ready` | 必要 SQL 均有结果或明确空结果 | 进入 parser evidence 阶段 | 忽略未完成任务 |

SQL ID follow-up 必须记录：

- SQL ID。
- 查询目的。
- 执行状态。
- 返回行数 / 聚合规模。
- 是否权限裁剪。
- 是否字段移除。
- 是否影响结论。
- 聚合摘要。
- 数据发现。
- 缺失证据。
- 权限限制。
- 质量风险。

规则：

- `running` 不能进入 evidence。
- SQL-only 不能进入 strong / medium evidence。
- 只有执行结果或明确空结果才能进入 parser evidence 阶段。
- 如果部分 SQL 完成、部分 running，只能生成 partial execution status，不能做最终判断。
- 聚合摘要优先，不返回全量明细。
- Data Agent 只取数，Dennis Agent 才解释证据。

## 5. 结论边界

- Data Agent 输出 `provider_conclusion_hint`。
- Dennis Agent 输出 `evidence_based_judgement`。
- 人工复核输出最终确认。
- 缺实时登录链路、实时设备指纹、策略引擎明细、外部钓鱼来源、在线关系图时，不得输出强结论。
- 用户申诉和人工备注只能作为背景和 golden hint，不得直接进入强证据。
- `sql_only / pending_execution` 只能支持“取证计划合理”，不能支持 ATO 风险结论。

## 6. Evidence 要求

首轮优先收集：

- 登录时间、登录方式、登录环境。
- 设备 / IP / 地区变化。
- token/session 被踢、复用、冲突或异常切换。
- 登录后发布作品、资料变更、换绑、改密、找回等敏感动作。
- 敏感动作与异常登录之间的时间链路。
- 风险画像、策略命中、回扫记录或处置链路。

必须保留：

- 数据发现 vs 模型推测。
- 反证。
- 缺失证据。
- 权限限制。
- 口径风险。
- Data Agent-only provider limitations。
- SQL-only / pending_execution 是否发生，以及是否已完成执行闭环。
- SQL ID、执行状态和聚合摘要是否完整。

## 7. 第一批 6 Case

| case_id | 样本定位 | 首轮用途 |
|---|---|---|
| ATO_CASE_001_PASSWORD_KPN_RESWEEP | 密码泄露 + 已回扫 | 正例链路，验证密码登录、异常设备、发布链路、回扫记录 |
| ATO_CASE_002_PHISHING_SHOP_NO_RESWEEP | 钓鱼欺诈 + 未回扫 | 测试钓鱼画像、未回扫和证据不足边界 |
| ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP | 扫码欺诈 + 地推 + 已回扫 | 测试扫码 / OAuth / token / 异地链路 |
| ATO_CASE_004_SMS_LEAK_OAUTH_TOKEN_KICK | 短信泄露 + OAuth 踢 token + 已回扫 | 测试短信验证码、OAuth、token 踢出、资料变更 |
| ATO_CASE_005_MEMBER_PHISHING_SMS_CODE | 会员钓鱼 + 验证码 + 未回扫 | 测试验证码钓鱼和发布链路 |
| ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE | 不确定 / 人工标签否 | 反例，测试不因申诉强判盗号 |

## 8. 第一轮建议运行

建议先跑：

1. `ATO_CASE_001_PASSWORD_KPN_RESWEEP`
2. `ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP`
3. `ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE`

原因：

- Case 001 是密码泄露 + 已回扫正例，适合验证强证据链路。
- Case 003 是扫码欺诈 + 地推链路，适合验证 OAuth / token / 异地接管边界。
- Case 006 是反例 / 不确定样本，适合验证不过度强判。

## 9. 审计与回放

每个真实 case 必须记录：

- 原始用户问题。
- case 输入。
- Data Agent question。
- Data Agent response 原文引用。
- parser 输出。
- `unified_normalized_evidence`。
- Dennis Agent evidence-based judgement。
- 人工最终判断。
- 是否需要回写 parser / question template / evidence boundaries / Skill。

## 10. 禁止行为

- 不调用真实 Data Agent 之外的未接入 provider。
- 不编造真实 API、真实表名、真实字段名、真实 SQL。
- 不编造 SQL 执行结果。
- 不把人工备注当作数据事实。
- 不把用户申诉当作盗号事实。
- 不把 SQL-only / pending_execution 当作已查数结果。
- 不输出处罚、冻结、扣除、封禁、自动解封或策略上线建议。
- 不把 Data Agent 的 provider hint 当作 Dennis 最终判断。
