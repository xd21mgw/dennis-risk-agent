# Platform Access Source Orchestration Examples v0.1

## ATO With Explicit Policy Hit

1. Build `time_window_reasoning`.
2. Trigger explicit target source: RCP `eventList` on `rcp.corp.kuaishou.com`.
3. Build eventList body from the HAR-confirmed pattern. `tableHeaderList` is an object array with `column_name` / `column_comment`, not a string array.
4. If `eventId/eventType/queryTime` are present, trigger `rcpEventDetail`.
5. If eventList lacks `policyCode`, `deviceId`, or strategy-detail fields, supplement via `rcpEventDetail`.
6. If `policyCode` is present, trigger `getPolicyVersionListByEvent`.
7. Trigger `nodePolicyAttribution` only when `eventId + policyCode + policyVersion + queryTime` are complete.
8. Cross-check with login log, Archives profile, Weapon graphData, and conditional riskData.

`eventList completed_no_hit` is not a no-risk conclusion. Missing event fields become `missing_upstream_id`.
`eventList` is a query-conditions plus dynamic-columns interface, not a fixed field table. `tableHeaderList` is HAR confirmed; `customColumns`, `selectedColumns`, and `featureList` are scenario-dependent candidates.

Correct eventList body pattern:

```yaml
tableHeaderList:
  - column_name: sourceId
    column_comment: 用户ID
  - column_name: eventId
    column_comment: 事件ID
  - column_name: _occurTime
    column_comment: 发生时间
startTime: "YYYY-MM-DD HH:mm:ss"
endTime: "YYYY-MM-DD HH:mm:ss"
currentTime: "YYYY-MM-DD HH:mm:ss"
pageIndex: 1
pageSize: 10
eventV2:
  eventType: "LIKE"
  hitPolicies: ""
  version: ""
  status: 2
  snapshotVersion: ""
  sourceIds: ""
  realTimeOp: "5"
  isPolicyTreeExperiment: false
  conditionList: []
  grayFeature: ""
  grayQueryStatus: 0
  region: "china"
```

Wrong body patterns:

- `tableHeaderList: ["sourceId", "eventId", "_occurTime"]` -> `wrong_request_body_shape`.
- `sourceIds: ["123"]` -> `wrong_request_body_shape`.
- epoch ms / epoch seconds time fields -> `wrong_time_field_format`.
- guessed HTTP direct body failure -> `guessed_body_failed_not_direct_unavailable`, not direct unavailable.

## Abnormal Publish ATO

1. Use publish time as the primary time anchor.
2. Look backward for login, scan/OAuth, token/session, device switch, and strategy hit.
3. Look forward for audit reason, punishment, and complaint.
4. Use publish device as a downstream `device_id` candidate for Weapon riskData.
5. Align publish day with track-analysis frontend activity.

## Device Risk Question

If the user provides a deviceId, call Weapon riskData directly. If only userId is provided, resolve device candidates from graphData, login log, publish chain, RCP detail, Archives, or track-analysis first. Do not pass userId as deviceId.

## Track-Analysis Event-Day Activity

1. Call `getLastestDateTime` with the complete query contract: `product=KUAISHOU|NEBULA`, `type=userId|deviceId`, `funcType=USER_PROFILE_QUERY`, and `_t`.
2. If `getLastestDateTime` returns code `603`, classify it as `parameter_contract_missing` / `invalid_parameter`, not auth failure.
3. Call `getDeviceIds` when device resolution is needed.
4. Call `getUseDuration` and parse `rows` as an object array with `date` and `duration`.
5. Call `profile` with millisecond `startTime/endTime`, `include=1`, `pageSize=100`, and the selected entity.
6. Compare event-day backend evidence with frontend `event_day_duration`.

If backend login, scan/OAuth, publish, or strategy hit exists on a day and the matching userId/deviceId duration is `0` or absent, mark `front_backend_activity_mismatch`. This is supporting evidence only and cannot independently classify risk.

## RCP Strategy Chain

`eventList -> rcpEventDetail -> rcpEventFeatureList(featureGroup="") -> getPolicyVersionListByEvent -> nodePolicyAttribution`

`fastQueryHbase` is a fallback / comparison source. `fastQueryHbase` blocked does not mean RCP/Tianshi unavailable.
