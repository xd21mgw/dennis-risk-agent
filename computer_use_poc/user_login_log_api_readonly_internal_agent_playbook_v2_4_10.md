# 用户登录统一日志 API readonly internal Agent playbook v2.4.10

## 1. 当前能力范围

```yaml
source_name: user_login_log_api_readonly_hand
endpoint: https://user-center-workbench.corp.kuaishou.com/rest/unified/log/search
method: GET
status: get_only_validated / api_readonly_poc
```

API hand 优先用于结构化读取统一登录日志。UI hand 保留为 auth bootstrap / fallback / 字段发现。

受控 runner：

```bash
python3 computer_use_poc/sso_session_runner.py \
  --platform login_log \
  --action query_user_login_log \
  --user-id <user_id> \
  --timeout 30 \
  --format json
```

`sso_session_runner.py` 是受控 SSO API executor，不是任意 HTTP 客户端。它只支持白名单 platform/action 构造统一登录日志 URL，并通过 live 环境提供的 `sso_session.SmartSSOSession.get()` 发起 GET。它不接受 `target_url` / arbitrary URL，不输出 cookie/token/session/header，不调用 DataAgent，不执行写操作。本地环境缺少 `SmartSSOSession` 时必须 fail closed，输出结构化 `blocked` observation。

认证态桥接边界：

- 统一登录日志只读查询必须走受控 wrapper / dennis-risk-agent source orchestration，不使用临时 curl + cookie。
- `sso_session_runner.py` 是统一登录日志 P0 的受控 real HTTP executor；认证失败、HTML 登录页、重定向、timeout、parse error 都必须输出结构化 observation。
- `sso_session.py` 代表认证注入能力；不能由 main agent 临时调用来拼接 curl/cookie 查询。
- SSO state 存在不等于 API direct 可用。
- curl + cookie 返回 302 redirect 时，标记 `auth_session_issue`，不得继续拼 cookie 重试。
- browser fetch 必须在 `user-center-workbench` 正确同源域名内执行；否则标记 `same_origin_error`。
- agent-browser profile lock / SingletonLock 标记 `profile_lock` 并快速降级。
- `auth_failed` / `redirect` / `same_origin_error` / `profile_lock` 都进入 `source_quality`，不得解释为 no_data。
- main agent 在 dennis-risk-agent timeout 后不得自己接管统一登录日志查询；只能记录 `subagent_timeout`，输出 partial / retry plan。
- 统一登录日志线上 API 按约 7 天可靠窗口处理；客诉时间不在窗口内时必须标记 `login_log_window_incomplete` 和 `source_time_range_gap`。
- admin / user-center-workbench 主要覆盖 APP 登录、refresh token、密码验证等登录侧行为；扫码 / OAuth / 地推欺诈 / 陌生链接诱导 / 发布违规 / 好友删除类客诉不能只靠 APP 登录日志排除 ATO。
- APP 登录日志 no_data、单 DID、IP 稳定只能输出 `app_login_visible_window_no_strong_anomaly`，不得写低风险 / 无风险 / 排除 ATO。

runner observation 必填：

```yaml
source_name: user_login_unified_log
source_status: completed | no_data | auth_failed | timeout | parse_error | blocked
user_id:
records_count:
evidence_time_range:
evidence_summary:
source_quality:
raw_reference_safe_id:
collected_at:
redaction_applied: true
real_platform_request_executed:
```

## 2. 标准请求参数

标准用户查询必须使用 `userId` 参数：

```yaml
standard_query_mode:
  userId: "{target_user_id}"
  did: ""
  query: ""
  from_timestamp: "{start_ms}"
  to_timestamp: "{end_ms}"
  recallSource: "2,0,1,3"
```

不要使用：

```yaml
wrong_user_query_mode:
  query: "{target_user_id}"
  userId: ""
```

fallback keyword 查询仅在用户明确要求 keyword 或非标准搜索时使用：

```yaml
fallback_query_mode:
  query: "{keyword}"
  userId: ""
  did: ""
```

## 3. 执行步骤

1. 生成 `from_timestamp` / `to_timestamp`，并检查 reliable window。
2. 组装 GET URL。
3. 用户维度查询时，将目标 ID 放入 `userId`。
4. 设备维度查询时，将目标 DID 放入 `did`。
5. 保持 `recallSource=2,0,1,3`，除非用户明确要求调整日志源。
6. 发送 GET-only 请求。
7. 检查 `status_code` 和 body `code`。
8. 读取 `totalCount` 和 `logSearchModels.length`。
9. 如果二者相等，标记 `api_full_result_loaded=true`。
10. parse `logContent` 时只输出 key 和允许保留的非凭证明文 value。
11. 凭证明文字段只输出 `present_redacted`。

## 4. response observation

```yaml
user_login_log_api_observation:
  query_mode: standard_user_id_exact_query | did_exact_query | keyword_fallback
  query_params:
    userId:
    did:
    query:
    from_timestamp:
    to_timestamp:
    recallSource:
  response_status:
    status_code:
    code:
    auth_blocked:
    redirected_to_login:
    auth_session_issue:
    same_origin_error:
    profile_lock:
    login_log_window_incomplete:
    source_time_range_gap:
    app_login_only_source_gap:
  pagination_discovery:
    total_count:
    logSearchModels_length:
    length_equals_totalCount:
    first_index:
    last_index:
    index_continuity:
    api_full_result_loaded:
    ui_frontend_pagination:
  event_summary:
    normalized_event_type_counts:
    method_counts:
    logSource_counts:
    did_distribution:
    time_range_observed:
  credential_fields_policy:
    raw_credential_output: false
    credential_fields_redacted:
```

## 5. logContent parse policy

允许保留：

- userId / deviceId / did
- userIp / userIpv6 / serverIp
- userAgent / appVer / sysVer
- uri / method / status / actionType / result / reason
- timestamp / dateTime
- loginType / deviceModel / osVersion / sdkVersion

只输出 `present_redacted`：

- token
- loginToken
- tokenId
- accessToken
- refreshToken
- session
- sessionId
- ticket
- authorization
- cookie
- rawAuthHeader

## 6. guardrail

- 标准用户查询必须使用 `userId` 参数。
- `query=用户ID` 只能作为 keyword fallback，不作为标准 userId 查询方式。
- API 返回空不等于无风险。
- API 返回空不等于用户无登录记录。
- API full result 只代表当前查询条件和 reliable window 内完整，不代表历史全量。
- 超出 reliable window 不得解释为历史无记录。
- API 401 / 403 / redirect 不等于无数据。
- 不输出完整 response。
- 不输出完整 `logContent`。
- 不输出 cookie / token / authorization 原值。

## 7. GET-only validated sample

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

说明：

- UI 翻页没有触发新的 search 请求，属于前端分页。
- API 一次性返回当前查询窗口内完整结果。
- 若未来出现 `logSearchModels.length < totalCount`，再探索 page / offset / cursor / searchAfter。
