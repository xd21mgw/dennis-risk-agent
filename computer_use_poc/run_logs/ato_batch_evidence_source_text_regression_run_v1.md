# ATO Batch Evidence Source Text Regression Run v1

## 1. 测试目标

- 验证 ATO 批量 case analysis 的证据卡、normalized_evidence、batch pattern summary 能稳定携带 `evidence_source` / `source_quality`。
- 验证 `model_inference`、`manual_input`、stale / window_incomplete、partial / blocked source 不会被误用为强证据。
- 验证 batch pattern summary 能输出 `source_coverage_summary`，并显式展示弱来源、缺来源和模型推断依赖。

执行边界：

- real_platform_called: false
- dataagent_called: false
- release_package_updated: false
- outputs_dist_updated: false
- sensitive_plaintext_output: false

## 2. 输入 Case 摘要

| case_id | case_type | input_summary | source_types |
|---|---|---|---|
| src_case_001 | 来源完整 | 登录链路 + 设备风险 + 用户描述均有来源 | internal_platform_api / browser_dom_read / manual_input |
| src_case_002 | 只有人工输入 | 用户称非本人操作，但无平台 observation | manual_input |
| src_case_003 | 只有模型推断 | 模型根据现象推断可能 ATO，但无原始证据 | model_inference |
| src_case_004 | 登录日志超窗 no_data | event_time 超过在线可靠窗口，login log no_data | internal_platform_api with over_reliable_window |
| src_case_005 | partial / blocked source | 档案可读，但策略平台 permission_blocked，登录日志 partial | internal_platform_api partial / permission_blocked |

## 3. Case-level Regression

### src_case_001: 证据来源完整 case

expected_behavior:

- 可以形成 medium / strong support。
- 必须展示每条证据来源。
- normalized_evidence 必须包含 `source_name`、`source_type`、`source_tool_or_hand`、`source_platform`、`collected_at`、`evidence_time_range`、`raw_result_reference`。

simulated_output_summary:

```yaml
normalized_evidence:
  - evidence_id: ev_login_001
    evidence_name: abnormal_login_then_sensitive_action
    evidence_strength: strong
    source_name: unified_login_log
    source_type: internal_platform_api
    source_tool_or_hand: login_log_read
    source_platform: user_login_unified_log
    collected_at: simulated_2026-05-21T10:00:00+08:00
    evidence_time_range: simulated_event_window
    raw_result_reference: safe_ref://src_case_001/login
    freshness_notes: within_reliable_window
    permission_notes: success
  - evidence_id: ev_device_001
    evidence_name: high_risk_device_signal
    evidence_strength: medium
    source_name: device_profile
    source_type: browser_dom_read
    source_tool_or_hand: device_risk_read
    source_platform: weapon
    collected_at: simulated_2026-05-21T10:02:00+08:00
    evidence_time_range: current_device_profile
    raw_result_reference: safe_ref://src_case_001/device
    freshness_notes: current_profile
    permission_notes: success
  - evidence_id: ev_claim_001
    evidence_name: user_claim_non_self_action
    evidence_strength: weak
    source_name: user_claim
    source_type: manual_input
    source_tool_or_hand: case_intake
    source_platform: none
    collected_at: simulated_2026-05-21T09:50:00+08:00
    evidence_time_range: user_reported_window
    raw_result_reference: safe_ref://src_case_001/manual
    freshness_notes: user_claim_only
    permission_notes: not_applicable
```

source_trace_check:

- evidence_source_present: pass
- source_quality_present: pass
- raw_sensitive_output_absent: pass
- conclusion_boundary: pass

result: pass

### src_case_002: 只有 manual_input 的 case

expected_behavior:

- 不能输出 strong conclusion。
- 只能标记为 clue / needs evidence。
- 必须提示需要登录日志、发布审计、token / OAuth、设备侧补证。

simulated_output_summary:

- conclusion_support_level: `insufficient_support`
- evidence_strength: `weak`
- source_type: `manual_input`
- source_quality.reliability_level: `low`
- required_next_evidence:
  - login_log_read
  - publish_audit
  - token_or_oauth_usage
  - device_risk_read

source_trace_check:

- manual_input_visible: pass
- strong_conclusion_blocked: pass
- missing_evidence_visible: pass

result: pass

### src_case_003: 只有 model_inference 的 case

expected_behavior:

- `model_inference` 不能作为 raw evidence。
- 不能支撑 strong conclusion。
- 只能输出 hypothesis，并进入 missing evidence。

simulated_output_summary:

- conclusion_support_level: `not_evaluated`
- inference_status: `hypothesis_only`
- source_type: `model_inference`
- source_quality.reliability_level: `model_inference_only`
- raw_evidence_present: false
- allowed_statement: `当前只是候选 ATO 路径，需要原始证据验证`
- forbidden_statement: `已确认 ATO`

source_trace_check:

- model_inference_labeled: pass
- raw_evidence_not_claimed: pass
- strong_conclusion_blocked: pass

result: pass

### src_case_004: 登录日志超窗 no_data case

expected_behavior:

- `no_data` 必须标记 freshness / window risk。
- 不得作为 counter evidence。
- 必须标记 `login_log_window_incomplete` / `offline_hive_required`。

simulated_output_summary:

- source_name: unified_login_log
- source_type: internal_platform_api
- source_quality.freshness_status: `over_reliable_window`
- source_quality.freshness_risk: `high`
- login_log_window_incomplete: true
- offline_hive_required: true
- no_data_interpretation: `data_gap`
- counter_evidence: false

source_trace_check:

- freshness_window_risk_visible: pass
- no_data_not_counter_evidence: pass
- offline_hive_required_visible: pass

result: pass

### src_case_005: partial / blocked source case

expected_behavior:

- permission_status 必须可见。
- 结论需要降级或标记缺口。
- blocked source 不能被写成 no_data。

simulated_output_summary:

- available_sources:
  - source_name: archives_center
    source_type: internal_platform_api
    permission_status: success
  - source_name: tianshi_strategy
    source_type: internal_platform_api
    permission_status: permission_blocked
  - source_name: unified_login_log
    source_type: internal_platform_api
    permission_status: partial
- conclusion_support_level: `partial_support`
- missing_evidence:
  - strategy_hit_observation
  - full_login_window
- quality_risk: `partial_or_blocked_sources`

source_trace_check:

- permission_status_visible: pass
- blocked_source_not_no_data: pass
- conclusion_downgraded: pass

result: pass

## 4. Batch Pattern Summary Source Coverage Check

source_coverage_summary:

| evidence_category | source_coverage | weak_source_only_cases | missing_source_cases | model_inference_dependency | result |
|---|---|---|---|---|---|
| 登录链路 | src_case_001 complete, src_case_004 over_window, src_case_005 partial | src_case_002 | src_case_003 | false | pass |
| 设备风险 | src_case_001 complete | src_case_002 | src_case_003, src_case_004, src_case_005 | false | pass |
| 用户申诉 | src_case_001, src_case_002 | src_case_002 | src_case_003 | false | pass |
| 模型推断 | src_case_003 only | src_case_003 | src_case_001, src_case_002, src_case_004, src_case_005 | true | pass |
| 策略命中 | src_case_005 blocked | none | src_case_001, src_case_002, src_case_003, src_case_004 | false | pass |

## 5. Failed / Risk Items

- failed_items: []
- risk_items:
  - model_inference 必须继续保持 hypothesis-only。
  - manual_input 只能作为 clue。
  - over-window login no_data 必须继续标记 freshness/window risk。
  - partial / blocked source 必须进入 missing evidence 或 quality risk。

## 6. 结论

- regression_result: pass
- evidence_source_trace_present: true
- source_quality_trace_present: true
- source_coverage_summary_present: true
- strong_conclusion_from_weak_source_detected: false
- model_inference_misused_as_raw_evidence: false
- manual_input_misused_as_strong_evidence: false
- over_window_no_data_misused_as_counter_evidence: false
- real_query_triggered: false
- release_package_updated: false

本轮文本回归通过。ATO batch evidence source metadata v1 可以支撑证据卡、normalized_evidence 和 batch pattern summary 的来源追踪，但后续 runtime 集成仍需真实 observation pipeline 输出同样字段。
