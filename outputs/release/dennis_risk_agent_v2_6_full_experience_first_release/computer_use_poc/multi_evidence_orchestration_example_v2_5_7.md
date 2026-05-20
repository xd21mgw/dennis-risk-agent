# v2.5.7 多手脚证据编排样例

## 1. 定位

v2.5.7 不新增平台能力，只沉淀 Dennis Agent 在“某用户是否有风险 / 为什么被拦截或验证”类问题下的多手脚证据编排样例。

核心原则：

- 天狮策略命中是重要策略证据，但不能单独替代最终风险判断。
- Dennis Agent 应生成多证据查询计划，明确已查、未查、支持证据、反证和缺口。
- DataAgent / Hive 只在需要批量统计、历史聚合、离线指标时进入，不作为默认万能手脚。

## 2. 适用问题

适用用户问题包括：

- “帮我看下 4231737183 今天是否有风险。”
- “这个用户为什么被拦截？”
- “这个用户为什么登录要验证？”
- “这个用户是不是风险用户？”
- “这个用户今天被风控打到了，帮我综合看下原因。”

不适用：

- 只问“是否命中策略”的单一策略查询：优先走 `tianshi_strategy_hit_check`。
- 只问登录链路细节：优先走 `unified_login_log_check`。
- 只问设备画像：优先走 `device_sdk_foundation_check`。
- 只问批量统计：优先生成 DataAgent / Hive 查询建议。

## 3. 多证据查询顺序

建议顺序：

| 顺序 | 手脚 / source | evidence_type | 目的 |
|---|---|---|---|
| 1 | `tianshi_strategy_hit_check` | `strategy_evidence` | 查是否命中生产风控 / 反作弊策略 |
| 2 | `unified_login_log_check` | `login_evidence` | 查登录、验证、OAuth、扫码、token/session、高危接口链路 |
| 3 | `archives_center_profile_check` | `profile_evidence` | 查账号画像、账号状态、历史风险、审核 / 打标补充 |
| 4 | `frontend_activity_profile_check` | `behavior_evidence` | 查前端活跃信号，判断是否存在基本前端行为痕迹 |
| 5 | `device_sdk_foundation_check` | `device_evidence` | 查设备环境、一致性、root/hook/多开/模拟器等设备侧线索 |
| 6 | `DataAgent / Hive` | `offline_aggregate_evidence` | 仅在需要批量统计、历史聚合、离线指标时使用 |

说明：

- 顺序不是强制串行，可根据问题场景裁剪。
- 如果用户问的是“为什么被策略拦”，天狮可先查。
- 如果用户问的是“是不是盗号 / 异常登录”，登录统一日志应优先于天狮。
- 如果用户问的是“是否真人行为”，前端活跃画像只能提供活跃存在性，不能证明真人或本人。

## 4. 查询计划模板

```yaml
multi_evidence_query_plan:
  user_question: "帮我看下 4231737183 今天是不是风险用户"
  source_id: "4231737183"
  time_window:
    start:
    end:
    source: user_provided_or_default_today
  intent: multi_evidence_risk_assessment
  evidence_sources:
    - name: tianshi_strategy_platform_rcp
      tool: tianshi_strategy_hit_check
      evidence_type: strategy_evidence
      purpose: 判断指定窗口内是否命中生产风控 / 反作弊策略
      required_inputs:
        source_id: "4231737183"
        start_time_ms:
        end_time_ms:
        fixed_eventTypeCodes:
          - BS
          - ANTICRAWL
          - ACTIVITY_ANTISPAM
          - ACCOUNT
          - FLOW_ANTISPAM
      expected_observation:
        - has_strategy_hit
        - raw_record_count
        - production_policy_hit_count
        - riskDecision_distribution
        - eventType_distribution
        - riskType_distribution
        - sample_hits
      fallback_when_failed: 标记 strategy_evidence unavailable，不输出无风险结论

    - name: user_login_unified_log
      tool: unified_login_log_check
      evidence_type: login_evidence
      purpose: 核查登录、验证、token/session、OAuth/扫码、高危接口调用链路
      required_inputs:
        user_id_or_source_id:
        time_window:
      expected_observation:
        - login_success_failure_distribution
        - login_method_sequence
        - token_or_session_events
        - high_risk_operation_sequence
        - device_and_ip_consistency
      fallback_when_failed: 标记 login_evidence missing，保留登录链路缺口

    - name: archives_center
      tool: archives_center_profile_check
      evidence_type: profile_evidence
      purpose: 补账号状态、账号画像、历史风险、审核 / 打标信息
      required_inputs:
        user_id:
      expected_observation:
        - account_status
        - risk_labels
        - user_analysis_summary
        - audit_or_label_log_summary
      fallback_when_failed: 标记 profile_evidence missing，不解释为用户无档案或无风险

    - name: frontend_activity_profile
      tool: frontend_activity_profile_check
      evidence_type: behavior_evidence
      purpose: 判断是否存在前端活跃信号及活跃强弱
      required_inputs:
        app_name:
        query_subject_type: userId_or_deviceId
        query_subject_value:
      expected_observation:
        - has_frontend_activity_signal
        - activity_strength
        - profile_card_fields
        - usage_duration_presence
      fallback_when_failed: 标记 behavior_evidence missing，不解释为无前端行为

    - name: device_sdk_foundation
      tool: device_sdk_foundation_check
      evidence_type: device_evidence
      purpose: 核查设备画像、设备一致性、root/hook/多开/模拟器等设备侧线索
      required_inputs:
        device_id_or_did:
      expected_observation:
        - device_basic_info
        - device_risk_profile
        - relation_summary
      fallback_when_failed: 标记 device_evidence missing，不解释为设备无风险

    - name: DataAgent_Hive
      tool: dataagent_hive_query_suggestion
      evidence_type: offline_aggregate_evidence
      purpose: 仅用于批量统计、历史聚合、离线指标补证
      required_inputs:
        query_goal:
        sample_scope:
        time_window:
      expected_observation:
        - aggregate_distribution
        - historical_baseline
        - cohort_comparison
      fallback_when_failed: 标记 offline_aggregate_evidence pending

  output_rule:
    - 不因单一证据直接定性
    - 明确 supporting_evidence / counter_evidence / missing_evidence
    - 明确哪些平台已查、哪些平台未查
    - 不把天狮命中等同最终作弊定性
    - 不把无命中等同无风险
```

## 5. 证据合并规则

```yaml
evidence_merge_rules:
  strategy_evidence:
    tianshi_hit:
      strength: strong_strategy_evidence
      boundary: 策略命中不等于最终作弊定性
    tianshi_no_hit:
      strength: missing_strategy_hit_in_window
      boundary: 无命中不代表无风险

  login_evidence:
    abnormal_login_or_verification:
      strength: login_behavior_evidence
      boundary: 需结合设备、账号画像和后续行为

  profile_evidence:
    risk_profile_or_history:
      strength: profile_evidence
      boundary: 历史画像不等于当前事件定性

  behavior_evidence:
    frontend_activity_present:
      strength: behavior_evidence
      boundary: 有前端活跃不等于真人 / 本人 / 具体动作发生
    frontend_activity_missing:
      strength: behavior_gap
      boundary: 无前端活跃画像不等于无行为，需查行为序列和后端日志

  device_evidence:
    device_environment_abnormal:
      strength: device_evidence
      boundary: 设备异常需结合登录链路和账号关系

  cross_source_consistency:
    multi_source_consistent:
      effect: conclusion_confidence_up
    single_source_only:
      effect: output_strong_suspicion_or_needs_more_evidence
      forbidden: definitive_conclusion
    conflicting_evidence:
      effect: must_list_counter_evidence_and_missing_evidence
```

结论规则：

- 多源一致时，结论置信度可以提升。
- 单源命中但其他证据缺失时，输出 `strong_suspicion` 或 `needs_more_evidence`，不输出 definitive conclusion。
- 证据冲突时，必须列 `counter_evidence` 和 `missing_evidence`。
- `no_obvious_risk` 只能在多个关键证据源均未见异常且覆盖范围明确时使用，并保留证据窗口边界。

## 6. 最终输出模板

```yaml
risk_assessment_evidence_summary:
  conclusion_level: strong_suspicion | medium_suspicion | insufficient_evidence | no_obvious_risk
  conclusion:
  key_findings:
    strategy_evidence:
      status:
      summary:
      boundary:
    login_evidence:
      status:
      summary:
      boundary:
    profile_evidence:
      status:
      summary:
      boundary:
    behavior_evidence:
      status:
      summary:
      boundary:
    device_evidence:
      status:
      summary:
      boundary:
  supporting_evidence:
    - source:
      finding:
      strength:
  counter_evidence:
    - source:
      finding:
      interpretation:
  missing_evidence:
    - source:
      reason:
      impact:
  recommended_next_checks:
    - source:
      purpose:
  boundary_notes:
    - 不因单一证据直接定性。
    - 策略命中不等于最终作弊定性。
    - 无策略命中不等于无风险。
    - DataAgent / Hive 只在批量统计、历史聚合、离线指标时使用。
```

## 7. 示例回答骨架

```text
初步看，这类问题不能只查天狮策略命中后就定性。建议按多证据计划看：

1. 先查天狮 strategy_hit_check：确认今天是否命中生产策略，以及 riskDecision / eventType / riskType 分布。
2. 再查统一登录日志：确认登录、验证、token/session、高危接口链路是否异常。
3. 补档案中心：看账号状态、历史风险、审核 / 打标记录。
4. 补前端活跃画像：看是否存在前端活跃信号，但不把它当真人证明。
5. 补设备 SDK：看设备环境和一致性。

输出时我会分 supporting_evidence、counter_evidence、missing_evidence，不会因为天狮命中就直接说用户一定作弊。
```

## 8. 禁止事项

- 不新增平台能力。
- 不调用真实内部平台。
- 不修改核心 Skill。
- 不更新 release package。
- 不改变 DataAgent / Hive 边界。
- 不把天狮策略命中等同最终作弊定性。
- 不把无命中等同无风险。
- 不把前端活跃等同真人 / 本人。
- 不把设备异常单独等同群控 / 协议 / 作弊。
