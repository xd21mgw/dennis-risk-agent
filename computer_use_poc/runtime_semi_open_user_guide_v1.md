# Runtime Semi-open User Guide v1

## 1. What Is Supported

Dennis Risk Agent semi-open runtime currently supports:

- ATO single-case readonly analysis.
- ATO small-batch case summary.
- Evidence card generation.
- Source coverage summary.
- Missing evidence summary.
- Candidate strategy direction draft.
- Manual review boundary.

Outputs should include conclusion level, evidence strength, evidence source, `source_quality`, missing evidence, and next actions.

## 2. What Is Not Supported

The current semi-open runtime does not support:

- Automatic disposition.
- Automatic strategy launch.
- Large-scale automatic expansion.
- Sensitive plaintext output.
- Default automatic DataAgent / Hive call.
- Write actions.
- Release / runtime logic modification from chat.

DataAgent / Hive appears only as query plan unless an explicitly authorized offline workflow is started.

## 3. Recommended User Input Fields

For ATO single-case or batch analysis, users should provide:

- `user_id`
- `event_time`
- `abnormal_action`
- `device_id`, if available
- `user_claim`, if available
- `available_evidence`, if available
- source channel or case origin

If required fields are missing, Dennis should ask for clarification or produce a generic plan. It must not fabricate entities.

## 4. Historical Case Window Boundary

Online unified login logs are treated as reliable only for a near 7-day window.

For historical cases:

- mark `login_log_window_incomplete`.
- do not treat online no_data as counter evidence.
- generate offline Hive / DataAgent query plan if full historical reconstruction is needed.

## 5. Output Boundary

Expected output:

- layered conclusion, not a binary assertion.
- strong / medium / weak / counter / missing evidence.
- evidence source and source quality.
- manual review boundary.
- candidate strategy direction only.

Forbidden output:

- cookie / token / session / browser_storage_state_marker / auth header plaintext.
- automatic ban / unblock / throttle / allow decision.
- model inference treated as raw evidence.
- device relation treated as final cheating conclusion.

Browser-backed fixed actions v1 output boundary:

- ATO / login anomaly evidence uses explicit source plan:
  `login_logs_search -> archives_user_profile -> archives_user_analysis -> track_analysis_check_data_ready`.
- Abnormal publish / content handoff uses:
  `archives_photo_search -> archives_user_profile -> archives_user_analysis`.
- Account spread uses:
  `archives_related_users -> archives_user_profile/login_logs_search/track_analysis_check_data_ready`.
- RCP event attribution uses:
  `rcp_event_detail -> rcp_event_feature_list`.
- Policy-tree explanation uses:
  `rcp_policy_tree_lookup` only.
- Every such answer must preserve `source_plan`, `actions`, `source_quality_matrix`, `missing_evidence`, `evidence_strength`, and `final_answer_boundary`.
- Controlled parallel source plans must preserve per-item `source_id`, `action`, `execution_group`, `depends_on`, `timeout_class`, `failure_policy`, `source_priority`, and `expected_observation`.
- ATO uses `login_logs_search` + `archives_user_profile` + `track_analysis_check_data_ready` as `independent_parallel`, then `archives_photo_search` + `archives_user_analysis` as `auth_sensitive_serial` follow-up. RCP uses `rcp_event_detail -> rcp_event_feature_list` as dependency-aware serial; large feature/user-analysis responses use `large_response_serial`.
- ATO single-case naked questions must collect realtime P0 sources first, then derive suspicious anchors, extract candidate control endpoint fields, and run `device_identity_consistency`; Track checkDataReady is P0 auxiliary for front/backend activity alignment, while Weapon / RCP remain conditional support sources.
- `response_too_large` from `login_logs_search` is `source_contract_gap`, not login evidence and not proof of high login volume. If UI no_data conflicts with wrapper large response, mark `wrapper_response_mismatch` and `login_log_evidence_unusable`.
- `no_data`, `auth_failed`, `blocked`, `timeout`, `parse_error`, `partial_observation_available`, and `large_response_limited` are source-quality states, not low-risk or no-risk conclusions.
- Risk entity identifiers can appear in internal risk review when necessary; credential secrets and strict PII remain forbidden.

## 6. Entry-specific Guidance

KIM:

- concise response.
- Routing Summary first for mixed requests.
- long evidence tables should become summary + safe_ref / follow-up.

APP:

- may show structured cards for evidence card, query plan, and follow-up buttons.
- still obey plan / execution / fast_ack boundaries.

Web:

- may show longer reports, evidence tables, and exports.
- still obey field output classification and DataAgent boundaries.

## 7. L1-L4 Responsibility Split

Default responsibility split for Dennis field-fact and commonality workflow:

- `L1` / seed observation layer:
  - run registered primary sources from seed entity
  - collect first-hop business facts and candidate anchors
  - do not output final risk judgement or group conclusion

- `L2` / anchor drilldown layer:
  - drill down only with explicit anchors such as `device_id`, `photo_id`, `event_id`, `policy_code`, `comment_id`, `message_id`, `target_user_id`
  - expand raw detail rows from follow-up sources
  - keep `layer`, `parent_observation_id`, and `anchor_lineage`
  - do not turn single-source / single-entity clues into final commonality

- `L3` / unified commonality and candidate feature layer:
  - merge `raw_detail_flat_table` and `standard_detail_table` across L1/L2 sources
  - compare field-value commonality, field-combination commonality, sequence commonality, and cross-source support
  - output `standard_field_commonality`, `sequence_comparison_features`, `candidate_features`, `commonality_matrix`, and candidate-only `group_profile_candidate`
  - answer only “像不像本质候选”, not “已经证明高覆盖/高鲁棒/低误伤”

- `L4` / validation layer:
  - validate whether L3 candidate features are truly high-coverage, robust, and low false-positive
  - requires baseline, control samples, lift, false-positive evaluation, wider coverage, and stability checks
  - only here can wording upgrade from candidate-like to validated pattern

Hard boundaries:

- L1/L2 are for clue discovery, field acquisition, and bounded drilldown control.
- L3 is for unified comparison and candidate feature generation.
- L4 is for validation, not for first-time discovery.
- `source completed`, `field extracted`, and `coverage_commonality` are not by themselves risk essence.
