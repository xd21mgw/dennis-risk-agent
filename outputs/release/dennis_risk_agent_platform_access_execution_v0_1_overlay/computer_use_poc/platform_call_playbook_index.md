# Platform Call Playbook Index Overlay

This focused overlay indexes Platform Access Execution v0.1 contracts. It is not the full playbook.

## Global Order

1. Classify runner invocation and dependencies.
2. Check base domain and endpoint contract.
3. Check parameter contract and upstream IDs.
4. Check same-origin requirements.
5. Check path permission.
6. Only then classify auth or user permission.

## RCP / Tianshi

- Base domain: `rcp.corp.kuaishou.com`.
- Primary entry: `POST /v2/rest/event/eventList`.
- Fallback: `GET /v2/rest/pc/event/fastQueryHbase`.
- `eventList` accepts `eventType`, `timeRange`, optional `sourceIds`, filters, `conditionGroups`, `tableHeaderList` / custom columns, and pagination.
- HAR-confirmed fields include `sourceId`, `eventId`, `_occurTime`, `_realTimeOp`, `_errorCode`, `_sideEffectOps`, `time`, `photoId`, `deviceId`, `hitFusePolicyCode`, `userRegisterIp`, `ipCity_zh`, and `openId`.
- Missing downstream fields map to `missing_upstream_id`, not auth failure.

## Weapon

- `graphData`: `/apiv2/graphData`.
- `riskData`: `/apiv2/riskData`.
- `riskData` is direct device-level evidence when `deviceId` is known.
- Do not use userId as deviceId.

## Login Log

- Use fixed online window.
- Do not loop-expand until timeout.
- `completed_no_data` is not no-risk evidence.

## Archives Center

- User analysis is ATO P0.
- Publish chain is P0-conditional for abnormal publish.
- Invocation method may be `browser_same_origin` when environment state is ready.
- Path or state gaps enter source quality and do not downgrade source priority.

## Track-Analysis

- Covered endpoints: `getLastestDateTime`, `getDeviceIds`, `getUseDuration`, `profile`.
- Use event-day activity alignment for login, scan/OAuth, publish, strategy hit, and device switch days.
- `front_backend_activity_mismatch` is auxiliary evidence.
