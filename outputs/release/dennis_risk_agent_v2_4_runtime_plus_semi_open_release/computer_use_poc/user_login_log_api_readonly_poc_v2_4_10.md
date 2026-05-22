# v2.4.10 用户登录统一日志 API readonly hand POC

## 1. 定位

`user_login_log_api_readonly_hand` 是用户登录统一日志的 API 优先读取方式。

目标：

- 减少 UI 点击、分页、modal、SPA route、submit button 等不稳定因素。
- API hand 优先用于结构化读取。
- UI hand 保留为 auth bootstrap / fallback / 字段发现。

当前接口：

```text
GET https://user-center-workbench.corp.kuaishou.com/rest/unified/log/search
```

当前状态：

```yaml
user_login_log_ui_hand: release_candidate_not_final
user_login_log_api_hand: get_only_validated / api_readonly_poc
final_release_package: not_updated
```

## 2. 标准查询模式

标准用户维度查询必须使用 `userId` 参数，不要把 userId 放到 `query` 参数里。

正确示例：

```text
GET https://user-center-workbench.corp.kuaishou.com/rest/unified/log/search?userId=4700398885&did=&query=&from_timestamp=1779169555398&to_timestamp=1779255955398&recallSource=2%2C0%2C1%2C3
```

错误示例：

```text
GET https://user-center-workbench.corp.kuaishou.com/rest/unified/log/search?query=4700398885&userId=&did=&recallSource=2,0,1,3&from_timestamp=1779168006259&to_timestamp=1779254406259
```

标准模式：

```yaml
standard_query_mode:
  user_id_exact_query:
    userId: "{target_user_id}"
    did: ""
    query: ""
```

fallback 模式：

```yaml
fallback_query_mode:
  keyword_query:
    query: "{keyword}"
    userId: ""
    did: ""
```

字段解释：

- `userId`：标准用户 ID 精确查询字段，Dennis Agent 用户维度查询默认使用它。
- `did`：设备 ID / DID 查询字段，设备维度查询使用它。
- `query`：通用 keyword 查询字段，仅作为 fallback，不作为标准 userId 查询方式。
- `recallSource`：日志来源范围，默认 `2,0,1,3`。
- `from_timestamp` / `to_timestamp`：查询时间窗口，仍需遵守 reliable window guardrail。

## 3. GET-only API 读取结论

本轮结果来自内部 Agent GET-only 实测，不是 Codex 直接访问平台。

```yaml
get_url_access_test:
  endpoint: /rest/unified/log/search
  accessible: true
  status_code: 200
  code: 0
  total_count: 141
  logSearchModels_length: 141
  first_index: 0
  last_index: 140
  length_equals_totalCount: true
  auth_blocked: false
  redirected_to_login: false
  api_full_result_loaded: true
```

补充观察：

- GET 直联可用，SSO 自动认证。
- 一次请求返回完整 141 条记录。
- `totalCount == logSearchModels.length`。
- UI 翻页没有触发新的 search 请求，属于前端分页。
- 当前用户 `4700398885` 在查询窗口内有 login/logout 循环、`TOKEN_ISSUED_LOG`、`TOKEN_REVOKE_LOG`、`changeOption` 等事件。
- 所有记录来自同一 DID：`3509C1CA-0DC3-4868-A5E8-9A88E83A8A81`。

## 4. unified_log_api_pagination_discovery

```yaml
unified_log_api_pagination_discovery:
  endpoint: /rest/unified/log/search
  total_count: 141
  logSearchModels_length: 141
  first_index: 0
  last_index: 140
  length_equals_totalCount: true
  pagination_request_triggered_on_ui_page_change: false
  pagination_mode: frontend_pagination
  api_full_result_loaded: true
  ui_frontend_pagination: true
```

解释：

- `index` 可能从 0 开始，也可能在不同场景有不同表现，不强约束必须从 1 开始。
- 只需要判断 `length_equals_totalCount` 和 `index_continuity`。
- 当 `logSearchModels.length == totalCount` 时，可标记 `api_full_result_loaded=true`。
- 当 `logSearchModels.length < totalCount` 时，才需要继续寻找 page / offset / cursor / searchAfter 等分页参数。

## 5. query schema

```yaml
user_login_log_api_query:
  standard_query_mode:
    userId:
    did:
    query:
  fallback_query_mode:
    query:
    userId:
    did:
  from_timestamp:
  to_timestamp:
  recallSource:
  reliable_window:
  over_reliable_realtime_window:
```

## 6. response schema

```yaml
user_login_log_api_response:
  status_code:
  code:
  total_count:
  logSearchModels_length:
  api_full_result_loaded:
  index_continuity:
    first_index:
    last_index:
    continuous:
  log_models:
    - date:
      timestamp:
      index:
      userIds:
      dids:
      method:
      logSource:
      logTags:
      logContent_keys:
      normalized_event_type:
      credential_fields_redacted:
```

## 7. logContent parse policy

`logContent` 是 JSON string，允许 parse key 和非凭证明文 value。

保留字段：

- `userId`
- `deviceId`
- `did`
- `userIp`
- `userIpv6`
- `serverIp`
- `userAgent`
- `appVer`
- `sysVer`
- `uri`
- `method`
- `status`
- `actionType`
- `result`
- `reason`
- `timestamp`
- `dateTime`
- `loginType`
- `deviceModel`
- `osVersion`
- `sdkVersion`

凭证明文字段只输出 `present_redacted`：

- `token`
- `loginToken`
- `tokenId`
- `accessToken`
- `refreshToken`
- `session`
- `sessionId`
- `ticket`
- `authorization`
- `cookie`
- `rawAuthHeader`

禁止：

- 输出完整 response。
- 输出完整 `logContent`。
- 输出 cookie / token / authorization 原值。

## 8. guardrail

- 标准用户查询必须用 `userId` 参数，不能用 `query` 参数替代。
- `query=用户ID` 只能视为 keyword fallback，不能作为 Dennis Agent 标准用户链路查询方式。
- API 返回空不等于无风险。
- API 返回空不等于用户无登录记录。
- API full result 只代表当前查询条件和可靠时间窗口内完整，不代表历史全量。
- 超出 reliable window 仍不得解释为历史无记录。
- API 401 / 403 / redirect 不等于无数据。
- 若 `logSearchModels.length == totalCount`，可标记 `api_full_result_loaded=true`。
- 若 `logSearchModels.length < totalCount`，才需要继续寻找 page / offset / cursor / searchAfter 等分页参数。
- UI hand 仍需标记 `ui_visible_page_only=true`。
- API hand 可标记 `api_full_result_loaded=true`。
- 不输出 cookie / token / authorization / 完整 response / 完整 `logContent`。

## 9. 当前不做

- 不修改核心 Skill。
- 不改变 DataAgent / Hive 边界。
- 不引入自动处置或自动风险定性。
- 不更新 final release package。
- 不把 API 空结果解释为无风险。
- 不把 API 当前窗口完整结果解释为历史全量。
