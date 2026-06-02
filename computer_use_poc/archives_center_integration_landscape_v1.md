# Archives Center Browser-Backed Action Landscape v1

## Purpose

Add Archives Center to the existing browser-backed fixed-action model without changing browser ownership, auth handling, or the default four-source account-security chain.

Dennis still calls only local fixed actions with typed params. The browser-backed service owns same-origin readiness, fixed platform path selection, platform request body construction, and raw response handling.

## Action Landscape

| action_name | priority | representative_path | request_body_status | response_shape_status | current_status | next_step |
| --- | --- | --- | --- | --- | --- | --- |
| `archives_user_analysis` | P0 | `POST /v3/user/log/coreLogs/fetch` | HAR/run-log confirmed fields: `userId`, `beginTime`, `endTime`, `pageIndex`, `pageSize`, `haveParamAuth`, operation filters | confirmed `data.totalCount` / `data.dataList`; records include operation/time/result/app/device/IP fields | implemented | keep service-side body builder fixed; live smoke only through browser-backed service with shape summary, no raw body |
| `archives_user_profile` | P0 | `GET /archives/user/home/info?userId=<user_id>` plus labels/shop/risk optional service-owned paths | profile home path known; Dennis passes only typed `user_id` | home/profile shape documented; mock fixture covers baseline summary | implemented | keep bundle expansion service-owned; output current-state profile summary only, not raw profile body |
| `archives_photo_search` | P0-default-for-ATO-content-handoff | `POST /v4/archives/report/photo/search` | corrected payload documented: `reportedIds=<user_id>`, `matchType`, `sort`, `begin`, `end`, `page`, `count` | validated `totalCount` / `dataList`; report text must be summarized only | implemented | default ATO content/publish handoff plus abnormal-publish/content anchoring; reports are signal, not final judgement |
| `archives_related_users` | P1 | `POST /archives/user/search/device` | corrected payload documented: `keyword=<user_id>`, `inputType=0`, `type=0/1` | validated same-device registered/login mapping; mock fixture covers relation summary | implemented | output counts, relation type, and internal-review risk entity IDs; relation alone is not judgement |
| `archives_related_devices` | P1 | likely user-analysis/profile/device summaries; no single dedicated action confirmed | request body not fixed for standalone related-device action | response shape not fixed for standalone related-device action | next_probe_needed | confirm whether device relation should come from user profile, user analysis, or same-device search before implementing |
| `archives_private_message_search` | P1 candidate | `POST /archives/user/message/search` | from/to directions validated; Dennis passes typed `direction=sent/received` only | totals observed; mock fixture covers count/status/time summary; private message plaintext never outputs | implemented | use for social-interaction context only; no plaintext or counterpart profile dump |
| `archives_past_four_items` | P1 candidate | `POST /v4/audit/user/fourinfo/log/search` | `keyword=<user_id>` and `infoType=0/1/2/3/4` mapping validated | mock fixture covers count/time/type/status summary; old/new text/media/operator suppressed | implemented | treat as four-info change-log summary; align with login/publish evidence before judgement |

## Implemented Actions

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

### `archives_photo_search`

Fixed service endpoint:

```yaml
browser_backed_action: archives_photo_search
local_service_endpoint: POST /actions/archives_photo_search
representative_platform_path: /v4/archives/report/photo/search
platform_method: POST
```

Typed params accepted by Dennis:

```yaml
typed_params:
  user_id: "<decimal user id>"
  mode: archives_photo_report_search
  begin: <millisecond timestamp>
  end: <millisecond timestamp>
  page: 1
  count: 20
  matchType: "0"
  sort: "0"
```

Service-side body builder summary:

- Map `user_id` to platform `reportedIds`.
- Use validated `begin` / `end`, not `beginTime` / `endTime`.
- Use `sort`, not `sortType`; keep `matchType` and `sort` as strings.
- Keep platform path fixed at `/v4/archives/report/photo/search`.
- Reject caller-provided URL/path/header/cookie/token/session.

Normalizer summary:

- Produces `photo_search_summary` with `photo_count`, `publish_time_range`, `status_summary`, `risk_context_summary`, and report reason summary.
- Preserves `key_entities.photo_ids` for internal review/source chaining.
- Forces `sensitive_output=false` and `no_data_not_risk_exclusion=true`.
- Suppresses raw full body and raw report text/content.

### `archives_user_profile`

Fixed service endpoint:

```yaml
browser_backed_action: archives_user_profile
local_service_endpoint: POST /actions/archives_user_profile
representative_platform_path: /archives/user/home/info
platform_method: GET
```

Typed params accepted by Dennis:

```yaml
typed_params:
  user_id: "<decimal user id>"
  mode: archives_user_home_profile
```

Service-side body builder summary:

- Map `user_id` to platform query field `userId`.
- Keep optional label/shop/risk paths service-owned; Dennis does not pass path or bundle config.
- Keep platform path fixed at `/archives/user/home/info`.
- Reject caller-provided URL/path/header/cookie/token/session.

Normalizer summary:

- Produces `profile_summary` with account status, registration, profile state, label/risk/shop/punish summaries, and coverage limitations.
- Preserves user/device/IP risk entity identifiers under internal review.
- Forces `sensitive_output=false` and `no_data_not_risk_exclusion=true`.
- Suppresses raw profile body, full phone, ID card, real name, and credential material.

### `archives_related_users`

Fixed service endpoint:

```yaml
browser_backed_action: archives_related_users
local_service_endpoint: POST /actions/archives_related_users
representative_platform_path: /archives/user/search/device
platform_method: POST
```

Typed params accepted by Dennis:

```yaml
typed_params:
  user_id: "<decimal user id>"
  mode: archives_same_device_related_users
  relation_type: same_device_registered | same_device_login
  inputType: 0
  type: 0 | 1
```

Service-side body builder summary:

- Map `user_id` to platform `keyword`.
- Use validated `inputType=0`.
- Map `same_device_registered` to `type=0` and `same_device_login` to `type=1`.
- Keep platform path fixed at `/archives/user/search/device`.
- Reject caller-provided URL/path/header/cookie/token/session.

Normalizer summary:

- Produces `related_users_summary` with `related_user_count`, `relation_type_summary`, status summary, and risk context summary.
- Preserves `key_entities.related_user_ids` for internal review/source chaining.
- Forces `sensitive_output=false` and `no_data_not_risk_exclusion=true`.
- Suppresses raw full body and raw related-user profile details.

### `archives_private_message_search`

Fixed service endpoint:

```yaml
browser_backed_action: archives_private_message_search
local_service_endpoint: POST /actions/archives_private_message_search
representative_platform_path: /archives/user/message/search
platform_method: POST
```

Typed params accepted by Dennis:

```yaml
typed_params:
  user_id: "<decimal user id>"
  mode: archives_private_message_summary
  direction: sent | received
  page: 1
  count: 20
  status: ""
  sort: "0"
```

Service-side body builder summary:

- Map `direction=sent` to platform `fromUserId=<user_id>`.
- Map `direction=received` to platform `toUserId=<user_id>`.
- Map `status`, `sort`, `page`, and `count` directly.
- Keep platform path fixed at `/archives/user/message/search`.
- Reject caller-provided URL/path/header/cookie/token/session.

Normalizer summary:

- Produces `private_message_summary` with count, direction, time range, status, counterpart count, and risk context summary.
- Preserves `counterpart_user_ids` only as risk entity identifiers for internal review/source chaining.
- Forces `sensitive_output=false` and `no_data_not_risk_exclusion=true`.
- Suppresses raw private message plaintext, counterpart nicknames, and raw full body.

### `archives_past_four_items`

Fixed service endpoint:

```yaml
browser_backed_action: archives_past_four_items
local_service_endpoint: POST /actions/archives_past_four_items
representative_platform_path: /v4/audit/user/fourinfo/log/search
platform_method: POST
```

Typed params accepted by Dennis:

```yaml
typed_params:
  user_id: "<decimal user id>"
  mode: archives_four_info_change_log_summary
  info_type: all | username | avatar | profile_description | background
  infoType: 0 | 1 | 2 | 3 | 4
  page: 1
  count: 20
  markResult: ""
  punishResult: ""
```

Service-side body builder summary:

- Map `user_id` to platform `keyword`; do not use `userId`.
- Map `info_type` to validated `infoType`: all=0, username=1, avatar=2, profile_description=3, background=4.
- Map `markResult`, `punishResult`, `page`, and `count` directly.
- Keep platform path fixed at `/v4/audit/user/fourinfo/log/search`.
- Reject caller-provided URL/path/header/cookie/token/session.

Normalizer summary:

- Produces `four_info_change_summary` with total changes, time range, info type summary, status summary, and profile-change risk summary.
- Forces `sensitive_output=false` and `no_data_not_risk_exclusion=true`.
- Suppresses raw old/new profile content, avatar/background URLs, operator names, and raw full body.

## Boundary

- This landscape does not start a browser.
- This landscape does not call Archives Center directly.
- This landscape does not call DataAgent/Hive.
- This landscape does not modify auth, gateway, safeBins, or TOOLS.
- This landscape does not add arbitrary URL fetch. All platform paths remain service-owned fixed paths.
- `user_id`, `device_id`, `ip`, `event_id`, `strategy_id`, `photo_id`, and `live_id` are risk entity identifiers for internal review and source chaining.
- Credential secrets, phone, ID card, real name, detailed address, raw full body, full `requestParam`, and full `extraParam` remain forbidden output.
