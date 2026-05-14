# Data Agent 迁移接入说明 v1

## 0. 目标

本文件说明 Dennis 风控 Agent 后续如何从当前 Codex 阶段迁移到可真实调用 Data Agent 的内部平台阶段。

当前阶段只沉淀工具抽象层，不调用 Data Agent，不定义真实 API，不编造表、字段、接口路径。

## 1. 当前 Codex 阶段

当前能力边界：

- 可以读取 `dataagent_capability_profile_v1.md` 理解 Data Agent 能力。
- 可以生成 `dataagent_tool_contract_v1.md` 中定义的 `query_intent`。
- 可以参考 `risk_evidence_to_dataagent_query_map_v1.md` 选择证据类型。
- 可以用 `dataagent_result_interpretation_rules_v1.md` 解释未来返回。
- 可以用 `dataagent_conclusion_thresholds_v1.md` 判断够不够下结论。
- 可以用 `dataagent_mock_response_schema_v1.md` 设计 mock 测试。

当前禁止：

- 真实调用 Data Agent。
- 声称已经访问内部平台。
- 编造 API、认证、真实表、字段、分区、看板、实验结果。

## 2. 未来内部平台阶段接入架构

建议分层：

1. Dennis 风控 Agent
   - 负责风险问题理解、Skill 路由、证据需求、结论解释、治理建议。

2. Tool Contract Adapter
   - 接收标准 `query_intent`。
   - 做参数校验、权限校验、审计记录。
   - 将抽象意图转换为真实 Data Agent 请求。

3. Data Agent
   - 执行数据查询、找表、SQL、看板分析、AB 分析、画像圈选。

4. Result Normalizer
   - 将 Data Agent 返回规范化为 `dataagent_mock_response_schema_v1.md` 的结构或其正式版本。

5. Dennis Result Interpreter
   - 基于解释规则和结论阈值输出风险结论与治理建议。

## 3. 接入流程

```text
用户风险问题
  -> Dennis 风控 Agent 识别领域 / 风险类型 / 主辅 Skill
  -> 生成 query_intent
  -> 平台校验权限和安全边界
  -> Adapter 转换为真实 Data Agent 请求
  -> Data Agent 执行数据任务
  -> Result Normalizer 标准化返回
  -> Dennis 风控 Agent 做证据解释
  -> 输出结论等级 / 反证 / 补证 / 治理 / 指标
```

## 4. query_intent 到平台调用的迁移要求

迁移时应保持以下原则：

- `risk_question` 必须保留用户原始业务问题。
- `target_evidence` 必须是明确证据类型，不能泛化为“查异常”。
- `minimum_inputs.missing` 非空时，不应直接触发真实查询，应先向用户或平台补齐。
- `query_dimensions` 只描述语义，真实表字段映射由平台侧或 Data Agent 完成。
- `safety_boundary` 必须随请求传递，防止结果被下游直接处罚化。
- 所有真实调用都需要审计、权限校验和结果留痕。

## 5. 返回结果标准化要求

未来 Data Agent 返回结果应被标准化为：

- 请求元信息。
- 输入回显。
- 指标摘要。
- 分层结果。
- 样本说明。
- 候选资产说明。
- 数据质量和权限限制。
- 解释提示。
- 推荐下一轮查询。

标准化后仍不得直接触发处罚，必须交给 Dennis 风控 Agent 做二次解释。

## 6. 权限和安全

必须纳入平台权限控制：

- 内部看板和数据集访问权限。
- 表和字段权限。
- AB 实验访问权限。
- 画像标签和人群圈选权限。
- 敏感数据访问和导出权限。
- 人群包创建、导出、管理权限。

敏感要求：

- HRBI 等敏感域不纳入 Data Agent 自动访问。
- 用户 ID、账号 ID、设备 ID、token、手机号等敏感标识必须脱敏或最小化。
- 结果只服务风险研判，不允许绕过治理审批。

## 7. 失败和降级

平台调用失败时，Dennis 风控 Agent 应：

1. 标明失败类型：权限不足、输入缺失、平台不支持、数据质量问题、执行失败。
2. 不编造结果。
3. 将结论降级为“证据不足”。
4. 输出人工查数清单或下一轮补证 `query_intent`。
5. 对高风险处置建议保留灰度、复核和回滚。

## 8. 回归测试建议

迁移前至少使用以下 case 验证：

- 前端无日志但官方包埋点缺失。
- 设备聚集但为合法商家/MCN 运营。
- 真人设备离散但任务化完成。
- 低钱效但无黑产收益链。
- CTIT 异常但由归因规则调整导致。
- 外网跟价但内部接口无异常。
- DAU/DNU 异常但由 SLA 或实验流量导致。
- 私信关注异常但缺少站外承接。

每个 case 必须验证：

- query_intent 是否问对证据。
- Data Agent 返回是否被正确解释。
- 结论是否按阈值降级。
- 是否输出反证和业务损伤。
- 是否避免直接处罚化。

## 9. 版本演进

后续建议版本：

- v1：能力画像、工具契约、证据映射、解释规则、阈值、mock schema。
- v2：接入真实平台 adapter，但仍由人工确认调用。
- v3：支持多轮自动补证，但高风险处置仍需人工审批。
- v4：沉淀字段级模板、指标字典和平台级审计看板。
