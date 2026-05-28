# Platform Access Source Orchestration Examples v0.1

## ATO With Explicit Policy Hit

1. Build `time_window_reasoning`.
2. Trigger explicit target source: RCP `eventList` on `rcp.corp.kuaishou.com`.
3. If `eventId/eventType/queryTime` are present, trigger `rcpEventDetail`.
4. If `policyCode` is present, trigger `getPolicyVersionListByEvent`.
5. Trigger `nodePolicyAttribution` only when `eventId + policyCode + policyVersion + queryTime` are complete.
6. Cross-check with login log, Archives profile, Weapon graphData, and conditional riskData.

`eventList completed_no_hit` is not a no-risk conclusion. Missing event fields become `missing_upstream_id`.

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

`fastQueryHbase` is a fallback. `fastQueryHbase` blocked does not mean RCP/Tianshi unavailable.
