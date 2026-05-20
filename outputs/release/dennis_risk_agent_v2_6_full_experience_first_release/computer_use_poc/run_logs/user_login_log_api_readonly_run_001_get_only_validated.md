# User Login Log API Readonly Run 001 GET-only Validated

```yaml
test_stage: v2.4.10
source_name: user_login_log_api_readonly_hand
test_type: get_only_api_access_and_full_result_discovery
validation_status: get_only_validated
endpoint: /rest/unified/log/search
```

## 1. query parameter correction

标准用户查询必须使用 `userId` 参数。

正确示例：

```text
GET https://user-center-workbench.corp.kuaishou.com/rest/unified/log/search?userId=4700398885&did=&query=&from_timestamp=1779169555398&to_timestamp=1779255955398&recallSource=2%2C0%2C1%2C3
```

错误示例：

```text
GET https://user-center-workbench.corp.kuaishou.com/rest/unified/log/search?query=4700398885&userId=&did=&recallSource=2,0,1,3&from_timestamp=1779168006259&to_timestamp=1779254406259
```

解释：

- `userId` 是标准用户 ID 精确查询字段。
- `query` 是通用 keyword fallback，不作为标准用户链路查询方式。

## 2. GET-only 实测结果

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

## 3. pagination discovery

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

- GET 直联可用，SSO 自动认证。
- 一次请求返回完整 141 条记录。
- `totalCount == logSearchModels.length`。
- UI 翻页没有触发新的 search 请求，属于前端分页。
- `index` 在本样例中为 0 到 140；不强约束所有场景必须从 0 或 1 开始，只判断连续性。

## 4. event observation

```yaml
event_observation:
  target_user_id: "4700398885"
  events_observed:
    - login/logout 循环
    - TOKEN_ISSUED_LOG
    - TOKEN_REVOKE_LOG
    - changeOption
  did_distribution:
    unique_did_count: 1
    did: "3509C1CA-0DC3-4868-A5E8-9A88E83A8A81"
```

## 5. sensitive policy

```yaml
sensitive_policy:
  full_response_output: false
  full_logContent_output: false
  cookie_output: false
  token_output: false
  authorization_output: false
  credential_fields: present_redacted_only
```

## 6. current status

```yaml
user_login_log_ui_hand: release_candidate_not_final
user_login_log_api_hand: get_only_validated / api_readonly_poc
final_release_package: not_updated
```

## 7. boundary

- API full result 只代表当前查询条件和可靠时间窗口内完整，不代表历史全量。
- API 返回空不等于无风险。
- API 返回空不等于用户无登录记录。
- 超出 reliable window 仍不得解释为历史无记录。
- API 401 / 403 / redirect 不等于无数据。
- 不引入自动处置或自动风险定性。
