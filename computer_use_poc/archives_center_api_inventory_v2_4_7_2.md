# 档案中心 API Inventory Validation v2.4.7.2

## 1. 定位

v2.4.7.2 是档案中心核心 API inventory validation。

本阶段目标是验证档案中心 `userId` direct URL 用户详情页中，除已验证的「用户分析 / APP端核心操作日志」`/v3/user/log/coreLogs/fetch` 之外，哪些核心候选 API 可以在已登录档案中心 browser session 内通过只读 API direct read 替代 DOM / selector 读取。

边界：

- 不是新平台。
- 不改变 DataAgent 边界。
- 不引入自动处置。
- 不引入自动风险定性。
- 不导出认证态。
- 不输出敏感明文。
- 不批量全量抓取。

## 2. 读取策略

档案中心后续默认使用 API direct read。页面 / DOM / selector 读取只作为 fallback，不应默认触发。

默认读取顺序：

1. API direct read。
2. DOM scoped JS eval fallback。
3. row feature filter fallback。
4. scoped snapshot fallback。

页面 fallback 仅在以下条件触发：

- `API failed`。
- `permission_blocked`。
- `response_shape_changed`。
- `key_fields_missing`。
- `link_url_only`。
- `mapping_pending_validation`。

解释：

- API direct read 若可用，优先用于结构化读取，降低 DOM selector noise、虚拟表格、重复渲染和页面滚动成本。
- DOM scoped JS eval 仍保留为 API shape 变化、关键字段缺失、权限阻断或 link-only 页面时的只读 fallback。
- row feature filter 仅用于列表型 DOM 混杂场景。
- scoped snapshot 只作为最后兜底，不应作为默认读取方式。

已验证 API 覆盖模块必须优先走 API：

- `home_info`。
- `negative / risk / label / shop / punish`。
- `reviewLogs`。
- `user_analyze_summary`。
- `coreLogs`。
- `photo_gallery / photo_detail`。
- `live_gallery`。
- `fans / follow`。
- `collect / collection`。
- `same_device_users`，v2.6.1 follow-up 已验证 `type=0` 为同设备注册用户、`type=1` 为同设备登录用户。

边界：

- 未验证 / 失败 / partial 接口不得标 fully validated。
- same_device `type=0 / type=1` 已在 v2.6.1 follow-up 中完成语义映射验证；后续不得回退到旧 `{userId, source, type}` payload。
- `requestParam` / `extraParam` / full JSON / token-like 字段不得输出。
- 页面兜底不应默认触发。
- API direct read 只代表读取路径可用，不代表自动风险定性。

## 3. 验证总览

```yaml
archives_center_api_inventory_validation:
  version: v2.4.7.2
  execution_mode: api_inventory_validation_poc
  candidate_api_count: 28
  success_count: 24
  failed_count: 3
  partial_count: 5
  auth_exported: false
  sensitive_raw_values_output: false
  write_operation_called: false
  batch_full_crawl: false
  risk_classification_generated: false
```

## 4. API 覆盖矩阵

### 4.1 home_info

```yaml
home_info:
  endpoint: /archives/user/home/info
  method: GET
  validation_status: validated
  api_can_replace_dom: true
  request_shape: userId query parameter
  response_shape: user home profile structure
  pagination: none
  sensitive_fields_policy: structure_and_derived_only
  fallback_strategy: DOM scoped JS eval / scoped snapshot
```

### 4.2 negative_report

```yaml
negative_report:
  endpoint: /v3/user/negative/report
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: userId payload with query context
  response_shape: negative status / realtime negative modules
  pagination: none_observed
  sensitive_fields_policy: field_names_status_counts_only
  fallback_strategy: DOM scoped JS eval
```

### 4.3 negative_uninterested

```yaml
negative_uninterested:
  endpoint: /v3/user/negative/unInterested
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: userId payload with query context
  response_shape: uninterested / negative related status structure
  pagination: none_observed
  sensitive_fields_policy: field_names_status_counts_only
  fallback_strategy: DOM scoped JS eval
```

### 4.4 risk_info

```yaml
risk_info:
  endpoint: /v3/user/risk/info
  method: GET
  validation_status: validated
  api_can_replace_dom: true
  request_shape: userId query parameter
  response_shape: risk info structure
  pagination: none
  sensitive_fields_policy: status_and_field_names_only
  fallback_strategy: DOM scoped JS eval
```

### 4.5 user_label

```yaml
user_label:
  endpoint: /archives/user/home/getUserLabel
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: userId payload
  response_shape: user label list / label status
  pagination: none_observed
  sensitive_fields_policy: label_names_status_counts_only
  fallback_strategy: DOM scoped JS eval
```

### 4.6 shop_info

```yaml
shop_info:
  endpoint: /archives/user/home/getUserShopInfo
  method: GET
  validation_status: validated
  api_can_replace_dom: true
  request_shape: userId query parameter
  response_shape: shop info structure
  pagination: none
  sensitive_fields_policy: field_visibility_and_status_only
  fallback_strategy: DOM scoped JS eval
```

### 4.7 punish_status

```yaml
punish_status:
  endpoint: /archives/draco/getPunishStatus
  method: POST
  validation_status: photo_live_validated_user_level_unsupported
  api_can_replace_dom: true
  request_shape: "{targetId: <photoId>, targetType: PHOTO} or {targetId: <liveStreamId>, targetType: LIVE_STREAM}"
  response_shape: punish status list / status summary
  pagination: none_observed
  sensitive_fields_policy: status_names_and_counts_only
  fallback_strategy: DOM scoped JS eval
  boundary: user-level unsupported; targetType must be uppercase PHOTO or LIVE_STREAM
```

### 4.8 review_log

```yaml
review_log:
  endpoint: /v3/user/log/reviewLogs/fetch
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: userId, time_range, filters, page fields
  response_shape: review log list with columns / total count
  pagination: supported_or_shape_detected
  sensitive_fields_policy: reviewer_or_remark_text_redacted; field_names_status_counts_only
  fallback_strategy: DOM scoped JS eval / scoped snapshot
```

失败候选：

```yaml
legacy_audit_log:
  endpoint: /archives/user/home/auditLog
  method: POST
  validation_status: failed
  api_can_replace_dom: false
  failure_reason: needs_punishId_or_required_param
  boundary: 单 userId 不足，不得写成可用
```

Partial option API：

```yaml
audit_log_options:
  endpoint: auditLogOptions / getLogOption
  method: GET / POST
  validation_status: partial
  api_can_replace_dom: false_for_data_list
  partial_scope: option_structure_only
  boundary: 只验证筛选项结构，非审核日志数据列表
```

### 4.9 user_analyze_summary

```yaml
user_analyze_summary:
  endpoint: /v3/user/analyze/fetch
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: userId, time_range, analyze filters
  response_shape: user analysis summary / matrix
  pagination: none_or_shape_specific
  sensitive_fields_policy: aggregate_counts_and_distribution_only
  fallback_strategy: DOM scoped JS eval
```

补充：`/v3/user/log/coreLogs/fetch` 已在 v2.4.7.1 验证，是「用户分析 / APP端核心操作日志」列表数据源；v2.4.7.2 不重复计入本 inventory 成功接口清单，但读取策略继续优先使用。

### 4.10 photo_gallery

```yaml
photo_gallery_top:
  endpoint: /v3/user/gallery/photo/top
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: userId payload
  response_shape: top photo gallery structure
  pagination: none_observed
  sensitive_fields_policy: photo_id_title_values_redacted_by_default
  fallback_strategy: DOM scoped JS eval

photo_gallery_list:
  endpoint: /v3/user/gallery/photo/list
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: userId, pageIndex, pageSize, filters
  response_shape: photo list with totalCount
  pagination:
    supported: true
    fields: pageIndex / pageSize / totalCount
  sensitive_fields_policy: photo_id_title_values_redacted_by_default; counts_and_status_allowed
  fallback_strategy: DOM scoped JS eval / scoped snapshot
```

### 4.11 photo_detail

```yaml
photo_profile:
  endpoint: /v3/photo/profile
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: photo identifier payload
  response_shape: photo profile structure
  pagination: none
  sensitive_fields_policy: field_names_status_counts_only
  fallback_strategy: DOM detail modal / scoped snapshot

photo_meta:
  endpoint: /v3/photo/meta
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: photo identifier payload
  response_shape: photo metadata structure
  pagination: none
  sensitive_fields_policy: field_names_status_counts_only
  fallback_strategy: DOM detail modal / scoped snapshot

photo_report_aggregate:
  endpoint: /v3/photo/report/aggregate
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: photo identifier payload
  response_shape: report aggregate structure
  pagination: none
  sensitive_fields_policy: aggregate_counts_only
  fallback_strategy: DOM detail modal / scoped snapshot

photo_user_autonomy:
  endpoint: /archives/photo/home/userAutonomy
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: photo identifier payload
  response_shape: autonomy status structure
  pagination: none
  sensitive_fields_policy: status_only
  fallback_strategy: DOM detail modal / scoped snapshot
```

### 4.12 live_gallery

```yaml
live_gallery:
  endpoint: /v4/archives/gallery/live/list
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: userId, page, count, filters
  response_shape: live list with total
  pagination:
    supported: true
    fields: page / count / total
  sensitive_fields_policy: live identifiers_and_titles_redacted_by_default; counts_and_status_allowed
  fallback_strategy: DOM scoped JS eval / scoped snapshot
```

### 4.13 fans_list

```yaml
fans_list:
  endpoint: /v3/user/profile/relation/fans/list
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: userId, pageIndex, pageSize
  response_shape: relation list with totalCount
  pagination:
    supported: true
    fields: pageIndex / pageSize / totalCount
  sensitive_fields_policy: related_user_ids_and_names_redacted; counts_only
  fallback_strategy: DOM scoped JS eval / scoped snapshot
```

### 4.14 follow_list

```yaml
follow_list:
  endpoint: /v3/user/profile/relation/follow/list
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: userId, pageIndex, pageSize
  response_shape: relation list with totalCount
  pagination:
    supported: true
    fields: pageIndex / pageSize / totalCount
  sensitive_fields_policy: related_user_ids_and_names_redacted; counts_only
  fallback_strategy: DOM scoped JS eval / scoped snapshot
```

### 4.15 collect_photo_list

```yaml
collect_photo_list:
  endpoint: /v3/user/collect/photo/list
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: userId, page, count
  response_shape: collect photo list with totalCount
  pagination:
    supported: true
    fields: page / count / totalCount
  sensitive_fields_policy: photo_ids_titles_related_users_redacted; counts_and_status_allowed
  fallback_strategy: DOM scoped JS eval / scoped snapshot
```

Partial search option APIs：

```yaml
collect_music_search_option:
  endpoint: /v3/user/collect/music/searchOption
  method: GET
  validation_status: partial
  api_can_replace_dom: false_for_data_list
  partial_scope: filter_option_structure_only
  boundary: 只验证筛选项，未验证实际收藏音乐列表

collect_folder_search_option:
  endpoint: /v3/user/collect/folder/searchOption
  method: GET
  validation_status: partial
  api_can_replace_dom: false_for_data_list
  partial_scope: filter_option_structure_only
  boundary: 只验证筛选项，未验证实际收藏文件夹列表
```

### 4.16 collection_list

```yaml
collection_list:
  endpoint: /archives/photo/collection/getCollectionList
  method: POST
  validation_status: validated
  api_can_replace_dom: true
  request_shape: userId, page, size
  response_shape: collection list with totalCount
  pagination:
    supported: true
    fields: page / size / totalCount
  sensitive_fields_policy: collection_ids_titles_related_users_redacted; counts_and_status_allowed
  fallback_strategy: DOM scoped JS eval / scoped snapshot
```

### 4.17 same_device_users

```yaml
same_device_users_type_0:
  endpoint: /archives/user/search/device
  method: POST
  validation_status: mapping_validated
  api_can_replace_dom: true
  request_shape: "{keyword: <user_id>, inputType: 0, type: 0}"
  response_shape: related user list
  pagination: shape_detected_if_present
  sensitive_fields_policy: related_user_ids_names_devices_redacted; counts_only
  fallback_strategy: DOM scoped JS eval / scoped snapshot
  mapping_status: mapping_validated
  boundary: type=0 表示同设备注册用户；不输出关联用户 ID / 昵称 / device 明文

same_device_users_type_1:
  endpoint: /archives/user/search/device
  method: POST
  validation_status: mapping_validated
  api_can_replace_dom: true
  request_shape: "{keyword: <user_id>, inputType: 0, type: 1}"
  response_shape: related user list
  pagination: shape_detected_if_present
  sensitive_fields_policy: related_user_ids_names_devices_redacted; counts_only
  fallback_strategy: DOM scoped JS eval / scoped snapshot
  mapping_status: mapping_validated
  boundary: type=1 表示同设备登录用户；不输出关联用户 ID / 昵称 / device 明文
```

## 5. 失败接口

```yaml
failed_apis:
  - endpoint: /archives/user/home/auditLog
    method: POST
    validation_status: failed
    failure_reason: needs_punishId_or_required_param
    boundary: 单 userId 不足，不得写成可用

  - endpoint: /archives/draco/getLabelLog
    method: POST
    validation_status: failed
    failure_reason: needs_punishId_or_required_param
    boundary: 单 userId 不足，不得写成可用

  - endpoint: /archives/report/countFlatted
    method: GET
    validation_status: failed
    failure_reason: result_500_or_extra_param_required
    boundary: 可能需要额外参数或权限，不得写成可用
```

## 6. Pagination Profile

已验证分页支持：

```yaml
pagination_validated:
  - endpoint: /v3/user/gallery/photo/list
    fields: pageIndex / pageSize / totalCount
  - endpoint: /v4/archives/gallery/live/list
    fields: page / count / total
  - endpoint: /v3/user/profile/relation/fans/list
    fields: pageIndex / pageSize / totalCount
  - endpoint: /v3/user/profile/relation/follow/list
    fields: pageIndex / pageSize / totalCount
  - endpoint: /v3/user/collect/photo/list
    fields: page / count / totalCount
  - endpoint: /archives/photo/collection/getCollectionList
    fields: page / size / totalCount
```

分页 guardrail：

- 未覆盖全部分页前必须标记 `partial_coverage=true`。
- `totalCount > visible_or_requested_count` 时不得声称已查看全量。
- API 可分页不等于允许批量全量抓取；本 POC 不做批量全量抓取。

## 7. 敏感字段策略

继续沿用档案中心只读敏感字段策略。

禁止输出明文：

- 手机号。
- IP。
- deviceId。
- open_id。
- sig。
- token。
- tokenId。
- refresh_token。
- 完整 `requestParam`。
- 完整 `extraParam`。
- 完整 response JSON。
- 关联用户 ID / 昵称 / device 明文。
- cookie / session / KIM code / authorization。

允许沉淀：

- 字段名。
- 计数。
- 分布。
- 状态。
- 分页字段。
- validation status。
- 派生特征。
- `present_redacted` / `absent` / `mapping_pending_validation` 等结构标记。

## 8. Failure / Partial 边界

- 失败接口不得写成可用。
- Partial 接口不得写成 fully validated。
- `auditLogOptions / getLogOption` 只验证 option 结构，不代表审核日志数据列表可用。
- `collect music / folder searchOption` 只验证筛选项，不代表实际数据列表可用。
- `/archives/user/search/device type=0/type=1` 在 v2.4.7.2 仅验证接口成功；v2.6.1 follow-up 已补齐页面入口文案和 payload 对应关系验证。
- same_device type 当前可按 v2.6.1 follow-up 使用：`type=0` 同设备注册用户，`type=1` 同设备登录用户。
- API inventory 只说明读取路径可用性，不输出风险定性。

## 9. 后续建议

- 将档案中心 deep-read 默认实现从 DOM 优先切换为 API direct read 优先。
- 对 failed APIs 补充 required param 来源探索时，必须继续保持只读，不得点击写操作。
- same_device type=0/type=1 已在 v2.6.1 follow-up 完成业务语义映射验证；后续重点是分页、脱敏和异常口径验证。
- 列表型 API 后续如进入完整覆盖，必须先定义分页上限、采样策略和输出 redaction 策略。

## 10. v2.6.1 Capability Map Linkage

v2.4.7.2 保持为历史 API inventory validation 记录，不继续派生新版本。v2.6.1 的新增沉淀见：

- `computer_use_poc/archives_center_core_capability_map_v2_6_1.md`

v2.6.1 将档案中心从页面 / Tab 视角升级为风控 capability 视角，核心 capability 包包括：

- `account_profile`
- `account_change_trace`
- `account_action_log`
- `content_gallery`
- `content_forensics`
- `social_interaction`
- `report_signal`
- `relation_graph`

v2.6.1 继续沿用 API-first 策略：

```text
API direct read
→ DOM scoped JS eval fallback
→ row feature filter fallback
→ scoped snapshot fallback
```

页面 fallback 仅在 `API failed`、`permission_blocked`、`response_shape_changed`、`key_fields_missing`、`link_url_only`、`mapping_pending_validation`、`need_required_param` 时触发。

### 10.0 v2.6.1 Capability Smoke Test Status

最新内部 Agent observation 已完成 `execution_mode=v2_6_1_capability_smoke_test`：

- 8 个 capability 均完成 API-first 小闭环验证。
- 6 个 capability 基本成功。
- 2 个 capability partial。
- 页面 / DOM / selector 未默认触发。
- fallback 只在允许条件下触发。
- 无敏感明文输出。
- 无认证态导出。
- 无写操作。
- 无风险定性。
- 无处罚建议。

边界：

- 这是 capability smoke test passed，不是全量接口回归。
- `empty_result` 不得解释为无行为、无日志、无风险或无变更。
- partial / 500 / request shape uncertain 不得写成 fully validated。
- `getPunishStatus` 不作为通用 user-level API；photo-level / live-level 已验证，需要 `targetType=PHOTO` 或 `targetType=LIVE_STREAM`。
- `message/search total` 语义不可信，只记录 `list_len` 和字段结构。
- `same_device type=0/type=1` 语义已验证：`type=0` 为同设备注册用户，`type=1` 为同设备登录用户。

### 10.0-A v2.6.1 Follow-up Validation Patch

Follow-up validation updated three previously partial / pending boundaries:

- `POST /v4/archives/report/photo/search` is validated with corrected payload shape:
  `{matchType:"0", reportedIds:"<user_id>", sort:"0", begin:<ms_timestamp>, end:<ms_timestamp>, page:1, count:20}`.
  `reportedIds` uses `user_id`, not `photoId`; `begin/end` are millisecond timestamps; `sort` is the field name, not `sortType`; `matchType` and `sort` are strings.
- `POST /archives/draco/getPunishStatus` is validated only for photo and live targets:
  `{targetId:"<photoId>", targetType:"PHOTO"}` and `{targetId:"<liveStreamId>", targetType:"LIVE_STREAM"}`.
  User-level is unsupported; lowercase targetType values are invalid.
- `POST /archives/user/search/device` mapping is validated with payload `{keyword:"<user_id>", inputType:0, type}`.
  `type=0` means same-device registered users; `type=1` means same-device login users.

### 10.1 v2.6.1 Added / Pending API Inventory

以下接口来自最新档案中心有效动作 HAR / 截图分析结果。它们应先进入 inventory，但不得仅凭截图内容写成接口 validated；`validation_status` 默认记录为 `pending_from_har_or_screenshot_analysis`，只有已解析接口 response 或已实跑 observation 才能升级为 `validated`。

| capability | endpoint | method | request fields | response shape | list / total / pagination fields | sensitive fields | validation_status | api_can_replace_dom | fallback condition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| report_signal | `/v4/archives/report/user/options` | GET | user/report context | option structure | none | reporter / target identifiers | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param / mapping_pending_validation |
| report_signal | `/v4/archives/report/user/search` | POST | userId, time/filter/page | user report list | empty_result observed in smoke sample | reporter / target identifiers, report text | smoke_validated_empty_result | true_for_observed_shape | key_fields_missing / empty_result_not_counter_evidence |
| account_change_trace | `/v4/audit/user/fourinfo/log/allTypes` | POST | userId/context | four-info type/options | none | operator / audit notes | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| account_change_trace | `/v4/audit/user/fourinfo/log/search` | POST | userId, type/time/page | four-info change list | empty_result observed in smoke sample | old/new profile text/media URL/operator | smoke_validated_empty_result | true_for_observed_shape | need_required_param / empty_result_not_counter_evidence |
| social_interaction | `/archives/photo/comment/search` | POST | photoId/userId/filter/page | comment list | list_len and field structure observed | comment plaintext, commenter id | smoke_validated | true_for_observed_shape | need_required_param |
| social_interaction | `/archives/photo/comment/types` | GET | comment context | type options | none | none expected | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/photo/comment/status` | POST | comment context | status options | none | none expected | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/photo/comment/userStatus` | POST | user/comment context | user status options | none | user identifiers | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/photo/comment/queryTypes` | POST | comment context | query type options | none | none expected | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/photo/comment/orders` | POST | comment context | order options | none | none expected | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/photo/comment/keyMaps` | POST | comment context | key map/options | none | internal field mapping | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| report_signal | `/v4/archives/report/photo/options` | GET | photo/report context | option structure | none | reporter / target identifiers | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param / mapping_pending_validation |
| report_signal | `/v4/archives/report/photo/search` | POST | `reportedIds=<user_id>`, `matchType/sort` strings, `begin/end` ms, `page/count` | photo report list | `totalCount`, `dataList`, page/count | reporter / target identifiers, report text | validated | true | API failed / permission_blocked / response_shape_changed / key_fields_missing |
| social_interaction | `/archives/user/message/search` | POST | userId/filter/page | private message list | list_len observed; total unreliable | private message plaintext, counterpart id | smoke_validated_partial_total_unreliable | true_for_list_shape_only | total_semantics_untrusted / permission_blocked |
| social_interaction | `/archives/user/message/options` | POST | user message context | option structure | none | internal field mapping | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/user/message/keyMaps` | POST | user message context | key map/options | none | internal field mapping | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| content_forensics | `/archives/livestream/home/info` | POST | liveId/userId | live home info | none | live media URL, anchors/users | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |
| content_forensics | `/archives/livestream/home/meta` | POST | liveId/userId | live meta | none | full live meta JSON | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |
| content_forensics | `/archives/livestream/home/log` | POST | liveId/userId/time | live audit/log list | list/total/page fields pending | operator / notes / raw log | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |
| social_interaction | `/archives/livestream/comment/statistics` | POST | liveId/filter | live comment statistics | aggregate fields | comment content samples | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |
| social_interaction | `/archives/livestream/comment/detail` | POST | liveId/filter/page | live comment detail list | list/total/page fields pending | comment plaintext, commenter id | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param / permission_blocked |
| content_gallery | `/archives/user/gallery/momentList` | POST | userId/page/filter | moment list | empty_result observed in smoke sample | content plaintext/media URL | smoke_validated_empty_result | true_for_observed_shape | key_fields_missing / empty_result_not_counter_evidence |
| content_gallery | `/archives/user/gallery/momentAuthority` | POST | userId/moment context | moment authority/status | none | internal status reason | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |
