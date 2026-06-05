# v2.4.7.1 档案中心用户分析 API direct POST POC

## 1. 定位

`archives_user_analysis_api_direct_post` 是档案中心“用户分析 / APP端核心操作日志”Tab 的 API direct POST 只读取数能力。

它属于档案中心用户分析 Tab，不属于用户登录统一日志平台。

用途：

- 替代 DOM / selector 方式提取档案中心用户分析日志。
- 作为 `focused_login_risk` 的默认优先路径。
- 从 API response 直接生成 `risk_event_scan`。
- 在 API 不可用或响应结构变化时，回退到 DOM scoped JS eval / row feature filter。

边界：

- 不替代用户登录统一日志。
- 不替代设备平台。
- 不替代埋点行为链路。
- 不做自动风险定性。
- 不建议处罚。
- 不批量全量抓取。

## 2. 接口信息

```yaml
endpoint: /v3/user/log/coreLogs/fetch
full_url: https://admin.p.adm-corp.kuaishou.com/v3/user/log/coreLogs/fetch
method: POST
auth_context:
  browser_session_required: true
  same_origin_fetch: true
  auth_header_export_required: false
  csrf_required: false
  sensitive_headers_output: false
readonly_safety_check: required
```

本轮验证：

- 在已登录档案中心 browser session 内，通过 same-origin fetch 直接 POST 成功。
- 不需要导出 cookie / token / session。
- 不需要额外 anti-forgery marker header。
- response JSON 成功返回。
- `data.totalCount` 返回总数。
- `data.dataList` 返回列表。

## 3. 请求结构

```yaml
required_payload_fields:
  - loginStart
  - registerBind
  - resetPass
  - protectAccount
  - liveStream
  - scanCode
  - logout
  - frozen
  - beginTime
  - endTime
  - userId
  - pageSize
  - pageIndex
  - haveParamAuth
```

字段说明：

| 字段 | 含义 |
|---|---|
| `beginTime` / `endTime` | 毫秒时间戳 |
| `userId` | 目标用户 ID |
| `pageIndex` | 页码，从 1 开始 |
| `pageSize` | 每页数量 |
| `haveParamAuth` | 参数权限相关开关，含义待确认 |
| `loginStart` / `registerBind` / `resetPass` / `protectAccount` / `liveStream` / `scanCode` / `logout` / `frozen` | 操作类型筛选开关，`1=启用`，`0=关闭` |

filter policy：

- POC 阶段可默认全部为 1，以复刻页面当前查询结果。
- 不得写成永久硬编码业务规则。
- 长期优先读取页面 checkbox 状态。
- 读取失败时 fallback 到 HAR / 当前观察到的 all-on 默认值。

## 4. 响应结构

top-level fields：

- `result`
- `currentTime`
- `data`
- `costTime`
- `port`
- `clientIp`
- `host`
- `message`

data fields：

- `totalCount`
- `dataList`

record fields：

- `operateUri`
- `time`
- `operateType`
- `operateResult`
- `appVersion`
- `userIpDesc`
- `deviceId`
- `photoInfo`
- `requestParam`
- `extraParam`

## 5. 分页策略

```yaml
pagination_supported: true
page_index_field: pageIndex
page_size_field: pageSize
total_count_field: data.totalCount
list_field: data.dataList
has_more_policy: pageIndex * pageSize < totalCount
```

本轮验证：

```yaml
page_1:
  pageIndex: 1
  pageSize: 30
  totalCount: 5
  dataList_length: 5
page_2:
  pageIndex: 2
  totalCount: 5
  dataList_length: 0
has_more: false
```

解释：

- `pageIndex + pageSize` 分页机制已验证成功。
- `pageIndex=1` 返回 5 条。
- `pageIndex=2` 返回 0 条，`totalCount` 仍为 5，`has_more=false`。

## 6. risk_event_scan 输出

从 API response 生成：

```yaml
risk_event_scan:
  total_records_visible:
  operation_type_counts:
  success_failure_counts:
  earliest_event_time:
  latest_event_time:
  login_method_sequence:
  ip_consistency:
  device_consistency:
  app_version_consistency:
  geo_consistency:
  suspicious_event_markers:
  pagination_required:
  coverage_limitations:
```

规则：

- API direct POST 可直接从 response 生成 `risk_event_scan`。
- 不需要 DOM row feature filter 才能得到日志行。
- API 返回 record_fields 与 DOM 表格列一致，说明 API 是 DOM 表格数据源。

## 7. 敏感字段策略

never_output_raw：

- cookie
- token
- tokenId
- session
- KIM code
- password
- authorization
- anti-forgery marker / anti-forgery marker
- refresh_token
- sig
- open_id 明文
- 完整 requestParam
- 完整 extraParam
- 完整 response JSON

runtime_readable_but_not_persisted：

- userIpDesc
- deviceId
- requestParam
- extraParam
- open_id
- egid
- sig
- token 字段存在性
- appVersion
- photoInfo
- operateUri

persistable_structure_or_derived_features：

- 字段名
- 操作类型
- 成功失败
- 时间范围
- 分布
- 计数
- 地域前缀
- 设备去重计数
- APP 版本分布
- token_field_visible / tokenId_field_visible / open_id_field_visible

重要安全发现：

- `requestParam` / `extraParam` 中包含大量客户端指纹和敏感参数。
- `extraParam` 中可见 token / tokenId 字段。
- `requestParam` 中可能包含 open_id、sig、refresh_token、egid 等字段。
- 这些字段只能执行态读取用于派生判断，不得输出明文，不得沉淀完整 JSON。

## 8. 与 DOM 提取关系

- API direct POST 若可用，作为 `focused_login_risk` 默认优先路径。
- DOM scoped JS eval / row feature filter 作为 fallback。
- API 返回字段和 DOM 表格列一致，说明 API 是 DOM 表格数据源。
- API 可避免 selector noise / DOM 重复渲染 / 虚拟表格干扰。

推荐优先级：

1. API direct POST `/v3/user/log/coreLogs/fetch`
2. DOM scoped JS eval
3. row feature filter
4. scoped snapshot fallback

## 9. Failure modes

```yaml
failure_modes:
  - API_POST_FAILED
  - BROWSER_SESSION_NOT_AUTHENTICATED
  - CSRF_REQUIRED_BUT_UNAVAILABLE
  - RESPONSE_SHAPE_CHANGED
  - PAGINATION_UNSUPPORTED
  - SENSITIVE_JSON_TOO_RICH
  - API_EMPTY_RESULT
  - API_PERMISSION_BLOCKED
```

解释：

- `BROWSER_SESSION_NOT_AUTHENTICATED` 不等于用户无数据。
- `API_EMPTY_RESULT` 只能说明当前查询条件下 API 未返回记录。
- `SENSITIVE_JSON_TOO_RICH` 时应停止输出明细，只保留字段存在性和派生摘要。
- `RESPONSE_SHAPE_CHANGED` 时回退 DOM fallback，不强行解析。

## 10. 边界

- 不属于用户登录统一日志。
- 不替代统一登录日志。
- 不替代设备平台。
- 不替代埋点行为链路。
- 不做自动风险定性。
- 不建议处罚。
- 不批量全量抓取。
- 不导出认证态。
- 不输出敏感明文。

## 11. 当前状态

```yaml
version: v2.4.7.1
capability: user_analysis_core_logs_api
validation_status: archives_user_analysis_api_direct_post_validated
focused_login_risk_priority_path: api_direct_post
dom_extraction_fallback: available
core_skill_modified: false
release_package_updated: false
dataagent_boundary_changed: false
```
