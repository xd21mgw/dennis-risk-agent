# ATO Small Batch Auth Bridge Source Boundary Unified Patch v1

## Run Scope

This run consolidates the recent ATO execution fixes into one local mother-body patch:

- single ATO execution source checkpoint and partial fallback
- 2-9 user ATO complaint small-batch execution with checkpoint
- unified login log authentication bridge boundary
- online login log reliable-window and APP-login-only source boundary
- routing metadata source quality fields for partial evidence output

This run is local documentation, routing, template, regression, and smoke-test closure only.

## Boundaries

- Did not access real internal platforms.
- Did not call DataAgent.
- Did not modify auth state or gateway config.
- Did not execute real platform queries.
- Did not update release packages or outputs/dist.
- Did not modify live workspace overlay.
- Did not commit git changes.
- Did not output cookie, token, session, header, API key, phone number, identity number, or raw platform response.

## Modified Areas

- `AGENTS.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/user_login_log_api_readonly_internal_agent_playbook_v2_4_10.md`
- `computer_use_poc/browser_auth_preflight_checklist_v2_4_9.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/runtime_integration_validation_checklist_v1.md`
- `computer_use_poc/smoke_tests.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/account_security_runtime_summary_v1.md`

## Single ATO Execution Closure

For a single explicit ATO user query:

- route remains `ato_case_analysis` / `account_security_expert_mode`
- execution mode remains `single_entity_execution_mode`
- readonly platform observation is allowed
- DataAgent is not called by default
- every source must write a source checkpoint as soon as it completes or fails
- completed source evidence must survive later source timeout or auth failure
- if any source times out, blocks, fails auth, or has parse error, the agent must output a partial evidence card instead of a naked timeout

Required source checkpoint fields:

- `user_id`
- `source_name`
- `source_type`
- `source_status`
- `evidence_summary`
- `evidence_time_range`
- `source_quality`
- `raw_reference_safe_id`
- `collected_at`
- `failure_reason`
- `next_source_decision`

Required failure statuses:

- `completed`
- `no_data`
- `blocked`
- `auth_failed`
- `timeout`
- `parse_error`
- `skipped`

## Overall Deadline Rule

- single ATO execution default budget: 180 seconds
- if any P0/P1 source is completed, the 120s / 150s checkpoint must stop expansion into slow P2 browser sources and start partial evidence generation
- P2 browser sources must not block P0/P1 completed evidence output
- near timeout, the final answer must include partial evidence card, source quality, missing evidence, next action, and routing metadata

## Source Priority

P0 sources:

- unified login log
- Weapon `riskData` / `graphData`
- Tianshi strategy hit summary

P1 sources:

- archives profile
- track-analysis stats-first
- device SDK risk labels

P2 sources:

- RCP browser
- archives browser recoverable preflight
- track-analysis SPA details

P0 completion is sufficient for a minimum partial evidence card. P2 browser sources are not part of the default small-batch path.

## Small Batch ATO Closure

For 2-9 user ATO complaint checks:

- mode is `small_batch_execution_with_checkpoint`
- not pure plan-only
- not large-batch clustering
- per-user P0 source execution is allowed
- unified login log is the first P0 source
- P1 sources are only added for anomalous or high-value users
- P2 browser sources are excluded by default
- each user/source has an independent checkpoint
- one user/source auth failure or timeout must not collapse the whole batch

Small-batch output must include:

- `batch_id`
- `user_count`
- `execution_mode: small_batch_execution_with_checkpoint`
- `per_user_evidence_card`
- `per_user_source_status`
- `completed_users`
- `blocked_users`
- `timeout_users`
- `users_with_login_log_window_gap`
- `users_with_app_login_only_source_gap`
- `high_suspicion_users`
- `insufficient_support_users`
- `missing_evidence_by_user`
- `batch_summary`
- `next_action`

## Unified Login Auth Bridge Boundary

Bad case: `BC-AUTH-BRIDGE-UNIFIED-LOGIN-001`.

Rules:

- main agent must not take over platform querying after dennis-risk-agent timeout by running ad hoc `sso_session.py`, curl with cookie, agent-browser state load, or same-origin fetch
- main agent records `subagent_timeout`, `auth_session_issue`, or `source_timeout`, then returns partial/retry plan or respawns the controlled sub-agent path
- unified login log readonly queries must go through a controlled wrapper / Dennis source orchestration
- SSO state exists does not mean API direct read is available
- `sso_session.py` means auth injection capability, not stable API data return
- curl + cookie returning 302 must be `auth_session_issue` / `redirect_to_sso_or_access_proxy`
- browser fetch must be same-origin
- profile lock / SingletonLock must be `profile_lock`
- `auth_failed`, redirect, same-origin error, and profile lock all go into `source_quality`
- these failures are not `no_data` and not risk counter-evidence

## Login Log Source Boundary

- unified login log online API has an approximately 7-day reliable window
- admin / user-center-workbench mainly covers APP login, refresh token, and password verification behavior
- when complaint time is outside the online window, output `login_log_window_incomplete` and `source_time_range_gap`
- APP login no_data, single DID, or stable IP can only support `app_login_visible_window_no_strong_anomaly`
- do not output "low risk", "no risk", or "ATO excluded" from APP login source alone
- scan/OAuth, ground promotion fraud, unfamiliar link inducement, violation posting, and friend deletion complaints need `app_login_only_source_gap`
- expected missing sources include `missing_oauth_or_scan_chain`, `missing_publish_audit`, `missing_device_sdk`, and `missing_strategy_hit`

## Routing Metadata

Related answers must emit standard YAML `routing_metadata` with:

- registered `route`
- registered `capability`
- registered `sub_capability` or `null`
- `execution_mode`
- `evidence_mode`
- `platform_called`
- `dataagent_called=false`
- `direct_tool_bypass=false`
- `sensitive_output=false`
- `redaction_applied=true`
- `boundary_flags`
- `source_quality`
- `partial_reason`
- `final_status`

Relevant execution modes:

- `single_entity_execution_mode`
- `small_batch_execution_with_checkpoint`
- `batch_clustering_mode`
- `plan_mode`
- `expert_mode`
- `denied`

## Regression Coverage

Added or strengthened:

- `SINGLE-ATO-SOURCE-CHECKPOINT-001`
- `SINGLE-ATO-OVERALL-DEADLINE-001`
- `AUTH-BRIDGE-LOGINLOG-001`
- `SMALL-BATCH-ATO-AUTH-FALLBACK-001`
- `SMALL-BATCH-LOGIN-WINDOW-BOUNDARY-001`
- `APP-LOGIN-ONLY-SOURCE-GAP-001`

## Current Status

No production runtime hook was changed in this run. The patch is ready for local review and later overlay / runtime validation.
