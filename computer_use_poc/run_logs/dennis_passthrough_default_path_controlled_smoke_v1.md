# Dennis Passthrough Default Path Controlled Smoke V1

## 1. Test Goal

- Validate that the Dennis browser-backed account-security main chain explicitly requests `response_mode=passthrough` by default.
- Validate that the current Dennis mother code can call the local browser-backed service, parse passthrough responses into `normalized_observation`, and generate an evidence card.
- Rebuild `outputs/full_runtime` from the mother repo and run the same controlled pilot there.
- Confirm that `compat_summary` is not used as the default path and remains only a legacy fallback.

## 2. Service Health

- Service endpoint: `http://127.0.0.1:8787`
- `ok=true`
- `service_mode=live`
- `auth-state category=ready`
- `action_count=19`
- Target origins ready:
  - Track Analysis: `ready`
  - Login Logs: `ready`
  - Weapon: `ready`
  - RCP: `ready`
- Credential material output observed: `false`

Only the local browser-backed service was called. No direct platform call, Chrome profile database read, cookie/token/session/header read, DataAgent call, or Hive call was performed.

## 3. Dennis Mother Controlled Smoke

Test case:

- `user_id=2871834924`
- Four sources:
  - `track_analysis_summary`
  - `login_logs_search`
  - `weapon_inventory`
  - `rcp_snapshot`

Result:

- `dennis_mother_passthrough_smoke_pass=true`
- `evidence_card_generated=true`
- `compat_summary_used_by_default=false`
- `raw_upstream_body_output=false`
- `sensitive_output=false`
- `dataagent_called=false`
- `final_risk_judgement_made=false`

Source completion matrix:

| bucket | sources |
| --- | --- |
| `completed_sources` | `track_analysis_summary`, `rcp_snapshot`, `weapon_inventory`, `login_logs_search` |
| `no_data_sources` | none |
| `blocked_sources` | none |
| `auth_failed_sources` | none |
| `timeout_sources` | none |
| `parse_error_sources` | none |
| `invalid_parameter_sources` | none |

Per-source result:

| source | source_status | response_mode | normalized_observation | key parser result |
| --- | --- | --- | --- | --- |
| `track_analysis_summary` | `completed` | `passthrough` | yes | `sub_interface=account_security_bundle`, completed `profile/getUseDuration/getDeviceIds/getLastestDateTime`, `device_ids_count=9` |
| `rcp_snapshot` | `completed` | `passthrough` | yes | `event_count=200`, raw event list suppressed |
| `weapon_inventory` | `completed` | `passthrough` | yes | `graph_status=completed`, `pointInfoMap_count=2`, `riskData_status=not_executed_missing_device_id` |
| `login_logs_search` | `completed` | `passthrough` | yes | `records_count=6`, raw records suppressed |

During the mother smoke, the Track account-security bundle merge path exposed a Dennis-side gap: per-subinterface parser output was present, but the merged bundle result did not keep a top-level `normalized_observation`. The mother client was fixed so the merged Track bundle preserves Dennis-owned `normalized_observation` without changing service behavior or falling back to `compat_summary`.

## 4. Full Runtime Rebuild

Command:

```bash
python3 computer_use_poc/runtime_snapshot_builder.py --mode full_runtime
```

Result:

- `full_runtime_build_pass=true`
- `status=created`
- `output_root=/Users/pengcheng/dennis-risk-agent/outputs/full_runtime`
- `missing_required=[]`
- Generated files include `AGENTS.md` and `RUNTIME_MANIFEST.md`
- `outputs/full_runtime` was generated only by the builder.
- `outputs/full_runtime` was not staged or submitted.

Validation under `outputs/full_runtime`:

- `py_compile` passed for `computer_use_poc/browser_backed_service_client.py`
- `browser_backed_service_client.py --self-test` passed
- `fixture_tests=84`
- No `.ks_sso`, `sso_session_runner.py`, `sso_session.py`, or cookie/token/session/header-named files were found in the generated runtime snapshot.

## 5. Full Runtime Controlled Pilot

Same test case:

- `user_id=2871834924`
- Same four sources
- Default explicit `response_mode=passthrough`

Result:

- `full_runtime_passthrough_smoke_pass=true`
- `evidence_card_generated=true`
- `compat_summary_used_by_default=false`
- `raw_upstream_body_output=false`
- `sensitive_output=false`
- `dataagent_called=false`
- `final_risk_judgement_made=false`

Source completion matrix:

| bucket | sources |
| --- | --- |
| `completed_sources` | `track_analysis_summary`, `rcp_snapshot`, `weapon_inventory`, `login_logs_search` |
| `no_data_sources` | none |
| `blocked_sources` | none |
| `auth_failed_sources` | none |
| `timeout_sources` | none |
| `parse_error_sources` | none |
| `invalid_parameter_sources` | none |

Per-source result:

| source | source_status | response_mode | normalized_observation | key parser result |
| --- | --- | --- | --- | --- |
| `track_analysis_summary` | `completed` | `passthrough` | yes | `sub_interface=account_security_bundle`, completed `profile/getUseDuration/getDeviceIds/getLastestDateTime`, `device_ids_count=9` |
| `rcp_snapshot` | `completed` | `passthrough` | yes | `event_count=200`, raw event list suppressed |
| `weapon_inventory` | `completed` | `passthrough` | yes | `graph_status=completed`, `pointInfoMap_count=2`, `riskData_status=not_executed_missing_device_id` |
| `login_logs_search` | `completed` | `passthrough` | yes | `records_count=6`, raw records suppressed |

Difference from mother smoke:

- No functional difference observed.
- Latency varied by source as expected for live local service calls.

## 6. Compatibility And Safety Checks

- Explicit default passthrough: `true`
- `compat_summary` default fallback used: `false`
- Silent fallback observed: `false`
- Raw upstream body output: `false`
- Raw login records output: `false`
- Raw Weapon `labelInfo` / `originalLog` output: `false`
- DataAgent / Hive called: `false`
- Final risk judgement made: `false`
- `no_data` / missing nested source state was not used as a low-risk or no-risk counter-signal.

`weapon_inventory` had `riskData_status=not_executed_missing_device_id`. This is a source-quality state from the Weapon chain, not a passthrough parser blocker. The graphData branch parsed successfully.

## 7. Conclusion

- `controlled_smoke_result=pass`
- Dennis mother passthrough default path passed.
- `full_runtime` rebuild passed.
- `full_runtime` controlled pilot passed.
- `compat_summary` remains available only as legacy migration fallback and was not used by default.
- No blocking issue remains for the first controlled smoke.

## 8. Next Step

- Start stabilizing Track / Login Logs default passthrough behavior under repeated controlled pilots.
- Mark `compat_summary` more clearly as deprecated legacy fallback after the next stable pilot window.
- Keep Weapon `riskData_status=not_executed_missing_device_id` as a source-quality caveat until the downstream raw device safe-handle path is fully validated.
