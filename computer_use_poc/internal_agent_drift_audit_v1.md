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

## Offline Validation Assets

- `source_orchestration_plan_v1.yaml`
- `source_orchestration_check.py`
- `runtime_preflight_check.py`
- `runtime_validation_cases_v1.yaml`
- `smoke_tests.md`

These assets catch drift before live overlay, but they do not replace live auth validation.
