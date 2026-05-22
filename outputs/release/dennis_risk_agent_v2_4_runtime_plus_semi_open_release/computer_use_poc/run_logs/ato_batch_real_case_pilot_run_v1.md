# ATO Batch Real-case Pilot Run v1

## 1. Pilot Goal

Validate whether Dennis Agent can process 7 real / historical ATO pilot cases in batch observation form and correctly identify:

- evidence source coverage
- online login-log reliable-window gaps
- source gaps and permission gaps
- offline Hive / DataAgent needs
- semi-open runtime boundaries

This run does not attempt to produce final ATO conclusions. It only validates readonly observation quality and whether the evidence source framework can expose missing evidence, stale evidence, partial source coverage, and offline follow-up needs.

## 2. Source Status

- input_material: `ato_pilot_batch_observation.md`
- local_file_found_in_repo: false
- run_log_basis: user-provided pilot observation summary
- case_count: 7
- positive_cases: 5
- counter_or_weak_cases: 2
- real_platform_called_by_codex: false
- dataagent_called_by_codex: false
- release_or_outputs_dist_modified: false

Because the source material is not present in this workspace, this run log uses safe references and does not invent raw user IDs, raw IPs, raw device IDs, tokens, headers, or platform payloads.

## 3. Input Case Overview

| case_id | user_id | event_time | abnormal_action | pilot_type |
|---|---|---|---|---|
| pos_001 | user_ref_pos_001 | historical_over_window | suspected account takeover with available partial event-time login trace | positive |
| pos_002 | user_ref_pos_002 | historical_over_window | suspected account takeover / abnormal post-login action | positive |
| pos_003 | user_ref_pos_003 | historical_over_window | suspected account takeover / abnormal publish or profile action | positive |
| pos_004 | user_ref_pos_004 | historical_over_window | suspected account takeover / abnormal account control action | positive |
| pos_005 | user_ref_pos_005 | historical_over_window | suspected account takeover / abnormal downstream behavior | positive |
| weak_001 | user_ref_weak_001 | historical_over_window | weak or counter example with insufficient online evidence | counter_or_weak |
| weak_002 | user_ref_weak_002 | historical_over_window | weak or counter example with insufficient online evidence | counter_or_weak |

## 4. Observation Source Coverage Summary

| source | coverage | result | interpretation |
|---|---:|---|---|
| Unified login log | 7/7 | All cases exceed the near-7-day online reliable window. `pos_001` has a small amount of event-time-window trace; most other cases are `totalCount=0` or metadata-only. | `login_log_window_incomplete`; online no_data / totalCount=0 is not counter evidence. |
| Weapon | 7/7 | API-direct OK, but nodes=0 / edges=0. | Low information density; empty graph is not counter evidence and does not mean no device risk. |
| Archives Center | 7/7 not_checked | Requires agent-browser recoverable_preflight. | Source gap, not no risk. |
| Tianshi / Strategy Platform | 7/7 not_checked | Requires browser same-origin fetch or strategy read path. | Source gap, not no strategy hit. |
| DataAgent / Hive | 0/7 | Not called. | Offline Hive needed for historical full-window evidence. |
| Write action | 0/7 | No write operation. | Readonly boundary preserved. |

## 5. Per-case Evidence Card Summary

### pos_001

- evidence_support_level: partial
- usable_evidence:
  - small amount of event-time-window login trace from online login log
  - historical ATO clue from pilot input
- weak_or_partial_evidence:
  - online login source is over reliable window for full-chain validation
  - Weapon API direct OK but empty graph
- missing_evidence:
  - Archives Center profile / audit context
  - Tianshi / strategy hit context
  - publish audit or account-control audit
  - token / OAuth / scan authorization chain
- source_quality_notes:
  - login_log: window_incomplete
  - Weapon: low_density_empty_graph
  - Archives / Tianshi: not_checked
- offline_hive_needed: true
- do_not_conclude: Do not produce final ATO conclusion from this partial online observation.

### pos_002

- evidence_support_level: source_gap
- usable_evidence:
  - pilot input indicates suspected ATO
- weak_or_partial_evidence:
  - online login log mostly totalCount=0 or metadata-only under over-window condition
  - Weapon nodes=0 / edges=0
- missing_evidence:
  - full historical login log around event_time
  - publish / security-operation audit
  - token / OAuth usage evidence
  - Archives and Tianshi sources
- source_quality_notes:
  - online_login_no_data: data_gap, not counter evidence
  - Weapon_empty_graph: not counter evidence
- offline_hive_needed: true
- do_not_conclude: Do not interpret online no_data as no abnormal login.

### pos_003

- evidence_support_level: source_gap
- usable_evidence:
  - pilot input indicates suspected abnormal post-login action
- weak_or_partial_evidence:
  - online API evidence is stale / incomplete
  - Weapon empty result has low evidentiary value
- missing_evidence:
  - historical login chain
  - post-login action audit
  - strategy / request-level decision evidence
  - Archives browser observation
- source_quality_notes:
  - source_coverage: insufficient for closure
  - permission_or_browser_preflight_gap: present
- offline_hive_needed: true
- do_not_conclude: Do not output final stolen-account support level.

### pos_004

- evidence_support_level: source_gap
- usable_evidence:
  - pilot input indicates possible account-control abnormality
- weak_or_partial_evidence:
  - online login window incomplete
  - online entity graph empty
- missing_evidence:
  - password reset / bind change / security operation audit
  - token revocation / stolen mark sequence
  - strategy hit or enforcement context
- source_quality_notes:
  - login_log_window_incomplete: true
  - source_gap: Archives and Tianshi not checked
- offline_hive_needed: true
- do_not_conclude: Treat as historical pilot requiring offline evidence backfill.

### pos_005

- evidence_support_level: source_gap
- usable_evidence:
  - pilot input indicates suspected ATO / abnormal downstream behavior
- weak_or_partial_evidence:
  - online evidence is insufficient
  - Weapon empty graph is not a risk-negative signal
- missing_evidence:
  - downstream behavior audit
  - full login / token / OAuth trace
  - Archives / Tianshi supporting sources
- source_quality_notes:
  - source_coverage: partial
  - online_window: incomplete
- offline_hive_needed: true
- do_not_conclude: Do not infer no ATO from online gaps.

### weak_001

- evidence_support_level: insufficient
- usable_evidence:
  - weak / counter pilot label
- weak_or_partial_evidence:
  - no complete source-backed ATO chain
  - online no_data is not counter evidence, only data gap
- missing_evidence:
  - full historical login
  - account-control audit
  - user/device continuity evidence
  - source-backed counter evidence
- source_quality_notes:
  - manual or historical input cannot be treated as strong counter evidence
- offline_hive_needed: true
- do_not_conclude: Do not call this a clean counterexample without offline evidence.

### weak_002

- evidence_support_level: insufficient
- usable_evidence:
  - weak / counter pilot label
- weak_or_partial_evidence:
  - incomplete online data
  - not_checked sources remain gaps
- missing_evidence:
  - offline login logs
  - publish / live / tool operation audit if relevant
  - strategy and enforcement timeline
- source_quality_notes:
  - source_gap: true
  - window_gap: true
- offline_hive_needed: true
- do_not_conclude: Do not produce final non-ATO conclusion.

## 6. Batch-level Pattern Summary

Commonality 1: historical cases generally exceed the online login-log reliable window.

Commonality 2: online APIs provide only partial evidence for old ATO cases.

Commonality 3: publish audit, scan / OAuth authorization, token chain, and ban reasons require offline Hive / DataAgent or equivalent offline log backfill.

Commonality 4: Weapon empty graph cannot be used as counter evidence.

Commonality 5: browser observation still needs a focused single-case smoke test before being treated as stable pilot execution.

## 7. Source Gap / Window Gap Conclusion

The main value of this pilot is not the number of strong ATO conclusions. The value is that Dennis Agent can identify source gaps and window gaps without overclaiming.

This validates why the pilot checklist is necessary. Before real historical cases enter batch analysis, the workflow must check:

- event_time
- reliable login-log window
- source coverage
- browser recoverable_preflight need
- offline Hive / DataAgent need
- permission/source gaps

## 8. Offline Hive / DataAgent Query Plan

These are query questions only. This run did not call DataAgent or Hive.

### Full Login Logs

- For each case, query event_time +/- 3 days and event_time +/- 7 days.
- Extract login success/failure, login type, IP / device / UA / appVersion, token lifecycle, and device switch behavior.

### Publish Audit Logs

- Query publish-related interfaces around event_time.
- Extract publish source, IP subnet, did/device reference, token source, user agent, and publish result.

### Scan / OAuth Authorization Chain

- Query scan login, OAuth authorization, third-party authorization, and authorization scope changes around event_time.
- Identify abnormal app / token source / authorization scope.

### Token Creation / Usage / Cross-device Chain

- Query token creation, refresh, switchUser, token reuse, expireAllTokens, and cross-device authentication failures.
- Identify token reuse across device or IP clusters.

### Ban Reason and Ban Timeline

- Query ban reason, enforcement timeline, stolen mark, token revoke, and risk-control kick events.
- Align enforcement with abnormal action timeline.

### Live Source / Live Companion / Tool-side Operation Logs

- For live-related cases, query live start source, Live Companion, tool-side operation logs, and cross-device live control signals.

## 9. Next Step Recommendation

- Do not continue checking all 7 cases online.
- Select only `pos_001` for agent-browser Archives Center + Tianshi smoke test.
- Move the remaining cases into offline Hive query planning.
- For future semi-open pilots, prefer fresh cases whose `event_time` is within the online reliable window.

## 10. Safety and Boundary

- readonly_only: true
- platform_write_action: false
- dataagent_called: false
- hive_called: false
- release_updated: false
- outputs_dist_updated: false
- credential_plaintext_output: false
- cookie_token_session_header_output: false
- raw_reference_policy: safe_ref only

No partial observation in this run log should be read as a final ATO conclusion.
