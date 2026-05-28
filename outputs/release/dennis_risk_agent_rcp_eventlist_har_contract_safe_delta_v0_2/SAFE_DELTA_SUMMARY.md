# Safe Delta Summary

This safe delta syncs the RCP eventList HAR-body contract from live handoff into the Codex mother repository package surface.

Confirmed eventList contract:

- `role: primary_strategy_hit_entry`
- `backend_semantics: clickhouse_like_event_query_builder`
- `primary_invocation: browser_same_origin`
- `http_sso_direct_status: needs_har_request_body_exact_replay`
- response wrapper paths are `data.eventList`, `data.pagination`, and `data.tableHeaderList`
- `tableHeaderList` is an object array, not a string array
- each `tableHeaderList` item uses `column_name` and `column_comment`
- `startTime`, `endTime`, and `currentTime` use `YYYY-MM-DD HH:mm:ss`
- `eventV2.sourceIds` is a string field, not a string array
- `conditionList` is a nested condition group for deviceId, sourceId, or feature filters

Failure boundary:

- Wrong body shape maps to `wrong_request_body_shape`.
- Wrong time format maps to `wrong_time_field_format`.
- Guessed direct body failures map to `guessed_body_failed` and do not prove direct mode unavailable.
- Request contract errors must not be classified as auth, permission, or platform-wide availability failures.

The package intentionally excludes workspace-only notes and transient runtime artifacts.

