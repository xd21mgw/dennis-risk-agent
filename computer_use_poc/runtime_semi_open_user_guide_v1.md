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

- cookie / token / session / storageState / auth header plaintext.
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
