# DataAgent Markdown Response Parser v1

## 0. 边界声明

本文件定义 Data Agent-only 阶段如何把 SSE / markdown response 解析为 `unified_normalized_evidence`。

- 当前不调用真实 Data Agent。
- 当前不定义真实 API、真实表名、真实字段名、真实 SQL。
- 当前只定义解析和降级规则。
- Data Agent 返回 markdown 不是结构化 evidence JSON，必须经过 parser 和降级判断。

## 1. 输入

输入可能包含：

```yaml
dataagent_response:
  sse_chunks:
  final_markdown_text:
  queryId:
  sessionId:
  result:
  error_msg:
```

字段说明：

- `sse_chunks`：SSE 分片文本。
- `final_markdown_text`：合并后的 markdown 正文。
- `queryId`：Data Agent 查询弱引用。
- `sessionId`：会话弱引用。
- `result`：Data Agent 返回状态标识。
- `error_msg`：错误信息。

## 2. 输出

输出为 `unified_normalized_evidence`。

```yaml
normalized_evidence:
  evidence_id:
  source_query_intent_id:
  source_provider_request_id:
  provider: dataagent_provider
  provider_response_id:
  status:
  evidence_type:
  applicable_skill:
  evidence_summary:
  key_findings:
  strong_evidence:
  medium_evidence:
  weak_evidence:
  counter_evidence:
  missing_evidence:
  quality_risks:
  freshness_notes:
  permission_notes:
  provider_limitations:
  provider_conclusion_hint:
  conclusion_support:
    level:
    reason:
  next_query_intent:
  recommended_next_provider:
    generated_by: router_or_dennis_agent
  manual_review_required:
  raw_result_reference:
  audit_reference:
  dennis_final_judgement:
    generated_by: Dennis 主 Agent
    filled_by_parser: false
```

## 3. SSE 合并规则

1. 按 SSE chunk 顺序拼接文本。
2. 保留 markdown 结构，包括标题、列表、表格、代码块。
3. 去除协议层包装和空事件。
4. 如果 chunk 中存在重复片段，按内部平台去重策略处理，当前文档只要求保留最终可读文本。
5. 如果流结束但没有正文，标记为 `empty_result`。
6. 如果流未正常结束，标记为 `partial` 或 `failed`，并记录质量风险。

## 4. Markdown 解析规则

解析以下结构：

- 标题：用于识别摘要、发现、结论、风险、建议、SQL、表格等区块。
- 列表：用于提取 key findings、missing evidence、counter evidence、quality risks。
- 表格：用于提取数据摘要和维度对比。
- 代码块：用于识别 SQL 或伪代码。
- 加粗文本：可作为重点提示，但不能直接当事实。

默认区块映射：

- “数据发现 / 结果 / 分析”：候选 key findings。
- “结论 / 判断 / 可能”：候选 provider_conclusion_hint，需与事实分离，不能作为 final judgement。
- “缺失 / 需要补充 / 信息不足”：missing evidence。
- “反证 / 可能原因 / 其他解释”：counter evidence。
- “风险 / 注意 / 口径”：quality risks。
- “SQL / 查询语句”：SQL generated，不等于执行结果。

## 5. SQL 代码块解析规则

当 markdown 中出现 SQL 代码块：

- 标记 `provider_limitations` 包含 `dataagent_sql_not_result`。
- 如果没有配套执行结果或数据摘要，`returned_type` 推断为 `sql_only`，status 推断为 `sql_only` 或 `partial`。
- SQL 中的逻辑可转为 weak evidence 的“待执行取证方案”，不能转为 strong evidence。
- 不保留真实 SQL 到对外 evidence 文本。
- 不把 SQL 生成结果当已查数结果。
- SQL 后的“假设性分析”“若返回量大”“如果占比高”等内容必须识别为模型推测，不得进入 strong_evidence。
- 如果 markdown 明确写明“SQL 不等于已查数结果”“仅供人工执行”“未经执行验证”，必须将 conclusion_support 降为 `insufficient_support`。

## 6. Markdown 表格解析规则

当 markdown 中出现表格：

- 识别表头和行数。
- 提取维度、指标、趋势、占比、异常方向等摘要。
- 表格可支持 key findings，但仍需检查是否覆盖时间窗、样本范围和口径。
- 表格缺少关键维度或口径说明时，加入 `quality_risks`。
- 表格仅表达 Data Agent 返回摘要，不代表原始明细可回放。

## 7. 数据发现提取规则

数据发现必须满足：

- 来自 markdown 中明确的数据摘要、表格、执行结果说明或看板 / 数据集分析结果。
- 能对应 query intent 的 target evidence。
- 能说明时间窗、对象范围或维度范围。

强度判定：

- strong_evidence：有明确数据摘要、覆盖关键时间窗、能支持目标证据，且对应事实不依赖假设推理。协议攻击场景中，破解包指纹标记与无 SDK 上报等强关联可进入 strong_evidence，但若策略引擎、群控标签、授权工具白名单或精确 join 口径仍缺失，结论仍不得升级为明确判断。
- medium_evidence：有数据摘要但反证未闭合，或覆盖范围不完整。
- weak_evidence：只有趋势描述、SQL 生成、口径说明、模型推测或样本范围不明。

result 为 `success` 只表示 Data Agent 技术执行成功，不等于证据充分。parser 必须继续检查：

- 是否有真实数据摘要或表格。
- 是否只是 SQL-only。
- 是否存在 missing_evidence。
- 是否存在 counter_evidence 未闭合。
- 是否存在 Data Agent-only 缺少实时 provider 的限制。
- 是否覆盖协议攻击关键反证：破解包、官方埋点缺失、join 口径、合法自动化、群控真机。

## 8. 结论 / 推测分离规则

parser 必须区分：

- 数据事实：Data Agent 返回的可识别数据摘要、表格结果、看板结果。
- 模型推测：markdown 中“可能、疑似、建议、看起来、推测”等描述。
- 风控结论：Dennis Agent 后续基于 normalized evidence 输出的判断。

处理原则：

- markdown 里的模型推测不能直接转为 strong evidence。
- markdown 里的“疑似协议 / 疑似黑产”只能进入 `provider_conclusion_hint` 或 interpretation note，不得进入 `dennis_final_judgement`。
- 最终结论等级由 Dennis Agent 根据 normalized evidence 决定。

## 8.1 Provider Conclusion Hint 规则

Data Agent 返回中的结论性文字，例如“高度疑似”“可能是协议攻击”“建议判断为异常”，只能抽取为 `provider_conclusion_hint`。

`provider_conclusion_hint` 的约束：

- 只代表 Data Agent 基于当前返回内容的提示。
- 不是 Dennis 主 Agent 的最终判断。
- 不得直接进入 strong_evidence。
- 不得直接生成治理动作。
- 不得填充 `dennis_final_judgement`。
- 如果 provider_conclusion_hint 与 missing_evidence / counter_evidence 冲突，parser 必须保留冲突并降级。

## 9. missing_evidence 提取规则

以下内容应进入 `missing_evidence`：

- markdown 明确说“无法判断 / 信息不足 / 需要补充”。
- query intent 要求但 response 未覆盖的证据。
- Data Agent-only 阶段无法覆盖的实时证据。
- 协议攻击场景中缺失实时日志、SDK / 指纹、策略引擎、破解包反证、合法自动化反证、群控真机反证。
- 渠道场景中缺投放策略、预算、品牌活动、归因窗口反证。
- 导流场景中缺站外承接、正常社交、授权运营反证。
- 策略复盘中缺申诉 / 客诉、对照组、后验质量。

## 10. counter_evidence 提取规则

以下内容应进入 `counter_evidence`：

- markdown 中列出的其他解释路径。
- 埋点缺失、join 口径问题、版本差异、采集延迟。
- 合法自动化 / 授权工具。
- 正常社交、普通关注、用户主动外联。
- 投放策略、预算、品牌活动、实验或版本变化。
- 策略命中但后验风险不支持。

每条反证必须包含：

- `counter_item`
- `related_misjudgment_risk`
- `whether_closed`

## 11. quality_risks 提取规则

以下内容应进入 `quality_risks`：

- 前端日志延迟或丢点。
- 后端日志采样或延迟。
- Data Agent 只返回 SQL。
- Data Agent markdown partial。
- 表格缺口径。
- 时间窗不一致。
- join 口径不一致。
- 权限受限。
- 样本范围不明。
- 指标口径不明。
- Data Agent-only 缺少实时 provider。

## 12. Status 推断规则

按以下顺序推断 status：

1. `error_msg` 包含“权限不足”“无权限”“访问被拒绝”“permission” -> `no_permission`。
2. `result != success` 或 `result = error`，且 `error_msg` 包含“超时”“timeout”“执行失败” -> `timeout` 或 `failed`。
3. `result != success` 或 `result = error`，且无权限特征也无超时特征 -> `failed`。
4. 流结束但内容为空 -> `empty_result`。
5. markdown 包含“查询执行成功，但返回 0 行”“Result: 0 rows” -> `empty_result`。
6. markdown 包含“SQL 不等于已查数结果”，或只有 SQL / 查询逻辑但无执行结果 -> `sql_only` 或 `partial`。
7. markdown 包含“无法判断 / 信息不足 / 需要补充” -> `ambiguous_result` 或 `partial`。
8. markdown 有部分数据，但明确缺关键数据源或关键反证未排除 -> `partial`。
9. markdown 有数据表和分析，但 missing_evidence / counter_evidence 仍未闭合 -> `success`，但 conclusion_support 不得超过 `highly_suspicious_support`。
10. markdown 返回完整数据发现并覆盖关键反证 -> `success`。

补充规则：

- 多种状态同时出现时，选择更保守的状态。
- `no_permission` 优先级高于 `empty_result` 和 `partial`。
- `timeout` / `failed` 等于零可靠数据支撑，不能给风险结论。
- `empty_result` 不能解释为无风险。
- `sql_only` 不能解释为已查数。
- parser 无法稳定识别 markdown 时，标记 `parse_failed`，并降级。

## 12.1 Returned Type 推断规则

`returned_type` 用于描述 Data Agent 返回内容形态：

- `table + analysis`：有 markdown 表格、数据摘要和分析结论。
- `sql_only`：只有 SQL 或查询逻辑，无执行结果。
- `partial_table + analysis`：有部分表格 / 数据摘要，但缺关键数据源或反证。
- `partial_table + permission_blocked`：有部分数据，但核心数据因权限不足不可见。
- `empty_result + analysis`：查询执行完成且返回 0 行，同时包含空结果解释。
- `none`：查询失败、超时或无任何可靠数据返回。
- `ambiguous_analysis`：自然语言分析多于数据发现，且明确无法判断。

## 13. raw_result_reference 生成规则

`raw_result_reference` 只做内部弱引用。

```yaml
raw_result_reference:
  provider: dataagent_provider
  queryId:
  sessionId:
  reference_strength: weak
  replay_supported: false
  note: queryId/sessionId 只能作为内部弱引用，不能当作可回放证据。
```

要求：

- queryId 只能作为弱引用。
- sessionId 只能作为弱引用。
- 不把 raw result 明细外泄到通用材料。
- 如果未来平台提供 result_id / trace_id / replay_id，再由内部平台扩展。

## 14. Conclusion Support 生成规则

parser 只能生成 `conclusion_support`，不能生成最终风控结论。

默认映射：

- `success` 且关键反证覆盖：可到 `highly_suspicious_support`；是否支持更高等级必须由 Dennis Agent 和人工确认。
- `success` 但关键反证未覆盖：不得超过 `highly_suspicious_support`。
- `success` 且只有局部路径闭合：局部可标记 `highly_suspicious_support`，整体应标记 `insufficient_support` 或拆分说明。
- `sql_only`：`insufficient_support`。
- `partial`：`insufficient_support`。
- `no_permission`：`insufficient_support`。
- `empty_result`：`insufficient_support`。
- `timeout`：`insufficient_support`。
- `ambiguous_result`：`insufficient_support` 或 `reverse_or_exclusion_support`。
- `failed`：`insufficient_support`。

协议攻击 Data Agent-only 阶段：

- 缺实时日志、SDK / 指纹、策略引擎或关键反证时，不得生成 `clear_support`。
- 只要缺破解包、官方埋点缺失、join 口径、合法自动化、群控真机等关键反证，协议攻击结论不能升级为“明确判断”。
- Data Agent-only 缺 `realtime_log_provider`、`device_fingerprint_provider`、`risk_engine_provider` 时，必须写入 `provider_limitations`。
- Data Agent 返回中的结论性文字只进入 `provider_conclusion_hint`，不得进入 `dennis_final_judgement`。
- `recommended_next_provider` 由 Router / Dennis Agent 根据 `missing_evidence` 和 `provider_limitations` 生成，Data Agent 原文中的“下一步建议”只能作为 next_action_hint 或 missing_evidence 参考。

## 14.1 Normalized Evidence 输出完整性规则

parser 输出 `unified_normalized_evidence` 时必须包含：

- `provider: dataagent_provider`
- `provider_response_id: queryId`
- `raw_result_reference: queryId + sessionId + 本地保存路径或内部引用`
- `provider_limitations`
- `key_findings`
- `strong_evidence`
- `medium_evidence`
- `weak_evidence`
- `counter_evidence`
- `missing_evidence`
- `quality_risks`
- `provider_conclusion_hint`
- `conclusion_support`
- `recommended_next_provider`，但该字段必须标记为 Router / Dennis Agent 生成，不得直接采用 Data Agent 的推荐
- `manual_review_required`

`raw_result_reference` 只能保存弱引用和内部路径，不得外泄敏感明细。

`dennis_final_judgement` 不得由 parser 填充。

## 14.2 Parser 期望识别的归属

“parser 期望识别”只用于 mock 样例、回归测试和 parser 校准。

- 不得写入真实 Data Agent question。
- 不得要求 Data Agent 输出 parser status、returned_type、strong_evidence、recommended_next_provider 等结构化字段。
- 真实 Data Agent 只需输出数据发现、覆盖范围、缺失证据、权限限制、口径风险和必要的数据侧提示。
- parser 负责把真实 markdown 映射为 normalized evidence。

## 15. 禁止行为

- 不得把 SQL 生成结果当已查数结果。
- 不得把 markdown 里的模型推测当事实。
- 不得把 `empty_result` 当无风险。
- 不得在 `no_permission` 时强结论。
- 不得把 queryId 当作可回放证据。
- 不得把 Data Agent markdown 直接当最终风控判断。
- 不得把 Data Agent 的结论性文字标记为 final judgement。
- 不得让 Data Agent 原文决定 recommended_next_provider。
- 不得把 parser 期望识别写入真实 Data Agent 请求。
- 不得忽略 missing evidence、counter evidence 和 quality risks。
- 不得在关键反证未闭合时输出明确判断支持。
