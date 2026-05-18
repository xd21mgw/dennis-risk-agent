# Query Intent Schema v2

## 0. 目标

本文件在 `dataagent_tool_contract_v1.md` 的基础上，补齐 Data Agent configs 层所需的结构化字段，让 `query_intent` 不只描述“要查什么证据”，还明确：

- 需要哪些数据域。
- 需要哪些字段类型。
- 需要哪些抽象 join 路径。
- 需要哪些数据质量检查。
- 返回后按什么结论阈值解释。

当前 Codex 阶段不调用真实 Data Agent，不编造真实表名、字段名、SQL 或 API。真实字段映射和真实 join key 由未来内部平台补充。

## 1. v2 标准结构

```yaml
query_intent:
  intent_id: "<稳定唯一标识>"
  intent_type: "<见 query_intent_to_data_source_map_v1.md>"
  risk_question: "<用户真实要回答的风险问题>"
  target_evidence: "<要补齐的证据类型>"
  applicable_skill:
    primary: "<主控 Skill>"
    auxiliary:
      - "<辅助 Skill>"

  minimum_inputs:
    required:
      - "<执行查询所需的最小输入>"
    optional:
      - "<有助于提升解释质量的输入>"
    missing:
      - "<当前缺失信息>"

  required_data_domains:
    - "<用户信息域 | 活动信息域 | 渠道信息域 | 设备信息域 | 前端行为域 | 后端数据域 | 风险画像域 | 策略引擎域 | 关联网络域>"
  optional_data_domains:
    - "<可选数据域>"
  field_types_needed:
    identity_and_account:
      - "<user_id | account_id | login_time 等字段类型>"
    device_and_network:
      - "<device_id | realtime_fingerprint | ip | ua 等字段类型>"
    session_and_chain:
      - "<token_id | frontend_event | backend_api | api_sequence 等字段类型>"
    activity_and_channel:
      - "<campaign_id | reward_status | click_time | ctit 等字段类型>"
    risk_and_strategy:
      - "<risk_label | strategy_hit | engine_decision 等字段类型>"
    relation_network:
      - "<relation_group_id | strong_device_relation 等字段类型>"
  join_paths_needed:
    - "<见 data_join_paths_v1.md 的 join_path_id>"

  query_dimensions:
    entities:
      - "<用户 / 账号 / 设备 / IP / token / 包 / 渠道 / 活动 / 直播间 / 收益主体>"
    group_by:
      - "<聚合或下钻维度，只写语义>"
    compare_with:
      - "<历史基线 | 同类人群 | 对照组 | 正常链路 | 合法矩阵 | 业务活动窗口>"
    joins:
      - "<抽象数据类型关联，不写真实表名>"

  time_window:
    baseline: "<历史基线窗口；未知写待补充>"
    observation: "<异常观测窗口；未知写待补充>"
    granularity: "<分钟 | 小时 | 天 | 周>"
  freshness_expectation: "<实时 | 准实时 | T+1 | 离线画像 | 长周期后验 | 待平台判断>"

  expected_outputs:
    metric_outputs:
      - "<指标、分布、趋势、比例、样本摘要>"
    evidence_outputs:
      - "<强证据 / 中证据 / 弱证据 / 反证需要的输出>"
    quality_outputs:
      - "<数据覆盖、缺失、延迟、口径、权限状态>"

  quality_checks:
    required:
      - "<前端日志延迟/丢点检查>"
      - "<后端与前端 join 口径检查>"
      - "<SDK/指纹时效检查>"
      - "<画像更新时间检查>"
      - "<策略命中与风险事实区分>"
    downgrade_if:
      - "<partial / failed / no_permission>"
      - "<关键反证未返回>"
      - "<样本量、时间窗口、join 口径不清>"

  interpretation_notes:
    strong_evidence_if:
      - "<什么结果可解释为强证据>"
    medium_evidence_if:
      - "<什么结果可解释为中证据>"
    weak_signal_if:
      - "<什么结果只能解释为弱信号>"
    counter_evidence_if:
      - "<什么结果构成反证>"

  conclusion_threshold:
    sufficient_for: "<明确判断 | 高度疑似 | 证据不足 | 反向排除>"
    must_combine_with:
      - "<必须组合的其他证据>"
    cannot_conclude_if:
      - "<不能下结论的情况>"

  permission_boundary: "<低敏 | 中敏 | 中高敏 | 高敏 | 待平台判断；只写抽象权限边界>"
  manual_review_required: "<true | false | 待平台判断>"
  safety_boundary:
    false_positive_risks:
      - "<误伤来源>"
    prohibited_actions:
      - "<当前结果不得直接触发的动作>"

  next_query_intent_when_insufficient:
    intent_type: "<下一轮 query_intent_type>"
    target_evidence: "<下一轮要补的证据>"
    reason: "<为什么当前证据不足，需要下一轮查询>"
```

## 2. intent_type 建议集合

以下类型应与 `query_intent_to_data_source_map_v1.md` 对齐：

- `protocol_frontend_backend_join`
- `sdk_bypass_or_cracked_app_check`
- `group_control_dispatch_check`
- `token_reuse_or_account_takeover_check`
- `activity_black_industry_or_low_quality_check`
- `channel_attribution_hijacking_check`
- `anti_crawler_asset_leakage_check`
- `traffic_diversion_chain_check`
- `legal_operation_matrix_check`
- `strategy_effect_and_false_positive_review`
- `batch_case_commonality_check`

## 3. 生成规则

1. `risk_question` 必须是风险问题，不是简单取数问题。
2. `target_evidence` 必须是证据类型，不能写“查异常”。
3. `required_data_domains` 必须来自 `data_domains_v1.md`。
4. `field_types_needed` 必须来自 `field_dictionary_template_v1.md`，不得写真实字段名。
5. `join_paths_needed` 必须来自 `data_join_paths_v1.md`，不得写真 join key。
6. `quality_checks` 必须覆盖至少一个数据质量风险或反证风险。
7. `conclusion_threshold` 必须说明不能下结论的条件。
8. `freshness_expectation` 使用标准取值：实时、准实时、T+1、离线画像、长周期后验、待平台判断。
9. `permission_boundary` 只写抽象权限边界，不写内部权限系统、审批流或 API。
10. 只要涉及高风险处置，`manual_review_required` 应为 true 或待平台判断。
11. `next_query_intent_when_insufficient` 必须给出下一步补证方向，避免证据不足时停在结论上。

## 4. 示例：协议链路排查

```yaml
query_intent:
  intent_id: "example_protocol_chain_001"
  intent_type: "protocol_frontend_backend_join"
  risk_question: "目标请求是否脱离正常端链路"
  target_evidence: "前后端链路一致性"
  applicable_skill:
    primary: "protocol_attack_expert_skill"
    auxiliary:
      - "cracked_app_expert_skill"
      - "evidence_decomposition_skill"
  minimum_inputs:
    required:
      - "user_id 或 device_id"
      - "api_name 或业务动作"
      - "time_window"
    optional:
      - "app_version"
      - "sdk_status"
    missing: []
  required_data_domains:
    - "前端行为域"
    - "后端数据域"
    - "设备信息域"
    - "策略引擎域"
  optional_data_domains:
    - "风险画像域"
  field_types_needed:
    identity_and_account:
      - "user_id"
    device_and_network:
      - "device_id"
      - "realtime_fingerprint"
      - "ip"
      - "ua"
    session_and_chain:
      - "frontend_event"
      - "backend_api"
      - "api_sequence"
      - "gateway_decision"
    activity_and_channel: []
    risk_and_strategy:
      - "strategy_hit"
      - "engine_decision"
    relation_network: []
  join_paths_needed:
    - "frontend_backend_chain_join"
    - "request_device_environment_join"
    - "strategy_gateway_decision_join"
  query_dimensions:
    entities:
      - "用户"
      - "设备"
      - "请求"
      - "前端事件"
    group_by:
      - "接口动作"
      - "客户端版本"
      - "链路完整性"
    compare_with:
      - "正常端链路"
      - "官方版本"
    joins:
      - "前端行为与后端请求"
      - "请求与设备环境"
      - "请求与策略/网关决策"
  time_window:
    baseline: "待补充"
    observation: "待补充"
    granularity: "小时"
  freshness_expectation: "准实时或 T+1，待平台判断"
  expected_outputs:
    metric_outputs:
      - "端链路覆盖摘要"
      - "接口序列重复摘要"
      - "环境冲突摘要"
    evidence_outputs:
      - "链路冲突证据"
      - "埋点/SDK/官方版本反证"
    quality_outputs:
      - "前端日志覆盖状态"
      - "join 口径说明"
  quality_checks:
    required:
      - "前端日志延迟/丢点检查"
      - "SDK 状态检查"
      - "官方版本对照"
    downgrade_if:
      - "只有前端无日志"
      - "关键反证未返回"
  interpretation_notes:
    strong_evidence_if:
      - "无端链路、接口直达、序列固化和环境冲突同时成立，并排除采集问题"
    medium_evidence_if:
      - "链路冲突和接口模板化成立，但环境或包证据不完整"
    weak_signal_if:
      - "只有前端无日志"
    counter_evidence_if:
      - "官方版本同样缺日志或 SDK 采集问题可解释"
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with:
      - "接口序列固化"
      - "token/device/ip/ua 一致性异常"
    cannot_conclude_if:
      - "仅前端无日志"
      - "官方版本或埋点问题可解释"
  permission_boundary: "中高敏；由未来 Data Agent / 内部平台判断权限"
  manual_review_required: "true"
  safety_boundary:
    false_positive_risks:
      - "埋点缺失"
      - "破解包绕采集"
      - "合法工具调用"
    prohibited_actions:
      - "不得仅凭链路冲突强拦截"
  next_query_intent_when_insufficient:
    intent_type: "sdk_bypass_or_cracked_app_check"
    target_evidence: "SDK日志覆盖与客户端包异常"
    reason: "排查破解包、官方包埋点缺失或 SDK 采集异常"
```

## 5. 禁止行为

- 禁止在 `field_types_needed` 写真实字段名。
- 禁止在 `joins` 写真实表名或真实 join key。
- 禁止把 `quality_checks` 省略。
- 禁止省略 `permission_boundary`、`freshness_expectation`、`manual_review_required` 和 `next_query_intent_when_insufficient`。
- 禁止把 Data Agent 返回直接解释为最终处罚依据。
