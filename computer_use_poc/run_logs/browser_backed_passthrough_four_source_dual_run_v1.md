# Browser-backed Passthrough Four-source Dual Run V1

## 1. Test Goal

- Validate first-batch four-source field coverage between `compat_summary` and `passthrough + Dennis parser`.
- Validate passthrough does not output raw upstream body.
- Validate the `compat_summary` default chain remains preserved and is not replaced.

## 2. Service Health

- `ok=true`
- `service_mode=live`
- `auth-state category=ready`
- `action_count=12`
- Track Analysis / Login Logs / Weapon / RCP origins were ready.

## 3. Dual Run Result

| action | compat source_status | passthrough source_status | normalized_observation |
| --- | --- | --- | --- |
| `track_analysis_summary` | `completed` | `completed` | yes |
| `login_logs_search` | `completed` | `completed` | yes |
| `weapon_inventory` | `completed` | `completed` | yes |
| `rcp_snapshot` | `completed` | `completed` | yes |

## 4. Track Result

- `sub_interface=profile`
- `profile_fields_observed` present
- `profile_sections_observed=["firstLevelProfile","secondLevelProfile"]`
- `device_ids_count=9`
- `records_count=1`
- `raw_body_suppressed=true`

## 5. Login Logs Result

- `records_count=6`
- `fields_observed` includes `logTags/userIds/dids/logSource/method/date/index/timestamp`
- Sample fields present: `logSource` / `method` / `timestamp`
- `raw_records_suppressed=true`

## 6. Weapon Result

- `graph_status=completed`
- `pointInfoMap_count=2`
- `relationEdgeList_count=1`
- `related_device_count=1`
- `related_user_count=1`
- `riskData_status=not_executed_missing_device_id`
- `risk_label_count=0`
- `raw_body_suppressed=true`
- `raw_labelInfo_suppressed=true`
- `raw_originalLog_suppressed=true`

`riskData` was not executed because of the `weapon_chain` state. This is not a parser blocker; graphData was parsed successfully from the live wrapper shape.

## 7. RCP Result

- `event_count=200`
- `eventId/sourceId/deviceId/hitFusePolicyCode/_occurTime` samples present
- `raw_eventList_full_dump_suppressed=true`

## 8. Conclusion

- `four_source_dual_run_pass=true`
- No blocking parser gap.
- `compat_summary` default chain preserved.
- Passthrough parser first batch is ready.

## 9. Migration Principles

- Parallel running is a migration-stage strategy, not the final architecture.
- Browser-backed service should ultimately retain only controlled passthrough.
- Dennis owns parser / `normalized_observation` / evidence card construction.
- Before switching defaults, full_runtime controlled pilot must pass.
- After switching defaults, remove redundant service-side summary / `source_card` / `source_quality` / evidence summary logic to avoid maintaining two processing chains long term.
