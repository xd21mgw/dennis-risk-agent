# Data Agent-only Pilot Overlay v1

## 0. 边界声明

本文件定义 v2.4 第一阶段 Data Agent-only 真实只读试点 overlay。

- 不修改核心 Skill。
- 不调用真实 Data Agent。
- 不定义真实 API、真实表名、真实字段名、真实 SQL。
- 不推翻 Evidence Tool Router 多 provider 架构。
- 只描述当前最低成本落地方式：Router 单 provider 试点模式。

## 1. 定位

当前 v2.4 第一阶段只接 Data Agent，作为最低成本真实只读试点。

定位说明：

- Evidence Tool Router 保留。
- active provider 只有 `dataagent_provider`。
- `realtime_log_provider`、`risk_engine_provider`、`device_fingerprint_provider`、`relation_graph_provider`、`structured_sql_or_feature_provider` 暂不接入。
- 其他 provider 暂作为 future provider / stub，只在 `recommended_next_provider`、`future_provider_needed` 和 `provider_limitations` 中体现。
- Data Agent-only 模式用于验证真实只读链路能否跑通，不用于证明所有实时风险判断都已具备。

## 2. 当前链路

```text
query_intent_schema_v2
→ evidence_tool_router
→ dataagent_provider
→ query_intent_to_question_encoder
→ Data Agent question-only API
→ SSE markdown response
→ markdown_response_parser
→ unified_normalized_evidence
→ Dennis Agent 解释
→ 人工复核
```

链路说明：

1. Dennis Agent 仍先生成 `query_intent_schema_v2`。
2. Evidence Tool Router 读取 query intent，但当前只允许选择 `dataagent_provider`。
3. `query_intent_to_question_encoder` 把证据需求编码为 Data Agent 可理解的自然语言 question。
4. Data Agent 返回 SSE markdown response。
5. `markdown_response_parser` 把 markdown 摘要转为结构化 evidence 草稿。
6. Router 生成 `unified_normalized_evidence`。
7. Dennis Agent 基于 evidence 做解释、降级、补证建议。
8. 人工复核记录是否过度自信、过度保守、漏反证或误读数据。

## 3. Data Agent-only 能覆盖什么

Data Agent-only 适合覆盖：

- Hive / 离线取数。
- SQL 生成。
- 表检索。
- 表结构 / 字段口径理解。
- 数据集分析。
- 看板 / 多维分析。
- AB 实验。
- 画像标签。
- 离线趋势。
- 离线聚合。
- 离线归因。
- 离线复盘。

适合的风险取证问题：

- 渠道 CTIT / 归因劫持的离线分析。
- 活动低质、奖励、提现、后验质量复盘。
- DAU / DNU、转化率、留存、支付等指标异常归因。
- 策略命中后的业务效果和误伤趋势复盘。
- 合法矩阵 / MCN / 商家运营的离线登记、历史违规和业务上下文分析。
- 协议攻击中的离线聚合趋势、异常请求样本复盘和口径排查辅助。

## 4. Data Agent-only 不能充分覆盖什么

Data Agent-only 不能充分覆盖：

- 实时前端日志。
- 实时后端 service 日志。
- NG 网关实时明细。
- 实时策略引擎决策链路。
- 实时设备指纹。
- 风控异步 SDK 与实时指纹的低延迟对齐。
- 设备画像在线查询。
- 在线强设备关联 / 用户团组图查询。
- 低延迟拦截前补证。
- 请求级实时处置链路。
- 需要直接依赖 provider trace 的在线回放。

这些证据只能作为 future provider 需求记录，不能在 Data Agent-only 阶段伪装为已覆盖。

## 5. 协议攻击试点中的结论上限

协议攻击试点在 Data Agent-only 阶段必须控制结论上限。

默认规则：

- 只通过 Data Agent 返回的离线 / Hive / markdown 结果，默认不能直接明确协议攻击。
- 如果缺实时日志、SDK、指纹、策略引擎、破解包反证，结论上限一般为“高度疑似”或“证据不足”。
- 如果 Data Agent 只返回 SQL、表检索、markdown 推测或 partial 结果，不得输出明确协议。
- 如果 Data Agent 返回空结果，不得解释为无风险。
- 如果 Data Agent 无权限或结果不完整，必须降级。

例外条件：

- 只有当 Data Agent 返回的数据已经充分覆盖并排除关键反证时，才可考虑更高结论。
- 即使考虑更高结论，仍需人工确认。
- 更高结论必须明确说明 Data Agent 覆盖了哪些反证：破解包绕 SDK、官方包埋点缺失、前后端 join 口径问题、合法自动化 / 授权工具、群控真机。

强保护：

- 前端无日志不得直接判协议。
- 后端有请求不得直接判协议。
- SDK 缺失不得直接判破解包或协议。
- 高频请求不得直接判协议。
- 策略命中不得直接当风险事实。

## 6. Router 行为

当 query intent 推荐 `realtime_log_provider`、`device_fingerprint_provider`、`risk_engine_provider`、`relation_graph_provider`，但当前未接入时，Router 应执行以下行为：

1. fallback 到 `dataagent_provider` 的离线取证能力。
2. 在 `normalized_evidence.provider_limitations` 中标记缺少实时 provider。
3. 生成 `next_query_intent` 或 `future_provider_needed`。
4. 不得强结论。
5. 在 `missing_evidence` 中保留未接 provider 所代表的证据缺口。
6. 在 `recommended_next_provider` 中记录后续应接入的 provider。
7. 在 `manual_review_required` 中标记强处置前需要人工确认。

### Data Agent-only Router 决策模板

```yaml
router_decision:
  mode: dataagent_only_pilot
  active_provider:
    - dataagent_provider
  future_provider_needed:
    - realtime_log_provider
    - device_fingerprint_provider
    - risk_engine_provider
    - relation_graph_provider
  fallback_reason:
  limitation_note:
  strong_conclusion_allowed: false
```

## 7. normalized_evidence 要求

Data Agent-only 阶段生成的 `unified_normalized_evidence` 必须包含：

```yaml
normalized_evidence:
  provider: dataagent_provider
  provider_limitations:
    - limitation:
      impact:
  missing_evidence:
    - missing_item:
      impact_on_conclusion:
      recommended_next_provider:
  counter_evidence:
    - counter_item:
      related_misjudgment_risk:
      whether_closed:
  quality_risks:
    - risk:
      affected_evidence:
      degrade_rule:
  conclusion_support:
    level:
    reason:
  recommended_next_provider:
  manual_review_required:
```

必须保留的 provider limitations：

- `dataagent_markdown_not_structured`
- `dataagent_sql_not_result`
- `dataagent_offline_not_realtime`
- `missing_realtime_log_provider`
- `missing_device_fingerprint_provider`
- `missing_risk_engine_provider`
- `missing_relation_graph_provider`

协议攻击场景中常见 missing evidence：

- 实时前端日志。
- 实时后端 service 日志。
- NG 网关明细。
- 实时 SDK / 指纹。
- 策略引擎决策链路。
- 破解包 / 官方包埋点缺失反证。
- 合法自动化 / 授权工具反证。
- 群控真机反证。

## 8. 验收标准

第一阶段成功标准不是“明确判断协议攻击”，而是：

- 能把 `query_intent_schema_v2` 编码成 Data Agent question。
- 能接收 Data Agent SSE markdown response。
- 能解析 Data Agent markdown。
- 能生成 `unified_normalized_evidence`。
- 能识别 Data Agent-only 的证据边界。
- 能正确降级。
- 能记录人工反馈。
- 能指出后续需要接哪个 provider。
- 能避免把 Data Agent markdown 推测当事实。
- 能避免把 SQL 文本当查询结果。
- 能避免因空结果、无权限、partial 返回输出强结论。

### 最小验收 case

1. 前端无日志 + 后端有请求。
2. 后端请求存在 + SDK 缺失。
3. 接口高频 + token / device / ip / ua 异常。

每个 case 至少输出：

- Data Agent question。
- SSE markdown response 摘要。
- markdown parser 结果。
- `unified_normalized_evidence`。
- provider limitations。
- missing evidence。
- conclusion support。
- recommended next provider。
- 人工复核意见。

## 9. 后续升级路径

### 阶段 1：Data Agent-only 只读试点

目标：

- 跑通 query intent → question → markdown → normalized evidence → Dennis 解释 → 人工复核。

结论上限：

- 大多数协议攻击 case 只能到“高度疑似”或“证据不足”。

### 阶段 2：接 realtime_log_provider

目标：

- 补齐实时前端日志、后端 service 日志、NG 网关明细、请求序列。

价值：

- 支持前后端链路一致性实时补证。

### 阶段 3：接 device_fingerprint_provider

目标：

- 补齐实时指纹、异步 SDK、设备画像、app 版本 / 签名、SDK 状态。

价值：

- 支持破解包绕采集、SDK 缺失、设备环境异常排查。

### 阶段 4：接 risk_engine_provider

目标：

- 补齐策略命中、风险分、决策结果、处置动作、灰度分组和命中规则链路。

价值：

- 支持策略链路解释和误伤复盘。

### 阶段 5：协议攻击多 provider 只读试点

目标：

- 组合 `realtime_log_provider`、`device_fingerprint_provider`、`risk_engine_provider`、`dataagent_provider`。

价值：

- 支持更完整的协议攻击补证闭环。

### 阶段 6：扩展到群控、token 泄露、渠道抢量、导流截流

目标：

- 群控：引入 `relation_graph_provider` 和设备 / 实时行为组合。
- token 泄露：引入实时日志、设备和账号安全链路。
- 渠道抢量：以 Data Agent 为主，结构化 provider 补低延迟专题数据。
- 导流截流：引入实时触达链路、关系图和人工站外承接复核。

## 10. 对 Router 架构的影响

Data Agent-only overlay 不改变 Router 架构，只是把 Router 配置为第一阶段单 provider 模式。

架构关系：

- Router 仍是上层取证入口。
- Data Agent 是当前唯一 active provider。
- 其他 provider 是 future provider / stub。
- `unified_normalized_evidence` 仍使用跨 provider schema。
- 后续新增 provider 时，不需要推翻当前 query intent 和 evidence schema。

