# RCP eventList HAR Body Contract Patch v0.1

## Background

Latest HAR review confirmed that RCP `eventList` is closer to a ClickHouse-like dynamic event query builder than a fixed-field query API.

Previous direct HTTP attempts used guessed bodies. Those failures do not prove HTTP+SSO direct unavailable.

## Contract Updates

- `eventList.backend_semantics=clickhouse_like_event_query_builder`
- `tableHeaderList` is an object array with `column_name` and `column_comment`.
- `tableHeaderList` is not a string array.
- `startTime`, `endTime`, and `currentTime` use `YYYY-MM-DD HH:mm:ss` string format.
- Time fields are not epoch milliseconds and not epoch seconds.
- `eventV2` is a full query object, not a simplified `{eventType,status,region}` body.
- `eventV2.sourceIds` is a string field in the HAR-confirmed body.
- `conditionList` is an array of condition groups that can express deviceId, sourceId, and custom feature filters.
- Response wrapper paths are `data.eventList`, `data.pagination`, and `data.tableHeaderList`.

## Corrected Failure Classification

- `tableHeaderList` string array failure -> `wrong_request_body_shape`.
- `sourceIds` string array failure -> `wrong_request_body_shape`.
- epoch time fields -> `wrong_time_field_format`.
- guessed HTTP direct body failure -> `guessed_body_failed_not_direct_unavailable`.
- These are not `auth_failed`, `permission_blocked`, or platform unavailable.

## Files Updated

- `computer_use_poc/platform_access/tianshi_rcp_api_contract_v0_1.yaml`
- `computer_use_poc/platform_access/platform_access_inventory_v0_1.yaml`
- `computer_use_poc/platform_access/source_orchestration_examples_v0_1.md`
- `computer_use_poc/source_orchestration_plan_v1.yaml`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/platform_access/failure_taxonomy_v0_1.yaml`
- `computer_use_poc/platform_access/observation_schema_v0_1.yaml`

## Boundaries

- Did not access real platforms.
- Did not call DataAgent or Hive.
- Did not modify auth, gateway, safeBins, or TOOLS.
- Did not copy raw HAR, headers, cookie, token, or session material.
- Did not output credential material.
- Did not rebuild a package.
- Did not commit git changes.

