# v2.5.8 E2E 多手脚只读验证模板

## 1. 测试目标

验证 Dennis Agent 在真实风险问题下，是否能：

- 理解用户问题。
- 生成多平台只读查询计划。
- 调度最小三手脚 observation。
- 消费多个 observation，形成 evidence_summary。
- 明确 supporting_evidence / counter_evidence / missing_evidence / boundary_notes。
- 不因单一策略命中直接输出最终作弊定性。

本轮不新增平台能力，不修改核心 Skill，不更新 release package。

## 2. 测试问题

```text
帮我看下 4231737183 今天是不是风险用户，为什么被阻止/验证？
```

## 3. 输入字段

```yaml
test_input:
  user_question: "帮我看下 4231737183 今天是不是风险用户，为什么被阻止/验证？"
  source_id: "4231737183"
  time_window:
    source: relative_today
    start_time_ms:
    end_time_ms:
  intent: e2e_multi_evidence_risk_assessment
```

说明：

- `source_id` 和 `time_window` 是本轮 E2E 的最小输入。
- “今天”应由执行环境按当前自然日转换为 `start_time_ms` / `end_time_ms`。
- 若无法转换时间窗口，应进入 blocker，不得继续生成伪 observation。

## 4. 查询计划

v2.5.8 只跑最小三手脚闭环：

1. `tianshi_strategy_hit_check`：策略命中证据。
2. `unified_login_log_check`：登录 / 验证链路证据。
3. `archives_center_profile_check`：账号画像 / 历史风险证据。

暂不强制跑：

- `frontend_activity_profile_check`
- `device_sdk_foundation_check`
- `DataAgent / Hive`

原因：先验证最小 E2E 链路，避免一次性拉太多平台导致阻塞。

```yaml
multi_evidence_query_plan:
  user_question: "帮我看下 4231737183 今天是不是风险用户，为什么被阻止/验证？"
  source_id: "4231737183"
  time_window:
    start_time_ms:
    end_time_ms:
    source: relative_today
  intent: e2e_multi_evidence_risk_assessment
  required_sources:
    - name: tianshi_strategy_platform_rcp
      tool: tianshi_strategy_hit_check
      evidence_type: strategy_evidence
      purpose: 查询今天是否命中生产反作弊 / 风控策略，以及阻止 / 验证分布
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

    - name: user_login_unified_log
      tool: unified_login_log_check
      evidence_type: login_evidence
      purpose: 查询登录、验证、token/session、高危接口链路是否能解释“阻止 / 验证”
      required_inputs:
        source_id_or_user_id: "4231737183"
        time_window:
      expected_observation:
        - login_success_failure_distribution
        - login_method_sequence
        - verification_or_block_events
        - token_or_session_events
        - high_risk_operation_sequence
        - pagination_observation

    - name: archives_center
      tool: archives_center_profile_check
      evidence_type: profile_evidence
      purpose: 查询账号状态、历史风险、审核 / 打标记录和用户画像补充
      required_inputs:
        user_id_or_source_id: "4231737183"
      expected_observation:
        - account_status
        - risk_labels
        - user_analysis_summary
        - audit_or_label_log_summary
        - profile_limitations

  optional_sources_not_required_in_v2_5_8:
    - frontend_activity_profile_check
    - device_sdk_foundation_check
    - DataAgent_Hive
```

## 5. 内部 Agent 执行顺序

```yaml
execution_order:
  - step: source_entry_resolution
    sources:
      - tianshi_strategy_platform_rcp
      - user_login_unified_log
      - archives_center
    rule: 不允许猜 URL 或手脚入口；找不到入口则返回 source_entry_missing。

  - step: auth_preflight
    sources:
      - user_login_unified_log
      - archives_center
    rule: browser 手脚必须先做 saved state / redirect / permission 检查。

  - step: tianshi_strategy_hit_check
    rule: 查询策略命中，只读，不做处置。

  - step: unified_login_log_check
    rule: 查询登录 / 验证链路；分页未覆盖时标记 partial_page_only。

  - step: archives_center_profile_check
    rule: 查询账号画像 / 历史风险；分页未覆盖时标记 partial_coverage。

  - step: dennis_digest
    rule: Dennis 消费 observation，输出 evidence_summary。
```

## 6. observation 收集要求

```yaml
internal_agent_observations:
  tianshi_strategy_hit_observation:
    required: true
    status: success | failed | permission_blocked | no_data | skipped
    fields:
      - has_strategy_hit
      - raw_record_count
      - production_policy_hit_count
      - riskDecision_distribution
      - eventType_distribution
      - riskType_distribution
      - sample_hits
      - limitations

  unified_login_log_observation:
    required: true
    status: success | failed | permission_blocked | no_data | skipped
    fields:
      - result_table_observation
      - risk_event_scan
      - detail_observation_if_opened
      - pagination_observation
      - no_result_observation
      - limitations

  archives_center_observation:
    required: true
    status: success | failed | permission_blocked | user_not_found | skipped
    fields:
      - account_status
      - profile_summary
      - user_analysis_summary
      - audit_or_label_log_summary
      - pagination_or_partial_coverage
      - limitations
```

收集规则：

- 每个 source 必须显式记录 `status`。
- `failed / permission_blocked / no_data / user_not_found` 不能被吞掉，必须进入 `missing_evidence` 或 `blockers`。
- 任意 observation 不得输出 token / session / ticket / authorization / cookie 等凭证明文。
- 不复制完整 JSON。
- 不点击处置、导出、审批、封禁、解封等写操作。

## 7. evidence_summary 输出模板

```yaml
evidence_summary:
  conclusion_level: strong_suspicion | medium_suspicion | insufficient_evidence | no_obvious_risk
  conclusion:
  source_status:
    tianshi_strategy_hit_check:
      status:
      coverage:
    unified_login_log_check:
      status:
      coverage:
    archives_center_profile_check:
      status:
      coverage:
  key_findings:
    strategy_evidence:
      summary:
      strength:
      boundary:
    login_evidence:
      summary:
      strength:
      boundary:
    profile_evidence:
      summary:
      strength:
      boundary:
  supporting_evidence:
    - source:
      finding:
      interpretation:
  counter_evidence:
    - source:
      finding:
      interpretation:
  missing_evidence:
    - source:
      reason:
      impact:
  blockers:
    - source:
      blocker:
      next_action:
  recommended_next_checks:
    - source:
      purpose:
  boundary_notes:
    - 单源 strong evidence 不得直接输出 definitive conclusion。
    - 策略命中不等于最终作弊定性。
    - 无命中 / 无结果不等于无风险。
    - 未覆盖分页时不得声称已查看全量。
```

## 8. 验收标准

通过标准：

- Dennis 能生成 `multi_evidence_query_plan`。
- 查询计划包含三手脚：天狮、用户登录统一日志、档案中心。
- 查询计划不强制包含前端活跃画像、设备 SDK、DataAgent / Hive。
- 每个 source 的 observation status 都被显式记录。
- `failed / permission_blocked / no_data` 进入 `missing_evidence` 或 `blockers`。
- evidence_summary 包含 `supporting_evidence`、`counter_evidence`、`missing_evidence`、`boundary_notes`。
- 不因天狮命中直接判定用户作弊。
- 不因天狮无命中、登录日志无结果、档案中心无结果直接判定无风险。
- 不建议自动处罚、封禁、冻结或策略上线。

不通过：

- 只查天狮就输出最终风险定性。
- 只输出一个平台 observation，不说明其他 source 未查。
- 把 `riskDecision=阻止/验证` 当成最终执行结果。
- 把分页第一页当全量。
- 把权限阻断 / 登录态阻断解释为无数据。

## 9. 风险边界

- 本模板是 E2E 测试模板，不是真实执行结果。
- v2.5.8 不新增平台能力。
- v2.5.8 不修改核心 Skill。
- v2.5.8 不更新 release package。
- DataAgent / Hive 仍只用于 Hive / 公司数仓取数分析，不替代 browser computer use 或在线平台。
- 最小三手脚闭环只验证 strategy / login / profile 三类证据，不代表完整风险闭环。
