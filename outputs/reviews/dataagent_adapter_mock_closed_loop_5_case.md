# Data Agent Adapter Mock Closed-loop 5 Case Regression

本轮验证 Data Agent adapter 设计是否能完成：

`query_intent_schema_v2 -> dataagent_request -> mock dataagent_response -> normalized_evidence -> Dennis Agent 证据解释`

约束：

- 不调用真实 Data Agent。
- 不编造真实 API、真实表名、真实字段、真实 SQL。
- mock response 仅用于验证解释能力，不代表真实数据结果。
- 不修改现有 Skill 文件。

---

## Case 1：AC-003 单纯协议判定，前端无日志

### 1. 用户问题

一批后端请求存在，但前端无日志，是否可以直接判定为协议攻击？

### 2. Skill 路由

- 主控 Skill：`protocol_attack_expert_skill`
- 辅助 Skill：`cracked_app_expert_skill`、`anti_crawler_expert_skill`、`evidence_decomposition_skill`

### 3. query_intent_schema_v2

```yaml
query_intent:
  intent_id: "AC-003_adapter_protocol_frontend_missing_001"
  intent_type: "protocol_frontend_backend_join"
  risk_question: "后端有请求但前端无日志时，是否能证明请求脱离正常端链路"
  target_evidence: "前后端链路一致性、SDK覆盖、请求环境一致性、协议反证排除"
  applicable_skill:
    primary: "protocol_attack_expert_skill"
    auxiliary: ["cracked_app_expert_skill", "anti_crawler_expert_skill", "evidence_decomposition_skill"]
  minimum_inputs:
    required: ["user_id 或 device_id", "api_name 或业务动作", "time_window"]
    optional: ["app_version", "sdk_status", "token_id", "官方版本或渠道语义"]
    missing: ["前端埋点口径", "官方版本对照", "合法自动化反证"]
  required_data_domains: ["前端行为域", "后端数据域", "设备信息域", "策略引擎域"]
  optional_data_domains: ["用户信息域", "风险画像域"]
  field_types_needed:
    identity_and_account: ["user_id", "account_id"]
    device_and_network: ["device_id", "realtime_fingerprint", "async_sdk_signal", "ip", "ua", "app_version", "app_signature", "sdk_status"]
    session_and_chain: ["token_id", "session_id", "frontend_event", "backend_api", "event_time", "request_time", "api_sequence", "gateway_decision"]
    activity_and_channel: []
    risk_and_strategy: ["risk_label", "strategy_hit", "engine_decision", "disposal_action"]
    relation_network: ["relation_group_id"]
  join_paths_needed: ["frontend_backend_chain_join", "request_device_environment_join", "token_session_environment_join", "strategy_decision_outcome_join"]
  query_dimensions:
    entities: ["用户", "设备", "token", "session", "接口", "IP", "UA", "客户端版本"]
    group_by: ["接口序列", "前端事件覆盖", "SDK状态", "token/device/ip/ua一致性", "网关决策", "版本/渠道"]
    compare_with: ["正常端链路", "官方版本", "同接口正常请求", "合法工具调用", "埋点覆盖基线"]
    joins: ["前端事件与后端请求关联", "请求与设备/SDK/指纹关联", "token与登录环境关联", "策略决策与请求关联"]
  time_window:
    baseline: "历史正常端请求窗口，未知时待补充"
    observation: "前端无日志异常窗口，未知时待补充"
    granularity: "分钟"
  expected_outputs:
    metric_outputs: ["前端事件覆盖率", "后端请求量", "SDK日志覆盖率", "接口序列相似度", "token/device/ip/ua冲突率"]
    evidence_outputs: ["协议强证据", "破解包或采集异常线索", "埋点缺失反证", "合法自动化反证"]
    quality_outputs: ["前端日志延迟/丢点状态", "SDK时效", "前后端join口径", "策略日志覆盖率"]
  quality_checks:
    required: ["前端日志延迟/丢点检查", "后端与前端join口径检查", "SDK/指纹时效检查", "官方版本对照", "合法工具反证检查"]
    downgrade_if: ["partial / failed / no_permission", "关键反证未返回", "只有单一数据域支持", "样本量或窗口不清"]
  freshness_expectation: "准实时"
  permission_boundary: "中高敏"
  manual_review_required: "true"
  safety_boundary:
    false_positive_risks: ["埋点缺失误判协议", "破解包误判单纯协议", "合法自动化误判攻击"]
    prohibited_actions: ["不得仅因前端无日志直接拦截或处罚", "不得自动上线协议策略"]
  next_query_intent_when_insufficient:
    intent_type: "sdk_bypass_or_cracked_app_check"
    target_evidence: "破解包绕SDK/采集异常证据"
    reason: "前端无日志可能由破解包或采集异常造成"
```

### 4. dataagent_request

```yaml
dataagent_request:
  request_id: "DAR-AC-003-001"
  source_query_intent_id: "AC-003_adapter_protocol_frontend_missing_001"
  task_type: "data_query"
  natural_language_question: "请验证后端有请求但前端无日志是否能证明请求脱离正常端链路；返回前后端链路、SDK覆盖、请求环境一致性、反证、缺失证据和质量风险，不做最终风控定性。"
  target_evidence: "前后端链路一致性、SDK覆盖、请求环境一致性、协议反证排除"
  data_domains:
    required: ["前端行为域", "后端数据域", "设备信息域", "策略引擎域"]
    optional: ["用户信息域", "风险画像域"]
  field_types_needed:
    identity_and_account: ["user_id", "account_id"]
    device_and_network: ["device_id", "realtime_fingerprint", "async_sdk_signal", "ip", "ua", "app_version", "app_signature", "sdk_status"]
    session_and_chain: ["token_id", "session_id", "frontend_event", "backend_api", "event_time", "request_time", "api_sequence", "gateway_decision"]
    activity_and_channel: []
    risk_and_strategy: ["risk_label", "strategy_hit", "engine_decision", "disposal_action"]
    relation_network: ["relation_group_id"]
  join_paths_needed: ["frontend_backend_chain_join", "request_device_environment_join", "token_session_environment_join", "strategy_decision_outcome_join"]
  time_window:
    baseline: "历史正常端请求窗口，未知时待补充"
    observation: "前端无日志异常窗口，未知时待补充"
    granularity: "分钟"
  query_dimensions:
    entities: ["用户", "设备", "token", "session", "接口", "IP", "UA", "客户端版本"]
    group_by: ["接口序列", "前端事件覆盖", "SDK状态", "token/device/ip/ua一致性", "网关决策", "版本/渠道"]
    compare_with: ["正常端链路", "官方版本", "同接口正常请求", "合法工具调用", "埋点覆盖基线"]
    joins: ["前端事件与后端请求关联", "请求与设备/SDK/指纹关联", "token与登录环境关联", "策略决策与请求关联"]
  expected_outputs:
    metric_outputs: ["前端事件覆盖率", "后端请求量", "SDK日志覆盖率", "接口序列相似度", "token/device/ip/ua冲突率"]
    evidence_outputs: ["协议强证据", "破解包或采集异常线索", "埋点缺失反证", "合法自动化反证"]
    quality_outputs: ["前端日志延迟/丢点状态", "SDK时效", "前后端join口径", "策略日志覆盖率"]
    returned_type_expected: ["dataset_analysis", "partial"]
  quality_checks:
    required: ["前端日志延迟/丢点检查", "后端与前端join口径检查", "SDK/指纹时效检查", "官方版本对照", "合法工具反证检查"]
    downgrade_if: ["partial / failed / no_permission", "关键反证未返回", "只有单一数据域支持", "样本量或窗口不清"]
  freshness_expectation: "准实时"
  permission_boundary: "中高敏"
  safety_boundary:
    false_positive_risks: ["埋点缺失误判协议", "破解包误判单纯协议", "合法自动化误判攻击"]
    prohibited_actions: ["不得仅因前端无日志直接拦截或处罚", "不得自动上线协议策略"]
```

### 5. mock dataagent_response

```yaml
mock_dataagent_response:
  status: "partial"
  returned_type: "dataset_analysis"
  response_summary: "返回了后端请求、部分前端覆盖和 SDK 覆盖摘要；官方版本对照和合法工具反证未完整返回。"
  key_findings:
    - "观测窗口内存在后端请求与前端事件覆盖不一致的样本摘要。"
    - "部分请求的 SDK 信号缺失或延迟，无法区分协议与端侧采集异常。"
    - "接口序列存在相似性，但 token/device/ip/ua 冲突证据不完整。"
  missing_evidence:
    - "官方版本对照"
    - "合法工具调用反证"
    - "完整 token/device/ip/ua 一致性结果"
  counter_evidence:
    - "存在前端埋点口径不一致的可能"
    - "存在破解包或 SDK 采集异常的可能"
  quality_risks:
    - "partial 返回"
    - "前后端 join 口径未完全确认"
    - "SDK 异步信号时效不一致"
  raw_result_reference: "mock-ref-AC-003-001"
```

### 6. normalized_evidence

```yaml
normalized_evidence:
  evidence_id: "NE-AC-003-001"
  source_query_intent_id: "AC-003_adapter_protocol_frontend_missing_001"
  source_dataagent_request_id: "DAR-AC-003-001"
  status: "partial"
  evidence_type: "前后端链路一致性与协议反证排除"
  applicable_skill:
    primary: "protocol_attack_expert_skill"
    auxiliary: ["cracked_app_expert_skill", "anti_crawler_expert_skill", "evidence_decomposition_skill"]
  evidence_summary: "存在前后端链路冲突和接口序列相似性，但关键反证未闭合。"
  key_findings:
    - finding: "后端请求与前端事件覆盖不一致"
      finding_type: "distribution"
      evidence_strength: "medium"
      caveat: "前端埋点和 join 口径未完全确认"
    - finding: "SDK 信号部分缺失"
      finding_type: "quality"
      evidence_strength: "weak"
      caveat: "可能是采集异常或破解包"
  strong_evidence: []
  medium_evidence: ["前后端链路存在冲突", "接口序列存在相似性"]
  weak_evidence: ["部分 SDK 信号缺失"]
  counter_evidence: ["埋点缺失可能", "破解包或采集异常可能", "合法工具反证未返回"]
  missing_evidence: ["官方版本对照", "合法工具反证", "完整 token/device/ip/ua 一致性"]
  quality_risks: ["partial 返回", "join 口径未完全确认", "SDK 时效不一致"]
  freshness_notes:
    expected: "准实时"
    actual: "部分准实时，部分异步"
    impact: "SDK 缺失不能直接解释为协议"
  permission_notes:
    boundary: "中高敏"
    access_status: "permission_limited"
    restricted_evidence: ["完整 token/device/ip/ua 一致性"]
  conclusion_support:
    level: "证据不足"
    reason: "partial 且关键反证未返回，不能直接判协议。"
    cannot_upgrade_because: ["官方版本对照缺失", "合法工具反证缺失", "SDK 异常可能来自采集问题"]
  next_query_intent:
    intent_type: "sdk_bypass_or_cracked_app_check"
    target_evidence: "破解包绕 SDK / 采集异常证据"
    reason: "需要排除端侧采集异常后才能升级协议判断"
  manual_review_required: "true"
  raw_result_reference:
    reference_id: "mock-ref-AC-003-001"
    sensitive_detail_export_allowed: false
```

### 7. Dennis Agent 解释

- 证据强度：中证据为前后端链路冲突和接口序列相似；弱证据为 SDK 缺失。
- 反证：埋点缺失、破解包/采集异常、合法工具调用未排除。
- 缺口：官方版本对照、合法工具反证、完整 token/device/ip/ua 一致性。
- 结论等级：证据不足。
- 治理建议：进入补证和监控；先补破解包/SDK 采集异常，不做协议强拦截。
- 是否需要人工确认：需要。

### 8. 是否符合 adapter_design 的规则

符合。`partial` 被降级，未给明确判断；返回数据集分析没有直接替代风险事实。

### 9. 如果不符合，需要修改哪个 adapter_design 文件

不需要修改。

---

## Case 2：AC-004 群控真机爬取

### 1. 用户问题

一批真机设备访问内容资产，频次高、路径相似，怀疑群控真机爬取，如何判断？

### 2. Skill 路由

- 主控 Skill：`group_control_expert_skill`
- 辅助 Skill：`anti_crawler_expert_skill`、`protocol_attack_expert_skill`、`legal_operation_matrix_playbook_v2_3`

### 3. query_intent_schema_v2

```yaml
query_intent:
  intent_id: "AC-004_adapter_group_control_asset_crawl_001"
  intent_type: "group_control_dispatch_check"
  risk_question: "真机设备访问内容资产是否存在群控统一调度和爬取链路"
  target_evidence: "设备团组、行为路径相似、同批启停、资产访问聚集、合法矩阵/热点反证"
  applicable_skill:
    primary: "group_control_expert_skill"
    auxiliary: ["anti_crawler_expert_skill", "protocol_attack_expert_skill", "legal_operation_matrix_playbook_v2_3"]
  minimum_inputs:
    required: ["账号/设备集合", "资产访问动作", "time_window"]
    optional: ["资产对象集合", "合法运营主体", "热点事件窗口"]
    missing: ["合法矩阵反证", "热点流量反证", "收益或变现结果"]
  required_data_domains: ["设备信息域", "前端行为域", "后端数据域", "关联网络域", "风险画像域"]
  optional_data_domains: ["活动信息域", "策略引擎域"]
  field_types_needed:
    identity_and_account: ["user_id", "account_id"]
    device_and_network: ["device_id", "device_profile", "realtime_fingerprint", "async_sdk_signal", "ip", "ua", "app_version"]
    session_and_chain: ["frontend_event", "backend_api", "event_time", "request_time", "page_path", "click_sequence", "api_sequence", "gateway_decision"]
    activity_and_channel: []
    risk_and_strategy: ["risk_label", "risk_score", "strategy_hit", "engine_decision"]
    relation_network: ["relation_group_id", "strong_device_relation", "user_group_id", "common_device_count", "relation_strength"]
  join_paths_needed: ["asset_access_device_network_join", "frontend_backend_chain_join", "request_device_environment_join", "batch_case_resource_reuse_join", "legal_operation_matrix_authorization_join"]
  query_dimensions:
    entities: ["资产", "设备", "账号", "IP", "页面", "接口", "团组"]
    group_by: ["设备团组", "行为路径", "同批启动/停止", "资产对象", "IP/UA", "合法矩阵状态"]
    compare_with: ["正常真人访问", "热点流量", "合法矩阵", "测试流量", "历史资产访问基线"]
    joins: ["资产访问与设备网络关联", "前端路径与后端请求关联", "设备团组与账号关系关联", "授权主体与批量行为关联"]
  time_window:
    baseline: "历史正常资产访问窗口，未知时待补充"
    observation: "疑似真机爬取窗口，未知时待补充"
    granularity: "分钟"
  expected_outputs:
    metric_outputs: ["资产访问量趋势", "设备团组聚集度", "路径相似度", "同批启停分布", "前后端链路覆盖"]
    evidence_outputs: ["群控统一调度证据", "真机资产访问证据", "合法矩阵/热点/测试反证"]
    quality_outputs: ["设备画像时效", "关系网络更新时间", "前后端日志覆盖"]
  quality_checks:
    required: ["设备画像时效检查", "设备聚集不能直接判群控检查", "热点/合法矩阵/测试反证检查", "前后端口径检查"]
    downgrade_if: ["partial / failed / no_permission", "合法矩阵未排除", "热点流量未排除", "只有设备聚集"]
  freshness_expectation: "准实时"
  permission_boundary: "高敏"
  manual_review_required: "true"
  safety_boundary:
    false_positive_risks: ["热点流量", "合法矩阵", "企业网络", "测试流量"]
    prohibited_actions: ["不得仅因设备聚集直接封禁", "不得自动上线强拦截"]
  next_query_intent_when_insufficient:
    intent_type: "anti_crawler_asset_leakage_check"
    target_evidence: "资产访问链路和外部复用证据"
    reason: "若调度证据不足，需要补资产泄漏链路"
```

### 4. dataagent_request

```yaml
dataagent_request:
  request_id: "DAR-AC-004-001"
  source_query_intent_id: "AC-004_adapter_group_control_asset_crawl_001"
  task_type: "data_query"
  natural_language_question: "请验证真机设备访问内容资产是否存在群控统一调度和爬取链路；返回设备团组、行为路径、同批启停、资产访问聚集、合法矩阵/热点/测试反证和质量风险。"
  target_evidence: "设备团组、行为路径相似、同批启停、资产访问聚集、合法矩阵/热点反证"
  data_domains:
    required: ["设备信息域", "前端行为域", "后端数据域", "关联网络域", "风险画像域"]
    optional: ["活动信息域", "策略引擎域"]
  field_types_needed:
    identity_and_account: ["user_id", "account_id"]
    device_and_network: ["device_id", "device_profile", "realtime_fingerprint", "async_sdk_signal", "ip", "ua", "app_version"]
    session_and_chain: ["frontend_event", "backend_api", "event_time", "request_time", "page_path", "click_sequence", "api_sequence", "gateway_decision"]
    activity_and_channel: []
    risk_and_strategy: ["risk_label", "risk_score", "strategy_hit", "engine_decision"]
    relation_network: ["relation_group_id", "strong_device_relation", "user_group_id", "common_device_count", "relation_strength"]
  join_paths_needed: ["asset_access_device_network_join", "frontend_backend_chain_join", "request_device_environment_join", "batch_case_resource_reuse_join", "legal_operation_matrix_authorization_join"]
  time_window:
    baseline: "历史正常资产访问窗口，未知时待补充"
    observation: "疑似真机爬取窗口，未知时待补充"
    granularity: "分钟"
  query_dimensions:
    entities: ["资产", "设备", "账号", "IP", "页面", "接口", "团组"]
    group_by: ["设备团组", "行为路径", "同批启动/停止", "资产对象", "IP/UA", "合法矩阵状态"]
    compare_with: ["正常真人访问", "热点流量", "合法矩阵", "测试流量", "历史资产访问基线"]
    joins: ["资产访问与设备网络关联", "前端路径与后端请求关联", "设备团组与账号关系关联", "授权主体与批量行为关联"]
  expected_outputs:
    metric_outputs: ["资产访问量趋势", "设备团组聚集度", "路径相似度", "同批启停分布", "前后端链路覆盖"]
    evidence_outputs: ["群控统一调度证据", "真机资产访问证据", "合法矩阵/热点/测试反证"]
    quality_outputs: ["设备画像时效", "关系网络更新时间", "前后端日志覆盖"]
    returned_type_expected: ["dataset_analysis"]
  quality_checks:
    required: ["设备画像时效检查", "设备聚集不能直接判群控检查", "热点/合法矩阵/测试反证检查", "前后端口径检查"]
    downgrade_if: ["partial / failed / no_permission", "合法矩阵未排除", "热点流量未排除", "只有设备聚集"]
  freshness_expectation: "准实时"
  permission_boundary: "高敏"
  safety_boundary:
    false_positive_risks: ["热点流量", "合法矩阵", "企业网络", "测试流量"]
    prohibited_actions: ["不得仅因设备聚集直接封禁", "不得自动上线强拦截"]
```

### 5. mock dataagent_response

```yaml
mock_dataagent_response:
  status: "success"
  returned_type: "dataset_analysis"
  response_summary: "返回设备团组、路径相似、同批启停、资产访问聚集和反证排查摘要。"
  key_findings:
    - "存在多个设备团组对同类资产形成集中访问。"
    - "访问路径和请求序列高度相似，并呈现同批启动/停止。"
    - "未发现授权矩阵能解释该批行为。"
    - "热点事件可解释少量访问峰值，但不能解释团组化和路径一致性。"
  missing_evidence:
    - "外部资产复用或变现证据"
  counter_evidence:
    - "少量访问峰值可能与热点有关"
  quality_risks:
    - "关联网络存在离线更新延迟"
    - "外部复用证据未返回"
  raw_result_reference: "mock-ref-AC-004-001"
```

### 6. normalized_evidence

```yaml
normalized_evidence:
  evidence_id: "NE-AC-004-001"
  source_query_intent_id: "AC-004_adapter_group_control_asset_crawl_001"
  source_dataagent_request_id: "DAR-AC-004-001"
  status: "success"
  evidence_type: "群控真机资产访问链路"
  applicable_skill:
    primary: "group_control_expert_skill"
    auxiliary: ["anti_crawler_expert_skill", "protocol_attack_expert_skill", "legal_operation_matrix_playbook_v2_3"]
  evidence_summary: "设备团组、路径相似、同批启停和资产访问聚集形成中强证据；仍缺外部复用/变现证据。"
  key_findings:
    - finding: "设备团组集中访问资产"
      finding_type: "graph"
      evidence_strength: "strong"
      caveat: "关联网络有离线延迟"
    - finding: "路径和请求序列高度相似"
      finding_type: "distribution"
      evidence_strength: "strong"
      caveat: "需结合热点反证解释"
    - finding: "无授权矩阵解释"
      finding_type: "counter_evidence"
      evidence_strength: "strong"
      caveat: "仅限 mock 返回范围"
  strong_evidence: ["设备团组集中", "行为路径高度相似", "同批启动/停止", "合法矩阵未解释"]
  medium_evidence: ["资产访问聚集"]
  weak_evidence: ["少量热点峰值仍存在"]
  counter_evidence: ["热点可解释少量峰值，但不能解释整体团组化"]
  missing_evidence: ["外部资产复用或变现证据"]
  quality_risks: ["关联网络离线更新延迟", "外部复用证据缺失"]
  freshness_notes:
    expected: "准实时"
    actual: "准实时与离线网络混合"
    impact: "团组证据可用，但外部闭环仍需补证"
  permission_notes:
    boundary: "高敏"
    access_status: "allowed"
    restricted_evidence: []
  conclusion_support:
    level: "高度疑似"
    reason: "群控调度链路证据成组，但资产外部复用/变现未闭合，不给明确判断。"
    cannot_upgrade_because: ["缺外部复用或变现证据", "关联网络存在离线延迟"]
  next_query_intent:
    intent_type: "anti_crawler_asset_leakage_check"
    target_evidence: "资产泄漏外部复用或变现链路"
    reason: "补齐反爬资产泄漏闭环"
  manual_review_required: "true"
  raw_result_reference:
    reference_id: "mock-ref-AC-004-001"
    sensitive_detail_export_allowed: false
```

### 7. Dennis Agent 解释

- 证据强度：强证据包括设备团组、路径相似、同批启停、合法矩阵未解释；中证据为资产访问聚集。
- 反证：热点只能解释少量峰值，不能解释整体团组化。
- 缺口：外部复用/变现证据。
- 结论等级：高度疑似。
- 治理建议：可做灰度限频、挑战、采集加强和外部复用补证；不直接大规模封禁。
- 是否需要人工确认：需要。

### 8. 是否符合 adapter_design 的规则

符合。`success` 也没有自动给“明确判断”，因为缺外部闭环证据。

### 9. 如果不符合，需要修改哪个 adapter_design 文件

不需要修改。

---

## Case 3：AS-001 token 泄露 / 登录态复用

### 1. 用户问题

同一登录态在多个环境使用，怀疑 token 泄露或登录态复用，如何避免误伤正常多端登录？

### 2. Skill 路由

- 主控 Skill：`account_security_expert_skill`
- 辅助 Skill：`protocol_attack_expert_skill`、`credential_stuffing_ato_skill`、`evidence_decomposition_skill`

### 3. query_intent_schema_v2

```yaml
query_intent:
  intent_id: "AS-001_adapter_token_reuse_001"
  intent_type: "token_reuse_or_account_takeover_check"
  risk_question: "同一登录态跨环境使用是否属于 token 泄露/登录态复用或账号接管"
  target_evidence: "token-session-设备-IP-UA一致性、账号生命周期变化、下游敏感动作"
  applicable_skill:
    primary: "account_security_expert_skill"
    auxiliary: ["protocol_attack_expert_skill", "credential_stuffing_ato_skill", "evidence_decomposition_skill"]
  minimum_inputs:
    required: ["user_id 或 account_id 或 token_id", "time_window", "敏感动作语义"]
    optional: ["登录事件窗口", "设备变更语义", "换绑/找回/改密线索", "申诉或客服线索"]
    missing: ["token生命周期口径", "多端登录策略", "正常设备迁移基线"]
  required_data_domains: ["用户信息域", "设备信息域", "后端数据域", "风险画像域", "策略引擎域"]
  optional_data_domains: ["前端行为域", "关联网络域"]
  field_types_needed:
    identity_and_account: ["user_id", "account_id", "login_time", "bind_change_time", "password_change_time", "account_recovery_time", "account_status"]
    device_and_network: ["device_id", "device_profile", "realtime_fingerprint", "ip", "ua", "app_version", "sdk_status"]
    session_and_chain: ["token_id", "session_id", "backend_api", "request_time", "api_sequence", "gateway_decision"]
    activity_and_channel: []
    risk_and_strategy: ["risk_label", "risk_score", "strategy_hit", "engine_decision", "disposal_action", "appeal_status"]
    relation_network: ["relation_group_id", "strong_device_relation"]
  join_paths_needed: ["token_session_environment_join", "account_lifecycle_device_join", "request_device_environment_join", "strategy_decision_outcome_join"]
  query_dimensions:
    entities: ["账号", "token", "session", "设备", "IP", "UA", "敏感动作"]
    group_by: ["token使用环境", "登录环境变化", "设备迁移", "敏感动作", "策略决策", "申诉状态"]
    compare_with: ["历史登录环境", "正常多端登录", "正常换机", "企业网络", "漫游场景"]
    joins: ["token与session关联", "session与设备/IP/UA关联", "账号生命周期与设备变化关联", "策略决策与下游动作关联"]
  time_window:
    baseline: "账号历史正常登录窗口，未知时待补充"
    observation: "疑似token复用窗口，未知时待补充"
    granularity: "分钟"
  expected_outputs:
    metric_outputs: ["token跨设备/IP/UA使用次数", "环境冲突率", "账号生命周期动作分布", "敏感动作突变", "策略命中分布"]
    evidence_outputs: ["token泄露证据", "登录态复用证据", "ATO转交证据", "正常多端/换机反证", "误伤样本"]
    quality_outputs: ["token生命周期口径", "设备指纹时效", "后端日志覆盖", "策略日志覆盖"]
  quality_checks:
    required: ["token生命周期检查", "设备/指纹时效检查", "多端登录策略检查", "后端日志口径检查", "策略命中与事实区分"]
    downgrade_if: ["partial / failed / no_permission", "token_id不可用", "多端策略不清", "只有单一环境异常"]
  freshness_expectation: "实时"
  permission_boundary: "高敏"
  manual_review_required: "true"
  safety_boundary:
    false_positive_risks: ["正常换机误伤", "企业网络误伤", "多端登录误伤", "漫游用户误伤"]
    prohibited_actions: ["不得仅因异地或UA变化冻结账号", "不得自动扣除或处罚"]
  next_query_intent_when_insufficient:
    intent_type: "strategy_effect_and_false_positive_review"
    target_evidence: "验证、限权、召回后的误伤和账号安全效果"
    reason: "token风险处置高敏，证据不足时应先评估验证或限权策略"
```

### 4. dataagent_request

```yaml
dataagent_request:
  request_id: "DAR-AS-001-001"
  source_query_intent_id: "AS-001_adapter_token_reuse_001"
  task_type: "data_query"
  natural_language_question: "请验证同一登录态跨环境使用是否属于 token 泄露/登录态复用或账号接管；返回 token-session-设备-IP-UA 一致性、账号生命周期变化、敏感动作、正常多端/换机反证和质量风险。"
  target_evidence: "token-session-设备-IP-UA一致性、账号生命周期变化、下游敏感动作"
  data_domains:
    required: ["用户信息域", "设备信息域", "后端数据域", "风险画像域", "策略引擎域"]
    optional: ["前端行为域", "关联网络域"]
  field_types_needed:
    identity_and_account: ["user_id", "account_id", "login_time", "bind_change_time", "password_change_time", "account_recovery_time", "account_status"]
    device_and_network: ["device_id", "device_profile", "realtime_fingerprint", "ip", "ua", "app_version", "sdk_status"]
    session_and_chain: ["token_id", "session_id", "backend_api", "request_time", "api_sequence", "gateway_decision"]
    activity_and_channel: []
    risk_and_strategy: ["risk_label", "risk_score", "strategy_hit", "engine_decision", "disposal_action", "appeal_status"]
    relation_network: ["relation_group_id", "strong_device_relation"]
  join_paths_needed: ["token_session_environment_join", "account_lifecycle_device_join", "request_device_environment_join", "strategy_decision_outcome_join"]
  time_window:
    baseline: "账号历史正常登录窗口，未知时待补充"
    observation: "疑似token复用窗口，未知时待补充"
    granularity: "分钟"
  query_dimensions:
    entities: ["账号", "token", "session", "设备", "IP", "UA", "敏感动作"]
    group_by: ["token使用环境", "登录环境变化", "设备迁移", "敏感动作", "策略决策", "申诉状态"]
    compare_with: ["历史登录环境", "正常多端登录", "正常换机", "企业网络", "漫游场景"]
    joins: ["token与session关联", "session与设备/IP/UA关联", "账号生命周期与设备变化关联", "策略决策与下游动作关联"]
  expected_outputs:
    metric_outputs: ["token跨设备/IP/UA使用次数", "环境冲突率", "账号生命周期动作分布", "敏感动作突变", "策略命中分布"]
    evidence_outputs: ["token泄露证据", "登录态复用证据", "ATO转交证据", "正常多端/换机反证", "误伤样本"]
    quality_outputs: ["token生命周期口径", "设备指纹时效", "后端日志覆盖", "策略日志覆盖"]
    returned_type_expected: ["no_permission"]
  quality_checks:
    required: ["token生命周期检查", "设备/指纹时效检查", "多端登录策略检查", "后端日志口径检查", "策略命中与事实区分"]
    downgrade_if: ["partial / failed / no_permission", "token_id不可用", "多端策略不清", "只有单一环境异常"]
  freshness_expectation: "实时"
  permission_boundary: "高敏"
  safety_boundary:
    false_positive_risks: ["正常换机误伤", "企业网络误伤", "多端登录误伤", "漫游用户误伤"]
    prohibited_actions: ["不得仅因异地或UA变化冻结账号", "不得自动扣除或处罚"]
```

### 5. mock dataagent_response

```yaml
mock_dataagent_response:
  status: "no_permission"
  returned_type: "no_permission"
  response_summary: "token/session 环境一致性证据需要更高权限，当前仅返回受限说明。"
  key_findings: []
  missing_evidence:
    - "token 与 session 使用环境"
    - "token 生命周期口径"
    - "敏感动作明细摘要"
  counter_evidence:
    - "正常多端登录、换机、漫游尚未排除"
  quality_risks:
    - "no_permission"
    - "关键证据不可见"
  raw_result_reference: "mock-ref-AS-001-001"
```

### 6. normalized_evidence

```yaml
normalized_evidence:
  evidence_id: "NE-AS-001-001"
  source_query_intent_id: "AS-001_adapter_token_reuse_001"
  source_dataagent_request_id: "DAR-AS-001-001"
  status: "no_permission"
  evidence_type: "token 登录态复用证据"
  applicable_skill:
    primary: "account_security_expert_skill"
    auxiliary: ["protocol_attack_expert_skill", "credential_stuffing_ato_skill", "evidence_decomposition_skill"]
  evidence_summary: "关键 token/session 证据无权限返回，当前不能支持风险定性。"
  key_findings:
    - finding: "关键证据无权限"
      finding_type: "permission"
      evidence_strength: "missing"
      caveat: "no_permission 不等于无风险"
  strong_evidence: []
  medium_evidence: []
  weak_evidence: []
  counter_evidence: ["正常多端登录、换机、漫游尚未排除"]
  missing_evidence: ["token 与 session 使用环境", "token 生命周期口径", "敏感动作明细摘要"]
  quality_risks: ["no_permission", "关键证据不可见"]
  freshness_notes:
    expected: "实时"
    actual: "unknown"
    impact: "无法评估实时风险"
  permission_notes:
    boundary: "高敏"
    access_status: "no_permission"
    restricted_evidence: ["token/session 环境一致性", "敏感动作摘要"]
  conclusion_support:
    level: "证据不足"
    reason: "无权限返回关键证据，不能解释为无风险，也不能支持 token 泄露判断。"
    cannot_upgrade_because: ["no_permission", "关键反证未排除", "关键闭环证据缺失"]
  next_query_intent:
    intent_type: "permission_or_lineage_check"
    target_evidence: "token/session 证据权限与可替代聚合口径"
    reason: "需权限补齐或寻找可用聚合证据后重放"
  manual_review_required: "true"
  raw_result_reference:
    reference_id: "mock-ref-AS-001-001"
    sensitive_detail_export_allowed: false
```

### 7. Dennis Agent 解释

- 证据强度：无有效强/中/弱风险证据，只有权限受限说明。
- 反证：正常多端、换机、漫游未排除。
- 缺口：token/session 使用环境、生命周期、敏感动作。
- 结论等级：证据不足。
- 治理建议：先做权限补齐或可替代聚合口径，最多建议二次验证或监控，不做冻结。
- 是否需要人工确认：需要。

### 8. 是否符合 adapter_design 的规则

符合。`no_permission` 被降级，没有解释为无风险，也没有强结论。

### 9. 如果不符合，需要修改哪个 adapter_design 文件

不需要修改。

---

## Case 4：ACT-003 渠道抢量 / 归因劫持

### 1. 用户问题

某渠道激活上涨、CTIT 异常，怀疑点击注入或归因抢量，如何避免只凭 CTIT 下结论？

### 2. Skill 路由

- 主控 Skill：`traffic_anti_cheating_expert_skill`
- 辅助 Skill：`activity_anti_cheating_expert_skill`、`evidence_decomposition_skill`

### 3. query_intent_schema_v2

```yaml
query_intent:
  intent_id: "ACT-003_adapter_channel_hijack_001"
  intent_type: "channel_attribution_hijacking_check"
  risk_question: "渠道激活上涨和CTIT异常是否属于点击注入/归因劫持，而不是预算、活动、版本或归因规则变化"
  target_evidence: "曝光-点击-激活链路、CTIT、自然量跷跷板、新客真实性、后验质量"
  applicable_skill:
    primary: "traffic_anti_cheating_expert_skill"
    auxiliary: ["activity_anti_cheating_expert_skill", "evidence_decomposition_skill"]
  minimum_inputs:
    required: ["channel_id 或 media_source 或 campaign_id", "time_window", "归因口径"]
    optional: ["预算变化", "活动窗口", "版本发布时间", "媒体策略变化", "后验质量窗口"]
    missing: ["归因窗口规则", "预算/活动变化", "自然量对照", "后验质量窗口"]
  required_data_domains: ["渠道信息域", "用户信息域", "设备信息域", "活动信息域"]
  optional_data_domains: ["风险画像域", "策略引擎域"]
  field_types_needed:
    identity_and_account: ["user_id", "account_id", "account_age", "register_time"]
    device_and_network: ["device_id", "device_profile", "ip", "ua", "app_version"]
    session_and_chain: ["event_time"]
    activity_and_channel: ["campaign_id", "return_user_flag", "exposure_time", "click_time", "activation_time", "channel_id", "media_source", "attribution_type", "ctit"]
    risk_and_strategy: ["risk_label", "risk_score", "strategy_hit"]
    relation_network: ["relation_group_id", "strong_device_relation"]
  join_paths_needed: ["channel_click_activation_user_join", "channel_quality_aftereffect_join", "batch_case_business_context_join", "risk_profile_behavior_outcome_join"]
  query_dimensions:
    entities: ["渠道", "媒体", "campaign", "用户", "设备", "曝光/点击/激活事件"]
    group_by: ["渠道", "媒体", "campaign", "归因类型", "CTIT区间", "新老用户", "设备新旧", "后验质量"]
    compare_with: ["自然量", "历史渠道基线", "同类媒体", "预算变化", "活动窗口", "版本变化", "归因规则"]
    joins: ["曝光-点击-激活链路", "激活与用户生命周期关联", "激活与设备画像关联", "渠道用户与后验质量关联", "业务上下文与渠道波动关联"]
  time_window:
    baseline: "历史渠道正常投放窗口，未知时待补充"
    observation: "渠道异常上涨窗口，未知时待补充"
    granularity: "小时"
  expected_outputs:
    metric_outputs: ["曝光/点击/激活趋势", "CTIT分布", "自然量/渠道量变化", "新客真实性", "老设备/老账号占比", "后验质量"]
    evidence_outputs: ["点击注入证据", "归因劫持证据", "预算/活动/版本/规则反证"]
    quality_outputs: ["归因口径完整性", "渠道数据延迟", "后验窗口完整性", "业务上下文覆盖"]
  quality_checks:
    required: ["渠道归因口径检查", "预算/活动/版本变化检查", "后验质量窗口检查", "设备画像时效检查", "CTIT不能单独定性检查"]
    downgrade_if: ["partial / failed / no_permission", "归因口径缺失", "自然量不可比", "业务反证未返回"]
  freshness_expectation: "T+1"
  permission_boundary: "中敏"
  manual_review_required: "true"
  safety_boundary:
    false_positive_risks: ["正常预算拉升误判抢量", "品牌活动误判作弊", "归因规则变更误判点击注入"]
    prohibited_actions: ["不得仅凭CTIT异常扣量或处罚渠道", "不得自动调整结算"]
  next_query_intent_when_insufficient:
    intent_type: "strategy_effect_and_false_positive_review"
    target_evidence: "渠道策略处置后的误伤、扣量影响和后验效果"
    reason: "渠道治理涉及结算和投放合作，证据不足时应先做效果评估"
```

### 4. dataagent_request

```yaml
dataagent_request:
  request_id: "DAR-ACT-003-001"
  source_query_intent_id: "ACT-003_adapter_channel_hijack_001"
  task_type: "dataset_analysis"
  natural_language_question: "请分析渠道激活上涨和 CTIT 异常是否支持点击注入/归因劫持；必须同时返回曝光-点击-激活链路、自然量对照、新客真实性、后验质量，以及预算、活动、版本、归因规则等反证。"
  target_evidence: "曝光-点击-激活链路、CTIT、自然量跷跷板、新客真实性、后验质量"
  data_domains:
    required: ["渠道信息域", "用户信息域", "设备信息域", "活动信息域"]
    optional: ["风险画像域", "策略引擎域"]
  field_types_needed:
    identity_and_account: ["user_id", "account_id", "account_age", "register_time"]
    device_and_network: ["device_id", "device_profile", "ip", "ua", "app_version"]
    session_and_chain: ["event_time"]
    activity_and_channel: ["campaign_id", "return_user_flag", "exposure_time", "click_time", "activation_time", "channel_id", "media_source", "attribution_type", "ctit"]
    risk_and_strategy: ["risk_label", "risk_score", "strategy_hit"]
    relation_network: ["relation_group_id", "strong_device_relation"]
  join_paths_needed: ["channel_click_activation_user_join", "channel_quality_aftereffect_join", "batch_case_business_context_join", "risk_profile_behavior_outcome_join"]
  time_window:
    baseline: "历史渠道正常投放窗口，未知时待补充"
    observation: "渠道异常上涨窗口，未知时待补充"
    granularity: "小时"
  query_dimensions:
    entities: ["渠道", "媒体", "campaign", "用户", "设备", "曝光/点击/激活事件"]
    group_by: ["渠道", "媒体", "campaign", "归因类型", "CTIT区间", "新老用户", "设备新旧", "后验质量"]
    compare_with: ["自然量", "历史渠道基线", "同类媒体", "预算变化", "活动窗口", "版本变化", "归因规则"]
    joins: ["曝光-点击-激活链路", "激活与用户生命周期关联", "激活与设备画像关联", "渠道用户与后验质量关联", "业务上下文与渠道波动关联"]
  expected_outputs:
    metric_outputs: ["曝光/点击/激活趋势", "CTIT分布", "自然量/渠道量变化", "新客真实性", "老设备/老账号占比", "后验质量"]
    evidence_outputs: ["点击注入证据", "归因劫持证据", "预算/活动/版本/规则反证"]
    quality_outputs: ["归因口径完整性", "渠道数据延迟", "后验窗口完整性", "业务上下文覆盖"]
    returned_type_expected: ["dataset_analysis", "ambiguous_result"]
  quality_checks:
    required: ["渠道归因口径检查", "预算/活动/版本变化检查", "后验质量窗口检查", "设备画像时效检查", "CTIT不能单独定性检查"]
    downgrade_if: ["partial / failed / no_permission", "归因口径缺失", "自然量不可比", "业务反证未返回"]
  freshness_expectation: "T+1"
  permission_boundary: "中敏"
  safety_boundary:
    false_positive_risks: ["正常预算拉升误判抢量", "品牌活动误判作弊", "归因规则变更误判点击注入"]
    prohibited_actions: ["不得仅凭CTIT异常扣量或处罚渠道", "不得自动调整结算"]
```

### 5. mock dataagent_response

```yaml
mock_dataagent_response:
  status: "ambiguous_result"
  returned_type: "dataset_analysis"
  response_summary: "CTIT 分布异常与渠道激活上涨存在，但预算变化和活动窗口也能解释一部分波动，后验质量窗口不足。"
  key_findings:
    - "渠道激活上涨与 CTIT 分布偏移同向。"
    - "自然量对照存在波动，但无法确认是否被挤压。"
    - "预算变化和活动窗口与异常时间重叠。"
    - "后验质量观察窗口不足。"
  missing_evidence:
    - "完整后验质量"
    - "归因规则变更确认"
    - "自然量可比性确认"
  counter_evidence:
    - "预算变化可解释部分增长"
    - "活动窗口可解释部分增长"
  quality_risks:
    - "ambiguous_result"
    - "后验窗口不足"
    - "自然量对照不可比"
  raw_result_reference: "mock-ref-ACT-003-001"
```

### 6. normalized_evidence

```yaml
normalized_evidence:
  evidence_id: "NE-ACT-003-001"
  source_query_intent_id: "ACT-003_adapter_channel_hijack_001"
  source_dataagent_request_id: "DAR-ACT-003-001"
  status: "ambiguous_result"
  evidence_type: "渠道归因劫持证据"
  applicable_skill:
    primary: "traffic_anti_cheating_expert_skill"
    auxiliary: ["activity_anti_cheating_expert_skill", "evidence_decomposition_skill"]
  evidence_summary: "CTIT 与激活异常是风险信号，但预算和活动反证同时存在，后验质量不足。"
  key_findings:
    - finding: "CTIT 分布偏移"
      finding_type: "distribution"
      evidence_strength: "medium"
      caveat: "CTIT 不能单独定性"
    - finding: "预算和活动窗口重叠"
      finding_type: "counter_evidence"
      evidence_strength: "counter"
      caveat: "可能解释部分增长"
  strong_evidence: []
  medium_evidence: ["CTIT 分布异常", "渠道激活上涨"]
  weak_evidence: ["自然量波动但不可比"]
  counter_evidence: ["预算变化可解释部分增长", "活动窗口可解释部分增长"]
  missing_evidence: ["完整后验质量", "归因规则变更确认", "自然量可比性确认"]
  quality_risks: ["ambiguous_result", "后验窗口不足", "自然量对照不可比"]
  freshness_notes:
    expected: "T+1"
    actual: "T+1，但后验需要更长窗口"
    impact: "短期数据不足以确认渠道作弊"
  permission_notes:
    boundary: "中敏"
    access_status: "allowed"
    restricted_evidence: []
  conclusion_support:
    level: "证据不足"
    reason: "CTIT 异常和激活上涨存在，但业务反证未排除且后验不足。"
    cannot_upgrade_because: ["预算变化未排除", "活动窗口未排除", "后验质量不足", "自然量不可比"]
  next_query_intent:
    intent_type: "strategy_effect_and_false_positive_review"
    target_evidence: "渠道治理或扣量策略的误伤和后验效果"
    reason: "若要治理，需要先补后验和误伤评估"
  manual_review_required: "true"
  raw_result_reference:
    reference_id: "mock-ref-ACT-003-001"
    sensitive_detail_export_allowed: false
```

### 7. Dennis Agent 解释

- 证据强度：中证据为 CTIT 偏移和激活上涨；弱证据为自然量波动。
- 反证：预算变化、活动窗口。
- 缺口：后验质量、归因规则确认、自然量可比性。
- 结论等级：证据不足。
- 治理建议：不扣量、不结算调整；补后验质量和归因规则，再做灰度策略评估。
- 是否需要人工确认：需要。

### 8. 是否符合 adapter_design 的规则

符合。`ambiguous_result` 被降级，CTIT 没有被当作强结论。

### 9. 如果不符合，需要修改哪个 adapter_design 文件

不需要修改。

---

## Case 5：AC-009 DAU/DNU 指标异常但缺攻击证据

### 1. 用户问题

DAU/DNU 指标异常波动，但缺少明确攻击证据，是否可以直接定义黑产或流量作弊？

### 2. Skill 路由

- 主控 Skill：`traffic_anti_cheating_expert_skill`
- 辅助 Skill：`business_domain_map_skill`、`evidence_decomposition_skill`、`risk_governance_design_skill`

### 3. query_intent_schema_v2

```yaml
query_intent:
  intent_id: "AC-009_adapter_metric_anomaly_001"
  intent_type: "strategy_effect_and_false_positive_review"
  risk_question: "DAU/DNU异常是否由口径、数据质量、实验、版本、活动、渠道或策略影响解释，而非直接黑产"
  target_evidence: "指标口径校验、数据质量、业务上下文、策略影响、攻击证据缺口"
  applicable_skill:
    primary: "traffic_anti_cheating_expert_skill"
    auxiliary: ["business_domain_map_skill", "evidence_decomposition_skill", "risk_governance_design_skill"]
  minimum_inputs:
    required: ["指标语义", "异常 time_window", "业务范围"]
    optional: ["版本/实验/活动窗口", "渠道变化", "策略变更", "口径变更", "对照组"]
    missing: ["指标口径", "数据延迟/SLA", "实验/版本/活动变化", "策略变更", "攻击样本"]
  required_data_domains: ["策略引擎域", "用户信息域", "前端行为域", "后端数据域", "活动信息域", "渠道信息域"]
  optional_data_domains: ["设备信息域", "风险画像域", "关联网络域"]
  field_types_needed:
    identity_and_account: ["user_id", "account_id", "register_time", "account_status"]
    device_and_network: ["device_id", "device_profile", "ip", "ua", "app_version"]
    session_and_chain: ["frontend_event", "backend_api", "event_time", "request_time", "page_path", "gateway_decision"]
    activity_and_channel: ["campaign_id", "return_user_flag", "exposure_time", "click_time", "activation_time", "channel_id", "media_source", "attribution_type"]
    risk_and_strategy: ["risk_label", "risk_score", "strategy_hit", "engine_decision", "disposal_action", "gray_group"]
    relation_network: ["relation_group_id", "user_group_id", "strong_device_relation"]
  join_paths_needed: ["metric_anomaly_business_context_join", "strategy_decision_outcome_join", "batch_case_business_context_join", "channel_click_activation_user_join", "risk_profile_behavior_outcome_join"]
  query_dimensions:
    entities: ["指标", "用户", "渠道", "活动", "版本", "实验", "策略", "设备"]
    group_by: ["日期/小时", "新老用户", "渠道", "版本", "实验组", "活动入口", "策略灰度组", "风险分层"]
    compare_with: ["历史趋势", "对照组", "同类业务", "口径变更前后", "策略变更前后", "渠道变化前后"]
    joins: ["指标波动与业务上下文关联", "指标波动与策略处置关联", "渠道激活与用户生命周期关联", "风险画像与行为结果关联"]
  time_window:
    baseline: "异常前历史趋势窗口，未知时待补充"
    observation: "DAU/DNU异常窗口，未知时待补充"
    granularity: "天"
  expected_outputs:
    metric_outputs: ["DAU/DNU趋势", "新老用户构成", "渠道/自然变化", "版本/实验/活动分布", "策略命中和处置影响", "风险画像占比"]
    evidence_outputs: ["口径/延迟/SLA解释", "业务上下文解释", "策略影响证据", "攻击证据缺口", "进一步风险补证方向"]
    quality_outputs: ["指标口径状态", "数据延迟状态", "灰度/对照可比性", "后端与前端口径一致性"]
  quality_checks:
    required: ["单日波动风险检查", "指标口径检查", "数据延迟/SLA检查", "策略命中与风险事实区分", "实验/版本/活动/渠道上下文检查"]
    downgrade_if: ["partial / failed / no_permission", "口径不清", "对照组缺失", "业务上下文缺失", "只有指标异常"]
  freshness_expectation: "T+1"
  permission_boundary: "中高敏"
  manual_review_required: "true"
  safety_boundary:
    false_positive_risks: ["正常业务波动误判黑产", "口径问题误判作弊", "策略误伤被误解为攻击"]
    prohibited_actions: ["不得因DAU/DNU异常直接定黑产", "不得自动扣量或上线拦截策略"]
  next_query_intent_when_insufficient:
    intent_type: "channel_attribution_hijacking_check"
    target_evidence: "若异常集中在渠道新客，补渠道抢量/归因劫持证据"
    reason: "DAU/DNU异常需要先定位波动来源，再按渠道、活动、协议或群控分流补证"
```

### 4. dataagent_request

```yaml
dataagent_request:
  request_id: "DAR-AC-009-001"
  source_query_intent_id: "AC-009_adapter_metric_anomaly_001"
  task_type: "dashboard_analysis"
  natural_language_question: "请分析 DAU/DNU 异常是否能被口径、数据质量、实验、版本、活动、渠道或策略影响解释；若业务上下文无法解释，再指出需要补哪些攻击证据。不要将单日指标波动直接定性为黑产。"
  target_evidence: "指标口径校验、数据质量、业务上下文、策略影响、攻击证据缺口"
  data_domains:
    required: ["策略引擎域", "用户信息域", "前端行为域", "后端数据域", "活动信息域", "渠道信息域"]
    optional: ["设备信息域", "风险画像域", "关联网络域"]
  field_types_needed:
    identity_and_account: ["user_id", "account_id", "register_time", "account_status"]
    device_and_network: ["device_id", "device_profile", "ip", "ua", "app_version"]
    session_and_chain: ["frontend_event", "backend_api", "event_time", "request_time", "page_path", "gateway_decision"]
    activity_and_channel: ["campaign_id", "return_user_flag", "exposure_time", "click_time", "activation_time", "channel_id", "media_source", "attribution_type"]
    risk_and_strategy: ["risk_label", "risk_score", "strategy_hit", "engine_decision", "disposal_action", "gray_group"]
    relation_network: ["relation_group_id", "user_group_id", "strong_device_relation"]
  join_paths_needed: ["metric_anomaly_business_context_join", "strategy_decision_outcome_join", "batch_case_business_context_join", "channel_click_activation_user_join", "risk_profile_behavior_outcome_join"]
  time_window:
    baseline: "异常前历史趋势窗口，未知时待补充"
    observation: "DAU/DNU异常窗口，未知时待补充"
    granularity: "天"
  query_dimensions:
    entities: ["指标", "用户", "渠道", "活动", "版本", "实验", "策略", "设备"]
    group_by: ["日期/小时", "新老用户", "渠道", "版本", "实验组", "活动入口", "策略灰度组", "风险分层"]
    compare_with: ["历史趋势", "对照组", "同类业务", "口径变更前后", "策略变更前后", "渠道变化前后"]
    joins: ["指标波动与业务上下文关联", "指标波动与策略处置关联", "渠道激活与用户生命周期关联", "风险画像与行为结果关联"]
  expected_outputs:
    metric_outputs: ["DAU/DNU趋势", "新老用户构成", "渠道/自然变化", "版本/实验/活动分布", "策略命中和处置影响", "风险画像占比"]
    evidence_outputs: ["口径/延迟/SLA解释", "业务上下文解释", "策略影响证据", "攻击证据缺口", "进一步风险补证方向"]
    quality_outputs: ["指标口径状态", "数据延迟状态", "灰度/对照可比性", "后端与前端口径一致性"]
    returned_type_expected: ["dashboard_analysis", "empty_result"]
  quality_checks:
    required: ["单日波动风险检查", "指标口径检查", "数据延迟/SLA检查", "策略命中与风险事实区分", "实验/版本/活动/渠道上下文检查"]
    downgrade_if: ["partial / failed / no_permission", "口径不清", "对照组缺失", "业务上下文缺失", "只有指标异常"]
  freshness_expectation: "T+1"
  permission_boundary: "中高敏"
  safety_boundary:
    false_positive_risks: ["正常业务波动误判黑产", "口径问题误判作弊", "策略误伤被误解为攻击"]
    prohibited_actions: ["不得因DAU/DNU异常直接定黑产", "不得自动扣量或上线拦截策略"]
```

### 5. mock dataagent_response

```yaml
mock_dataagent_response:
  status: "empty_result"
  returned_type: "dashboard_analysis"
  response_summary: "业务上下文归因未返回明确异常原因；也未返回攻击证据。该空结果不能解释为无风险。"
  key_findings:
    - "未返回可解释 DAU/DNU 波动的单一业务事件。"
    - "未返回设备、账号、渠道或行为攻击证据摘要。"
    - "对照组和口径校验不完整。"
  missing_evidence:
    - "指标口径确认"
    - "数据延迟/SLA状态"
    - "对照组"
    - "渠道/活动/版本/实验完整上下文"
    - "攻击样本"
  counter_evidence: []
  quality_risks:
    - "empty_result"
    - "口径和对照组不完整"
    - "业务上下文缺失"
  raw_result_reference: "mock-ref-AC-009-001"
```

### 6. normalized_evidence

```yaml
normalized_evidence:
  evidence_id: "NE-AC-009-001"
  source_query_intent_id: "AC-009_adapter_metric_anomaly_001"
  source_dataagent_request_id: "DAR-AC-009-001"
  status: "empty_result"
  evidence_type: "指标异常业务上下文归因"
  applicable_skill:
    primary: "traffic_anti_cheating_expert_skill"
    auxiliary: ["business_domain_map_skill", "evidence_decomposition_skill", "risk_governance_design_skill"]
  evidence_summary: "未返回明确业务归因，也未返回攻击证据；空结果不能解释为无风险。"
  key_findings:
    - finding: "业务上下文无明确归因"
      finding_type: "quality"
      evidence_strength: "missing"
      caveat: "口径和对照组不完整"
    - finding: "未返回攻击证据"
      finding_type: "missing"
      evidence_strength: "missing"
      caveat: "不能等同无攻击"
  strong_evidence: []
  medium_evidence: []
  weak_evidence: ["DAU/DNU 指标异常仍存在，但缺归因和攻击证据"]
  counter_evidence: []
  missing_evidence: ["指标口径确认", "数据延迟/SLA状态", "对照组", "渠道/活动/版本/实验完整上下文", "攻击样本"]
  quality_risks: ["empty_result", "口径和对照组不完整", "业务上下文缺失"]
  freshness_notes:
    expected: "T+1"
    actual: "unknown"
    impact: "指标异常不能解释为风险事实"
  permission_notes:
    boundary: "中高敏"
    access_status: "unknown"
    restricted_evidence: []
  conclusion_support:
    level: "证据不足"
    reason: "empty_result 且口径、对照组、业务上下文和攻击样本均缺失，不能定性黑产。"
    cannot_upgrade_because: ["empty_result 不能解释为无风险", "业务上下文缺失", "攻击证据缺失", "口径不清"]
  next_query_intent:
    intent_type: "metric_anomaly_business_context_join"
    target_evidence: "补指标口径、SLA、对照组、渠道/活动/版本/实验/策略上下文"
    reason: "先补业务归因；若仍解释不了，再进入渠道、活动、协议或群控补证"
  manual_review_required: "true"
  raw_result_reference:
    reference_id: "mock-ref-AC-009-001"
    sensitive_detail_export_allowed: false
```

### 7. Dennis Agent 解释

- 证据强度：只有弱信号，指标异常仍存在。
- 反证：无有效反证返回。
- 缺口：口径、SLA、对照组、业务上下文、攻击样本。
- 结论等级：证据不足。
- 治理建议：先做指标口径和业务上下文归因；不能直接定黑产，不能直接扣量或上线拦截。
- 是否需要人工确认：需要。

### 8. 是否符合 adapter_design 的规则

符合。`empty_result` 没有被解释为无风险，也没有支持强结论。

### 9. 如果不符合，需要修改哪个 adapter_design 文件

不需要修改。

---

## 汇总

### 1. 5 case 是否都能完成 query_intent → request → response → normalized_evidence

完成：`5/5`。

- AC-003：`partial` 成功降级为证据不足。
- AC-004：`success` 支持高度疑似，但因外部闭环缺失未给明确判断。
- AS-001：`no_permission` 被降级为证据不足。
- ACT-003：`ambiguous_result` 被降级为证据不足。
- AC-009：`empty_result` 被降级为证据不足，未解释为无风险。

### 2. 哪些 returned_type / status 最容易导致误判

- `dashboard_analysis`：容易把指标趋势误判为风险事实。
- `dataset_analysis`：容易把分布异常或低质结果误判为黑产。
- `profile_tags`：容易把风险画像误判为事实标签，本轮未覆盖但设计中已约束。
- `partial`：容易忽略缺失反证后过度自信。
- `no_permission`：容易误解为查无异常。
- `empty_result`：容易误解为无风险。
- `ambiguous_result`：容易在竞争解释未排除时强行定性。

### 3. normalized_evidence_schema_v1 是否够用

够用。它能稳定表达：

- 强/中/弱证据。
- 反证。
- 缺失证据。
- 质量风险。
- 新鲜度限制。
- 权限限制。
- 当前证据最多支持的结论等级。
- 下一步 query_intent。

本轮未发现 schema 阻塞项。

### 4. error_and_degrade_policy 是否足够

足够。`partial`、`no_permission`、`empty_result`、`ambiguous_result` 均能明确降级，并禁止自动处罚、冻结、扣除、结算调整或策略上线。

### 5. 是否可以进入内部平台最小试点设计

可以进入最小试点设计。建议首期只做三类能力：

1. `query_intent -> dataagent_request` 转换器。
2. `dataagent_response -> normalized_evidence` 标准化器。
3. `status/error/degrade` 审计和回放链路。

首期不要做自动治理动作，只返回证据、质量状态、缺口和下一步补证。

### 6. 是否修改了 Skill 文件

否。本轮未修改任何 Skill 文件，只新增回归输出文件：

- `outputs/reviews/dataagent_adapter_mock_closed_loop_5_case.md`
