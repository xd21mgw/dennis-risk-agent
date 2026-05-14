# Data Agent Query Intent 8 Case Regression

本轮继续验证 `query_intent_schema_v2`、`data_domains_v1`、`evidence_sources_v1`、`field_dictionary_template_v1`、`query_intent_to_data_source_map_v1`、`data_join_paths_v1`、`data_freshness_and_quality_rules_v1` 对高频数据取证场景的覆盖能力。

约束：

- 不调用真实 Data Agent。
- 不生成 mock response。
- 不编造真实表名、字段名、SQL 或 API。
- 不修改 Skill 文件。
- 所有字段均为抽象字段类型，所有 join 均为抽象 join path。

---

## Case 1：AC-003 单纯协议判定，前端无日志

### 1. 用户问题

一批后端请求存在，但前端无日志，是否可以直接判定为协议攻击？

### 2. 应触发 Skill

- 主控：`protocol_attack_expert_skill`
- 辅助：`cracked_app_expert_skill`、`anti_crawler_expert_skill`、`evidence_decomposition_skill`

### 3. 目标证据

- 前后端链路一致性。
- SDK 日志覆盖与端侧采集状态。
- token / device / ip / ua 一致性。
- 接口序列是否固化。
- 埋点缺失、破解包、官方版本缺陷、合法工具调用等反证。

### 4. query_intent_schema_v2 完整结构

```yaml
query_intent:
  intent_id: "AC-003_protocol_frontend_missing_v2_001"
  intent_type: "protocol_frontend_backend_join"
  risk_question: "后端有请求但前端无日志时，是否能证明请求脱离正常端链路"
  target_evidence: "前后端链路一致性、SDK覆盖、请求环境一致性、协议反证排除"
  applicable_skill:
    primary: "protocol_attack_expert_skill"
    auxiliary:
      - "cracked_app_expert_skill"
      - "anti_crawler_expert_skill"
      - "evidence_decomposition_skill"
  minimum_inputs:
    required: ["user_id 或 device_id", "api_name 或业务动作", "time_window"]
    optional: ["app_version", "sdk_status", "token_id", "ip/ua 语义", "官方版本或渠道语义"]
    missing: ["端 SDK 覆盖口径", "前端埋点口径", "官方版本对照", "合法自动化反证"]
  required_data_domains: ["前端行为域", "后端数据域", "设备信息域", "策略引擎域"]
  optional_data_domains: ["用户信息域", "风险画像域"]
  field_types_needed:
    identity_and_account: ["user_id", "account_id"]
    device_and_network: ["device_id", "realtime_fingerprint", "async_sdk_signal", "ip", "ua", "app_version", "app_signature", "sdk_status"]
    session_and_chain: ["token_id", "session_id", "frontend_event", "backend_api", "event_time", "request_time", "api_sequence", "gateway_decision"]
    activity_and_channel: []
    risk_and_strategy: ["risk_label", "strategy_hit", "engine_decision", "disposal_action"]
    relation_network: ["relation_group_id"]
  join_paths_needed:
    - "frontend_backend_chain_join"
    - "request_device_environment_join"
    - "token_session_environment_join"
    - "strategy_decision_outcome_join"
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
    evidence_outputs: ["协议强证据", "破解包或采集异常线索", "埋点缺失反证", "合法自动化反证", "网关处置链路"]
    quality_outputs: ["前端日志延迟/丢点状态", "SDK时效", "前后端join口径", "策略日志覆盖率"]
  interpretation_notes:
    strong_evidence_if: ["无端请求、SDK缺失、请求环境冲突、接口序列固化同时出现，且埋点/官方版本/合法工具反证已排除"]
    medium_evidence_if: ["前后端链路冲突明显，但破解包或埋点缺失仍未排除"]
    weak_signal_if: ["只有前端无日志或只有高频请求"]
    counter_evidence_if: ["官方版本也缺日志", "埋点缺失或采样解释成立", "存在授权工具调用", "端侧 SDK 延迟"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["前后端链路", "SDK覆盖", "请求环境一致性", "接口序列", "反证排除"]
    cannot_conclude_if: ["只有前端无日志", "破解包/埋点缺失/合法工具未排除", "join口径不清"]
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
    reason: "前端无日志可能由破解包或采集异常造成，需要先排除端侧绕采集"
```

### 5-15. 结构检查

- required_data_domains 是否合理：合理，协议需要前端、后端、设备和策略四域联动。
- optional_data_domains 是否合理：合理，用户和画像只做补充分层。
- field_types_needed 是否合理：合理，覆盖账号、设备、token、SDK、前后端事件和策略决策。
- join_paths_needed 是否合理：合理，主链路是前后端 join，辅以请求环境、token 环境和策略结果。
- quality_checks 是否覆盖关键误判：覆盖，重点约束“前端无日志不等于协议”。
- freshness_expectation 是否合理：准实时合理，协议排查通常需要较短延迟。
- permission_boundary 是否有基本说明：中高敏合理，涉及请求、设备、token 语义。
- manual_review_required 是否合理：合理，强处置前必须人工确认。
- next_query_intent_when_insufficient 是否可执行：可执行，转入破解包/SDK 绕过补证。
- 当前是否足够发给未来 adapter：足够。
- 如果不够，缺什么输入：缺前端埋点口径、SDK 覆盖口径、官方版本对照、合法工具调用线索。

---

## Case 2：AC-005 破解包绕 SDK / 采集异常

### 1. 用户问题

一批请求前端采集缺失、SDK 日志异常，怀疑是破解包绕 SDK，也可能是官方包埋点或采集问题，怎么生成取证 query_intent？

### 2. 应触发 Skill

- 主控：`cracked_app_expert_skill`
- 辅助：`protocol_attack_expert_skill`、`anti_crawler_expert_skill`、`evidence_decomposition_skill`

### 3. 目标证据

- SDK 缺失和实时指纹异常。
- app_version / app_signature 抽象异常线索。
- 前端采集缺失但后端请求存在。
- 官方版本对照、埋点缺失、采集延迟反证。
- 协议、群控真机、插件辅助的边界。

### 4. query_intent_schema_v2 完整结构

```yaml
query_intent:
  intent_id: "AC-005_cracked_app_sdk_bypass_v2_001"
  intent_type: "sdk_bypass_or_cracked_app_check"
  risk_question: "SDK缺失或采集异常是否由破解包绕采集造成，而不是官方包埋点或采集口径问题"
  target_evidence: "SDK覆盖、实时指纹、版本/签名语义、前后端采集冲突、官方版本反证"
  applicable_skill:
    primary: "cracked_app_expert_skill"
    auxiliary: ["protocol_attack_expert_skill", "anti_crawler_expert_skill", "evidence_decomposition_skill"]
  minimum_inputs:
    required: ["device_id 或账号集合", "风险请求集合", "time_window", "版本/签名语义"]
    optional: ["官方版本对照", "渠道语义", "runtime前台行为语义", "插件/动态加载线索"]
    missing: ["官方版本对照", "包签名分布", "SDK日志覆盖率", "安全模块替换线索"]
  required_data_domains: ["设备信息域", "前端行为域", "后端数据域"]
  optional_data_domains: ["风险画像域", "策略引擎域", "关联网络域"]
  field_types_needed:
    identity_and_account: ["user_id", "account_id"]
    device_and_network: ["device_id", "device_profile", "realtime_fingerprint", "async_sdk_signal", "ip", "ua", "app_version", "app_signature", "sdk_status", "emulator_flag", "cloud_phone_flag"]
    session_and_chain: ["frontend_event", "backend_api", "event_time", "request_time", "page_path", "api_sequence", "gateway_decision"]
    activity_and_channel: []
    risk_and_strategy: ["risk_label", "risk_score", "strategy_hit", "engine_decision"]
    relation_network: ["relation_group_id", "strong_device_relation"]
  join_paths_needed:
    - "request_device_environment_join"
    - "frontend_backend_chain_join"
    - "risk_profile_behavior_outcome_join"
    - "batch_case_resource_reuse_join"
  query_dimensions:
    entities: ["设备", "账号", "请求", "客户端版本", "包签名语义", "SDK状态"]
    group_by: ["SDK状态", "实时指纹状态", "版本/渠道", "包签名语义", "前后端采集覆盖", "设备画像"]
    compare_with: ["官方版本", "正常采集基线", "同版本用户", "协议无端请求", "群控真机行为"]
    joins: ["请求与设备/SDK关联", "前端采集与后端请求关联", "设备风险与行为结果关联", "跨样本资源共性关联"]
  time_window:
    baseline: "官方版本正常采集窗口，未知时待补充"
    observation: "SDK缺失或采集异常窗口，未知时待补充"
    granularity: "小时"
  expected_outputs:
    metric_outputs: ["SDK日志覆盖率", "实时指纹异常率", "版本/签名分布", "前端采集缺失比例", "风险请求与异常包关联度"]
    evidence_outputs: ["破解包嫌疑证据", "官方包埋点缺失反证", "协议补证线索", "群控真机转交线索", "插件辅助线索"]
    quality_outputs: ["SDK信号时效", "版本对照完整性", "前后端口径一致性", "设备画像更新时间"]
  interpretation_notes:
    strong_evidence_if: ["SDK缺失、签名/版本语义异常、安全模块异常线索、后端风险请求关联同时出现，且官方版本对照正常"]
    medium_evidence_if: ["SDK缺失和后端请求关联明显，但签名/版本或官方对照不完整"]
    weak_signal_if: ["只有SDK缺失", "只有前端采集缺失"]
    counter_evidence_if: ["官方包同版本也缺日志", "埋点或采集延迟解释成立", "无包/版本异常线索"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["SDK覆盖", "实时指纹", "版本/签名语义", "后端请求关联", "官方版本对照"]
    cannot_conclude_if: ["只有SDK缺失", "官方版本也异常", "版本/签名语义缺失", "采集延迟未排除"]
  quality_checks:
    required: ["SDK/指纹时效检查", "官方版本对照", "前后端采集口径检查", "设备画像更新时间检查", "风险画像事实性检查"]
    downgrade_if: ["partial / failed / no_permission", "官方版本对照缺失", "包签名/版本语义不可用", "只有单一SDK异常"]
  freshness_expectation: "准实时"
  permission_boundary: "中高敏"
  manual_review_required: "true"
  safety_boundary:
    false_positive_risks: ["官方包采集缺陷被误判破解包", "埋点缺失被误判绕SDK", "协议攻击被误判破解包"]
    prohibited_actions: ["不得仅因SDK缺失直接强制处罚", "不得自动上线版本封禁策略"]
  next_query_intent_when_insufficient:
    intent_type: "protocol_frontend_backend_join"
    target_evidence: "无端请求和接口序列固化证据"
    reason: "如果无端行为且无包证据，需要转入协议补证而非继续强判破解包"
```

### 5-15. 结构检查

- required_data_domains 是否合理：合理，破解包核心是设备、前端采集和后端请求。
- optional_data_domains 是否合理：合理，画像、策略和关联网络用于分层和共性，不是主证据。
- field_types_needed 是否合理：合理，覆盖 SDK、指纹、版本、签名、请求和前端采集。
- join_paths_needed 是否合理：合理，主看请求环境与前后端采集，批量资源共性作为辅助。
- quality_checks 是否覆盖关键误判：覆盖，强调 SDK 缺失不能直接判破解包。
- freshness_expectation 是否合理：准实时合理。
- permission_boundary 是否有基本说明：中高敏合理。
- manual_review_required 是否合理：合理，版本限制或强升前需确认。
- next_query_intent_when_insufficient 是否可执行：可执行，转协议链路补证。
- 当前是否足够发给未来 adapter：足够。
- 如果不够，缺什么输入：缺官方版本对照、包签名分布、渠道语义、安全模块异常线索。

---

## Case 3：AS-001 token 泄露 / 登录态复用

### 1. 用户问题

同一登录态在多个环境使用，怀疑 token 泄露或登录态复用，如何取证并避免误伤正常多端登录？

### 2. 应触发 Skill

- 主控：`account_security_expert_skill`
- 辅助：`protocol_attack_expert_skill`、`credential_stuffing_ato_skill`、`evidence_decomposition_skill`

### 3. 目标证据

- token 与设备、IP、UA、session 的一致性。
- 登录环境是否突变。
- 换绑、找回、改密等账号生命周期动作。
- 下游敏感动作是否突变。
- 正常换机、漫游、多端登录、企业网络反证。

### 4. query_intent_schema_v2 完整结构

```yaml
query_intent:
  intent_id: "AS-001_token_reuse_v2_001"
  intent_type: "token_reuse_or_account_takeover_check"
  risk_question: "同一登录态跨环境使用是否属于token泄露/登录态复用或账号接管"
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
  join_paths_needed:
    - "token_session_environment_join"
    - "account_lifecycle_device_join"
    - "request_device_environment_join"
    - "strategy_decision_outcome_join"
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
  interpretation_notes:
    strong_evidence_if: ["token在不合理设备/IP/UA环境复用，伴随敏感动作突变、账号生命周期异常和策略风险命中"]
    medium_evidence_if: ["登录环境突变明显，但敏感动作或生命周期证据不足"]
    weak_signal_if: ["只有异地登录", "只有UA变化", "只有IP变化"]
    counter_evidence_if: ["正常多端登录", "正常换机", "漫游或企业网络", "用户主动操作和验证链路完整"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["token环境冲突", "登录迁移", "敏感动作", "生命周期变化", "正常使用反证"]
    cannot_conclude_if: ["只有IP/UA变化", "token生命周期口径不清", "多端登录策略未确认", "敏感动作缺失"]
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
    reason: "token风险处置高敏，证据不足时应先评估验证或限权策略的误伤与效果"
```

### 5-15. 结构检查

- required_data_domains 是否合理：合理，token 泄露需要用户、设备、后端、画像、策略联动。
- optional_data_domains 是否合理：合理，前端和关系网络辅助解释行为和团组。
- field_types_needed 是否合理：合理，覆盖 token、session、账号生命周期、设备网络、策略。
- join_paths_needed 是否合理：合理，以 token-session-environment 为主。
- quality_checks 是否覆盖关键误判：覆盖正常换机、多端、漫游、企业网络。
- freshness_expectation 是否合理：实时合理，账号安全风险响应要求高。
- permission_boundary 是否有基本说明：高敏合理。
- manual_review_required 是否合理：合理，强处置前必须人工确认。
- next_query_intent_when_insufficient 是否可执行：可执行，转策略效果/误伤评估。
- 当前是否足够发给未来 adapter：足够。
- 如果不够，缺什么输入：缺 token 生命周期口径、多端登录策略、敏感动作定义、验证链路。

---

## Case 4：AS-003 撞库 / ATO

### 1. 用户问题

登录失败和成功后敏感动作异常，怀疑撞库或 ATO，如何生成不依赖真实表名的取证意图？

### 2. 应触发 Skill

- 主控：`credential_stuffing_ato_skill`
- 辅助：`account_security_expert_skill`、`protocol_attack_expert_skill`、`risk_governance_design_skill`

### 3. 目标证据

- 登录尝试、失败率、成功率和环境集中度。
- 账号控制权变化。
- 成功登录后的敏感动作突变。
- 设备/IP/UA/请求序列是否自动化。
- 忘密找回、正常登录、企业网络、活动登录高峰反证。

### 4. query_intent_schema_v2 完整结构

```yaml
query_intent:
  intent_id: "AS-003_credential_stuffing_ato_v2_001"
  intent_type: "token_reuse_or_account_takeover_check"
  risk_question: "登录异常是否属于撞库/ATO，而不是正常登录高峰、忘密找回或企业网络集中"
  target_evidence: "登录失败/成功模式、账号控制权变化、自动化请求环境、下游敏感动作"
  applicable_skill:
    primary: "credential_stuffing_ato_skill"
    auxiliary: ["account_security_expert_skill", "protocol_attack_expert_skill", "risk_governance_design_skill"]
  minimum_inputs:
    required: ["账号集合或登录入口语义", "time_window", "登录结果语义"]
    optional: ["IP/设备样本", "敏感动作定义", "找回/改密/换绑窗口", "业务活动窗口"]
    missing: ["登录失败/成功口径", "敏感动作定义", "正常登录基线", "验证链路口径"]
  required_data_domains: ["用户信息域", "设备信息域", "后端数据域", "风险画像域", "策略引擎域"]
  optional_data_domains: ["前端行为域", "关联网络域"]
  field_types_needed:
    identity_and_account: ["user_id", "account_id", "login_time", "bind_change_time", "password_change_time", "account_recovery_time", "account_status"]
    device_and_network: ["device_id", "device_profile", "realtime_fingerprint", "ip", "ua", "sdk_status", "emulator_flag", "cloud_phone_flag"]
    session_and_chain: ["session_id", "backend_api", "request_time", "api_sequence", "gateway_decision"]
    activity_and_channel: []
    risk_and_strategy: ["risk_label", "risk_score", "strategy_hit", "engine_decision", "disposal_action", "appeal_status"]
    relation_network: ["relation_group_id", "strong_device_relation", "common_device_count"]
  join_paths_needed:
    - "account_lifecycle_device_join"
    - "request_device_environment_join"
    - "token_session_environment_join"
    - "strategy_decision_outcome_join"
    - "batch_case_resource_reuse_join"
  query_dimensions:
    entities: ["账号", "登录入口", "设备", "IP", "UA", "session", "敏感动作"]
    group_by: ["登录结果", "失败/成功序列", "设备/IP/UA聚集", "账号生命周期动作", "下游敏感动作", "策略决策"]
    compare_with: ["历史登录基线", "业务活动登录高峰", "正常找回/改密", "企业网络", "正常多账号代管"]
    joins: ["登录与设备环境关联", "登录与账号生命周期关联", "登录成功与下游敏感动作关联", "策略处置与申诉结果关联"]
  time_window:
    baseline: "历史正常登录窗口，未知时待补充"
    observation: "登录异常窗口，未知时待补充"
    granularity: "分钟"
  expected_outputs:
    metric_outputs: ["登录失败率", "登录成功率", "设备/IP/UA集中度", "账号生命周期异常比例", "敏感动作突变比例", "验证/拦截命中"]
    evidence_outputs: ["撞库证据", "ATO证据", "协议自动化线索", "正常找回/登录高峰反证", "误伤样本"]
    quality_outputs: ["登录口径完整性", "验证链路覆盖", "策略日志覆盖", "关联网络更新时间"]
  interpretation_notes:
    strong_evidence_if: ["批量账号登录尝试、失败/成功模式异常、环境集中、成功后敏感动作突变同时出现"]
    medium_evidence_if: ["登录环境和失败/成功模式异常，但下游敏感动作不完整"]
    weak_signal_if: ["只有登录失败率升高", "只有IP集中", "只有策略命中"]
    counter_evidence_if: ["业务活动登录高峰", "正常找回或改密", "企业网络或机构代管", "用户验证链路完整"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["登录模式", "环境聚集", "账号生命周期", "下游敏感动作", "反证排除"]
    cannot_conclude_if: ["只有失败率升高", "敏感动作缺失", "登录口径不清", "正常高峰未排除"]
  quality_checks:
    required: ["登录成功/失败口径检查", "后端日志延迟检查", "设备画像时效检查", "策略命中与事实区分", "业务活动窗口检查"]
    downgrade_if: ["partial / failed / no_permission", "敏感动作未返回", "验证链路缺失", "只有单一登录指标异常"]
  freshness_expectation: "实时"
  permission_boundary: "高敏"
  manual_review_required: "true"
  safety_boundary:
    false_positive_risks: ["业务登录高峰误判撞库", "企业网络误伤", "账号找回误判ATO"]
    prohibited_actions: ["不得仅凭失败率升高冻结账号", "不得自动处罚或扣除权益"]
  next_query_intent_when_insufficient:
    intent_type: "protocol_frontend_backend_join"
    target_evidence: "登录接口自动化和前后端链路一致性"
    reason: "如果登录模式异常但ATO证据不足，需要判断是否存在协议化登录尝试"
```

### 5-15. 结构检查

- required_data_domains 是否合理：合理，撞库/ATO 与账号、设备、后端、画像、策略强相关。
- optional_data_domains 是否合理：合理，前端和关系网络用于补充行为路径与资源共性。
- field_types_needed 是否合理：合理，覆盖登录、生命周期、设备环境、策略处置。
- join_paths_needed 是否合理：合理，兼顾账号接管、协议自动化和批量资源复用。
- quality_checks 是否覆盖关键误判：覆盖业务高峰、找回改密、企业网络。
- freshness_expectation 是否合理：实时合理。
- permission_boundary 是否有基本说明：高敏合理。
- manual_review_required 是否合理：合理。
- next_query_intent_when_insufficient 是否可执行：可执行，转协议链路。
- 当前是否足够发给未来 adapter：足够。
- 如果不够，缺什么输入：缺登录结果口径、验证链路、敏感动作定义、业务活动窗口。

---

## Case 5：ACT-003 渠道抢量 / 归因劫持

### 1. 用户问题

某渠道激活上涨、CTIT 异常，怀疑点击注入或归因抢量，如何避免只凭 CTIT 下结论？

### 2. 应触发 Skill

- 主控：`traffic_anti_cheating_expert_skill`
- 辅助：`activity_anti_cheating_expert_skill`、`evidence_decomposition_skill`

### 3. 目标证据

- 曝光、点击、激活链路。
- CTIT 分布。
- 自然量/渠道量跷跷板。
- 新客真实性、老设备/老账号占比。
- 后验质量。
- 预算、活动、版本、媒体策略和归因窗口反证。

### 4. query_intent_schema_v2 完整结构

```yaml
query_intent:
  intent_id: "ACT-003_channel_attribution_hijacking_v2_001"
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
  join_paths_needed:
    - "channel_click_activation_user_join"
    - "channel_quality_aftereffect_join"
    - "batch_case_business_context_join"
    - "risk_profile_behavior_outcome_join"
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
    evidence_outputs: ["点击注入证据", "归因劫持证据", "品牌量抢占线索", "预算/活动/版本/规则反证"]
    quality_outputs: ["归因口径完整性", "渠道数据延迟", "后验窗口完整性", "业务上下文覆盖"]
  interpretation_notes:
    strong_evidence_if: ["CTIT异常、自然量被挤压、老设备/老账号占比异常、后验质量差，并排除预算/活动/版本/归因规则变化"]
    medium_evidence_if: ["CTIT和自然量跷跷板明显，但后验质量或业务反证不完整"]
    weak_signal_if: ["只有CTIT异常", "只有激活上涨", "只有后验差"]
    counter_evidence_if: ["预算提升", "品牌活动", "版本发布", "归因窗口调整", "媒体策略变化", "新客质量正常"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["曝光点击激活链路", "CTIT", "自然量对照", "新客真实性", "后验质量", "业务反证"]
    cannot_conclude_if: ["只有CTIT异常", "归因规则不清", "预算/活动/版本未排除", "后验窗口不足"]
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
    reason: "渠道治理涉及结算和投放合作，证据不足时应先做策略效果与误伤评估"
```

### 5-15. 结构检查

- required_data_domains 是否合理：合理，渠道风险核心是渠道、用户、设备、活动。
- optional_data_domains 是否合理：合理，画像和策略只辅助分层。
- field_types_needed 是否合理：合理，覆盖曝光、点击、激活、CTIT、新客和设备。
- join_paths_needed 是否合理：合理，渠道链路和后验质量都覆盖。
- quality_checks 是否覆盖关键误判：覆盖 CTIT 单点误判、预算/活动/版本/规则变化。
- freshness_expectation 是否合理：T+1 合理，渠道后验通常需要观察。
- permission_boundary 是否有基本说明：中敏合理。
- manual_review_required 是否合理：合理，涉及结算和渠道合作。
- next_query_intent_when_insufficient 是否可执行：可执行，转策略效果/误伤。
- 当前是否足够发给未来 adapter：足够。
- 如果不够，缺什么输入：缺归因规则、预算活动变化、自然量对照、后验窗口。

---

## Case 6：ACT-002 活动低质但无黑产证据

### 1. 用户问题

活动低钱效用户很多、后验质量差，但没有明确黑产证据，是否可以直接定义活动黑产？

### 2. 应触发 Skill

- 主控：`activity_anti_cheating_expert_skill`
- 辅助：`real_user_crowdsourcing_skill`、`risk_governance_design_skill`

### 3. 目标证据

- 活动参与路径、回流路径、邀请关系。
- 奖励/提现状态。
- 留存、付费、复访等后验质量。
- 设备/账号/团组聚集和风险画像。
- 活动目标、冷启动、自然传播、预算目标等反证。

### 4. query_intent_schema_v2 完整结构

```yaml
query_intent:
  intent_id: "ACT-002_activity_low_quality_no_black_evidence_v2_001"
  intent_type: "activity_black_industry_or_low_quality_check"
  risk_question: "活动低钱效和后验质量差是否只能定义为活动低质，而不能直接定义黑产"
  target_evidence: "活动参与、奖励/提现、后验质量、设备/账号聚集、黑产反证"
  applicable_skill:
    primary: "activity_anti_cheating_expert_skill"
    auxiliary: ["real_user_crowdsourcing_skill", "risk_governance_design_skill"]
  minimum_inputs:
    required: ["campaign_id 或活动语义", "用户/账号集合", "time_window", "奖励动作语义"]
    optional: ["活动目标", "预算目标", "邀请规则", "后验质量窗口", "自然用户对照组"]
    missing: ["活动目标", "低质口径", "黑产证据", "自然对照组", "后验质量窗口"]
  required_data_domains: ["活动信息域", "用户信息域", "设备信息域", "风险画像域", "关联网络域", "策略引擎域"]
  optional_data_domains: ["前端行为域", "渠道信息域"]
  field_types_needed:
    identity_and_account: ["user_id", "account_id", "account_age", "register_time", "login_time", "account_status"]
    device_and_network: ["device_id", "device_profile", "ip", "ua", "app_version"]
    session_and_chain: ["frontend_event", "event_time", "page_path", "click_sequence"]
    activity_and_channel: ["campaign_id", "invite_relation", "return_user_flag", "activity_participation", "reward_status", "withdraw_status", "channel_id", "media_source"]
    risk_and_strategy: ["risk_label", "risk_score", "strategy_hit", "engine_decision", "disposal_action"]
    relation_network: ["relation_group_id", "user_group_id", "relation_edge_type", "relation_strength"]
  join_paths_needed:
    - "activity_participation_device_reward_join"
    - "invite_relation_network_join"
    - "risk_profile_behavior_outcome_join"
    - "strategy_decision_outcome_join"
    - "batch_case_business_context_join"
  query_dimensions:
    entities: ["活动", "用户", "账号", "设备", "邀请关系", "奖励/提现", "策略处置"]
    group_by: ["参与路径", "邀请关系", "回流状态", "奖励/提现", "后验质量", "设备/用户团组", "活动入口"]
    compare_with: ["活动目标", "自然用户对照组", "历史同类活动", "冷启动目标", "正常低质用户", "真人众包样本"]
    joins: ["活动参与与设备/账号关联", "邀请关系与团组关联", "活动结果与风险画像关联", "策略命中与后验结果关联", "业务目标与低质结果关联"]
  time_window:
    baseline: "历史同类活动或自然用户窗口，未知时待补充"
    observation: "活动低质观测窗口，未知时待补充"
    granularity: "天"
  expected_outputs:
    metric_outputs: ["活动参与量", "奖励/提现分布", "留存/付费/复访后验", "邀请关系聚集", "设备/账号团组", "风险画像占比"]
    evidence_outputs: ["活动低质证据", "黑产强证据缺失说明", "真人众包嫌疑", "自然传播/活动目标反证", "治理分层建议所需证据"]
    quality_outputs: ["后验窗口完整性", "活动目标口径", "画像来源说明", "策略命中与事实区分"]
  interpretation_notes:
    strong_evidence_if: ["低质伴随奖励/提现聚集、设备/账号团组、邀请异常、任务化线索和风险画像一致"]
    medium_evidence_if: ["后验质量差且奖励集中，但团组/收益链/任务化证据不足"]
    weak_signal_if: ["只有低钱效", "只有后验质量差", "只有参与量高"]
    counter_evidence_if: ["活动目标本身是拉新/回流", "冷启动用户自然低留存", "自然传播可解释", "无奖励/提现聚集", "无设备/账号团组"]
  conclusion_threshold:
    sufficient_for: "证据不足"
    must_combine_with: ["活动参与路径", "奖励/提现", "后验质量", "设备/账号聚集", "活动目标反证"]
    cannot_conclude_if: ["只有低钱效", "缺少收益链和团组", "活动目标未确认", "后验窗口不足"]
  quality_checks:
    required: ["活动目标检查", "低钱效不能等同黑产检查", "后验窗口检查", "邀请关系与设备收益联动检查", "风险画像事实性检查"]
    downgrade_if: ["partial / failed / no_permission", "活动目标缺失", "后验窗口不足", "只有低质指标"]
  freshness_expectation: "长周期后验"
  permission_boundary: "高敏"
  manual_review_required: "true"
  safety_boundary:
    false_positive_risks: ["低质用户被误判黑产", "冷启动目标被误判作弊", "活动自然传播被误伤"]
    prohibited_actions: ["不得因低钱效直接处罚用户", "不得自动扣除奖励或冻结账号"]
  next_query_intent_when_insufficient:
    intent_type: "strategy_effect_and_false_positive_review"
    target_evidence: "低质分层治理的业务影响、误伤和效果"
    reason: "无黑产证据时应按低质治理和监控赋能处理，而不是强打黑产"
```

### 5-15. 结构检查

- required_data_domains 是否合理：合理，活动低质需要活动、用户、设备、画像、关系、策略。
- optional_data_domains 是否合理：合理，前端和渠道用于解释入口和来源。
- field_types_needed 是否合理：合理，覆盖活动、奖励、提现、后验、画像和关系。
- join_paths_needed 是否合理：合理，活动参与、邀请关系、画像后验、业务上下文都覆盖。
- quality_checks 是否覆盖关键误判：覆盖低钱效不等于黑产。
- freshness_expectation 是否合理：长周期后验合理。
- permission_boundary 是否有基本说明：高敏合理，涉及用户分层和奖励。
- manual_review_required 是否合理：合理。
- next_query_intent_when_insufficient 是否可执行：可执行，转低质治理效果复盘。
- 当前是否足够发给未来 adapter：足够。
- 如果不够，缺什么输入：缺活动目标、低质定义、自然对照组、奖励/提现口径、后验窗口。

---

## Case 7：AC-009 DAU/DNU 异常但缺攻击证据

### 1. 用户问题

DAU/DNU 指标异常波动，但缺少明确攻击证据，是否可以直接定义黑产或流量作弊？

### 2. 应触发 Skill

- 主控：`traffic_anti_cheating_expert_skill`
- 辅助：`business_domain_map_skill`、`strategy_effect_and_false_positive_review`、`evidence_decomposition_skill`

### 3. 目标证据

- 指标口径、数据延迟、SLA、实验、版本、活动、渠道变化。
- 用户构成、新客真实性、渠道/自然变化。
- 策略命中和处置影响。
- 攻击证据是否存在：设备聚集、行为异常、账号风险、渠道异常。

### 4. query_intent_schema_v2 完整结构

```yaml
query_intent:
  intent_id: "AC-009_dau_dnu_anomaly_no_attack_evidence_v2_001"
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
  join_paths_needed:
    - "strategy_decision_outcome_join"
    - "batch_case_business_context_join"
    - "channel_click_activation_user_join"
    - "risk_profile_behavior_outcome_join"
  query_dimensions:
    entities: ["指标", "用户", "渠道", "活动", "版本", "实验", "策略", "设备"]
    group_by: ["日期/小时", "新老用户", "渠道", "版本", "实验组", "活动入口", "策略灰度组", "风险分层"]
    compare_with: ["历史趋势", "对照组", "同类业务", "口径变更前后", "策略变更前后", "渠道变化前后"]
    joins: ["指标波动与策略处置关联", "指标波动与业务上下文关联", "渠道激活与用户生命周期关联", "风险画像与行为结果关联"]
  time_window:
    baseline: "异常前历史趋势窗口，未知时待补充"
    observation: "DAU/DNU异常窗口，未知时待补充"
    granularity: "天"
  expected_outputs:
    metric_outputs: ["DAU/DNU趋势", "新老用户构成", "渠道/自然变化", "版本/实验/活动分布", "策略命中和处置影响", "风险画像占比"]
    evidence_outputs: ["口径/延迟/SLA解释", "业务上下文解释", "策略影响证据", "攻击证据缺口", "进一步风险补证方向"]
    quality_outputs: ["指标口径状态", "数据延迟状态", "灰度/对照可比性", "后端与前端口径一致性"]
  interpretation_notes:
    strong_evidence_if: ["指标异常可被口径、延迟、实验、版本、活动、渠道或策略变更充分解释"]
    medium_evidence_if: ["业务上下文能部分解释，但仍有风险样本未闭环"]
    weak_signal_if: ["只有DAU/DNU单日波动", "只有策略命中量变化"]
    counter_evidence_if: ["存在设备/账号/渠道/行为多维攻击证据，且业务口径反证已排除"]
  conclusion_threshold:
    sufficient_for: "证据不足"
    must_combine_with: ["口径校验", "数据质量", "业务上下文", "对照组", "风险证据"]
    cannot_conclude_if: ["只有单日波动", "攻击证据缺失", "口径和SLA未确认", "实验/版本/活动未排除"]
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

### 5-15. 结构检查

- required_data_domains 是否合理：合理，DAU/DNU 需要策略、用户、前后端、活动、渠道多域校验。
- optional_data_domains 是否合理：合理，设备、画像、关系用于攻击证据补充。
- field_types_needed 是否合理：合理，覆盖指标构成、渠道、活动、策略、设备和风险。
- join_paths_needed 是否合理：基本合理，当前用策略效果、业务上下文、渠道链路和画像后验组合表达。
- quality_checks 是否覆盖关键误判：覆盖单日波动、口径、SLA、实验/版本/活动/渠道。
- freshness_expectation 是否合理：T+1 合理，指标复盘通常看天级趋势。
- permission_boundary 是否有基本说明：中高敏合理。
- manual_review_required 是否合理：合理。
- next_query_intent_when_insufficient 是否可执行：可执行，按来源转渠道补证；也可转活动或协议补证。
- 当前是否足够发给未来 adapter：足够但偏泛。
- 如果不够，缺什么输入：缺指标口径、SLA、异常分布、业务日历、策略/实验/版本变更。

---

## Case 8：策略复盘 策略命中后误伤和效果评估

### 1. 用户问题

某风控策略上线后命中量较高，需要评估风险治理效果、业务损伤和误伤，如何生成 Data Agent 取证意图？

### 2. 应触发 Skill

- 主控：`risk_governance_design_skill`
- 辅助：`traffic_anti_cheating_expert_skill`、`account_security_expert_skill`、`activity_anti_cheating_expert_skill`

### 3. 目标证据

- 策略命中量、处置结果、灰度分组。
- 后验风险结果。
- 业务指标影响。
- 申诉/客诉和误伤样本。
- 对照组差异和回滚条件。

### 4. query_intent_schema_v2 完整结构

```yaml
query_intent:
  intent_id: "STRATEGY-REVIEW_false_positive_effect_v2_001"
  intent_type: "strategy_effect_and_false_positive_review"
  risk_question: "策略命中后是否有效降低风险，并且误伤和业务损伤是否可接受"
  target_evidence: "策略命中、处置、后验风险、业务影响、申诉/客诉、对照组差异"
  applicable_skill:
    primary: "risk_governance_design_skill"
    auxiliary: ["traffic_anti_cheating_expert_skill", "account_security_expert_skill", "activity_anti_cheating_expert_skill"]
  minimum_inputs:
    required: ["策略语义", "命中对象集合", "处置窗口", "后验窗口"]
    optional: ["灰度分组", "对照组", "业务指标", "申诉/客诉语义", "回滚阈值"]
    missing: ["对照组", "后验风险定义", "业务损伤指标", "误伤样本口径", "回滚阈值"]
  required_data_domains: ["策略引擎域", "用户信息域", "前端行为域", "后端数据域", "活动信息域", "风险画像域"]
  optional_data_domains: ["设备信息域", "渠道信息域", "关联网络域"]
  field_types_needed:
    identity_and_account: ["user_id", "account_id", "account_status"]
    device_and_network: ["device_id", "device_profile", "ip", "ua", "app_version"]
    session_and_chain: ["frontend_event", "backend_api", "event_time", "request_time", "gateway_decision"]
    activity_and_channel: ["campaign_id", "activity_participation", "reward_status", "withdraw_status", "channel_id", "media_source"]
    risk_and_strategy: ["risk_label", "risk_score", "strategy_hit", "engine_decision", "disposal_action", "gray_group", "appeal_status"]
    relation_network: ["relation_group_id", "user_group_id", "relation_strength"]
  join_paths_needed:
    - "strategy_decision_outcome_join"
    - "risk_profile_behavior_outcome_join"
    - "batch_case_business_context_join"
  query_dimensions:
    entities: ["策略", "命中对象", "灰度组", "处置动作", "业务结果", "申诉/客诉", "风险后验"]
    group_by: ["策略版本", "灰度组", "处置动作", "风险分层", "业务场景", "用户类型", "后验结果", "申诉状态"]
    compare_with: ["对照组", "上线前基线", "灰度组", "未命中相似人群", "历史同类策略"]
    joins: ["策略命中与处置结果关联", "处置与用户后验行为关联", "风险画像与后验结果关联", "业务上下文与指标变化关联"]
  time_window:
    baseline: "策略上线前基线窗口，未知时待补充"
    observation: "策略上线后处置和后验窗口，未知时待补充"
    granularity: "天"
  expected_outputs:
    metric_outputs: ["策略命中量", "处置分布", "风险后验变化", "业务指标影响", "申诉/客诉率", "对照组差异", "灰度组差异"]
    evidence_outputs: ["策略有效性证据", "误伤证据", "业务损伤证据", "回滚或扩量依据", "规则优化方向"]
    quality_outputs: ["灰度/对照可比性", "后验窗口完整性", "策略日志覆盖", "申诉/客诉样本完整性"]
  interpretation_notes:
    strong_evidence_if: ["命中组风险后验显著下降、对照组可比、业务损伤和申诉可控"]
    medium_evidence_if: ["风险下降明显，但对照组或误伤样本不完整"]
    weak_signal_if: ["只有策略命中量上涨", "只有拦截量上涨", "只有风险画像占比下降"]
    counter_evidence_if: ["申诉/客诉异常升高", "业务核心指标明显受损", "对照组无差异", "风险后验未改善"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["策略命中", "处置结果", "后验风险", "业务指标", "误伤样本", "对照组"]
    cannot_conclude_if: ["只有策略命中量", "后验窗口不足", "对照组缺失", "申诉/客诉未返回", "业务影响未评估"]
  quality_checks:
    required: ["策略命中与风险事实区分", "灰度和对照口径检查", "后验窗口检查", "申诉/客诉样本偏差检查", "业务指标口径检查"]
    downgrade_if: ["partial / failed / no_permission", "对照组缺失", "后验结果缺失", "误伤样本不可用", "只有命中量"]
  freshness_expectation: "长周期后验"
  permission_boundary: "高敏"
  manual_review_required: "true"
  safety_boundary:
    false_positive_risks: ["策略命中被误读为风险事实", "短期风险下降掩盖长期误伤", "申诉样本偏差"]
    prohibited_actions: ["不得仅凭命中量扩量", "不得自动回滚或自动扩量", "不得自动处罚、冻结、扣除"]
  next_query_intent_when_insufficient:
    intent_type: "batch_case_commonality_check"
    target_evidence: "误伤样本共性、风险样本共性和可切分优化空间"
    reason: "若策略效果不清，需要进一步拆分误伤与真阳样本共性，支持局部规则优化"
```

### 5-15. 结构检查

- required_data_domains 是否合理：合理，策略复盘需要策略、用户、前后端、活动、画像。
- optional_data_domains 是否合理：合理，设备、渠道、关联网络按业务场景补充。
- field_types_needed 是否合理：合理，覆盖策略命中、灰度、处置、申诉和后验。
- join_paths_needed 是否合理：合理，策略效果以 `strategy_decision_outcome_join` 为核心。
- quality_checks 是否覆盖关键误判：覆盖策略命中不等于风险事实、对照组和后验窗口问题。
- freshness_expectation 是否合理：长周期后验合理。
- permission_boundary 是否有基本说明：高敏合理。
- manual_review_required 是否合理：合理，策略扩量/回滚需人工确认。
- next_query_intent_when_insufficient 是否可执行：可执行，转误伤/真阳共性分析。
- 当前是否足够发给未来 adapter：足够。
- 如果不够，缺什么输入：缺策略版本、灰度/对照、后验定义、业务损伤指标、申诉/客诉口径。

---

## 汇总

### 1. 8 case 完整率

完整率：`8/8`。

8 个 case 都能按 `query_intent_schema_v2` 生成完整结构，并覆盖：

- 目标证据。
- 数据域。
- 字段类型。
- join path。
- 质量检查。
- 新鲜度预期。
- 权限边界。
- 人工确认。
- 证据不足时的下一步 query_intent。

### 2. 可发给 adapter 的 case 数

可发给 adapter：`8/8`。

其中 `AC-009 DAU/DNU异常` 由于业务上下文依赖强，属于“可发但需要 adapter 支持业务日历、实验、版本、渠道、策略变更等上下文路由”。

### 3. 勉强可用 case 数

勉强可用：`0/8`。

没有结构层面无法表达的 case。部分 case 在结论层必须保守，但 query_intent 已能表达查询计划和降级规则。

### 4. 不可用 case 数

不可用：`0/8`。

### 5. 哪些数据域选择不稳定

- `AC-009 DAU/DNU异常`：数据域跨度最大，既可能是数据口径/业务变化，也可能是渠道、活动、策略或攻击，需要 adapter 支持先定位波动来源。
- `ACT-002 活动低质`：是否加入渠道信息域取决于活动入口和投放依赖，当前作为 optional 合理。
- `AS-003 撞库/ATO`：前端行为域是否必选取决于登录链路埋点覆盖，当前作为 optional 合理。

### 6. 哪些 join path 仍缺

本轮没有阻塞性缺失。

可选后续增强：

- `metric_anomaly_business_context_join`：专门服务 DAU/DNU、GMV、转化率等指标异常，联动口径、SLA、实验、版本、活动、渠道、策略。
- `login_attempt_outcome_join`：专门服务撞库/登录失败-成功-验证-敏感动作链路。目前可由 `account_lifecycle_device_join`、`request_device_environment_join`、`token_session_environment_join` 组合覆盖。

### 7. 哪些 schema 字段不好用

- `permission_boundary`：目前只能写抽象等级，真实权限仍需未来平台承接；但本轮不纠结权限，抽象表达足够。
- `freshness_expectation`：对同时需要实时处置和长周期后验的 case 表达不够细，可以未来支持数组或按证据分层表达。
- `next_query_intent_when_insufficient`：只能放一个下一步方向，复杂 case 可能需要多个分支。当前为保持 schema 简洁，可以先不改。

### 8. 是否建议进入 adapter 设计

建议进入 adapter 设计。

第一阶段 adapter 建议只做三件事：

1. 将 `required_data_domains`、`field_types_needed`、`join_paths_needed` 转成内部平台可理解的查询计划。
2. 返回结构化结果、质量状态和缺失证据，不给最终风控定性。
3. 将 `quality_checks`、`conclusion_threshold`、`next_query_intent_when_insufficient` 原样回传给 Dennis Agent 做解释和追问。

### 9. 是否修改了 Skill 文件

否。本轮未修改任何 Skill 文件，只新增回归输出文件：

- `outputs/reviews/dataagent_query_intent_8_case_regression.md`
