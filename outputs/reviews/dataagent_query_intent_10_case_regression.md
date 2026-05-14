# Data Agent Query Intent 10 Case 回归

说明：本轮只验证 Dennis Agent 能否把历史风控问题稳定转成 `query_intent_schema_v2`。不调用真实 Data Agent，不生成 mock response，不编造真实表名、字段名、SQL 或 API。

## Case 1：AC-003 单纯协议判定，前端无日志

### 1. 用户问题

一批关键接口服务端有请求，但前端无日志，怀疑是单纯协议攻击，能否判断？

### 2. 应触发 Skill

- 主控：`protocol_attack_expert_skill`
- 辅助：`cracked_app_expert_skill`、`evidence_decomposition_skill`

### 3. 目标证据

前后端链路一致性、接口序列固化、token/device/ip/ua 一致性、SDK/包采集反证、合法工具反证。

### 4. query_intent_schema_v2

```yaml
query_intent:
  intent_id: "AC-003_protocol_frontend_missing_v2_001"
  intent_type: "protocol_frontend_backend_join"
  risk_question: "前端无日志的关键接口请求是否属于脱端协议攻击"
  target_evidence: "前后端链路一致性 + 接口序列固化 + 环境一致性"
  applicable_skill:
    primary: "protocol_attack_expert_skill"
    auxiliary: ["cracked_app_expert_skill", "evidence_decomposition_skill"]
  minimum_inputs:
    required: ["user_id 或 device_id", "api_name 或业务动作", "time_window"]
    optional: ["app_version", "sdk_status", "授权工具语义"]
    missing: ["风险请求集合口径", "前端事件口径", "官方版本对照口径"]
  data_source_plan:
    required_data_domains: ["前端行为域", "后端数据域", "设备信息域", "策略引擎域"]
    optional_data_domains: ["风险画像域"]
    field_types_needed:
      identity_and_account: ["user_id", "account_id"]
      device_and_network: ["device_id", "realtime_fingerprint", "async_sdk_signal", "ip", "ua", "app_version", "sdk_status"]
      session_and_chain: ["frontend_event", "backend_api", "event_time", "request_time", "api_sequence", "gateway_decision"]
      activity_and_channel: []
      risk_and_strategy: ["strategy_hit", "engine_decision"]
      relation_network: []
    join_paths_needed: ["frontend_backend_chain_join", "request_device_environment_join", "strategy_gateway_decision_join"]
  query_dimensions:
    entities: ["用户", "账号", "设备", "请求", "前端事件", "token"]
    group_by: ["接口动作", "客户端版本", "SDK状态", "链路完整性", "接口序列模板"]
    compare_with: ["正常端链路", "官方版本", "授权工具调用"]
    joins: ["前端行为与后端请求", "请求与设备环境", "请求与策略/网关决策"]
  time_window:
    baseline: "待补充历史正常窗口"
    observation: "待补充异常请求窗口"
    granularity: "小时"
    freshness_expectation: "准实时或 T+1，待平台判断"
  expected_outputs:
    metric_outputs: ["端链路覆盖摘要", "无前端事件请求占比", "接口序列重复摘要", "环境冲突摘要"]
    evidence_outputs: ["链路冲突证据", "接口直达嫌疑", "SDK/官方版本/授权工具反证"]
    quality_outputs: ["前端日志覆盖状态", "SDK覆盖状态", "join口径说明", "权限状态"]
  interpretation_notes:
    strong_evidence_if: ["无端链路、接口直达、序列固化、环境冲突同时成立，并排除采集和授权反证"]
    medium_evidence_if: ["链路冲突和接口模板化成立，但环境或包证据不完整"]
    weak_signal_if: ["只有前端无日志或高频请求"]
    counter_evidence_if: ["官方版本同样缺日志、SDK采集问题、授权工具调用可解释"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["接口序列固化", "token/device/ip/ua 一致性异常", "SDK/包反证排除"]
    cannot_conclude_if: ["仅前端无日志", "官方版本或埋点问题可解释", "授权接口化调用可解释"]
  quality_checks:
    required: ["前端日志延迟/丢点检查", "后端与前端 join 口径检查", "SDK/指纹时效检查", "官方版本对照"]
    downgrade_if: ["partial / failed / no_permission", "关键反证未返回", "样本量、时间窗口、join口径不清"]
  permission_boundary: "中高敏；由未来 Data Agent / 内部平台判断权限"
  manual_review_required: true
  safety_boundary:
    false_positive_risks: ["埋点缺失", "破解包绕采集", "官方工具", "合法接口化运营"]
    prohibited_actions: ["不得仅凭前端无日志直接定协议", "不得直接强拦截"]
  next_query_intent_when_insufficient:
    intent_type: "sdk_bypass_or_cracked_app_check"
    target_evidence: "SDK日志覆盖与客户端包异常"
    reason: "排查破解包、SDK缺失、官方版本采集问题"
```

### 5. 为什么选择这些数据域

协议判断需要同时看端链路、服务端请求、设备/SDK 环境和网关/策略决策；单独后端请求或前端缺失都不足以定性。

### 6. 为什么选择这些 join path

`frontend_backend_chain_join` 还原端到服务端链路；`request_device_environment_join` 验证请求环境；`strategy_gateway_decision_join` 补网关和风控处置上下文。

### 7. 哪些质量风险会导致降级

前端日志延迟、埋点缺失、SDK 缺失、官方版本口径、join 失败、授权工具未排除。

### 8. 当前 query_intent 是否足够发给未来 dataagent adapter

基本足够。

### 9. 如果不够，还缺什么输入

缺风险请求集合口径、前端事件口径、官方版本对照和授权工具排除口径。

## Case 2：AC-004 群控真机爬取

### 1. 用户问题

一批真机设备疑似统一调度访问核心内容资产，是否群控真机爬取？

### 2. 应触发 Skill

- 主控：`anti_crawler_expert_skill`
- 辅助：`group_control_expert_skill`、`risk_chain_reconstruction_skill`

### 3. 目标证据

设备团组、同批启停、行为路径相似、资产访问集中、合法矩阵/热点/测试反证。

### 4. query_intent_schema_v2

```yaml
query_intent:
  intent_id: "AC-004_group_control_crawler_v2_001"
  intent_type: "anti_crawler_asset_leakage_check"
  risk_question: "真机设备是否被统一调度批量访问核心资产"
  target_evidence: "设备团组 + 同批调度 + 资产访问链路"
  applicable_skill:
    primary: "anti_crawler_expert_skill"
    auxiliary: ["group_control_expert_skill", "risk_chain_reconstruction_skill"]
  minimum_inputs:
    required: ["device_id 或账号集合", "资产类型或页面语义", "time_window"]
    optional: ["业务活动日历", "授权矩阵语义", "外部复用线索"]
    missing: ["核心资产定义", "异常设备/账号集合", "合法运营排除口径"]
  data_source_plan:
    required_data_domains: ["前端行为域", "后端数据域", "设备信息域", "关联网络域", "风险画像域"]
    optional_data_domains: ["策略引擎域"]
    field_types_needed:
      identity_and_account: ["user_id", "account_id"]
      device_and_network: ["device_id", "device_profile", "realtime_fingerprint", "ip", "ua"]
      session_and_chain: ["frontend_event", "backend_api", "page_path", "click_sequence", "api_sequence", "request_time"]
      activity_and_channel: []
      risk_and_strategy: ["risk_label", "strategy_hit"]
      relation_network: ["relation_group_id", "strong_device_relation", "user_group_id", "relation_strength"]
    join_paths_needed: ["asset_access_device_network_join", "frontend_backend_chain_join", "batch_case_business_context_join"]
  query_dimensions:
    entities: ["设备", "账号", "IP", "资产", "页面", "接口", "团组"]
    group_by: ["设备团组", "账号团组", "分钟级启动窗口", "访问路径模板", "资产类型"]
    compare_with: ["正常资产访问", "自然热点窗口", "合法运营矩阵", "测试流量"]
    joins: ["资产访问与设备网络", "前端行为与后端请求", "业务上下文反证"]
  time_window:
    baseline: "待补充历史正常资产访问窗口"
    observation: "待补充异常访问窗口"
    granularity: "分钟或小时"
    freshness_expectation: "准实时 + T+1，待平台判断"
  expected_outputs:
    metric_outputs: ["设备/账号团组摘要", "同批启停同步摘要", "资产访问集中度", "路径模板摘要"]
    evidence_outputs: ["统一调度证据", "资产访问链路", "合法矩阵/热点/测试反证"]
    quality_outputs: ["设备画像更新时间", "前后端覆盖状态", "业务日历对照状态"]
  interpretation_notes:
    strong_evidence_if: ["真机团组、同批调度、路径模板、资产集中和反证排除同时成立"]
    medium_evidence_if: ["设备团组和路径相似明显，但合法矩阵或业务反证未完整返回"]
    weak_signal_if: ["只有高频访问或设备聚集"]
    counter_evidence_if: ["热点事件、合法运营、测试流量、企业网络可解释"]
  conclusion_threshold:
    sufficient_for: "明确判断"
    must_combine_with: ["设备团组", "同批启停", "路径相似", "资产访问链路", "反证排除"]
    cannot_conclude_if: ["只有设备聚集", "合法矩阵或热点可解释"]
  quality_checks:
    required: ["设备画像更新时间检查", "前端/后端链路覆盖检查", "业务活动/热点/测试流量排除"]
    downgrade_if: ["partial / failed / no_permission", "合法矩阵未排除", "资产定义不清"]
  permission_boundary: "中高敏到高敏；由未来 Data Agent / 内部平台判断权限"
  manual_review_required: true
  safety_boundary:
    false_positive_risks: ["热点流量", "合法矩阵", "企业网络", "测试流量"]
    prohibited_actions: ["不得仅凭设备聚集打群控", "不得未排白名单强封"]
  next_query_intent_when_insufficient:
    intent_type: "legal_operation_matrix_check"
    target_evidence: "合法矩阵/授权工具反证"
    reason: "排除商家、达人、机构或内部工具批量访问"
```

### 5-9. 说明

- 数据域选择：资产访问需前端/后端，真机调度需设备和关联网络，风险画像用于分层。
- join path 选择：资产访问链路是主链路，前后端链路排协议/埋点问题，业务上下文排热点/合法运营。
- 降级风险：设备画像延迟、热点活动、企业网络、合法矩阵未排除。
- 是否足够：基本足够。
- 缺输入：核心资产定义、异常对象集合、业务活动/测试/授权排除口径。

## Case 3：AC-001 外网跟价但内部无明显攻击

### 1. 用户问题

外网出现跟价，但内部没有明显接口异常，是否内部接口被爬？

### 2. 应触发 Skill

- 主控：`anti_crawler_expert_skill`
- 辅助：`risk_chain_reconstruction_skill`、`evidence_decomposition_skill`

### 3. 目标证据

资产访问路径、内部访问异常、外部泄漏时间对齐、缓存/前端/合作方/内部导出/真人访问反证。

### 4. query_intent_schema_v2

```yaml
query_intent:
  intent_id: "AC-001_external_price_sync_v2_001"
  intent_type: "anti_crawler_asset_leakage_check"
  risk_question: "外网跟价是否由内部价格资产被批量获取导致"
  target_evidence: "资产访问链路 + 内外部时间对齐 + 多路径反证"
  applicable_skill:
    primary: "anti_crawler_expert_skill"
    auxiliary: ["risk_chain_reconstruction_skill", "evidence_decomposition_skill"]
  minimum_inputs:
    required: ["资产类型", "外网跟价时间线", "内部价格变更窗口"]
    optional: ["合作方同步窗口", "缓存/CDN变更语义", "前端公开入口语义"]
    missing: ["外部样本时间线", "内部价格变更口径", "合作方/缓存/内部导出反证口径"]
  data_source_plan:
    required_data_domains: ["前端行为域", "后端数据域", "设备信息域", "关联网络域"]
    optional_data_domains: ["风险画像域", "策略引擎域"]
    field_types_needed:
      identity_and_account: ["user_id", "account_id"]
      device_and_network: ["device_id", "ip", "ua", "realtime_fingerprint", "device_profile"]
      session_and_chain: ["frontend_event", "backend_api", "page_path", "request_time", "api_sequence", "gateway_decision"]
      activity_and_channel: []
      risk_and_strategy: ["risk_label", "strategy_hit"]
      relation_network: ["relation_group_id", "strong_device_relation"]
    join_paths_needed: ["asset_access_device_network_join", "frontend_backend_chain_join", "batch_case_business_context_join"]
  query_dimensions:
    entities: ["资产", "接口", "页面", "账号", "设备", "IP", "外部样本"]
    group_by: ["资产类型", "访问入口", "访问主体", "时间差", "设备/IP聚集"]
    compare_with: ["正常资产访问", "外部跟价时间", "合作方同步", "缓存/前端公开路径", "内部导出窗口"]
    joins: ["资产访问与设备网络", "前端与后端链路", "业务上下文反证"]
  time_window:
    baseline: "待补充正常价格访问窗口"
    observation: "待补充跟价前后窗口"
    granularity: "分钟或小时"
    freshness_expectation: "T+1 或长周期后验，待平台判断"
  expected_outputs:
    metric_outputs: ["资产访问量趋势", "主体聚集摘要", "内外部时间差摘要"]
    evidence_outputs: ["疑似内部访问链路", "外部复用时间对齐", "缓存/合作方/内部导出/真人访问反证"]
    quality_outputs: ["外部样本时间可信度", "资产访问口径", "join覆盖状态"]
  interpretation_notes:
    strong_evidence_if: ["内部异常访问与外部跟价时间差稳定，且访问主体聚集并排除其他路径"]
    medium_evidence_if: ["外部跟价明显且内部访问有波动，但入口或主体未闭合"]
    weak_signal_if: ["只有外网跟价截图或单点样本"]
    counter_evidence_if: ["缓存、前端公开、合作方同步、内部导出、真人访问可解释"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["内部资产访问异常", "外部时间对齐", "主体聚集", "多路径反证排除"]
    cannot_conclude_if: ["内部无访问异常", "外部样本时间不可信", "合作方/缓存路径可解释"]
  quality_checks:
    required: ["外部样本时间可信度检查", "资产访问口径检查", "缓存/合作方/内部导出反证检查"]
    downgrade_if: ["只有外网样本", "内部接口无异常", "反证未返回"]
  permission_boundary: "中高敏；由未来 Data Agent / 内部平台判断权限"
  manual_review_required: true
  safety_boundary:
    false_positive_risks: ["缓存/CDN", "前端公开", "合作方同步", "内部导出", "真人访问"]
    prohibited_actions: ["不得仅凭外网跟价定内部接口被爬"]
  next_query_intent_when_insufficient:
    intent_type: "batch_case_commonality_check"
    target_evidence: "多个跟价样本的时间差与入口共性"
    reason: "单样本不足，需批量样本验证稳定时间差和入口复用"
```

### 5-9. 说明

- 数据域选择：外网跟价需资产访问和主体聚集，反证依赖业务上下文。
- join path：资产访问主链路 + 前后端链路 + 业务上下文反证。
- 降级风险：外部时间线不准、缓存/合作方可解释、内部无异常。
- 是否足够：中等，依赖外部样本时间线。
- 缺输入：外部样本、价格变更窗口、合作方/缓存/导出口径。

## Case 4：AS-001 token 泄露 / 登录态复用

### 1. 用户问题

账号出现登录态跨环境使用和敏感动作，怀疑 token 泄露或登录态复用。

### 2. 应触发 Skill

- 主控：`account_security_expert_skill`
- 辅助：`protocol_attack_expert_skill`、`evidence_decomposition_skill`

### 3. 目标证据

token 与设备/IP/UA 一致性、登录迁移/验证链路、敏感动作、正常换机/漫游/企业网络反证。

### 4. query_intent_schema_v2

```yaml
query_intent:
  intent_id: "AS-001_token_reuse_v2_001"
  intent_type: "token_reuse_or_account_takeover_check"
  risk_question: "账号异常是否由 token 泄露或登录态复用导致"
  target_evidence: "token/session 环境一致性 + 账号生命周期 + 敏感动作"
  applicable_skill:
    primary: "account_security_expert_skill"
    auxiliary: ["protocol_attack_expert_skill", "evidence_decomposition_skill"]
  minimum_inputs:
    required: ["user_id 或 account_id", "token_id 或登录态语义", "time_window", "敏感动作语义"]
    optional: ["可信设备确认口径", "验证链路语义", "企业网络/漫游口径"]
    missing: ["token集合", "敏感动作窗口", "可信设备/用户确认口径"]
  data_source_plan:
    required_data_domains: ["用户信息域", "设备信息域", "后端数据域", "风险画像域", "策略引擎域"]
    optional_data_domains: ["前端行为域"]
    field_types_needed:
      identity_and_account: ["user_id", "account_id", "login_time", "bind_change_time", "password_change_time", "account_recovery_time", "account_status"]
      device_and_network: ["device_id", "ip", "ua", "realtime_fingerprint", "device_profile", "app_version"]
      session_and_chain: ["token_id", "session_id", "backend_api", "request_time", "gateway_decision"]
      activity_and_channel: []
      risk_and_strategy: ["risk_label", "risk_score", "strategy_hit", "engine_decision", "disposal_action"]
      relation_network: ["strong_device_relation"]
    join_paths_needed: ["token_session_environment_join", "account_lifecycle_device_join", "strategy_decision_outcome_join"]
  query_dimensions:
    entities: ["账号", "用户", "token", "session", "设备", "IP", "UA", "敏感动作"]
    group_by: ["环境冲突类型", "登录迁移状态", "验证状态", "敏感动作类型", "风险画像"]
    compare_with: ["历史登录环境", "可信设备", "正常换机", "企业网络/漫游"]
    joins: ["token/session与设备环境", "账号生命周期与设备", "策略决策与后续动作"]
  time_window:
    baseline: "待补充历史正常登录窗口"
    observation: "待补充异常动作窗口"
    granularity: "小时或天"
    freshness_expectation: "准实时 + T+1，待平台判断"
  expected_outputs:
    metric_outputs: ["token跨环境使用摘要", "登录环境突变摘要", "敏感动作后置链路"]
    evidence_outputs: ["无迁移/无验证证据", "账号控制权变化证据", "正常场景反证"]
    quality_outputs: ["token生命周期口径", "验证链路覆盖", "策略命中解释"]
  interpretation_notes:
    strong_evidence_if: ["token新环境使用、无迁移验证、敏感动作和正常场景排除同时成立"]
    medium_evidence_if: ["环境突变和敏感动作相关，但验证链路或反证不完整"]
    weak_signal_if: ["只有异地IP或UA变化"]
    counter_evidence_if: ["正常换机、可信设备确认、企业网络、漫游、多设备登录可解释"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["新环境token使用", "无登录迁移/验证", "敏感动作", "正常场景排除"]
    cannot_conclude_if: ["只有IP/UA变化", "可信设备或正常换机可解释"]
  quality_checks:
    required: ["token生命周期口径检查", "登录迁移/验证链路检查", "正常换机/漫游/企业网络反证检查"]
    downgrade_if: ["验证链路缺失", "反证未返回", "时间窗口不清"]
  permission_boundary: "高敏；由未来 Data Agent / 内部平台判断权限"
  manual_review_required: true
  safety_boundary:
    false_positive_risks: ["正常换机", "漫游", "企业网络", "多设备登录", "SDK升级"]
    prohibited_actions: ["不得仅凭IP/UA变化冻结账号"]
  next_query_intent_when_insufficient:
    intent_type: "strategy_effect_and_false_positive_review"
    target_evidence: "step-up验证和敏感动作处置后的误伤/效果"
    reason: "账号安全治理高误伤，需要后验复盘"
```

### 5-9. 说明

- 数据域选择：token 泄露核心在用户生命周期、设备环境、后端请求、风险画像和策略处置。
- join path：token 环境、账号生命周期、策略效果三条链路必须闭合。
- 降级风险：正常换机、漫游、多设备登录、可信设备确认缺失。
- 是否足够：基本足够。
- 缺输入：token 集合、敏感动作定义、验证链路口径。

## Case 5：ACT-003 渠道抢量 / 归因劫持

### 1. 用户问题

某渠道转化上涨且 CTIT 异常，怀疑点击注入或归因抢量。

### 2. 应触发 Skill

- 主控：`traffic_anti_cheating_expert_skill`
- 辅助：`risk_chain_reconstruction_skill`、`evidence_decomposition_skill`

### 3. 目标证据

曝光-点击-激活链路、CTIT、自然量跷跷板、新客真实性、后验质量、设备/IP/UA 或点击模板、预算/活动/版本/归因规则反证。

### 4. query_intent_schema_v2

```yaml
query_intent:
  intent_id: "ACT-003_channel_hijack_v2_001"
  intent_type: "channel_attribution_hijacking_check"
  risk_question: "目标渠道是否存在点击注入或归因抢量"
  target_evidence: "CTIT / 渠道归因 + 自然量跷跷板 + 后验质量 + 业务变更反证"
  applicable_skill:
    primary: "traffic_anti_cheating_expert_skill"
    auxiliary: ["risk_chain_reconstruction_skill", "evidence_decomposition_skill"]
  minimum_inputs:
    required: ["channel_id 或 media_source", "time_window", "归因口径", "转化动作语义"]
    optional: ["campaign_id", "预算调整语义", "活动排期语义", "版本发布语义", "归因规则变更语义"]
    missing: ["目标渠道集合", "归因规则变更窗口", "自然量对照口径"]
  data_source_plan:
    required_data_domains: ["渠道信息域", "用户信息域", "设备信息域", "活动信息域"]
    optional_data_domains: ["风险画像域", "策略引擎域"]
    field_types_needed:
      identity_and_account: ["user_id", "account_id", "account_age", "register_time"]
      device_and_network: ["device_id", "ip", "ua", "device_profile"]
      session_and_chain: []
      activity_and_channel: ["campaign_id", "exposure_time", "click_time", "activation_time", "channel_id", "media_source", "attribution_type", "ctit", "return_user_flag"]
      risk_and_strategy: ["risk_label"]
      relation_network: []
    join_paths_needed: ["channel_click_activation_user_join", "channel_quality_aftereffect_join", "batch_case_business_context_join"]
  query_dimensions:
    entities: ["渠道", "点击", "激活", "新客", "设备", "活动", "媒体"]
    group_by: ["渠道", "媒体来源", "CTIT时间桶", "自然/付费来源", "设备分群", "新客质量"]
    compare_with: ["历史渠道基线", "自然量", "其他渠道", "预算/活动/版本/归因规则窗口"]
    joins: ["渠道点击激活与用户设备", "渠道后验质量", "业务上下文反证"]
  time_window:
    baseline: "待补充历史投放窗口"
    observation: "待补充异常归因窗口"
    granularity: "小时或天"
    freshness_expectation: "T+1 或长周期后验，待平台判断"
  expected_outputs:
    metric_outputs: ["CTIT分布", "渠道份额变化", "自然量变化", "后验质量摘要", "新客真实性摘要"]
    evidence_outputs: ["点击注入/抢量嫌疑", "设备/IP/UA或点击模板线索", "业务变更反证"]
    quality_outputs: ["归因口径状态", "预算/活动/版本变更覆盖", "后验窗口覆盖"]
  interpretation_notes:
    strong_evidence_if: ["CTIT异常、自然量跷跷板、后验质量差、点击/设备异常同时成立，并排除业务变更"]
    medium_evidence_if: ["CTIT和自然量结构异常，但点击/设备或后验证据不完整"]
    weak_signal_if: ["只有渠道上涨或CTIT偏移"]
    counter_evidence_if: ["预算、活动、版本、归因规则或媒体策略变化可解释"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["CTIT异常", "自然量跷跷板", "后验质量异常", "点击/设备异常", "业务变更排除"]
    cannot_conclude_if: ["只有CTIT异常", "业务变更可解释", "后验质量无异常"]
  quality_checks:
    required: ["预算变化检查", "归因窗口检查", "活动/版本/媒体策略检查", "后验窗口检查"]
    downgrade_if: ["点击链路权限不足", "业务变更未返回", "后验窗口不足"]
  permission_boundary: "中敏；渠道结算相关需人工确认"
  manual_review_required: true
  safety_boundary:
    false_positive_risks: ["预算调整", "归因规则变化", "品牌活动", "版本发布", "媒体策略变化"]
    prohibited_actions: ["不得仅凭CTIT异常拒付或扣减结算"]
  next_query_intent_when_insufficient:
    intent_type: "strategy_effect_and_false_positive_review"
    target_evidence: "分渠道治理后的结算影响与误伤复盘"
    reason: "渠道治理涉及结算，需要后验复盘"
```

### 5-9. 说明

- 数据域选择：渠道链路、用户新客、设备历史、活动/预算反证缺一不可。
- join path：渠道点击激活是主链路，后验质量和业务上下文用于反证。
- 降级风险：归因规则变化、预算活动、后验窗口短、点击模板缺失。
- 是否足够：基本足够。
- 缺输入：目标渠道、归因口径、预算/活动/版本变更。

## Case 6：MIX-001 直播间截流 / 站外添加

### 1. 用户问题

直播间用户被站外添加，怀疑存在截流或私信导流。

### 2. 应触发 Skill

- 主控：`traffic_diversion_interception_skill`
- 辅助：`anti_crawler_expert_skill`、`evidence_decomposition_skill`

### 3. 目标证据

信息暴露入口、搜索/关注/私信触达、站外承接、触达账号矩阵、正常社交/授权运营反证。

### 4. query_intent_schema_v2

```yaml
query_intent:
  intent_id: "MIX-001_live_diversion_v2_001"
  intent_type: "traffic_diversion_chain_check"
  risk_question: "直播间用户被站外添加是否属于导流截流链路"
  target_evidence: "信息暴露入口 + 搜索/关注/私信触达 + 站外承接"
  applicable_skill:
    primary: "traffic_diversion_interception_skill"
    auxiliary: ["anti_crawler_expert_skill", "evidence_decomposition_skill"]
  minimum_inputs:
    required: ["直播间或场景语义", "目标用户集合", "time_window", "站外添加线索"]
    optional: ["触达账号集合", "内容样本", "投诉/举报线索", "授权运营口径"]
    missing: ["目标用户集合", "触达账号集合", "站外承接样本"]
  data_source_plan:
    required_data_domains: ["前端行为域", "用户信息域", "关联网络域", "风险画像域", "后端数据域"]
    optional_data_domains: ["策略引擎域"]
    field_types_needed:
      identity_and_account: ["user_id", "account_id", "account_status"]
      device_and_network: ["device_id", "ip", "ua"]
      session_and_chain: ["frontend_event", "page_path", "click_sequence", "backend_api", "request_time"]
      activity_and_channel: []
      risk_and_strategy: ["risk_label", "risk_score", "strategy_hit"]
      relation_network: ["relation_group_id", "user_group_id", "relation_edge_type", "relation_strength"]
    join_paths_needed: ["diversion_exposure_touch_offsite_join", "risk_profile_behavior_outcome_join"]
  query_dimensions:
    entities: ["直播间", "目标用户", "触达账号", "搜索", "关注", "私信", "站外承接线索"]
    group_by: ["信息暴露入口", "目标获取路径", "触达方式", "账号矩阵", "承接方式"]
    compare_with: ["正常社交", "普通关注", "授权客服/达人运营", "用户主动外联"]
    joins: ["目标暴露到触达链路", "风险画像与行为结果"]
  time_window:
    baseline: "待补充历史正常互动窗口"
    observation: "待补充异常触达窗口"
    granularity: "小时或天"
    freshness_expectation: "T+1 或长周期后验，待平台判断"
  expected_outputs:
    metric_outputs: ["入口分布", "搜索/关注/私信转化摘要", "账号矩阵摘要", "投诉/举报摘要"]
    evidence_outputs: ["目标获取链路", "触达链路", "站外承接线索", "正常社交/授权触达反证"]
    quality_outputs: ["内容样本覆盖", "投诉样本覆盖", "授权触达覆盖"]
  interpretation_notes:
    strong_evidence_if: ["目标获取、触达、站外承接、账号矩阵闭合，并排除正常社交/授权触达"]
    medium_evidence_if: ["批量触达明显，但站外承接或投诉证据不足"]
    weak_signal_if: ["只有私信/关注异常"]
    counter_evidence_if: ["正常社交、用户主动外联、授权运营可解释"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["信息暴露入口", "触达链路", "站外承接", "账号矩阵"]
    cannot_conclude_if: ["无站外承接证据", "正常社交或授权运营可解释"]
  quality_checks:
    required: ["站外承接样本覆盖检查", "授权运营触达反证检查", "正常社交基线检查"]
    downgrade_if: ["站外承接缺失", "触达账号集合不清", "投诉样本不足"]
  permission_boundary: "高敏；涉及私信/关系网络，由未来 Data Agent / 内部平台判断权限"
  manual_review_required: true
  safety_boundary:
    false_positive_risks: ["正常社交", "普通关注", "用户主动外联", "授权客服/达人运营"]
    prohibited_actions: ["不得无站外承接证据直接定导流黑产"]
  next_query_intent_when_insufficient:
    intent_type: "legal_operation_matrix_check"
    target_evidence: "授权触达 / 合法运营反证"
    reason: "排除客服、达人、MCN、商家授权触达"
```

### 5-9. 说明

- 数据域选择：导流链路需要前端触达、用户关系、账号矩阵和风险画像；后端只在涉及接口时辅助。
- join path：`diversion_exposure_touch_offsite_join` 是主链路。
- 降级风险：无站外承接、正常社交、授权运营、用户主动外联。
- 是否足够：中等，取决于站外承接和触达账号输入。
- 缺输入：目标用户、触达账号、内容/投诉样本。

## Case 7：ADV-003 真实用户同任务且设备离散

### 1. 用户问题

大量真实用户完成相同任务，设备离散，是否群控？

### 2. 应触发 Skill

- 主控：`real_user_crowdsourcing_skill`
- 辅助：`activity_anti_cheating_expert_skill`、`group_control_expert_skill`

### 3. 目标证据

任务化完成、任务窗口、奖励/提现、后验质量、设备离散、任务平台/教程话术线索、自然传播反证。

### 4. query_intent_schema_v2

```yaml
query_intent:
  intent_id: "ADV-003_real_user_task_v2_001"
  intent_type: "activity_black_industry_or_low_quality_check"
  risk_question: "设备离散但目标一致的真实用户行为是否属于真人众包或活动低质"
  target_evidence: "任务化完成 + 奖励/提现 + 后验质量 + 设备离散"
  applicable_skill:
    primary: "real_user_crowdsourcing_skill"
    auxiliary: ["activity_anti_cheating_expert_skill", "group_control_expert_skill"]
  minimum_inputs:
    required: ["活动/任务语义", "用户集合", "time_window", "任务完成动作"]
    optional: ["奖励动作语义", "提现口径", "外部任务平台线索", "自然传播口径"]
    missing: ["任务平台/教程线索", "奖励/提现口径", "自然用户对照"]
  data_source_plan:
    required_data_domains: ["活动信息域", "用户信息域", "设备信息域", "前端行为域", "风险画像域", "关联网络域"]
    optional_data_domains: ["策略引擎域"]
    field_types_needed:
      identity_and_account: ["user_id", "account_id", "account_age", "register_time"]
      device_and_network: ["device_id", "device_profile", "ip", "ua"]
      session_and_chain: ["frontend_event", "page_path", "click_sequence", "event_time"]
      activity_and_channel: ["campaign_id", "activity_participation", "reward_status", "withdraw_status", "return_user_flag"]
      risk_and_strategy: ["risk_label", "risk_score", "strategy_hit"]
      relation_network: ["user_group_id", "relation_edge_type", "relation_strength"]
    join_paths_needed: ["activity_participation_device_reward_join", "risk_profile_behavior_outcome_join", "invite_relation_network_join"]
  query_dimensions:
    entities: ["用户", "账号", "设备", "活动任务", "奖励", "提现", "邀请关系"]
    group_by: ["任务完成窗口", "设备离散度", "行为路径模板", "奖励/提现状态", "后验质量"]
    compare_with: ["自然用户", "活动规则", "达人传播", "正常任务路径"]
    joins: ["活动参与与设备奖励", "画像与行为后验", "邀请/关系网络"]
  time_window:
    baseline: "待补充自然用户对照窗口"
    observation: "待补充任务完成窗口"
    granularity: "小时或天"
    freshness_expectation: "T+1 + 长周期后验，待平台判断"
  expected_outputs:
    metric_outputs: ["任务窗口集中度", "设备离散度", "路径相似度", "奖励/提现聚集", "后验质量"]
    evidence_outputs: ["真人众包嫌疑", "活动低质证据", "群控反证/支持证据", "自然传播反证"]
    quality_outputs: ["后验窗口覆盖", "奖励/提现覆盖", "自然对照覆盖"]
  interpretation_notes:
    strong_evidence_if: ["行为真实、目标任务化、任务窗口集中、收益聚集、任务平台/教程线索闭合"]
    medium_evidence_if: ["目标一致和后验质量差明显，但收益链或任务平台证据不足"]
    weak_signal_if: ["只有设备离散和任务一致"]
    counter_evidence_if: ["自然传播、活动规则、达人运营可解释"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["任务窗口集中", "奖励/提现聚集", "后验质量", "自然传播反证排除"]
    cannot_conclude_if: ["只有目标一致", "只有低质", "活动规则可解释"]
  quality_checks:
    required: ["活动规则检查", "后验窗口检查", "奖励/提现口径检查", "自然传播反证检查"]
    downgrade_if: ["无收益链", "无任务平台线索", "自然对照缺失"]
  permission_boundary: "中高敏；由未来 Data Agent / 内部平台判断权限"
  manual_review_required: true
  safety_boundary:
    false_positive_risks: ["真实用户参与", "自然传播", "活动规则引导", "达人运营"]
    prohibited_actions: ["不得因设备离散直接判自然用户", "不得因目标一致直接判群控"]
  next_query_intent_when_insufficient:
    intent_type: "batch_case_commonality_check"
    target_evidence: "任务窗口、收益主体、教程线索的批量共性"
    reason: "真人众包常需批量共性和收益链补证"
```

### 5-9. 说明

- 数据域选择：活动、用户、设备、前端行为、画像、网络用于区分众包/群控/自然用户。
- join path：活动奖励主链路，画像后验解释质量，邀请网络看组织化。
- 降级风险：没有收益链、没有任务平台线索、活动规则可解释。
- 是否足够：中等。
- 缺输入：任务平台/教程线索、奖励提现口径、自然对照。

## Case 8：ADV-008 直播间用户被站外添加但无爬虫证据

### 1. 用户问题

直播间用户被站外添加，但没有爬虫证据，应如何取证？

### 2. 应触发 Skill

- 主控：`traffic_diversion_interception_skill`
- 辅助：`evidence_decomposition_skill`

### 3. 目标证据

目标信息暴露入口、搜索/关注/私信触达、站外承接、正常社交/授权运营反证；不默认查反爬强结论。

### 4. query_intent_schema_v2

```yaml
query_intent:
  intent_id: "ADV-008_live_offsite_no_crawler_v2_001"
  intent_type: "traffic_diversion_chain_check"
  risk_question: "无爬虫证据时，直播间用户被站外添加是否属于导流截流链路"
  target_evidence: "目标信息暴露入口 + 触达链路 + 站外承接反证"
  applicable_skill:
    primary: "traffic_diversion_interception_skill"
    auxiliary: ["evidence_decomposition_skill"]
  minimum_inputs:
    required: ["直播间/场景语义", "被站外添加用户集合", "time_window"]
    optional: ["触达账号集合", "站外添加线索", "私信/关注/搜索行为语义", "投诉/举报"]
    missing: ["触达账号集合", "站外承接线索", "正常社交/授权运营口径"]
  data_source_plan:
    required_data_domains: ["前端行为域", "用户信息域", "关联网络域", "风险画像域"]
    optional_data_domains: ["后端数据域", "策略引擎域"]
    field_types_needed:
      identity_and_account: ["user_id", "account_id", "account_status"]
      device_and_network: ["device_id", "ip", "ua"]
      session_and_chain: ["frontend_event", "page_path", "click_sequence", "event_time"]
      activity_and_channel: []
      risk_and_strategy: ["risk_label", "strategy_hit"]
      relation_network: ["relation_group_id", "user_group_id", "relation_edge_type", "relation_strength"]
    join_paths_needed: ["diversion_exposure_touch_offsite_join", "risk_profile_behavior_outcome_join"]
  query_dimensions:
    entities: ["直播间", "目标用户", "触达账号", "搜索", "关注", "私信", "站外线索"]
    group_by: ["信息暴露入口", "触达方式", "账号矩阵", "承接方式"]
    compare_with: ["正常社交", "普通关注", "用户主动外联", "授权运营触达"]
    joins: ["目标暴露到触达链路", "风险画像与行为后验"]
  time_window:
    baseline: "待补充正常直播互动窗口"
    observation: "待补充站外添加窗口"
    granularity: "小时或天"
    freshness_expectation: "T+1 或长周期后验，待平台判断"
  expected_outputs:
    metric_outputs: ["暴露入口分布", "触达链路摘要", "账号矩阵摘要"]
    evidence_outputs: ["导流链路证据", "站外承接线索", "正常社交/授权触达反证"]
    quality_outputs: ["私信/关注/搜索覆盖", "投诉/站外样本覆盖"]
  interpretation_notes:
    strong_evidence_if: ["目标获取、触达、站外承接、账号矩阵闭合"]
    medium_evidence_if: ["批量触达明显但站外承接不足"]
    weak_signal_if: ["只有站外添加反馈或单次关注/私信"]
    counter_evidence_if: ["正常社交、用户主动外联、授权运营可解释"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["信息暴露入口", "触达链路", "站外承接"]
    cannot_conclude_if: ["无站外承接", "正常社交可解释", "只有用户反馈"]
  quality_checks:
    required: ["站外样本覆盖检查", "正常社交基线检查", "授权运营反证检查"]
    downgrade_if: ["无触达账号", "无承接线索", "投诉样本不足"]
  permission_boundary: "高敏；由未来 Data Agent / 内部平台判断权限"
  manual_review_required: true
  safety_boundary:
    false_positive_risks: ["正常社交", "普通关注", "用户主动外联", "授权运营"]
    prohibited_actions: ["不得无爬虫证据转反爬强结论", "不得无承接证据定导流黑产"]
  next_query_intent_when_insufficient:
    intent_type: "legal_operation_matrix_check"
    target_evidence: "授权触达反证"
    reason: "先排除客服、主播、达人、MCN 合法触达"
```

### 5-9. 说明

- 数据域选择：核心是导流触达链路，不是反爬接口链路。
- join path：导流链路 join 足够，后端数据仅可选。
- 降级风险：无承接、无触达账号、正常社交。
- 是否足够：中等。
- 缺输入：触达账号、站外承接、投诉/举报样本。

## Case 9：合法矩阵 商家/达人/MCN 批量登录或接口化运营

### 1. 用户问题

商家/达人/MCN 批量登录或接口化运营，是否协议、群控或合法矩阵？

### 2. 应触发 Skill

- 主控：`legal_operation_matrix_playbook_v2_3`
- 辅助：`account_security_expert_skill`、`protocol_attack_expert_skill`、`group_control_expert_skill`

### 3. 目标证据

授权主体、账号范围、工具来源、操作人、接口范围、敏感动作、收益主体、历史违规、超范围动作。

### 4. query_intent_schema_v2

```yaml
query_intent:
  intent_id: "LEGAL-001_operation_matrix_v2_001"
  intent_type: "legal_operation_matrix_check"
  risk_question: "批量登录或接口化运营是否属于合法矩阵、超范围违规或黑产自动化"
  target_evidence: "授权主体 + 账号范围 + 工具来源 + 敏感动作 + 历史违规"
  applicable_skill:
    primary: "legal_operation_matrix_playbook_v2_3"
    auxiliary: ["account_security_expert_skill", "protocol_attack_expert_skill", "group_control_expert_skill"]
  minimum_inputs:
    required: ["主体或账号集合", "工具来源语义", "操作场景", "time_window"]
    optional: ["授权记录语义", "敏感动作语义", "收益主体语义", "历史违规语义"]
    missing: ["授权主体", "账号范围", "操作人", "工具来源"]
  data_source_plan:
    required_data_domains: ["用户信息域", "后端数据域", "策略引擎域", "关联网络域", "风险画像域"]
    optional_data_domains: ["前端行为域", "活动信息域"]
    field_types_needed:
      identity_and_account: ["user_id", "account_id", "login_time", "account_status"]
      device_and_network: ["device_id", "ip", "ua", "app_version"]
      session_and_chain: ["backend_api", "api_sequence", "request_time", "gateway_decision"]
      activity_and_channel: ["campaign_id", "withdraw_status"]
      risk_and_strategy: ["risk_label", "strategy_hit", "engine_decision", "disposal_action"]
      relation_network: ["relation_group_id", "relation_edge_type", "relation_strength"]
    join_paths_needed: ["strategy_decision_outcome_join", "batch_case_resource_reuse_join", "account_lifecycle_device_join"]
  query_dimensions:
    entities: ["主体", "账号", "工具", "操作人", "接口", "敏感动作", "收益主体"]
    group_by: ["授权主体", "账号范围", "工具来源", "调用接口", "敏感动作", "历史违规"]
    compare_with: ["授权范围", "合法矩阵", "超范围动作", "无授权工具"]
    joins: ["主体/账号/工具关系", "策略决策与处置", "账号生命周期与设备"]
  time_window:
    baseline: "待补充正常运营窗口"
    observation: "待补充批量运营窗口"
    granularity: "小时或天"
    freshness_expectation: "T+1，待平台判断"
  expected_outputs:
    metric_outputs: ["授权匹配摘要", "超范围动作摘要", "敏感动作分布", "历史违规摘要"]
    evidence_outputs: ["合法矩阵依据", "局部违规证据", "黑产/协议/群控转交证据"]
    quality_outputs: ["授权信息覆盖", "工具来源覆盖", "审计链路覆盖"]
  interpretation_notes:
    strong_evidence_if: ["授权主体、账号范围、工具来源和审计完整，或超范围动作可定位"]
    medium_evidence_if: ["存在业务合理性但授权/审计不完整"]
    weak_signal_if: ["只有批量登录或接口化调用"]
    counter_evidence_if: ["无授权、工具来源异常、规避平台规则、收益主体异常"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["授权主体", "账号范围", "工具来源", "操作审计", "敏感动作边界"]
    cannot_conclude_if: ["只有批量行为", "授权信息缺失", "收益主体不清"]
  quality_checks:
    required: ["授权范围检查", "工具来源检查", "敏感动作审计检查", "历史违规检查"]
    downgrade_if: ["授权主体缺失", "工具来源缺失", "操作人不可追溯"]
  permission_boundary: "高敏；由未来 Data Agent / 内部平台判断权限"
  manual_review_required: true
  safety_boundary:
    false_positive_risks: ["合法商家运营", "达人/MCN矩阵", "客服代管", "官方工具"]
    prohibited_actions: ["不得因批量行为直接判群控/协议", "不得因有授权放过导流/欺诈/支付风险"]
  next_query_intent_when_insufficient:
    intent_type: "protocol_frontend_backend_join"
    target_evidence: "无授权接口化调用是否脱端"
    reason: "若无授权且接口异常，再转协议证据链"
```

### 5-9. 说明

- 数据域选择：合法矩阵核心看用户/主体、接口、策略、关系和画像。
- join path：目前缺专门 legal matrix join path，只能复用资源、账号生命周期、策略结果。
- 降级风险：授权缺失、工具来源不清、操作人不可追溯。
- 是否足够：勉强足够。
- 缺输入：授权主体、账号范围、工具来源、操作人、收益主体。

## Case 10：策略复盘 某策略命中后评估误伤和效果

### 1. 用户问题

某风控策略上线后需要评估命中效果、误伤和是否回滚。

### 2. 应触发 Skill

- 主控：`risk_governance_design_skill`
- 辅助：`evidence_decomposition_skill`、`material_delivery_skill`

### 3. 目标证据

策略命中、处置结果、后验风险、业务指标影响、申诉/客诉、对照组/灰度组差异。

### 4. query_intent_schema_v2

```yaml
query_intent:
  intent_id: "STRATEGY-001_effect_false_positive_v2_001"
  intent_type: "strategy_effect_and_false_positive_review"
  risk_question: "策略命中后是否有效降低风险且误伤可控，是否需要扩大、回滚或调整"
  target_evidence: "策略命中 + 处置结果 + 后验风险 + 误伤/业务影响"
  applicable_skill:
    primary: "risk_governance_design_skill"
    auxiliary: ["evidence_decomposition_skill", "material_delivery_skill"]
  minimum_inputs:
    required: ["策略语义", "命中对象集合", "处置窗口", "后验窗口"]
    optional: ["灰度组语义", "对照组语义", "业务指标口径", "申诉/客诉口径"]
    missing: ["对照组", "后验指标口径", "误伤样本定义"]
  data_source_plan:
    required_data_domains: ["策略引擎域", "用户信息域", "前端行为域", "后端数据域", "风险画像域"]
    optional_data_domains: ["活动信息域", "渠道信息域"]
    field_types_needed:
      identity_and_account: ["user_id", "account_id", "account_status"]
      device_and_network: ["device_id", "ip", "ua"]
      session_and_chain: ["frontend_event", "backend_api", "event_time", "request_time"]
      activity_and_channel: ["campaign_id", "reward_status", "channel_id"]
      risk_and_strategy: ["risk_label", "risk_score", "strategy_hit", "engine_decision", "disposal_action", "gray_group", "appeal_status"]
      relation_network: []
    join_paths_needed: ["strategy_decision_outcome_join", "risk_profile_behavior_outcome_join"]
  query_dimensions:
    entities: ["策略", "用户", "账号", "设备", "处置动作", "灰度组", "申诉"]
    group_by: ["策略命中", "处置动作", "灰度组", "风险分层", "业务场景", "申诉状态"]
    compare_with: ["对照组", "策略前基线", "未命中人群", "灰度组"]
    joins: ["策略决策与用户后验", "风险画像与行为后验"]
  time_window:
    baseline: "待补充策略前窗口"
    observation: "待补充策略后窗口"
    granularity: "天或周"
    freshness_expectation: "T+1 + 长周期后验，待平台判断"
  expected_outputs:
    metric_outputs: ["策略命中量", "处置结果", "后验风险变化", "业务指标影响", "申诉/客诉摘要"]
    evidence_outputs: ["策略有效性证据", "误伤证据", "回滚/扩大依据"]
    quality_outputs: ["灰度/对照口径", "后验窗口覆盖", "申诉样本覆盖"]
  interpretation_notes:
    strong_evidence_if: ["命中后风险下降、业务损伤可控、申诉/误伤低、对照组差异成立"]
    medium_evidence_if: ["风险下降但误伤或业务影响口径不完整"]
    weak_signal_if: ["只有策略命中量"]
    counter_evidence_if: ["申诉集中、业务指标异常、对照组无差异、口径变化可解释"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["后验风险", "业务指标", "申诉/客诉", "对照组或灰度组"]
    cannot_conclude_if: ["只有策略命中量", "没有后验窗口", "没有误伤定义"]
  quality_checks:
    required: ["灰度/对照口径检查", "后验窗口检查", "策略命中与风险事实区分", "申诉/客诉覆盖检查"]
    downgrade_if: ["无对照组", "后验窗口不足", "业务指标口径不清"]
  permission_boundary: "高敏；由未来 Data Agent / 内部平台判断权限"
  manual_review_required: true
  safety_boundary:
    false_positive_risks: ["策略命中不等于风险事实", "灰度口径错误", "业务波动", "申诉延迟"]
    prohibited_actions: ["不得只凭命中量扩大策略", "不得无误伤评估强推全"]
  next_query_intent_when_insufficient:
    intent_type: "batch_case_commonality_check"
    target_evidence: "误伤样本共性与策略命中链路"
    reason: "若误伤不清，需要聚类误伤样本定位策略问题"
```

### 5-9. 说明

- 数据域选择：策略复盘必须结合策略引擎、用户/行为/后端结果和风险画像。
- join path：策略决策到后验是主链路，画像到行为用于解释命中人群。
- 降级风险：无对照组、后验不足、申诉延迟、业务波动。
- 是否足够：基本足够。
- 缺输入：策略窗口、对照组、后验指标、误伤定义。

## 汇总

### 1. 10 个 case 中 query_intent 完整率

完整率：**8/10 基本可发给未来 adapter，2/10 勉强可用。**

- 基本可发：AC-003、AC-004、AC-001、AS-001、ACT-003、MIX-001、ADV-003、策略复盘。
- 勉强可用：ADV-008、合法矩阵。原因都是输入依赖强，且合法矩阵缺专门 join path。

### 2. 数据域选择是否合理

整体合理。协议、群控、token、渠道、导流、策略复盘都能稳定落到对应数据域。ADV-003 能正确避免“设备离散即自然用户”，转向活动、设备、后验、关系网络组合。

### 3. join path 是否合理

大部分合理。现有 join path 能覆盖主流链路：

- 协议：`frontend_backend_chain_join` + `request_device_environment_join`
- 群控/反爬：`asset_access_device_network_join`
- token：`token_session_environment_join`
- 活动/众包：`activity_participation_device_reward_join`
- 渠道：`channel_click_activation_user_join`
- 导流：`diversion_exposure_touch_offsite_join`
- 策略：`strategy_decision_outcome_join`

明显缺口：合法矩阵没有专门的 `legal_operation_matrix_authorization_join`。

### 4. 哪些 case 缺输入最多

1. 合法矩阵：缺授权主体、账号范围、工具来源、操作人、收益主体。
2. ADV-008 / MIX-001：缺触达账号、站外承接样本、投诉/举报。
3. AC-001：缺外部样本时间线、内部价格变更窗口、合作方/缓存/导出反证。
4. ADV-003：缺任务平台/教程线索、奖励提现口径、自然对照。

### 5. 哪些 query_intent schema 字段不好用

- `permission_boundary`：当前 schema 原本放在 `safety_boundary` 外，但 v2 标准结构没有单独定义这一字段；本轮为了满足回归输出加了独立字段。建议回写 schema。
- `freshness_expectation`：当前在 `time_window` 内，但用户要求单列；建议 schema 同时允许顶层摘要字段或保持在 `time_window` 中并明确映射。
- `next_query_intent_when_insufficient`：当前 v2 标准结构没有定义，但实际非常有用。建议回写。
- `required_data_domains` 与 `field_types_needed` 当前在 `data_source_plan` 下，但用户要求单列；结构本身没问题，后续输出模板可以支持扁平摘要。

### 6. 是否需要回写 query_intent_schema_v2 或 data_join_paths_v1

需要轻量回写：

1. `query_intent_schema_v2.md`
   - 增加顶层或标准字段：`permission_boundary`
   - 增加：`next_query_intent_when_insufficient`
   - 明确 `freshness_expectation` 可在 `time_window` 内，也可在摘要中单列
   - 明确输出展示时可把 `data_source_plan.required_data_domains` 扁平展示

2. `data_join_paths_v1.md`
   - 新增 `legal_operation_matrix_authorization_join`
   - 用于授权主体、账号范围、工具来源、操作人、调用接口、敏感动作、收益主体、历史违规之间的抽象关联。

