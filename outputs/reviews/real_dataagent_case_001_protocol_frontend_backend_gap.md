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
current_status: blocked_by_missing_minimum_inputs
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
    entity_identifier:
      required: true
      at_least_one:
        - user_id
        - device_id
        - session_id
        - trace_id
        - risk_event_id
        - request_id
      current_status: missing
    time_window:
      required: true
      current_status: missing
    business_context:
      required: recommended
      current_status: missing
    target_api_or_action:
      required: recommended
      current_status: missing
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
    - session_id
    - trace_id
    - risk_event_id
    - request_id
    - frontend_event
    - backend_api
    - sdk_status
    - app_version
    - app_signature
    - token_id
    - ip
    - ua
    - request_time
    - event_time
    - strategy_hit
    - engine_decision
  join_paths_needed:
    - protocol_frontend_backend_join
    - sdk_bypass_or_cracked_app_check
    - token_reuse_or_account_takeover_check
    - legal_operation_matrix_authorization_join
  query_dimensions:
    - 时间窗
    - 业务场景
    - 业务动作 / 接口类型
    - 用户维度
    - 设备维度
    - app 版本 / 渠道 / 包类型
    - SDK 状态
    - token / device / ip / ua 一致性
    - 策略命中状态
    - 是否存在授权工具或合法矩阵
  time_window: missing
  expected_outputs:
    - 后端请求是否存在以及规模
    - 是否存在对应前端事件或 SDK 上报
    - 是否存在 SDK 缺失、版本异常、包类型异常线索
    - 是否存在 token / device / ip / ua 冲突线索
    - 是否存在策略命中或处置链路
    - 是否存在破解包、官方埋点缺失、join 口径问题、合法自动化、群控真机等反证或缺口
  interpretation_notes:
    - 前端无日志不能直接判协议。
    - 后端有请求不能直接判协议。
    - Data Agent-only 只支持离线 / 数据平台取证，不能替代 realtime_log / device_fingerprint / risk_engine。
    - 缺 entity_identifier 或 time_window 时，不得调用 Data Agent。
  conclusion_threshold:
    clear_support: Data Agent-only 阶段原则上不直接给明确协议；需要多域证据闭合且关键反证排除，并由 Dennis 主 Agent 和人工复核确认。
    highly_suspicious_support: 存在多项离线数据强疑点，但仍缺实时日志、设备指纹、策略引擎或关键反证排除。
    insufficient_support: 缺最小输入、SQL-only、partial、no_permission、empty_result、failed 或关键反证未闭合。
  quality_checks:
    - 缺具体 case 标识时不能跑 SQL。
    - 缺时间窗口时不能定位分区和查询范围。
    - 缺业务场景 / 接口范围时无法稳定找表和生成 SQL。
    - queryId / sessionId 只能作为弱引用。
  freshness_expectation: Data Agent-only 阶段按数据平台可用时效解释；如需实时判断，应标记缺 realtime provider。
  permission_boundary:
    - 只读取证。
    - 不绕过权限。
    - 不导出敏感明细。
  manual_review_required: true
  safety_boundary:
    - 不自动处罚。
    - 不自动冻结。
    - 不自动扣除。
    - 不自动封禁。
    - 不自动上线策略。
    - 不把 Data Agent 返回直接作为最终风控定性。
  next_query_intent_when_insufficient:
    - 先补齐 entity_identifier。
    - 先补齐 time_window。
    - 建议补齐 business_context。
    - 建议补齐 target_api_or_action。
```

## 3. natural_language_question

当前不生成可执行 Data Agent question。

原因：

- 缺具体 case 标识。
- 缺时间窗口。
- 业务场景 / 接口范围不明确。

### missing_input_request

```yaml
missing_input_request:
  status: blocked_by_missing_minimum_inputs
  missing_required_inputs:
    - entity_identifier:
        at_least_one:
          - user_id
          - device_id
          - session_id
          - trace_id
          - risk_event_id
          - request_id
    - time_window:
        accepted:
          - start_time + end_time
          - 具体日期区间
  missing_recommended_inputs:
    - business_context:
        examples:
          - 主站
          - 电商
          - 商业化
          - 直播
          - 活动
          - 账号安全
    - target_api_or_action:
        examples:
          - 目标业务动作
          - 目标接口模式
          - 目标页面 / 事件 / 行为
  message_to_user: 请补充至少一个具体 case 标识和明确时间窗口；建议补充业务场景和目标接口 / 行为范围。补齐前不调用 Data Agent。
```

## 4. 本次真实 Data Agent 返回记录

### 4.1 SSE / markdown 原文

```text
核心缺失：没有具体 case 和时间窗，没法跑 SQL。
需要你提供：
具体 case 标识（必需）——用户ID / 设备ID / 可疑请求的 session_id / trace_id，至少一个
时间窗口（必需）——比如 2026-05-10 ~ 2026-05-15
业务场景（可选但有用）——主站/电商/商业化？涉及哪些接口？
补了这些，我才能让 Data Agent 去找对应的 Hive 表、生成 SQL、跑出实际数据发现，而不是停留在“框架”层面。

另外，Data Agent 也明确了它的能力边界：离线 Hive / BI / 看板可以查，实时前端日志、后端 service 日志、网关明细、实时策略引擎、实时指纹、在线关系图——这些都是缺失证据，只能标记，不能取证。
```

### 4.2 sessionId

```text
未提供
```

### 4.3 queryId

```text
未提供
```

### 4.4 result

```text
边界反馈 / 未进入真实查询
```

### 4.5 error_msg

```text
缺少最小输入，无法跑 SQL。
```

### 4.6 final markdown

```markdown
Data Agent 返回的是最小输入边界反馈，不是真实查询结果。
```

## 5. parser 输出区

```yaml
parser_output:
  status: blocked_by_missing_minimum_inputs
  returned_type: missing_input_boundary_feedback
  key_findings:
    - Data Agent 明确缺少具体 case 标识，无法跑 SQL。
    - Data Agent 明确缺少时间窗口，无法定位分区和查询范围。
    - Data Agent 明确业务场景 / 接口范围不清，无法稳定找表和生成 SQL。
    - Data Agent 明确自身可查离线 Hive / BI / 看板 / SQL / 表检索。
    - Data Agent 明确实时前端日志、实时后端 service 日志、NG 网关明细、实时策略引擎、实时指纹、在线关系图不可直接取证。
  strong_evidence: []
  medium_evidence: []
  weak_evidence: []
  counter_evidence: []
  missing_evidence:
    - entity_identifier
    - time_window
    - business_context
    - target_api_or_action
    - realtime_log_provider
    - device_fingerprint_provider
    - risk_engine_provider
    - relation_graph_provider
  quality_risks:
    - 缺 case 标识会导致无法定位样本。
    - 缺时间窗口会导致无法定位分区和查询范围。
    - 缺业务场景 / 接口范围会导致找表和 SQL 生成不稳定。
  permission_notes: []
  provider_limitations:
    - dataagent_requires_minimum_executable_inputs
    - dataagent_offline_hive_bi_only
    - missing_realtime_log_provider
    - missing_device_fingerprint_provider
    - missing_risk_engine_provider
    - missing_relation_graph_provider
  provider_conclusion_hint:
    text: 当前只能停留在框架层面，无法跑 SQL 或形成数据发现。
    boundary_note: provider hint only; not dennis_final_judgement.
  conclusion_support:
    level: insufficient_support
    reason: 最小输入缺失，未进入真实取数，不能形成风险证据。
  recommended_next_provider:
    generated_by: router_or_dennis_agent
    providers: []
  next_action:
    generated_by: Dennis 主 Agent
    actions:
      - 补充 entity_identifier。
      - 补充 time_window。
      - 补充 business_context。
      - 补充 target_api_or_action。
      - 补齐后重新生成 Data Agent question。
  manual_review_required: true
  raw_result_reference:
    provider: dataagent_provider
    queryId: null
    sessionId: null
    reference_strength: none
    replay_supported: false
```

## 6. Dennis Agent 解释区

```yaml
dennis_agent_interpretation:
  evidence_strength: 无风险证据。当前只有最小输入边界反馈。
  why_not_strong_conclusion:
    - 没有具体 case 标识。
    - 没有时间窗口。
    - 业务场景 / 接口范围不明确。
    - Data Agent 未跑 SQL，未返回数据发现。
  next_evidence_actions:
    - 请补充 user_id / device_id / session_id / trace_id / risk_event_id / request_id 至少一个。
    - 请补充 start_time / end_time 或具体日期区间。
    - 请补充业务场景，如主站 / 电商 / 商业化 / 直播 / 活动 / 账号安全。
    - 请补充目标业务动作或目标接口模式。
  conclusion_level: 证据不足
  governance_suggestion: 不治理，不拦截，不处罚，不上线策略；先补输入后重跑只读取证。
  human_review_feedback: 本次反馈是有效边界命中，不是 Data Agent 查询失败。
```

## 7. 验收标准

- [x] Data Agent 是否理解 question：部分理解，但指出缺最小输入。
- [x] 返回是否可解析：可解析为 `blocked_by_missing_minimum_inputs`。
- [x] parser 是否正确降级：是。
- [x] 是否没有因为前端无日志直接判协议：是。
- [x] 是否正确标注 Data Agent-only provider limitation：是。
- [x] 是否需要接 `realtime_log_provider`：后续如需实时链路，需要。
- [x] 是否需要接 `device_fingerprint_provider`：后续如需实时指纹，需要。
- [x] 是否需要接 `risk_engine_provider`：后续如需策略链路，需要。
- [x] 是否保留 missing_evidence / quality_risks：是。
- [x] 是否需要人工复核：需要补输入后重跑。

