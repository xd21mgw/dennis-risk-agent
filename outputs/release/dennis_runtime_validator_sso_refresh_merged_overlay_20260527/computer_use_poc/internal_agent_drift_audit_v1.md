# Dennis Risk Agent Internal Agent Drift Audit v1

This audit records recurring execution drift risks and turns them into local validators, regression cases, and smoke tests. It is an offline guardrail: it does not access real platforms, call DataAgent, change gateway / safeBins / tools, or prove live authentication.

## 1. Routing Drift

Manifestation:
- Single-user account security / ATO questions may fall back to methodology instead of `single_entity_execution_mode`.
- 2-9 `user_id` complaint batches may be treated as pure plan mode or as large batch clustering.
- Methodology / strategy design questions may incorrectly trigger platform execution.

Risk:
- Real cases receive empty analysis, or method questions spend platform budget and risk unsafe calls.

Detection:
- Runtime validation cases for `single_entity_execution_mode`, `small_batch_execution_with_checkpoint`, and methodology `plan_mode`.
- `runtime_preflight_check.py` checks routing guard markers.

Fix:
- Keep `DENNIS_ROUTING_GUARD_V1` and route names canonical.
- Use `multi_entry_runtime_guard_v1.md` as the route boundary source.

## 2. Source Orchestration Drift

Manifestation:
- `user_login_unified_log` returns `no_data` and the agent stops.
- Source plan or source completion matrix is omitted.
- Required P0 sources are skipped.

Risk:
- Single-source no-data becomes an implicit low-risk judgement.

Detection:
- `source_orchestration_plan_v1.yaml` defines required P0 sources and stop conditions.
- `source_orchestration_check.py` fails login-log-only matrices and missing source completion matrices.

Fix:
- Require `user_login_unified_log`, `weapon_user_to_device_graph`, and `weapon_device_risk`.
- Conditional sources must be marked checked / blocked / auth_failed / timeout / not_checked rather than silently omitted.

## 3. Platform Path Drift

Manifestation:
- Weapon uses `/api/graphData` or frontend paths instead of `/apiv2/graphData`.
- `riskData` receives userId or malformed parameters.
- product / productName / groupKey / dimKey are guessed or omitted.

Risk:
- The agent queries the wrong endpoint and mislabels path errors as no_data.

Detection:
- `source_orchestration_check.py` validates `/apiv2/graphData`, `/apiv2/riskData`, `product=KUAISHOU`, `productName=KUAISHOU`, `groupKey=USER_ID`, `dimKey=DEVICE_ID`, and `deviceIds=`.

Fix:
- Fail closed on path drift.
- Record `/apiv2/*` auth_failed / blocked / timeout in `source_quality`; do not freely explore unverified paths.

## 4. Auth / Session Drift

Manifestation:
- Runtime checks cookie-state file existence but not HTTP 200 + JSON.
- `auth_failed` does not trigger controlled refresh + retry.
- Refresh failure is returned as no_data.

Risk:
- Authentication errors are confused with risk absence.

Detection:
- Runner preflight checks `auth_refresh_attempted`, `retry_after_refresh`, and `source_status_before_refresh`.
- Source validator flags completed entries with non-200 `http_status` or non-JSON `response_type` when those fields are present.

Fix:
- Completed source requires structured response evidence.
- Auth failures remain `auth_failed` / `blocked`; never no_data.

## 5. Tool Boundary Drift

Manifestation:
- Main agent directly queries platforms after dennis-risk-agent timeout.
- dennis-risk-agent tries to write ad hoc scripts.
- curl + cookie injection appears as a fallback.

Risk:
- Runtime bypasses safeBins / tools.deny and leaks auth material.

Detection:
- Source validator rejects `access_method` values: `curl_cookie`, `manual_cookie`, `main_agent_direct_exec`, `arbitrary_url`.
- Source validator rejects `write_edit_attempted=true`.

Fix:
- Use controlled wrappers and source orchestration only.
- Main agent records subagent timeout and returns partial / retry plan, not direct platform queries.

## 6. Evidence Semantic Drift

Manifestation:
- `no_data`, `timeout`, `blocked`, or `auth_failed` is treated as low-risk counter evidence.
- `source_gap` and `source_quality` are omitted.

Risk:
- The final conclusion overstates safety from incomplete evidence.

Detection:
- Source validator rejects `low_risk`, `no_risk`, `risk_excluded`, or `ato_excluded` when all sources are no_data / blocked / auth_failed / timeout / parse_error.
- Smoke tests require source quality.

Fix:
- Use partial evidence cards and conclusion states such as `insufficient_support`.

## 7. Stale Data Drift

Manifestation:
- Historical observations or cached data are presented as "no cache" realtime results.
- `collected_at`, `evidence_time_range`, or `source_provenance` is missing.

Risk:
- Old evidence is treated as live source output.

Detection:
- Source plan requires `collected_at`, `evidence_time_range`, and `source_provenance`.
- Source validator rejects cached / historical provenance when `--no-cache` is set.

Fix:
- Every source checkpoint must include collection time, evidence window, and provenance.

## 8. Capability Status Drift

Manifestation:
- `api_direct_confirmed` is treated as completed without executable endpoint verification.
- track-analysis endpoint is unverified but marked completed.
- `partial_api_direct` or `pending_api_direct_confirmation` is upgraded by wording.

Risk:
- The agent claims evidence that was not actually collected.

Detection:
- Source validator rejects `track_analysis_if_endpoint_verified` with `source_status=completed` unless `endpoint_verified=true`.

Fix:
- Contract status and execution status are separate.
- Unverified executable endpoint means `pending_api_direct_confirmation` / `source_gap`.

## 9. Source Plan Not Executed

Manifestation:
- The agent outputs a source plan, but `executed_sources` / `source_completion_matrix` does not match planned required sources.
- Example: the plan contains Weapon graph/risk sources, but runtime only executes login log.

Risk:
- The answer looks planned and complete while required evidence was never attempted.

Detection:
- Compare planned required sources with `source_completion_matrix`.
- Required sources must appear with a real status or an explicit `blocked`, `auth_failed`, `not_checked`, `missing_required_fields`, `timeout`, or `parse_error` explanation.

Fix:
- Fail validation with `source_plan_not_executed` if planned required sources are missing without explanation.

## 10. Source Status Mismatch

Manifestation:
- A source is marked `completed` without a real request.
- HTTP 302 / HTML login page is written as `no_data`.
- File-level or contract-level validation is described as live execution.

Risk:
- Authentication or environment failures become false evidence.

Detection:
- `completed` requires `real_platform_request_executed=true`, `http_status=200`, `response_type=json`, and an execution observation id.
- `no_data` requires `http_status=200`, `response_type=json`, and `records_count=0`.
- `auth_failed` must map to 302 / login page / access proxy redirect.

Fix:
- Fail validation with `source_status_mismatch`; keep auth / parse / blocked separate from no_data.

## 11. Cross Source Entity Misuse

Manifestation:
- A device id from track-analysis / Archives is used for Weapon riskData, but the answer implies Weapon graphData resolved it.

Risk:
- Entity provenance is lost and downstream device risk appears stronger than it is.

Detection:
- If `device_id_source` is not Weapon graphData, require `cross_source_device_id=true`.
- If Weapon graphData returned zero edges and downstream riskData uses a device id, require `weapon_graphData_empty=true`.

Fix:
- Mark cross-source device provenance explicitly and keep relation strength separate.

## 12. Capability Registry Overtrust

Manifestation:
- `capability_registry.md` says `api_direct_confirmed`, and runtime marks a source `completed` without current execution observation.

Risk:
- Capability availability is confused with evidence collection.

Detection:
- `completed` requires current execution observation metadata.

Fix:
- `api_direct_confirmed` means executable capability, not source completion.

## 13. Environment Issue As Platform Gap

Manifestation:
- Sandbox missing browser, expired SSO ticket, missing node/macOS capability, or tool absence is written as platform unavailable.

Risk:
- A local runtime issue is mistaken for platform evidence.

Detection:
- `source_gap_type` must distinguish `platform_gap`, `environment_gap`, `auth_gap`, `tool_gap`, and generic `source_gap`.
- Environment/tool/auth markers cannot be labelled as `platform_gap`.

Fix:
- Label environment and tool failures precisely; do not conclude platform unavailability.

## 14. Manual Exploration Creep

Manifestation:
- Normal risk execution tries unverified URLs such as `/api/profile`, `/rest/profile`, or `/api/user/profile`.

Risk:
- Endpoint discovery leaks into routine case handling and creates inconsistent path usage.

Detection:
- `unapproved_endpoint_attempts` is forbidden outside explicit `endpoint_discovery`.
- Endpoints not in playbook / contract / source plan fail validation during normal execution.

Fix:
- Use registered endpoints only; endpoint discovery must be a separate explicit task.

## 15. Summary Overclaim Drift

Manifestation:
- Evidence card says `needs_more_evidence` / partial, but the one-line summary says low risk, no risk, or tends to exclude ATO.

Risk:
- Human readers follow the stronger summary and ignore evidence limitations.

Detection:
- `final_summary_conclusion` must match `evidence_card.conclusion_state`.
- Incomplete source matrices cannot support `low_risk`, `no_risk`, or `data_against_ato_suspicion`.

Fix:
- Use `insufficient_support` / partial conclusion until source coverage is complete.

## 16. Overlay Manifest Path Drift

Manifestation:
- The release / overlay manifest path differs from the live fallback path, but fallback is not recorded.

Risk:
- Runtime reads different files than reviewers expect.

Detection:
- If `actual_path != manifest_path`, require `fallback_path_used=true`, `fallback_reason`, and `runtime_readable=true`.

Fix:
- Treat this as a warning first, not a critical blocker, but make fallback explicit.

## Offline Validation Assets

- `source_orchestration_plan_v1.yaml`
- `source_orchestration_check.py`
- `runtime_preflight_check.py`
- `runtime_validation_cases_v1.yaml`
- `smoke_tests.md`

These assets catch drift before live overlay, but they do not replace live auth validation.
