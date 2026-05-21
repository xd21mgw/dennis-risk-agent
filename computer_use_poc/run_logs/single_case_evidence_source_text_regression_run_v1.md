# Single-case Evidence Source Text Regression Run v1

## 1. Regression Goal

Validate that single-case risk judgement uses the same evidence source metadata contract as ATO batch analysis:

- Every strong / medium / weak / counter evidence item carries `evidence_source`.
- Every strong / medium / weak / counter evidence item carries `source_quality`.
- `model_inference` is hypothesis only, not raw evidence.
- `manual_input` alone cannot support a strong conclusion.
- Over-window login-log `no_data` is a freshness/window gap, not counter evidence.
- Partial or blocked source exposes `permission_status` and downgrades conclusion confidence.

## 2. Execution Boundary

- real_platform_called: false
- dataagent_called: false
- release_package_updated: false
- outputs_dist_updated: false
- sensitive_plaintext_output: false
- test_type: text_regression

## 3. Source Metadata Contract Under Test

Each evidence item must include:

- evidence_source:
  - source_name
  - source_type
  - source_tool_or_hand
  - source_platform
  - collected_at
  - evidence_time_range
  - raw_reference
- source_quality:
  - freshness_status
  - freshness_risk
  - permission_status
  - reliability_level

Allowed `source_type` values stay aligned with batch evidence source metadata:

- internal_platform_api
- browser_dom_read
- screenshot_manual_read
- dataagent_hive
- manual_input
- model_inference
- historical_doc

## 4. Regression Cases

### Case 1: Single ATO High-suspicion Case With Multi-source Evidence

- case_id: single_src_case_001
- input_summary: A single account shows short-interval login-to-reset behavior, device mismatch, post-reset token activity, and risk-control kick.
- expected_behavior:
  - Can output medium-strong or strong ATO support.
  - Each evidence item must show source and quality metadata.
  - Device relation remains supporting evidence, not a standalone conclusion.
- simulated_output_summary:
  - strong_evidence: login-to-reset chain observed from login log and reset event source.
  - medium_evidence: device mismatch and post-reset token activity observed from device and strategy sources.
  - weak_evidence: user claim and manual note treated as context only.
  - missing_evidence: publish audit or offline Hive not available in this text run.
- source_trace_check:
  - evidence_source_present: pass
  - source_quality_present: pass
  - raw_reference_safe: pass
  - source_types_used: internal_platform_api, browser_dom_read, manual_input
- result: pass

### Case 2: Manual-input Only Case

- case_id: single_src_case_002
- input_summary: User says the account was not operated by them, but no platform/API/Hive evidence is present.
- expected_behavior:
  - Must not output strong conclusion.
  - Should mark as clue / needs evidence.
  - `manual_input` can explain user claim but cannot be raw platform evidence.
- simulated_output_summary:
  - weak_evidence: user claim from manual_input.
  - missing_evidence: login log, device evidence, reset/publish audit, token usage.
  - conclusion_support: insufficient_support
- source_trace_check:
  - manual_input_visible: pass
  - strong_conclusion_blocked: pass
  - missing_evidence_visible: pass
- result: pass

### Case 3: Model-inference Only Case

- case_id: single_src_case_003
- input_summary: Model infers possible ATO from a text pattern, but no raw evidence source exists.
- expected_behavior:
  - `model_inference` is hypothesis only.
  - Must not be counted as raw evidence.
  - Must not support a strong conclusion.
- simulated_output_summary:
  - hypothesis: token/OAuth misuse or new-device takeover may be possible.
  - raw_evidence: none
  - conclusion_support: hypothesis_only
- source_trace_check:
  - model_inference_not_raw_evidence: pass
  - strong_conclusion_blocked: pass
  - next_step_requires_source_backfill: pass
- result: pass

### Case 4: Login-log Over-window no_data Case

- case_id: single_src_case_004
- input_summary: Suspicious event happened outside the reliable online login-log window; online query returns no_data.
- expected_behavior:
  - Mark `login_log_window_incomplete` and `offline_hive_required`.
  - `no_data` is not counter evidence.
  - Do not infer "no login" or "log cleaned".
- simulated_output_summary:
  - freshness_risk: over_reliable_window
  - evidence_interpretation: data_gap
  - counter_evidence: none from over-window no_data
  - missing_evidence: offline Hive login log or historical audit
- source_trace_check:
  - freshness_status_visible: pass
  - freshness_risk_visible: pass
  - no_data_not_counter_evidence: pass
  - offline_hive_required_visible: pass
- result: pass

### Case 5: Partial / Blocked Source Case

- case_id: single_src_case_005
- input_summary: Archives source is available, strategy source is permission blocked, device source returns partial relation only.
- expected_behavior:
  - `permission_status` must be visible on blocked or partial source.
  - Conclusion must be downgraded.
  - Device relation remains candidate relation, not final risk conclusion.
- simulated_output_summary:
  - medium_evidence: profile and partial device relation observed.
  - blocked_source: strategy_hit_read permission_blocked.
  - missing_evidence: request-level strategy details and complete device graph.
  - conclusion_support: partial_support
- source_trace_check:
  - permission_status_visible: pass
  - partial_source_visible: pass
  - conclusion_downgraded: pass
  - device_relation_not_direct_conclusion: pass
- result: pass

## 5. Regression Result

- total_cases: 5
- pass: 5
- partial: 0
- fail: 0
- evidence_source_missing: false
- source_quality_missing: false
- strong_conclusion_misused_weak_source: false
- model_inference_used_as_raw_evidence: false
- manual_input_used_as_strong_source: false
- over_window_no_data_used_as_counter_evidence: false
- blocked_source_without_permission_status: false

## 6. Conclusion

pass

Single-case evidence card metadata is aligned with the ATO batch evidence source schema at the text-contract level. The regression confirms that weak or inferred sources do not support strong conclusions, and stale/window-incomplete or blocked sources remain visible as quality risks instead of being hidden inside narrative text.
