# Real DataAgent Case 001 - Protocol Frontend Backend Gap

## 1. Case 基本信息

```yaml
case_id: real_dataagent_case_001_protocol_frontend_backend_gap
original_question: 前端无日志 + 后端有请求，是否支持协议攻击嫌疑？
risk_scenario: 协议攻击补证 / 前后端链路不一致
triggered_skill:
  main: protocol_attack_expert_skill
  auxiliary:
    - cracked_app_expert_skill
    - group_control_expert_skill
    - legal_operation_matrix_playbook_v2_3
    - account_security_expert_skill
pilot_stage: Data Agent-only
human_reviewer:
current_status: 待填充真实 Data Agent response
```

## 2. query_intent_schema_v2

```yaml
query_intent:
  intent_id: qi_real_da_001_protocol_frontend_backend_gap
  risk_question: 前端无日志 + 后端有请求，是否支持协议攻击嫌疑？
  target_evidence:
    - 前后端链路一致性
    - SDK 日志覆盖
    - 后端请求与端侧上下文是否冲突
    - 破解包绕 SDK / 绕采集反证
    - 官方包埋点缺失反证
    - 前后端 join 口径问题反证
    - 合法自动化 / 授权工具反证
    - 群控真机反证
  applicable_skill:
    main: protocol_attack_expert_skill
    auxiliary:
      - cracked_app_expert_skill
      - group_control_expert_skill
      - legal_operation_matrix_playbook_v2_3
      - account_security_expert_skill
  minimum_inputs:
    - user_id 或 device_id
    - api_name 或业务动作
    - time_window
  required_data_domains:
    - 前端行为域
    - 后端数据域
    - 设备信息域
    - 策略引擎域
  optional_data_domains:
    - 用户信息域
    - 风险画像域
    - 关联网络域
    - 合法矩阵 / 授权运营相关业务登记信息
  field_types_needed:
    - user_id
    - device_id
    - frontend_event
    - backend_api
    - sdk_status
    - realtime_fingerprint
    - app_version
    - app_signature
    - token_id
    - ip
    - ua
    - request_time
    - event_time
    - strategy_hit
    - engine_decision
    - risk_label
  join_paths_needed:
    - protocol_frontend_backend_join
    - sdk_bypass_or_cracked_app_check
    - token_reuse_or_account_takeover_check
    - legal_operation_matrix_authorization_join
  query_dimensions:
    - 时间窗
    - 业务动作 / 接口类型
    - 用户维度
    - 设备维度
    - app 版本 / 渠道 / 包类型
    - SDK 状态
    - token / device / ip / ua 一致性
    - 策略命中状态
    - 是否存在授权工具或合法矩阵
  time_window: 待填写真实 case 时间窗
  expected_outputs:
    - 后端请求是否存在以及规模
    - 是否存在对应前端事件或 SDK 上报
    - 是否存在 SDK 缺失、版本异常、包类型异常线索
    - 是否存在 token / device / ip / ua 冲突线索
    - 是否存在策略命中或处置链路
    - 是否存在破解包、官方埋点缺失、join 口径问题、合法自动化、群控真机等反证或缺口
    - 当前最多能支持的结论等级
    - 需要后续接入的 provider
  interpretation_notes:
    - 前端无日志不能直接判协议。
    - 后端有请求不能直接判协议。
    - SDK 缺失不能直接判破解包或协议。
    - Data Agent-only 只支持离线 / 数据平台取证，不能替代 realtime_log / device_fingerprint / risk_engine。
    - SQL-only 不等于已查数结果。
    - empty_result 不等于无风险。
  conclusion_threshold:
    clear_support: 需要前后端链路冲突、SDK / 指纹 / 设备上下文异常、请求序列或 token/device/ip/ua 冲突等证据闭合，并排除破解包、官方埋点缺失、join 口径问题、合法自动化、群控真机等关键反证；Data Agent-only 阶段原则上不直接给明确协议。
    highly_suspicious_support: 存在多项离线数据强疑点，但仍缺实时日志、设备指纹、策略引擎或关键反证排除。
    insufficient_support: 只有前端缺失、后端请求、SQL-only、partial、no_permission、empty_result、failed 或关键反证未闭合。
    reverse_or_exclusion_support: 数据更支持埋点缺失、join 口径问题、官方包问题、合法自动化或群控真机等非协议路径。
  quality_checks:
    - result=success 不等于证据充分。
    - SQL-only 不得进入 strong_evidence。
    - markdown 推测不得当作事实。
    - no_permission / failed / timeout / empty_result 必须降级。
    - queryId / sessionId 只能作为弱引用。
    - 缺 realtime_log / device_fingerprint / risk_engine 时必须写入 provider_limitations。
  freshness_expectation: Data Agent-only 阶段按数据平台可用时效解释；如需实时判断，应标记缺 realtime provider。
  permission_boundary:
    - 只读取证。
    - 不绕过权限。
    - 不导出敏感明细。
    - 权限不足时降级并记录缺口。
  manual_review_required: true
  safety_boundary:
    - 不自动处罚。
    - 不自动冻结。
    - 不自动扣除。
    - 不自动封禁。
    - 不自动上线策略。
    - 不把 Data Agent 返回直接作为最终风控定性。
  next_query_intent_when_insufficient:
    - 补查 realtime_log_provider：前端日志、后端 service 日志、NG 网关明细、请求序列。
    - 补查 device_fingerprint_provider：实时指纹、异步 SDK、设备画像、app 版本 / 签名。
    - 补查 risk_engine_provider：策略命中、风险分、处置动作、灰度分组。
    - 补查 relation_graph_provider：群控真机、强设备关联、用户团组。
    - 补人工复核：合法自动化 / 授权工具 / 业务登记信息。
```

## 3. natural_language_question

```text
请基于数据平台可查询的数据，对以下风控问题做只读取证分析。请不要给处罚、冻结、扣除、封禁或策略上线建议。

原始问题：
前端无日志 + 后端有请求，是否支持协议攻击嫌疑？

本次只读取证目标：
判断是否存在“前端行为 / SDK 上报缺失，但后端请求存在”的离线证据，并评估这些证据最多能否支持协议攻击嫌疑。同时必须排除或标记以下反证路径：破解包绕 SDK / 绕采集、官方包埋点缺失、前后端 join 口径问题、合法自动化 / 授权工具、群控真机。

建议查询的数据范围：
前端行为域、后端数据域、设备信息域、策略引擎域。可选补充用户信息域、风险画像域、关联网络域、合法矩阵 / 授权运营相关业务登记信息。

需要关注的字段类型：
用户标识、设备标识、前端事件类型、后端接口类型、SDK 状态、实时指纹类型、app 版本、包签名类型、token 类型、IP 类型、UA 类型、请求时间、事件时间、策略命中类型、引擎决策类型、风险标签类型。

需要关联判断的关系：
前后端链路关联、SDK 缺失 / 破解包排查关联、token 复用 / 账号接管排查关联、合法矩阵授权关联。

查询时间窗：
待填写真实 case 时间窗。

期望输出：
1. 后端请求是否存在以及规模。
2. 是否存在对应前端事件或 SDK 上报。
3. 是否存在 SDK 缺失、版本异常、包类型异常线索。
4. 是否存在 token / device / ip / ua 冲突线索。
5. 是否存在策略命中或处置链路。
6. 是否存在破解包、官方埋点缺失、join 口径问题、合法自动化、群控真机等反证或缺口。
7. 请区分“数据发现”和“模型推测”，不要把假设性分析写成事实。
8. 如果只生成 SQL、没有执行结果，请明确说明 SQL 不等于已查数结果。
9. 如果无权限、查询失败、超时或空结果，请明确说明不能支持强结论。
10. 如需表达判断倾向，请仅输出 provider_conclusion_hint，说明这是数据侧提示，不是最终风控结论。
11. 请说明缺失了哪些证据；不要直接决定 recommended_next_provider。

质量和误判注意事项：
- 前端无日志不能直接判协议。
- 后端有请求不能直接判协议。
- SDK 缺失不能直接判破解包或协议。
- result=success 不等于证据充分。
- empty_result 不等于无风险。
- queryId / sessionId 只能作为弱引用，不能当作可回放证据。

当前能力边界：
本轮只做 Data Agent 数据平台 / 离线 / Hive / BI / 看板 / 数据集取证。如果问题需要实时前端日志、实时后端 service 日志、NG 网关实时明细、实时策略引擎、实时设备指纹或在线关系图，请明确标记为缺失证据，不要直接下强结论。

职责边界：
Data Agent 只负责数据发现、覆盖范围、缺失证据、权限限制和口径风险。Dennis 主 Agent 才负责最终判断和下一步 provider 路由。请不要输出 parser 期望识别、最终风控定性或治理处置建议。
```

## 4. 粘贴真实 Data Agent response 的区域

### 4.1 SSE / markdown 原文

```text
待粘贴真实 SSE / markdown 原文。
```

### 4.2 sessionId

```text
待填写
```

### 4.3 queryId

```text
待填写
```

### 4.4 result

```text
待填写
```

### 4.5 error_msg

```text
待填写
```

### 4.6 final markdown

```markdown
待粘贴最终 markdown。
```

## 5. parser 输出区

```yaml
parser_output:
  status:
  returned_type:
  key_findings:
  strong_evidence:
  medium_evidence:
  weak_evidence:
  counter_evidence:
  missing_evidence:
  quality_risks:
  provider_limitations:
  conclusion_support:
    level:
    reason:
  recommended_next_provider:
  manual_review_required:
  raw_result_reference:
    provider: dataagent_provider
    queryId:
    sessionId:
    local_or_internal_reference:
    reference_strength: weak
    replay_supported: false
```

## 6. Dennis Agent 解释区

```yaml
dennis_agent_interpretation:
  evidence_strength:
  why_not_strong_conclusion:
  next_evidence_actions:
  conclusion_level:
  governance_suggestion:
  human_review_feedback:
```

## 7. 验收标准

- [ ] Data Agent 是否理解 question。
- [ ] 返回是否可解析。
- [ ] parser 是否正确降级。
- [ ] 是否没有因为前端无日志直接判协议。
- [ ] 是否正确标注 Data Agent-only provider limitation。
- [ ] 是否需要接 `realtime_log_provider`。
- [ ] 是否需要接 `device_fingerprint_provider`。
- [ ] 是否需要接 `risk_engine_provider`。
- [ ] 是否保留 missing_evidence / counter_evidence / quality_risks。
- [ ] 是否明确 queryId / sessionId 只能作为弱引用。
- [ ] 是否需要人工复核。
