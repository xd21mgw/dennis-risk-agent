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
  data_findings:
  speculation_notes:
  hypothesis_notes:
  counter_evidence_exclusion_status:
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
- “数据发现 vs 模型推测分界”：必须拆为 `data_findings`、`speculation_notes`、`hypothesis_notes`。
- “反证路径 / 排除状态 / 排除情况”：必须解析为 `counter_evidence_exclusion_status`。
- “P0 / P1 / P2 / P3”：必须解析为缺口优先级和 Router / Dennis 的 next action 依据。
- “策略引擎 / BLOCK / CHALLENGE / MONITOR”：必须解析为不同强度的策略证据。
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
- 假设性分析：markdown 中“如果 / 若 / 假设 / 可推断 / 需要验证后才成立”等未被数据执行结果支撑的推理。
- 风控结论：Dennis Agent 后续基于 normalized evidence 输出的判断。

处理原则：

- “数据发现”可以进入 `data_findings`、`key_findings` 和 evidence。
- markdown 里的模型推测不能直接转为 strong evidence。
- “模型推测”只能进入 `weak_evidence`、`quality_risks`、`speculation_notes` 或 `provider_conclusion_hint`。
- “假设性分析”必须进入 `hypothesis_notes`，不得进入 strong_evidence。
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

## 10.1 反证路径排除状态表解析规则

parser 必须解析复杂 Data Agent markdown 中的“反证路径排除状态表”。

至少支持以下状态：

- `已排除`
- `部分排除`
- `未排除`
- `未查`
- `无权限`
- `待验证`

标准结构：

```yaml
counter_evidence_exclusion_status:
  - counter_evidence_path:
    status:
    evidence_basis:
    impact_on_conclusion:
    priority:
```

协议攻击场景 P0 反证路径：

- 破解包绕 SDK / 绕采集
- 官方包埋点缺失
- 前后端 join 口径问题
- 合法自动化 / 授权工具
- 群控真机

如果任一 P0 反证状态为 `未排除`、`未查`、`无权限`、`待验证`，则 conclusion_support 不得超过 `highly_suspicious_support`，且通常应整体降为 `insufficient_support` 或“局部高度疑似 + 整体证据不足”。

`部分排除` 只能支持局部路径，不能支持全量明确判断。

## 10.2 P0 / P1 / P2 / P3 下一步解析规则

parser 必须识别 Data Agent markdown 中的 P0 / P1 / P2 / P3 下一步。

标准映射：

- P0：影响结论上限的关键缺口，写入 `missing_evidence` 和 Router / Dennis 生成 `recommended_next_provider` 的依据；存在 P0 缺口时 `manual_review_required = true`。
- P1：重要补证，影响置信度和治理范围。
- P2：增强解释或复盘的补证。
- P3：长期能力建设或效率优化。

parser 不直接采用 Data Agent 的 provider 推荐作为最终 `recommended_next_provider`，只能把 P0/P1/P2/P3 作为 Router / Dennis 的路由依据。

## 10.3 策略引擎决策强度解析规则

parser 必须区分策略引擎决策强度：

- `BLOCK`：较强处置证据。只能说明策略已强处置，不等于风险事实；可进入 medium_evidence 或在反证闭合时辅助 strong_evidence。
- `CHALLENGE`：中等风险 / 验证证据。通常进入 medium_evidence。
- `MONITOR`：观察证据。只能进入 weak_evidence 或 quality_risks，不能作为强打击证据。

策略证据必须保留限制：

- 策略命中不等于风险事实。
- 策略处置需要后验验证。
- 如果策略引擎域无权限，必须进入 `permission_notes` 和 `missing_evidence`。

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
- 模型推测和假设性分析未与数据发现分离。
- 反证路径排除状态不完整。
- 策略引擎 BLOCK / CHALLENGE / MONITOR 语义被混用。

## 11.1 Permission Notes 规则

no_permission 或 partial 中的无权限域必须进入 `permission_notes`。

对结论有影响的无权限域还必须进入 `missing_evidence`：

- 前端行为域无权限：无法确认前端真实缺失。
- 策略引擎域无权限：无法确认命中、拦截、验证、监控或放行。
- 关联网络域无权限：无法排除群控真机和强关联团组。
- 授权运营域无权限：无法排除合法自动化 / 授权工具。
- 设备 / SDK / 指纹域无权限：无法判断破解包、SDK 绕采集或设备环境。

无权限场景必须建议权限申请后重查，但该建议应作为 Router / Dennis next action，不是 Data Agent 最终决策。

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
- complex success 也不能自动升级为“明确判断”。只要存在 P0 关键反证未排除，结论上限不能超过 `highly_suspicious_support`。
- complex partial 中，可查域产生的数据发现可以进入 evidence；未查关键域必须进入 missing_evidence；结论应支持“局部高度疑似 + 整体证据不足”的组合表达。
- complex no_permission 中，无权限域必须进入 permission_notes；对结论有影响的无权限域必须进入 missing_evidence；结论不得强于“证据不足 / 高度疑似”。

## 12.1 Returned Type 推断规则

`returned_type` 用于描述 Data Agent 返回内容形态：

- `table + analysis`：有 markdown 表格、数据摘要和分析结论。
- `complex_table + full_spec_analysis`：多数据域联合取证、包含反证路径、策略引擎、P0/P1/P2/P3、数据发现 vs 推测分界的完整规格分析。
- `sql_only`：只有 SQL 或查询逻辑，无执行结果。
- `partial_table + analysis`：有部分表格 / 数据摘要，但缺关键数据源或反证。
- `complex_partial_table + analysis`：多数据域规格中部分域可查、部分关键域缺失，支持局部高度疑似但整体证据不足。
- `partial_table + permission_blocked`：有部分数据，但核心数据因权限不足不可见。
- `complex_permission_blocked`：多数据域规格中核心域无权限，必须降级并生成 permission notes。
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
- P0 反证存在未排除、未查、无权限或待验证时，不得生成 `clear_support`。
- complex success 只有在 P0 反证均已排除且数据发现覆盖核心链路时，才可接近明确判断；Data Agent-only 阶段仍建议由 Dennis Agent 和人工复核确认。
- partial 版本允许表达“局部高度疑似 + 整体证据不足”，不得压平成全量高度疑似。

## 14.1 Normalized Evidence 输出完整性规则

parser 输出 `unified_normalized_evidence` 时必须包含：

- `provider: dataagent_provider`
- `provider_response_id: queryId`
- `raw_result_reference: queryId + sessionId + 本地保存路径或内部引用`
- `provider_limitations`
- `data_findings`
- `speculation_notes`
- `hypothesis_notes`
- `counter_evidence_exclusion_status`
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
