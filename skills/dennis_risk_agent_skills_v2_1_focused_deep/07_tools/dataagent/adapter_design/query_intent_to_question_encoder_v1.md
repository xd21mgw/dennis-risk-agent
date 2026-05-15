# Query Intent to Question Encoder v1

## 0. 边界声明

本文件定义 Data Agent-only 阶段的 `query_intent_schema_v2` 到自然语言 question 的编码规则。

- 当前不调用真实 Data Agent。
- 当前不定义真实 API、真实表名、真实字段名、真实 SQL。
- 当前只设计 question 编码方式。
- Data Agent 只接受自然语言 question，不假设其支持 structured constraints。

## 1. 输入

输入为 `query_intent_schema_v2`。

关键字段：

```yaml
query_intent:
  intent_id:
  risk_question:
  target_evidence:
  applicable_skill:
  minimum_inputs:
  required_data_domains:
  optional_data_domains:
  field_types_needed:
  join_paths_needed:
  query_dimensions:
  time_window:
  expected_outputs:
  interpretation_notes:
  conclusion_threshold:
  quality_checks:
  freshness_expectation:
  permission_boundary:
  manual_review_required:
  safety_boundary:
  next_query_intent_when_insufficient:
```

## 1.1 调用前最小输入校验

Data Agent-only 真实取数前，必须先做最小输入校验。

必须具备：

```yaml
minimum_executable_inputs:
  entity_identifier:
    required: true
    at_least_one:
      - user_id
      - device_id
      - session_id
      - trace_id
      - risk_event_id
      - request_id
  time_window:
    required: true
    accepted:
      - start_time + end_time
      - 具体日期区间
  business_context:
    required: recommended
    examples:
      - 主站
      - 电商
      - 商业化
      - 直播
      - 活动
      - 账号安全
  target_api_or_action:
    required: recommended
    examples:
      - 目标业务动作
      - 目标接口模式
      - 目标页面 / 事件 / 行为
```

如果缺少 `entity_identifier` 或 `time_window`：

- 不生成可执行 Data Agent question。
- 不调用 Data Agent。
- 不进入 parser 阶段。
- 不生成 normalized evidence。
- 生成 `missing_input_request`，明确告诉用户需要补哪些信息。

如果缺少 `business_context` 或 `target_api_or_action`：

- 可以生成补充信息请求。
- 不建议直接调用 Data Agent。
- 如用户坚持，也必须在 question 中标注“业务场景 / 接口范围不明确，可能无法找表或生成可执行 SQL”。

### missing_input_request 结构

```yaml
missing_input_request:
  status: blocked_by_missing_minimum_inputs
  missing_required_inputs:
    - entity_identifier
    - time_window
  missing_recommended_inputs:
    - business_context
    - target_api_or_action
  message_to_user:
  next_step:
```

## 2. 输出

输出为 Data Agent 可消费的自然语言 question。

```yaml
natural_language_question:
  source_query_intent_id:
  question_text:
  encoder_notes:
  dataagent_only_limitations:
```

如果最小输入缺失，则输出：

```yaml
missing_input_request:
  source_query_intent_id:
  status: blocked_by_missing_minimum_inputs
  missing_required_inputs:
  missing_recommended_inputs:
  message_to_user:
```

## 3. 编码原则

编码必须遵循：

- 保留用户原始问题。
- 把 `required_data_domains` 编码成自然语言“建议查询的数据范围”。
- 把 `field_types_needed` 编码成“需要关注的字段类型”。
- 把 `join_paths_needed` 编码成“需要关联判断的关系”。
- 把 `time_window` 编码进正文。
- 把 `expected_outputs` 编码成明确输出要求。
- 把 `quality_checks` 编码成“请注意不要直接下结论”。
- 把 `provider_limitations` 编码成“当前只做离线 / 数据平台取证”。
- 不写真实表名。
- 不写真实字段名。
- 不写真实 SQL。
- 不把 query intent 当真实数据。
- 不在缺少实体标识或时间窗口时生成可执行 question。
- 不要求 Data Agent 直接给最终处罚、冻结、扣除、封禁或策略上线建议。
- 不要求 Data Agent 输出最终风控定性。
- 不要求 Data Agent 决定 recommended_next_provider。
- 如需 Data Agent 表达倾向，只能要求其输出“基于数据发现的提示”，后续由 Dennis Agent 解释。

## 4. 通用 Question 模板

```text
请基于数据平台可查询的数据，围绕以下风控问题做只读取证分析。

原始问题：
{risk_question}

本次只读取证目标：
{target_evidence}

建议查询的数据范围：
{required_data_domains}

需要关注的字段类型：
{field_types_needed}

需要关联判断的关系：
{join_paths_needed}

查询时间窗：
{time_window}

建议分析维度：
{query_dimensions}

期望输出：
{expected_outputs}

质量和误判注意事项：
{quality_checks}

当前能力边界：
本轮只做 Data Agent 数据平台 / 离线 / Hive / BI / 看板 / 数据集 / AB / 画像标签取证。
如果问题需要实时前端日志、实时后端 service 日志、NG 网关实时明细、实时策略引擎、实时设备指纹或在线关系图，请明确标记为缺失证据，不要直接下强结论。

请输出：
1. 数据发现：只写数据平台可支持的事实、覆盖范围和数据摘要。
2. 缺失证据：说明哪些证据未覆盖。
3. 反证或误判来源：说明可能的其他解释路径。
4. 数据质量风险：说明口径、权限、时效、join、样本范围问题。
5. provider_conclusion_hint：如需表达判断倾向，只能作为提示，不是最终风控结论。
```

## 5. 协议攻击 Question 模板

```text
请基于数据平台可查询的数据，辅助判断以下协议攻击疑点，但不要仅因前端无日志或后端有请求直接判定协议攻击。

原始问题：
{risk_question}

重点取证：
- 是否存在前端行为与后端请求不一致的离线证据。
- 是否存在 SDK 日志覆盖异常的离线聚合线索。
- 是否存在 token / device / ip / ua 一致性异常的离线聚合线索。
- 是否存在接口序列固化、高频请求或异常请求模式的离线聚合线索。
- 是否存在官方包埋点缺失、join 口径问题、破解包绕采集、合法自动化 / 授权工具、群控真机等反证线索。

建议查询的数据范围：
{required_data_domains}

需要关注的字段类型：
{field_types_needed}

需要关联判断的关系：
{join_paths_needed}

时间窗：
{time_window}

期望输出：
1. 支持协议疑点的数据发现。
2. 支持破解包、埋点缺失、join 口径问题、合法自动化、群控真机的反证或缺口。
3. 数据覆盖范围、缺失证据和数据质量风险。
4. provider_conclusion_hint：如需表达协议疑点强弱，只能作为数据侧提示，不是最终判断。

注意：
当前只做 Data Agent 离线取证。如果缺实时日志、SDK / 指纹、策略引擎或在线设备证据，请明确标记缺失证据，不要推荐 provider，也不要输出最终风控判断。
```

## 6. 群控 Question 模板

```text
请基于数据平台可查询的数据，辅助判断以下群控疑点，但不要仅因设备聚集或行为高频直接判群控。

原始问题：
{risk_question}

重点取证：
- 是否存在设备 / 账号聚集的离线线索。
- 是否存在同批启动 / 停止、行为路径相似、目标任务一致的离线聚合线索。
- 是否存在收益、奖励、资产访问或目标结果聚集。
- 是否存在合法矩阵、真人众包、活动低质、自然用户聚集等反证。

建议查询的数据范围：
{required_data_domains}

需要关注的字段类型：
{field_types_needed}

需要关联判断的关系：
{join_paths_needed}

时间窗：
{time_window}

期望输出：
1. 支持统一调度的数据发现。
2. 只能说明聚集但不能说明作恶的证据。
3. 反证与缺失证据。
4. provider_conclusion_hint：如需表达群控疑点强弱，只能作为数据侧提示，不是最终判断。
```

## 7. 渠道抢量 Question 模板

```text
请基于数据平台可查询的数据，分析以下渠道抢量 / 归因劫持疑点。

原始问题：
{risk_question}

重点取证：
- 曝光、点击、激活链路是否异常。
- CTIT 分布是否异常。
- 自然量与渠道量是否存在跷跷板。
- 新客真实性、老设备 / 老账号占比、后验质量是否异常。
- 是否存在投放策略、预算、品牌活动、归因窗口变化等反证。

建议查询的数据范围：
{required_data_domains}

需要关注的字段类型：
{field_types_needed}

需要关联判断的关系：
{join_paths_needed}

时间窗：
{time_window}

期望输出：
1. 渠道异常数据发现。
2. 业务上下文反证。
3. 数据质量风险。
4. provider_conclusion_hint：如需表达渠道异常倾向，只能作为数据侧提示，不是最终判断。
```

## 8. 导流截流 Question 模板

```text
请基于数据平台可查询的数据，辅助分析以下导流截流 / 站外添加疑点，但不要默认归为协议攻击或反爬。

原始问题：
{risk_question}

重点取证：
- 信息暴露入口是否存在异常。
- 搜索、关注、私信、互动等触达链路是否存在聚集。
- 是否存在主页、签名、动态、私信等站外承接线索。
- 是否存在账号矩阵或投诉 / 举报聚合。
- 是否存在正常社交、普通关注、用户主动外联、授权运营等反证。

建议查询的数据范围：
{required_data_domains}

需要关注的字段类型：
{field_types_needed}

需要关联判断的关系：
{join_paths_needed}

时间窗：
{time_window}

期望输出：
1. 导流截流链路的数据发现。
2. 站外承接证据是否充分。
3. 正常社交和授权触达反证。
4. provider_conclusion_hint：如需表达导流截流疑点强弱，只能作为数据侧提示，不是最终判断。
```

## 9. 策略复盘 Question 模板

```text
请基于数据平台可查询的数据，复盘以下策略命中后的效果和误伤风险。请注意，策略命中不等于风险事实。

原始问题：
{risk_question}

重点取证：
- 策略命中后的业务指标变化。
- 处置用户的后验风险、留存、转化、申诉 / 客诉等趋势。
- 灰度组、对照组或策略前后对比。
- 是否存在数据口径、实验、版本、渠道、活动变化等反证。

建议查询的数据范围：
{required_data_domains}

需要关注的字段类型：
{field_types_needed}

需要关联判断的关系：
{join_paths_needed}

时间窗：
{time_window}

期望输出：
1. 策略效果数据发现。
2. 误伤风险线索。
3. 数据质量和业务上下文风险。
4. provider_conclusion_hint：如需表达策略效果倾向，只能作为数据侧提示，不是最终判断。
```

## 10. Data Agent-only 的表达边界

question 中必须显式表达：

- 当前只做离线 / 数据平台取证。
- Data Agent 返回 markdown 不是最终风控结论。
- Data Agent 返回 SQL 不等于已查数结果。
- 如果需要实时日志、实时指纹、策略引擎、关系图，应标记为缺失证据。
- 如果缺关键反证排除，应建议降级。
- Data Agent 不负责决定 recommended_next_provider。
- Data Agent 不负责输出 dennis_final_judgement。
- parser 期望识别、status 预期、normalized evidence 字段要求只用于回归测试，不得进入真实 Data Agent question。

## 11. 禁止行为

- 禁止写真实表名。
- 禁止写真实字段名。
- 禁止写真实 SQL。
- 禁止编造 Data Agent API。
- 禁止把 query intent 当真实数据。
- 禁止缺少 entity_identifier 或 time_window 时调用 Data Agent。
- 禁止把缺输入场景伪装成 Data Agent 查询失败。
- 禁止要求 Data Agent 直接做最终风控定性。
- 禁止要求 Data Agent 输出 dennis_final_judgement。
- 禁止要求 Data Agent 决定 recommended_next_provider。
- 禁止把 parser 期望识别写入真实 Data Agent question。
- 禁止要求 Data Agent 直接处罚、冻结、扣除、封禁或上线策略。
- 禁止在 question 中诱导“前端无日志即协议”“低钱效即黑产”“策略命中即风险事实”。
