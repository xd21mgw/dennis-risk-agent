# User Login Log Readonly POC v2.4.8 Run 007

```yaml
test_stage: v2.4.8
test_type: multi_source_focused_login_risk_e2e
validation_status: multi_source_e2e_validated_with_partial_coverage

target:
  user_id: "4700398885"
  same_user_id_used: true

archives_center_source:
  direct_url: "https://admin.p.adm-corp.kuaishou.com/frontend/archives/index.html#/archives/user/profile?userId={userId}"
  saved_state_name: archives_center_4700398885_20260519
  accessible: true
  query_success: true
  result_present: true
  user_profile_visible: true
  user_analysis_tab_visible: true
  app_core_operation_log_visible: true
  time_range: "2025-11-20 ~ 2026-05-19"
  partial_coverage: true

user_login_unified_log_source:
  accessible: true
  query_success: true
  result_present: true
  total_count: 133
  page_size: 20
  visible_row_count: 20
  partial_page_only: true

cross_source_alignment:
  same_user_id_used: true
  did_consistent: true
  aligned_behaviors:
    - 历史一键登录
    - 退出登录
  archives_center_contribution:
    - 账号状态
    - 设备型号
    - 地域
    - 用户分析日志
  user_login_unified_log_contribution:
    - token 生命周期
    - 高危接口调用
    - 多账号登录
    - 精确时间戳

observation_categories:
  high_confidence_observations:
    - 档案中心与用户登录统一日志使用同一 user_id。
    - 档案中心 userId direct URL 可访问，用户主页与用户分析 Tab 可见。
    - 用户登录统一日志查询成功，返回 total_count=133、page_size=20、visible_row_count=20。
    - DID 可跨源对齐。
    - 历史一键登录 / 退出登录行为可跨源对齐。
  medium_confidence_observations:
    - 档案中心提供约 6 个月用户分析窗口，但当前仅查看部分数据。
    - 统一登录日志提供 token 生命周期、高危接口调用、多账号登录等链路线索，但当前只覆盖当前页。
  weak_or_contextual_observations:
    - 档案中心账号状态、设备型号、地域可作为账号安全上下文。
    - 统一登录日志精确时间戳可作为后续对齐锚点。
  missing_observations:
    - 统一登录日志全分页遍历。
    - 档案中心用户分析全分页遍历。
    - 设备攻防平台验证。
    - 审核 / 打标日志验证。
    - 权限阻断行为验证。

guardrail_check:
  no_cross_user_merge: true
  no_auto_risk_conclusion: true
  no_punishment_recommendation: true
  no_safe_json_summary_copied: true
  credential_raw_value_output: false
  partial_page_only_marked_if_needed: true
  readonly_safety_check: PASSED

validation_result:
  e2e_joint_observation_success: true
  multi_source_schema_ready: focused_login_risk_observation_only
  blockers: []

not_validated_or_not_implied:
  automatic_risk_classification_completed: false
  full_historical_data_reviewed: false
  device_platform_verified: false
  audit_or_label_logs_reviewed: false
  final_risk_conclusion_generated: false
```

## 当前结论

本轮同 userId 多源 e2e 已跑通，状态为 `multi_source_e2e_validated_with_partial_coverage`。

该结论只说明：Dennis / browser computer use 可以在同一 userId 下联动读取档案中心和用户登录统一日志，并形成 focused_login_risk observation。它不代表自动风险定性完成，也不代表全量历史数据、设备平台、审核 / 打标日志已经验证。

## 边界

- 不修改核心 Skill。
- 不更新 release package。
- 不改变 DataAgent / Hive 边界。
- 不引入自动处置或自动风险定性。
- 不把 `high_confidence_observations` 解释为风险强证据或最终结论。
- 不把当前页 observation 解释为全量结果。
