# Archives Center Browser-Backed Action Landscape v1

## Purpose

Add Archives Center to the existing browser-backed fixed-action model without changing browser ownership, auth handling, or the default four-source account-security chain.

Dennis still calls only local fixed actions with typed params. The browser-backed service owns same-origin readiness, fixed platform path selection, platform request body construction, and raw response handling.

## Action Landscape

| action_name | priority | representative_path | request_body_status | response_shape_status | current_status | next_step |
| --- | --- | --- | --- | --- | --- | --- |
| `archives_user_analysis` | P0 | `POST /v3/user/log/coreLogs/fetch` | HAR/run-log confirmed fields: `userId`, `beginTime`, `endTime`, `pageIndex`, `pageSize`, `haveParamAuth`, operation filters | confirmed `data.totalCount` / `data.dataList`; records include operation/time/result/app/device/IP fields | implemented | keep service-side body builder fixed; live smoke only through browser-backed service with shape summary, no raw body |
| `archives_user_profile` | P0 | `GET /archives/user/home/info?userId=<user_id>` plus labels/shop/risk optional paths | profile home path known; multi-call profile bundle body not finalized for browser-backed action | home/profile shape documented, bundle merge shape pending | candidate_only | decide whether to expose as separate `archives_user_profile` action or merge into broader profile bundle after body/normalizer fixture is available |
| `archives_photo_search` | P0-conditional | `POST /v4/archives/report/photo/search` | corrected payload documented: `reportedIds=<user_id>`, `matchType`, `sort`, `begin`, `end`, `page`, `count` | validated `totalCount` / `dataList`; report text must be summarized only | candidate_only | implement after P0 user analysis if abnormal-publish/content case needs it |
| `archives_related_users` | P1 | `POST /archives/user/search/device` | corrected payload documented: `keyword=<user_id>`, `inputType=0`, `type=0/1` | validated same-device registered/login mapping | candidate_only | implement as relation summary with counts only; do not output related user raw list by default |
| `archives_related_devices` | P1 | likely user-analysis/profile/device summaries; no single dedicated action confirmed | request body not fixed for standalone related-device action | response shape not fixed for standalone related-device action | next_probe_needed | confirm whether device relation should come from user profile, user analysis, or same-device search before implementing |
| `archives_private_message_search` | P1 candidate | `POST /archives/user/message/search` | from/to directions documented, but browser-backed typed params not finalized | totals observed; private message plaintext must never output | candidate_only | add only after typed direction contract and text-suppression fixture are ready |
| `archives_past_four_items` | P1 candidate | `POST /v4/audit/user/fourinfo/log/search` | `keyword=<user_id>` and `infoType` mapping documented, but action semantics need naming decision | change-log shape documented; old/new text/media/operator must be summarized | next_probe_needed | clarify whether "past four items" means four-info audit logs before action exposure |

## Implemented Action

### `archives_user_analysis`

Fixed service endpoint:

```yaml
browser_backed_action: archives_user_analysis
local_service_endpoint: POST /actions/archives_user_analysis
representative_platform_path: /v3/user/log/coreLogs/fetch
platform_method: POST
```

Typed params accepted by Dennis:

```yaml
typed_params:
  user_id: "<decimal user id>"
  mode: focused_login_risk_core_logs
  beginTime: <millisecond timestamp>
  endTime: <millisecond timestamp>
  pageIndex: 1
  pageSize: 30
  haveParamAuth: 1
  operation_filters:
    loginStart: 1
    registerBind: 1
    resetPass: 1
    protectAccount: 1
    liveStream: 1
    scanCode: 1
    logout: 1
    frozen: 1
```

Service-side body builder summary:

- Map `user_id` to platform `userId`.
- Map `beginTime` / `endTime` / `pageIndex` / `pageSize` directly.
- Expand `operation_filters` into the eight platform operation filter fields.
- Keep platform path fixed at `/v3/user/log/coreLogs/fetch`.
- Reject caller-provided URL/path/header/cookie/token/session.

Normalizer summary:

- Reads only standard browser-backed source result fields.
- Preserves `source_status`, `source_card`, `source_quality`, `key_entities`, `missing_fields`, `next_action`.
- Produces `archives_user_analysis` business summary with `risk_event_scan`.
- Forces `sensitive_output=false` and `no_data_not_risk_exclusion=true`.
- Suppresses raw full body, full `requestParam`, full `extraParam`, token/tokenId/open_id/sig/refresh_token, and raw records.

## Boundary

- This landscape does not start a browser.
- This landscape does not call Archives Center directly.
- This landscape does not call DataAgent/Hive.
- This landscape does not modify auth, gateway, safeBins, or TOOLS.
- This landscape does not add arbitrary URL fetch. All platform paths remain service-owned fixed paths.
- `user_id`, `device_id`, `ip`, `event_id`, `strategy_id`, `photo_id`, and `live_id` are risk entity identifiers for internal review and source chaining.
- Credential secrets, phone, ID card, real name, detailed address, raw full body, full `requestParam`, and full `extraParam` remain forbidden output.
