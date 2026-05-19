# Real DataAgent Case 001 Boundary Rerun

## 0. 回归目标

验证 `real_dataagent_case_001_protocol_frontend_backend_gap.md` 在边界校正后是否满足：

- Data Agent 只作为 evidence provider。
- Data Agent 结论性文字只进入 `provider_conclusion_hint`。
- `dennis_final_judgement` 由 Dennis 主 Agent 单独生成。
- `recommended_next_provider` 由 Router / Dennis Agent 生成。
- 前端无日志 + 后端有请求不直接判明确协议。

本轮不调用真实 Data Agent，不编造真实 API、真实表名、真实字段名、真实 SQL。

## 1. Data Agent Question 检查

来源文件：

`outputs/reviews/real_dataagent_case_001_protocol_frontend_backend_gap.md`

### 检查结果

通过。

当前 `natural_language_question` 要求 Data Agent 输出：

- 后端请求是否存在以及规模。
- 是否存在对应前端事件或 SDK 上报。
- SDK 缺失、版本异常、包类型异常线索。
- token / device / ip / ua 冲突线索。
- 策略命中或处置链路是否存在。
- 破解包、官方埋点缺失、join 口径、合法自动化、群控真机等反证或缺口。
- 数据发现与模型推测分离。
- SQL-only、无权限、失败、超时、空结果的边界。
- `provider_conclusion_hint`，且明确不是最终风控结论。

当前 question 明确禁止：

- 处罚、冻结、扣除、封禁或策略上线建议。
- 因前端无日志直接判协议。
- 把 queryId / sessionId 当可回放证据。
- 让 Data Agent 直接决定 `recommended_next_provider`。
- 输出 parser 期望识别、最终风控定性或治理处置建议。

### 边界说明

`query_intent_schema_v2` 内部仍保留 `conclusion_threshold` 和 `next_query_intent_when_insufficient`，这是 Dennis / Router 的规划字段；真实发给 Data Agent 的 `natural_language_question` 已经收口为数据发现、覆盖范围、缺失证据和口径风险。

## 2. Mock Data Agent 返回中的结论性文字

用于边界验证的 mock provider 文字：

```text
从已查数据看，后端请求存在且前端事件覆盖不足，部分设备存在 SDK 异常，数据侧提示为“存在协议攻击疑点”。但当前缺少实时日志、策略引擎、群控真机排查和授权工具白名单，无法确认协议攻击。
```

该文字中的“存在协议攻击疑点”属于 Data Agent 结论性表达，只能进入 `provider_conclusion_hint`。

## 3. Parser 映射检查

### provider_conclusion_hint

```yaml
provider_conclusion_hint:
  text: 存在协议攻击疑点
  source_section: Data Agent markdown 数据侧提示 / 分析段
  confidence_words:
    - 疑点
  conflicts_with_missing_evidence: true
  conflicts_with_counter_evidence: true
  boundary_note: 仅为 Data Agent 数据侧提示，不是 Dennis 最终判断。
```

检查结果：通过。

Data Agent 的结论性文字被放入 `provider_conclusion_hint`，没有进入最终判断。

## 4. unified_normalized_evidence 检查

```yaml
unified_normalized_evidence:
  provider: dataagent_provider
  provider_response_id: queryId
  status: partial
  returned_type: partial_table + analysis
  key_findings:
    - 后端请求存在。
    - 前端事件覆盖不足。
    - 部分设备存在 SDK 异常线索。
  strong_evidence: []
  medium_evidence:
    - 后端请求与前端事件覆盖存在不一致线索。
    - SDK 异常支持协议 / 破解包疑点，但不能单独定性。
  weak_evidence:
    - Data Agent 的“协议攻击疑点”文字仅为 provider_conclusion_hint。
  counter_evidence:
    - 官方包埋点缺失。
    - 前后端 join 口径偏差。
    - 合法自动化 / 授权工具。
    - 群控真机。
  missing_evidence:
    - 实时前端日志。
    - 实时后端 service 日志。
    - NG 网关明细。
    - 实时 SDK / 指纹。
    - 策略引擎命中与处置链路。
    - 群控标签 / 关联网络。
    - 授权工具白名单。
  quality_risks:
    - Data Agent-only 是离线 / 数据平台取证，不覆盖实时链路。
    - 前后端 join 口径可能影响“无匹配”判断。
    - SDK 异常可能来自版本差异、采集延迟或官方包埋点缺失。
  provider_limitations:
    - dataagent_markdown_not_structured
    - dataagent_offline_not_realtime
    - missing_realtime_log_provider
    - missing_device_fingerprint_provider
    - missing_risk_engine_provider
    - missing_relation_graph_provider
  provider_conclusion_hint:
    text: 存在协议攻击疑点
    boundary_note: provider hint only
  conclusion_support:
    level: insufficient_support
    reason: 关键反证未闭合，缺实时日志、设备指纹、策略引擎、群控和授权工具排查。
  recommended_next_provider:
    generated_by: router_or_dennis_agent
    providers:
      - realtime_log_provider
      - device_fingerprint_provider
      - risk_engine_provider
      - relation_graph_provider
      - manual_review_provider
  manual_review_required: true
  raw_result_reference:
    provider: dataagent_provider
    queryId: 待真实填充
    sessionId: 待真实填充
    reference_strength: weak
    replay_supported: false
```

### dennis_final_judgement 字段检查

通过。

`unified_normalized_evidence` 不包含 `dennis_final_judgement` 字段。该字段由 Dennis 主 Agent 在解释区单独生成。

## 5. Dennis 主 Agent 单独生成 dennis_final_judgement

```yaml
dennis_final_judgement:
  judgement_level: 证据不足
  one_sentence_judgement: 当前存在协议攻击疑点，但仅凭 Data Agent-only 的离线发现不能明确协议攻击。
  reason:
    - 前端无日志 + 后端有请求不是协议攻击充分条件。
    - Data Agent 返回的“协议疑点”只是 provider_conclusion_hint。
    - 缺实时前端日志、NG 网关、设备指纹、策略引擎、群控标签、授权工具白名单。
    - 破解包、官方埋点缺失、join 口径、合法自动化、群控真机反证未闭合。
  next_action_owner: Router / Dennis Agent
  governance_boundary:
    - 不自动处罚
    - 不自动冻结
    - 不自动扣除
    - 不自动上线策略
```

检查结果：通过。

Dennis 主 Agent 的最终判断与 Data Agent 的 provider hint 分离。

## 6. recommended_next_provider 归属检查

通过。

`recommended_next_provider` 不由 Data Agent 原文直接决定，而由 Router / Dennis Agent 基于以下字段生成：

- `missing_evidence`
- `provider_limitations`
- `quality_risks`
- `counter_evidence`

本 case 推荐：

- `realtime_log_provider`：补实时前端日志、后端 service 日志、NG 网关明细。
- `device_fingerprint_provider`：补实时 SDK / 指纹、设备画像、app 包上下文。
- `risk_engine_provider`：补策略命中、风险分、处置动作、灰度分组。
- `relation_graph_provider`：补群控真机、强设备关联、用户团组。
- `manual_review_provider`：补授权工具、合法自动化和业务登记确认。

## 7. 证据结构保留检查

通过。

回归仍保留：

- strong_evidence：当前为空，避免离线疑点过度升级。
- medium_evidence：后端请求与前端覆盖不一致线索、SDK 异常线索。
- weak_evidence：provider hint 和不完整线索。
- counter_evidence：官方埋点缺失、join 口径、合法自动化、群控真机。
- missing_evidence：实时日志、设备指纹、策略引擎、关系图、授权白名单。
- quality_risks：Data Agent-only 离线边界、join 口径、SDK 采集风险。

## 8. 降级检查

通过。

前端无日志 + 后端有请求没有被直接判为明确协议。

当前最多支持：

```text
Data Agent provider_conclusion_hint：存在协议攻击疑点。
Dennis final judgement：证据不足，需补 realtime_log / device_fingerprint / risk_engine / relation_graph / manual_review。
```

## 9. 总结

| 检查项 | 结果 |
|---|---|
| Data Agent question 是否只要求数据发现、覆盖范围、缺失证据、口径风险 | 通过 |
| parser 是否把 Data Agent 结论性文字标记为 provider_conclusion_hint | 通过 |
| unified_normalized_evidence 是否不包含 dennis_final_judgement | 通过 |
| Dennis 主 Agent 是否单独生成 dennis_final_judgement | 通过 |
| recommended_next_provider 是否由 Router / Dennis Agent 生成 | 通过 |
| 是否保留强/中/弱证据、反证、missing_evidence、quality_risks | 通过 |
| 是否正确降级，不直接判明确协议 | 通过 |

## 10. 是否修改核心 Skill

否。本轮只新增回归输出文件。

