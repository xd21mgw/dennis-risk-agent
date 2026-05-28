# Platform Access Source Orchestration Examples v0.1

## ATO With Explicit Policy Hit

1. Build `time_window_reasoning`.
2. Trigger explicit target source: RCP `eventList` on `rcp.corp.kuaishou.com`.
3. Select `tableHeaderList` / scenario-dependent dynamic columns for policy, device, IP, and operation fields.
4. If `eventId/eventType/queryTime` are present, trigger `rcpEventDetail`.
5. If eventList lacks `policyCode`, `deviceId`, or strategy-detail fields, supplement via `rcpEventDetail`.
6. If `policyCode` is present, trigger `getPolicyVersionListByEvent`.
7. Trigger `nodePolicyAttribution` only when `eventId + policyCode + policyVersion + queryTime` are complete.
8. Cross-check with login log, Archives profile, Weapon graphData, and conditional riskData.

`eventList completed_no_hit` is not a no-risk conclusion. Missing event fields become `missing_upstream_id`.
`eventList` is a query-conditions plus dynamic-columns interface, not a fixed field table. `tableHeaderList` is HAR confirmed; `customColumns`, `selectedColumns`, and `featureList` are scenario-dependent candidates.

## Abnormal Publish ATO

1. Use publish time as the primary time anchor.
2. Look backward for login, scan/OAuth, token/session, device switch, and strategy hit.
3. Look forward for audit reason, punishment, and complaint.
4. Use publish device as a downstream `device_id` candidate for Weapon riskData.
5. Align publish day with track-analysis frontend activity.

## Device Risk Question

If the user provides a deviceId, call Weapon riskData directly. If only userId is provided, resolve device candidates from graphData, login log, publish chain, RCP detail, Archives, or track-analysis first. Do not pass userId as deviceId.

## RCP Strategy Chain

`eventList -> rcpEventDetail -> rcpEventFeatureList(featureGroup="") -> getPolicyVersionListByEvent -> nodePolicyAttribution`

`fastQueryHbase` is a fallback / comparison source. `fastQueryHbase` blocked does not mean RCP/Tianshi unavailable.
