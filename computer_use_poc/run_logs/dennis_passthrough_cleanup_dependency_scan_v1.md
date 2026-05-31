# Dennis Passthrough Cleanup Dependency Scan V1

## 1. Scope

This is a read-only dependency scan after the Dennis passthrough default-path controlled smoke.

- Dennis repo: `/Users/pengcheng/dennis-risk-agent`
- Browser-backed service repo: `/Users/pengcheng/dennis-local/browser-backed-api-poc`
- Dennis HEAD: `96d6ca90bb5e00437140970809a79f910952d356`
- Service HEAD observed during scan: `13991c6f7ac3f7b1f388b7485b97204356197f92`
- No real platform access.
- No browser-backed service startup.
- No DataAgent / Hive call.
- No code deletion.
- No direct `outputs/full_runtime` modification.

## 2. Scanned Paths

Dennis focused paths:

- `computer_use_poc/browser_backed_service_client.py`
- `computer_use_poc/browser_backed_service_adapter_v1.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/runtime_required_file_manifest_v1.yaml`
- `computer_use_poc/run_logs/*passthrough*`

Service focused paths:

- `src/actions.js`
- `src/service.js`
- `src/quality.js`
- `src/browser.js`
- `test/mock.test.js`
- `README.md`
- `ACTION_REGISTRY.md`
- `BROWSER_BACKED_AGENT_SKILL.md`
- `PASSTHROUGH_SERVICE_CONTRACT.md`
- `TEAM_HANDOFF_CHECKLIST.md`

## 3. Scan Counts

Dennis focused scan:

| pattern group | observed count |
| --- | ---: |
| `compat_summary` | 15 |
| `allow_compat_fallback` | 8 |
| `source_card` in focused paths | 342 |
| `source_quality` in focused paths | 514 |
| `normalized_observation` in focused paths | 100 |
| `response_mode` in focused paths | 75 |
| `passthrough` in focused paths | 206 |

Service focused scan:

| pattern | observed count |
| --- | ---: |
| `compat_summary` | 68 |
| `source_card` | 78 |
| `source_quality` | 72 |
| `response_mode` | 67 |
| combined cleanup regex across focused paths | 969 |

These counts are inventory signals, not deletion counts. Most Dennis `source_quality` references are Dennis-owned evidence quality semantics and must remain.

## 4. Dennis Compat Summary Dependencies

### Active executable dependencies

- `computer_use_poc/browser_backed_service_client.py`
  - `RESPONSE_MODE_COMPAT_SUMMARY` remains defined.
  - `BrowserBackedServiceClient.call_action()` defaults to `compat_summary` for direct legacy single-action calls.
  - `call_account_security_sources()` defaults to `ACCOUNT_SECURITY_DEFAULT_RESPONSE_MODE=passthrough`.
  - `allow_compat_fallback=false` by default.
  - Compatibility fallback only executes when `allow_compat_fallback=true` and the passthrough result has a fallback-trigger status.
  - `normalize_service_response()` still parses legacy service responses containing `source_card`, `source_quality`, and `data.response_summary`.

### Test and fixture dependencies

- `computer_use_poc/browser_backed_service_client.py --self-test`
  - Keeps `compat_summary_fixture_not_regressed`.
  - Keeps `compat_summary_fallback_requires_explicit_allow_flag`.
  - Several legacy action fixture tests still expect `source_card` and `source_quality`.

### Documentation dependencies

- `computer_use_poc/browser_backed_service_adapter_v1.md`
  - States passthrough is the target main chain.
  - States `compat_summary` is legacy fallback only.
  - Still documents legacy `source_card/source_quality` response shape for migration context.
- `computer_use_poc/answer_experience_templates.md`
  - States account-security four-source main chain requests `response_mode=passthrough`.
  - States service-side summary/source-card/source-quality logic should be removed after deletion gates pass.
- `computer_use_poc/smoke_tests.md`
  - Keeps regression cases for passthrough default, no silent fallback, and explicit legacy fallback.
- Passthrough run logs keep historical dual-run and controlled-smoke evidence.

## 5. Default Chain Dependency Check

No default Dennis account-security chain dependency on `compat_summary` was found.

Current default path:

- `call_account_security_sources()` default: `response_mode=passthrough`
- Four-source account-security path:
  - `track_analysis_summary`
  - `login_logs_search`
  - `weapon_inventory`
  - `rcp_snapshot`
- Evidence card consumes `normalized_observation` first where available.
- `compat_summary_used_by_default=false` in the latest controlled smoke.

Important caveat:

- `call_action()` still defaults to `compat_summary` for generic single-action calls. This is legacy-safe behavior, but it is a cleanup dependency if the service removes `compat_summary` globally.

## 6. Fallback Dependency List

Fallback still exists only for explicit migration use:

- `allow_compat_fallback=true` in `call_account_security_sources()`.
- Direct caller can explicitly pass `response_mode=compat_summary`.
- 7-day login-log parse fallback to 24h exists only when running the legacy `compat_summary` path.
- Legacy fixture payloads still model `source_card/source_quality`.

No silent fallback was observed in code or controlled smoke.

## 7. Full Runtime Dependency Situation

- `full_runtime` is built from the mother repo via `runtime_snapshot_builder.py`.
- The latest controlled pilot passed under `outputs/full_runtime`.
- `outputs/full_runtime` inherits the same client behavior:
  - default account-security path is explicit passthrough;
  - legacy fallback code remains present;
  - `compat_summary` is not used by default.
- `outputs/full_runtime` should not be manually edited or committed during cleanup.

Before service-side summary deletion, rebuild `full_runtime` and rerun the controlled pilot after Dennis removes or gates all explicit service-summary assumptions.

## 8. What Dennis Must Complete Before Service Summary Deletion

Required before browser-backed service Phase C deletion:

1. Change generic `call_action()` default to `passthrough` or require an explicit mode for any legacy compatibility call.
2. Remove or quarantine `normalize_service_response()` from the main execution path.
3. Update self-tests so the default path for every service action expected in Dennis is passthrough.
4. Keep a small archived legacy fixture test only if needed for rollback documentation, not as a main-chain requirement.
5. Add or confirm passthrough parsers/generic normalizers for all dual-mode service actions Dennis may call:
   - first four account-security actions are already covered;
   - Archives/RCP drill-down/Track readiness still need parser coverage or a generic passthrough fixed-shape normalizer before service summary is removed.
6. Rebuild `full_runtime`.
7. Run controlled pilot again and confirm:
   - `compat_summary_used_by_default=false`
   - `allow_compat_fallback` not needed for pass
   - no `source_card` requirement in default source results
   - `normalized_observation` exists or failure is represented in Dennis-owned `source_quality`.

## 9. Can Service Cleanup Start?

Conclusion: service cleanup can enter Phase A now, but should not immediately delete summary code.

Recommended status:

- `service_cleanup_phase_a_ready=true`
- `service_summary_deletion_phase_c_ready=false`

Reasoning:

- The first four-source passthrough main chain passed in Dennis mother and `full_runtime`.
- Dennis default path does not use `compat_summary`.
- But Dennis still keeps explicit fallback and several non-main-chain fixture/contract paths that expect service-side `source_card/source_quality`.
- Some dual-mode actions outside the four-source main chain still need passthrough parser or generic normalizer readiness before service summary can be removed.

## 10. Recommended Dennis Follow-up

Phase A:

- Mark `compat_summary` as deprecated in Dennis docs and tests.
- Keep explicit fallback for one more controlled pilot window.

Phase B:

- Make generic `call_action()` default explicit passthrough or require callers to pass mode.
- Convert remaining browser-backed action tests from `source_card/source_quality` fixture expectations to `normalized_observation` expectations.
- Rebuild `full_runtime` and rerun controlled pilot.

Phase C:

- Remove service-summary assumptions from Dennis main tests.
- Keep only historical run logs and rollback notes.

Phase D:

- After service-side deletion, run:
  - Dennis self-test
  - text dry-run/demo if affected
  - `full_runtime` rebuild
  - controlled pilot
