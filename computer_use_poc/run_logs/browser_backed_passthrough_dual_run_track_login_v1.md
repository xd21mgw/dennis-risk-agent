# Browser-Backed Passthrough Dual Run: Track + Login Logs v1

## Scope

This run log records the completed dual-run comparison for Dennis browser-backed `compat_summary` mode versus explicit `passthrough` mode with Dennis-side parser normalization.

No test was re-run for this log. The content below is a run-log capture of the prior successful dual run.

## Baseline

- Service health: ready
- Service URL: `http://127.0.0.1:8787`
- Current HEAD: `c213117 fix track passthrough profile parser priority`
- `compat_summary` remains the default chain.
- `passthrough` was used only through explicit request mode.

## Tested Actions

1. `track_analysis_summary`
   - `sub_interface=profile`
   - `user_id=2871834924`
   - `appName=KUAISHOU`
2. `login_logs_search`
   - `user_id=2871834924`

## Service Health Summary

- `ok=true`
- `service_mode=live`
- `auth_state=ready`
- `track_analysis=ready`
- `login_logs=ready`

## compat_summary Results

### track_analysis_summary

- `source_status=completed`
- `failure_layer=no_failure`
- `sensitive_output=false`
- `response_shape_summary` included Track Analysis shape context.

### login_logs_search

- `source_status=completed`
- `failure_layer=no_failure`
- `sensitive_output=false`
- `response_shape_summary` included Login Logs shape context.

## passthrough Normalized Observation Results

### track_analysis_summary

- `source_status=completed`
- `sub_interface=profile`
- `entity.userId=2871834924`
- `records_count=1`
- `device_ids_count=9`
- `profile_fields_observed` present
- `profile_sections_observed=["firstLevelProfile", "secondLevelProfile"]`
- `raw_body_suppressed=true`

### login_logs_search

- `source_status=completed`
- `records_count=6`
- `fields_observed` included:
  - `logTags`
  - `userIds`
  - `dids`
  - `logSource`
  - `method`
  - `date`
  - `index`
  - `timestamp`
- `raw_records_suppressed=true`

## Safety And Boundary

- No raw `upstream.body` output.
- No cookie/token/session/header output.
- No Chrome profile, `.ks_sso`, cookie, token, session, or header read by Dennis.
- DataAgent/Hive not called.
- No final risk judgement was made from this parser validation.
- No browser-backed-api-poc code was modified.
- `outputs/full_runtime` was not modified.

## Comparison Result

- `track_analysis_summary`: compat and passthrough both completed.
- `login_logs_search`: compat and passthrough both completed.
- Track passthrough parser correctly preserved `sub_interface=profile` even though the body also contained `deviceIds`.
- Login Logs passthrough parser continued to recognize `data.logSearchModels`.
- `dual_run_pass=true`

## Conclusion

Track + Login Logs passthrough parser first-stage validation passed. The `compat_summary` default chain remains unaffected.
