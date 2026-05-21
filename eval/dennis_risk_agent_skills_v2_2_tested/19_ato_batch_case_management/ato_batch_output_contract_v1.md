# ATO Batch Output Contract v1

## 1. 定位

ATO batch output contract 用于固定 5-20 个 ATO / 盗号 case 批量分析的输出结构，保证用户、内部 Agent、Codex 文档沉淀和人工复核看到的是同一种结果形态。

本 contract 只定义输出结构，不代表真实查询已经发生，不代表策略可以自动上线，也不允许自动处置用户。

核心原则：
- 每个核心结论必须引用 `evidence_source` / `source_quality`。
- `manual_input` 和 `model_inference` 不能单独支撑 strong conclusion。
- 设备关联、IP 聚集、行为相似只能作为候选证据，不能直接定性作弊或盗号。
- strategy 只能输出 candidate direction，不能自动上线策略。
- 输出必须脱敏，不输出 cookie / token / session / header / 完整 IP / 手机号明文。

## 2. 固定输出结构

```yaml
ato_batch_analysis_output:
  batch_summary:
  case_registry_quality:
  per_case_evidence_cards:
  batch_pattern_summary:
  source_coverage_summary:
  missing_evidence_summary:
  candidate_strategy_direction:
  manual_review_boundary:
  next_actions:
```

## 3. batch_summary

用途：先给用户一个可读的批量结论摘要，但不能替代证据明细。

字段：
- `sample_set_id`
- `case_count`
- `analysis_scope`
- `batch_status`
- `overall_support_level`: strong / medium-strong / medium / weak / insufficient
- `one_sentence_summary`
- `risk_type`: ATO / token_leak / OAuth_abuse / account_takeover / insufficient_evidence
- `not_auto_disposition`: true
- `not_auto_strategy_launch`: true
- `boundary_note`

要求：
- 如果 evidence source 覆盖不足，`overall_support_level` 必须降级。
- 如果登录日志超窗，必须显式标记 `login_log_window_incomplete` / `offline_hive_required`。

## 4. case_registry_quality

用途：说明输入 case table 的质量，避免把缺字段 case 当成完整样本。

字段：
- `total_cases`
- `valid_cases`
- `needs_fields_cases`
- `unsupported_case_type_cases`
- `field_coverage`
  - `user_id_coverage`
  - `event_time_coverage`
  - `abnormal_action_coverage`
  - `device_id_coverage`
  - `available_evidence_coverage`
- `quality_risks`
- `normalization_notes`

## 5. per_case_evidence_cards

用途：每个 case 输出一张证据卡，支撑批量聚合。

每个 case 必须包含：
- `case_id`
- `case_status`
- `support_level`: strong / medium / weak / insufficient / needs_evidence
- `strong_evidence`
- `medium_evidence`
- `weak_evidence`
- `counter_evidence`
- `missing_evidence`
- `freshness_risk`
- `permission_or_data_gap`
- `evidence_quality`
- `next_step_recommendation`

每条 evidence 必须携带：
- `evidence_name`
- `evidence_summary`
- `evidence_source`
  - `source_name`
  - `source_type`
  - `source_tool_or_hand`
  - `source_platform`
  - `collected_at`
  - `evidence_time_range`
  - `raw_reference`
- `source_quality`
  - `freshness_status`
  - `freshness_risk`
  - `permission_status`
  - `reliability_level`

边界：
- `model_inference` 只能写入 hypothesis / interpretation，不能写入 raw evidence。
- `manual_input` 可以作为 clue，但不能单独形成 strong evidence。
- 超出统一登录日志在线可靠窗口的 no_data 只能写入 missing / freshness risk，不得写为 counter evidence。

## 6. batch_pattern_summary

用途：将单 case evidence card 聚合成批量模式。

字段：
- `case_clustering_result`
- `common_entity_pattern`
- `common_login_or_token_pattern`
- `common_device_or_did_pattern`
- `common_ip_or_network_pattern`
- `common_behavior_path`
- `shared_missing_evidence`
- `suspected_attack_path`
- `confidence_level`
- `model_inference_boundary`

要求：
- 只总结本 batch 已覆盖 case，不外推到未查样本。
- 后置动作只能作为 ATO 后置异常动作，不能直接当作 ATO 主因。
- 设备关联关系只能作为候选关系，不直接等于风险定性。

## 7. source_coverage_summary

用途：说明批量模式依赖哪些来源，以及哪些结论需要降级。

字段：
- `source_type_distribution`
- `source_by_core_conclusion`
- `cases_with_multi_source_support`
- `cases_with_manual_input_only`
- `cases_with_model_inference_only`
- `cases_with_stale_or_window_incomplete_source`
- `cases_with_partial_or_blocked_source`
- `conclusions_requiring_downgrade`
- `source_gap_notes`

要求：
- 每类核心证据来自哪些 source 必须可见。
- 依赖 `model_inference` 的结论必须标记为 hypothesis。
- stale / partial / blocked source 必须在输出中显式可见。

## 8. missing_evidence_summary

字段：
- `missing_evidence_name`
- `affected_case_ids`
- `priority`: P0 / P1 / P2
- `why_it_matters`
- `recommended_source`
- `fallback_if_unavailable`

常见 P0 缺口：
- 登录日志超窗，需要 offline Hive / 离线日志。
- 发布 / 改密 / token 使用链路缺失。
- OAuth 授权记录缺失。
- 设备 did / deviceId 解析缺失。

## 9. candidate_strategy_direction

用途：输出候选策略方向，不输出自动上线策略。

字段：
- `direction_name`
- `candidate_rule_idea`
- `supporting_evidence`
- `required_additional_evidence`
- `false_positive_risk`
- `ab_or_holdout_plan`
- `kill_and_observe_separation`
- `manual_review_requirement`
- `not_auto_launch`: true

边界：
- 不允许写“直接上线”“直接封禁”“自动处置”。
- 必须包含误伤风险、补证建议、AB / 查杀分离 / 人工复核建议。

## 10. manual_review_boundary

字段：
- `high_priority_review_cases`
- `needs_more_data_cases`
- `not_recommended_for_action_cases`
- `requires_offline_hive_cases`
- `requires_policy_review_before_action`
- `human_review_notes`

## 11. next_actions

字段：
- `immediate_next_step`
- `offline_hive_query_plan_needed`
- `additional_readonly_observation_needed`
- `manual_review_needed`
- `strategy_review_needed`
- `blocked_by`

推荐输出：
- 对 strong / medium-strong batch：进入人工策略评审和离线扩量。
- 对 insufficient batch：补齐关键 evidence source 后再判断。
- 对 unsupported case：转入对应风险场景，不强行归入 ATO。

