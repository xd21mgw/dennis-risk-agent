# Observation Schema

## 1. 输出结构

```yaml
platform:
execution_mode:
target_duration:
actual_duration:
extraction_strategy:
query_object:
query_value:
auth_path:
state_saved:
state_file_policy:
login_status:
permission_status:
network_status:
page_status:
expected_failure:
failure_type:
safe_to_continue:
visible_modules:
hidden_or_missing_modules:
key_fields_observed:
sensitive_fields_visible:
sensitive_runtime_evidence_policy:
identity_context:
risk_relevant_observations:
next_suggested_platforms:
failure_reason:
manual_review_required:
readonly_safety_check:
tabs_requested:
tabs_observed:
list_sample_policy:
table_schema_probe:
risk_event_scan:
selector_profile:
time_range_policy:
api_direct_post_profile:
api_inventory_profile:
browser_spa_loop_guard:
evidence_card:
```

## 2. 字段说明

| 字段 | 含义 | 示例取值 |
|---|---|---|
| platform | 查询平台 | archives_center |
| execution_mode | 执行模式 | quick / focused_login_risk / focused_punishment_review / focused_content_risk / deep |
| target_duration | 目标耗时 | 1-2m / 3-5m / 5-7m |
| actual_duration | 实际耗时 | 实跑记录填写 |
| extraction_strategy | 抽取策略 | scoped_snapshot / structured_js_eval / full_snapshot_fallback |
| query_object | 查询对象类型 | user_id |
| query_value | 查询值 | 只记录用户输入，不额外扩展 |
| auth_path | 认证路径 | sso_kim_code, archives_independent_login, userid_direct_url |
| state_saved | 是否保存认证态 | true / false / unknown |
| state_file_policy | state 文件策略 | local_only_do_not_commit / not_saved |
| login_status | 登录状态 | logged_in / not_logged_in / unknown |
| permission_status | 权限状态 | permitted / no_permission / unknown |
| network_status | 网络状态 | ok / vpn_required / timeout / failed |
| page_status | 页面状态 | user_home_visible / no_result / load_failed / blocked |
| expected_failure | 是否为预期失败 | true / false |
| failure_type | 失败类型 | USER_NOT_FOUND / no_permission / saved_state_expired |
| safe_to_continue | 是否可继续当前查询 | true / false |
| visible_modules | 可见模块 | 用户基础信息、处罚状态、设备信息 |
| hidden_or_missing_modules | 不可见或缺失模块 | 登录信息、审核记录 |
| key_fields_observed | 关键字段可见性 | user_id visible, punish_status visible |
| sensitive_fields_visible | 高敏字段是否可见 | phone visible with masked_redacted |
| sensitive_runtime_evidence_policy | 敏感字段执行态与沉淀态策略 | runtime_read_allowed, persist_redacted |
| identity_context | 页面身份信息归属 | user_header target_object_allowed, nav_menu operator_identity_redacted |
| risk_relevant_observations | 风险相关页面观察 | 仅记录页面事实，不做最终结论 |
| next_suggested_platforms | 下一步建议平台 | 用户登录统一日志、设备攻防基建平台、天狮 |
| failure_reason | 失败原因 | no_permission / no_result / invalid_user_id |
| manual_review_required | 是否需要人工复核 | true / false |
| readonly_safety_check | 只读安全检查 | passed / stopped_due_to_write_risk |
| tabs_requested | 请求观察的 Tab | user_info_tab, user_analysis_tab |
| tabs_observed | 实际观察的 Tab | user_info_tab |
| list_sample_policy | 列表采样策略 | max_rows_observed=3 |
| table_schema_probe | 字段结构探测 | 表头 + 前 3 条结构，值 redacted |
| risk_event_scan | 风险事件扫描摘要 | 操作类型分布、成功失败分布、关键事件序列 |
| selector_profile | 选择器 / fallback 状态 | non_standard, mixed, fallback_used=true |
| time_range_policy | 时间范围策略 | record_actual_page_value |
| api_direct_post_profile | API direct POST 读取档案中心用户分析日志的结构 | endpoint, request_shape, response_shape, pagination_profile |
| api_inventory_profile | 档案中心 API inventory 覆盖矩阵 | module, endpoint, validation_status, fallback_strategy |
| browser_spa_loop_guard | browser / SPA 操作循环保护 | operation_loop_detected, failed_attempt_count, browser_overuse |
| evidence_card | 单案证据卡 | conclusion, confidence, strong/medium/weak/counter/missing evidence |

## 3. 输出边界

- observation 不等于 final judgement。
- 不记录高敏明文；redaction 是输出和沉淀策略，不是执行态研判禁止。
- 不输出用户名、手机号、设备 ID、IP、昵称、快手号等明文。
- 脱敏手机号也不输出具体脱敏串，只记录 `visible_masked_value_redacted`。
- IP、设备 ID、手机号、open_id、第三方登录标识、APP 版本、系统版本、地理位置描述、操作 URL path 和结果可以在内部 Agent 执行态用于生成派生风险特征，但不得在 run log、长期文档或普通 observation 中输出明文。
- cookie、token、session、KIM code、password、access token、refresh token、完整认证票据不得读取、不得输出、不得沉淀。
- 不生成封禁、解封、冻结、审批、策略上线等处置结论。
- 如页面无法确认字段含义，应写入 `failure_reason` 或 `risk_relevant_observations` 的“不确定”说明。
- 同一 browser / SPA 操作失败超过 3 次，必须写入 `browser_spa_loop_guard.operation_loop_detected=true` 并停止该 source。
- 单案研判 observation 应包含 `evidence_card` 或说明为何只能输出 partial evidence card。
- `USER_NOT_FOUND` 时 `expected_failure=true`、`safe_to_continue=false`，但 `readonly_safety_check` 仍可为 `PASSED`。

## 3.1 状态枚举

`state_reuse_status` 可取：

- `SUCCESS`
- `EXPIRED_RELOGIN_REQUIRED`
- `FAILED`
- `UNKNOWN`

`tab_status` 可取：

- `fully_loaded`
- `loaded_empty_or_no_rows`
- `permission_blocked`
- `failed`
- `not_clicked`

## 4. 敏感字段观测格式

敏感字段分为三层：

1. 禁止采集 / 禁止输出类：`cookie`、`token`、`session`、`KIM code`、`password`、`access token`、`refresh token`、完整认证票据。策略为 `never_collect`。
2. 执行态可读、沉淀态脱敏类：IP、设备 ID / did / egid、手机号、open_id、第三方登录标识、APP 版本、系统版本、地理位置描述、操作 URL path 和结果。允许执行态用于风控判断，沉淀时只能输出派生特征、计数、分布、一致性判断、hash 或 redacted 标记。
3. 可沉淀结构类：字段名、操作类型、成功 / 失败、时间范围、表头、Tab / 模块名、是否有数据、操作类型分布、成功失败分布。

```yaml
sensitive_runtime_evidence_policy:
  raw_value_access: never_collect / runtime_allowed / structure_only
  raw_value_persistence: never_persist / redacted_only / structure_allowed
  raw_value_display: never_display / redacted_only / structure_allowed
  derived_feature_output: allowed / not_allowed
```

敏感字段必须使用以下结构：

```yaml
- field_name:
  visibility:
  value_policy: redacted / masked_redacted / not_collected
  reason:
```

示例：

```yaml
- field_name: phone_number
  visibility: visible_masked
  value_policy: masked_redacted
  reason: 脱敏手机号可见，但 run log 不输出具体脱敏串
```

## 5. 身份信息观测格式

页面身份信息必须区分查询目标对象和当前登录操作者。

```yaml
identity_context:
  user_header:
    visibility:
    object_type: target_user
    user_id_match:
    value_policy: target_object_allowed / redacted
    reason:
  nav_menu:
    visibility:
    object_type: operator_account
    value_policy: operator_identity_redacted
    reason:
```

解释规则：

- `user_header` 如果展示的是查询目标用户，可用于确认页面对象是否与 `query_value` 匹配。
- `nav_menu`、右上角头像、当前登录账号名、操作者邮箱等属于 operator 身份，必须隐藏。
- 如果无法判断某个身份信息属于 target object 还是 operator，默认按 operator 处理并 redacted。

## 6. Execution Report Header

后续 deep-read observation 必须增加：

```yaml
execution_mode:
target_duration:
actual_duration:
extraction_strategy:
  - scoped_snapshot
  - structured_js_eval
  - full_snapshot_fallback
tabs_requested:
tabs_observed:
list_sample_policy:
time_range_policy:
```

## 7. List Sample Policy

列表读取分为两层：`table_schema_probe` 和 `risk_event_scan`。

`table_schema_probe` 只用于字段结构探测，不得用于完整风险判断。

```yaml
table_schema_probe:
  max_rows_observed: 3
  values_policy: redacted
  purpose: infer_table_schema_only
  pagination_followed: false
```

`risk_event_scan` 用于登录风险 / ATO / 协议上号 / 高危操作研判。

```yaml
risk_event_scan:
  enabled:
  time_range:
    start:
    end:
    source:
  operation_types_in_scope:
    - 启动登录
    - 注册绑定
    - 重置密码
    - 用户设置
    - 扫码
    - 注销
    - 冻结
  scan_policy:
    mode:
    pagination_policy:
    values_policy: redacted
  outputs:
    total_records_visible:
    operation_type_counts:
    success_failure_counts:
    earliest_event_time:
    latest_event_time:
    key_event_sequence:
    ip_consistency:
    device_consistency:
    app_version_consistency:
    geo_consistency:
    login_method_sequence:
    phone_or_binding_event_visible:
    third_party_login_visible:
    suspicious_event_markers:
    pagination_required:
    coverage_limitations:
  dedupe_policy:
    enabled:
    dedupe_key:
    raw_candidate_rows:
    deduped_rows:
    duplicate_reason:
```

规则：

- `table_schema_probe` 只看结构，不用于风险判断。
- `risk_event_scan` 可以使用执行态敏感字段生成派生判断，但不输出明文。
- IP、设备号、手机号、open_id、第三方登录标识、APP 版本、系统版本、地理位置描述、操作 URL path 和结果默认沉淀为 redacted 或派生特征。
- cookie、token、session、KIM code、password、access token、refresh token、完整认证票据永远 `never_collect`。
- 记录很多时，不全量输出；输出聚合摘要和关键事件序列。
- 分页未覆盖完整时间窗口时，必须标记 `pagination_required=true`。
- 不得根据前 3 条样例得出无风险结论。

## 8. API Direct POST Profile

档案中心用户分析 / APP端核心操作日志已验证 API direct POST 路径。

```yaml
api_direct_post_profile:
  endpoint:
  method:
  auth_context:
    browser_session_required:
    same_origin_fetch:
    auth_header_export_required:
    csrf_required:
    sensitive_headers_output:
  request_shape:
    required_payload_fields:
    filter_policy:
  response_shape:
    top_level_fields:
    data_fields:
    record_fields:
  pagination_profile:
    pagination_supported:
    page_index_field:
    page_size_field:
    total_count_field:
    list_field:
    has_more_policy:
  sensitive_json_policy:
    never_output_raw:
    runtime_readable_but_not_persisted:
    persistable_structure_or_derived_features:
```

解释规则：

- API direct POST 属于档案中心用户分析 Tab，不属于用户登录统一日志。
- API direct POST 若可用，作为 `focused_login_risk` 默认优先路径。
- DOM scoped JS eval / row feature filter 作为 fallback。
- `requestParam` / `extraParam` 中可能包含 token、tokenId、refresh_token、sig、open_id、egid 等敏感字段，只能执行态读取用于派生判断。
- 不输出完整 `requestParam`、完整 `extraParam`、完整 response JSON。
- 不输出 cookie、token、tokenId、refresh_token、sig、open_id 明文。

## 8.1 Archives Center API Inventory Profile

v2.4.7.2 已验证档案中心核心 API inventory。该 profile 用于记录档案中心模块级 API direct read 覆盖状态。

```yaml
api_inventory_profile:
  version: v2.4.7.2
  platform: archives_center
  default_read_strategy:
    - api_direct_read
    - dom_scoped_js_eval_fallback
    - row_feature_filter_fallback
    - scoped_snapshot_fallback
  page_fallback_trigger_conditions:
    - API failed
    - permission_blocked
    - response_shape_changed
    - key_fields_missing
    - link_url_only
    - mapping_pending_validation
  summary:
    candidate_api_count:
    success_count:
    failed_count:
    partial_count:
    auth_exported:
    sensitive_raw_values_output:
    write_operation_called:
    batch_full_crawl:
  modules:
    - module_name:
      endpoint:
      method:
      validation_status: validated / partial / failed
      api_can_replace_dom:
      request_shape:
      response_shape:
      pagination:
        supported:
        fields:
      sensitive_fields_policy:
      fallback_strategy:
      boundary:
  failed_apis:
    - endpoint:
      method:
      failure_reason:
      boundary:
  partial_apis:
    - endpoint:
      method:
      partial_scope:
      mapping_status:
      boundary:
```

规则：

- `validation_status=failed` 的接口不得写成可用。
- `validation_status=partial` 的接口不得写成 fully validated。
- `same_device type=0/type=1` 已在 v2.6.1 follow-up 完成映射验证：`type=0` 为同设备注册用户，`type=1` 为同设备登录用户；关联用户 ID / 昵称 / device 仍不得明文输出。
- API direct read 可替代 DOM 只代表读取路径可用，不代表自动风险定性。
- 页面 / DOM / selector 读取只作为 fallback，不应默认触发。
- 列表接口如未覆盖所有分页，必须记录 `partial_coverage=true`。
- 不输出手机号、IP、deviceId、open_id、sig、token、tokenId、refresh_token、完整 `requestParam`、完整 `extraParam`、完整 response JSON、关联用户 ID / 昵称 / device 明文。

## 8-B. Archives Capability Map Profile v2.6.1

v2.6.1 将档案中心 observation 从页面 / Tab 视角升级为 capability 视角。该 schema 用于记录档案中心 API-first capability observation，不代表自动风险定性。

```yaml
archives_capability_observation:
  version: v2.6.1
  platform: archives_center
  execution_mode: v2_6_1_capability_smoke_test / api_direct_read / fallback_read
  smoke_test_status:
    capability_smoke_test_passed:
    capability_count:
    basically_success_count:
    partial_count:
    full_api_regression:
  capability_package: account_profile / account_change_trace / account_action_log / content_gallery / content_forensics / social_interaction / report_signal / relation_graph
  scene:
  read_strategy:
    primary: api_direct_read
    fallback_order:
      - dom_scoped_js_eval
      - row_feature_filter
      - scoped_snapshot
  api_observations:
    - endpoint:
      method:
      validation_status: validated / smoke_validated / smoke_validated_empty_result / smoke_validated_partial_total_unreliable / mapping_validated / partial / failed / pending_from_har_or_screenshot_analysis / server_error_500_request_shape_uncertain_pending
      request_fields:
      response_shape:
      list_total_pagination_fields:
      list_len:
      total_semantics: trusted / unreliable / not_present / not_checked
      api_can_replace_dom:
      fallback_condition:
      partial_coverage:
      sensitive_fields:
      output_policy: derived_features_only
  fallback_used:
    used:
    reason: API failed / permission_blocked / response_shape_changed / key_fields_missing / link_url_only / mapping_pending_validation / need_required_param
    method: dom_scoped_js_eval / row_feature_filter / scoped_snapshot
  evidence_summary:
    current_metric_or_api_evidence:
    derived_features:
    report_or_user_feedback_signal:
    missing_evidence:
    counter_evidence:
  special_boundaries:
    empty_result_interpretation: not_counter_evidence
    getPunishStatus_user_level: unsupported
    getPunishStatus_photo_level: validated_with_targetType_PHOTO
    getPunishStatus_live_level: validated_with_targetType_LIVE_STREAM
    photo_report_search_status: validated_with_reportedIds_user_id_begin_end_sort
    message_search_total_semantics: unreliable_use_list_len_only
    photo_meta_missing_fields_proxy: use_profile_uploadSource_photoMethod_when_publishDevice_publishVersion_isImport_missing
    same_device_payload_shape: "{keyword, inputType: 0, type}"
    same_device_type_mapping: "type=0 same-device registered users; type=1 same-device login users"
  sensitive_output_check:
    never_output_raw:
      - cookie
      - token
      - tokenId
      - session
      - KIM code
      - password
      - authorization
      - CSRF/XSRF
      - access token / refresh token
      - open_id plaintext
      - sig plaintext
      - deviceId plaintext
      - IP plaintext
      - phone plaintext
      - full requestParam
      - full extraParam
      - full response JSON
      - full video meta JSON
      - full userRouteTrace
      - full private message content
      - full comment content
      - related user ID / nickname / device plaintext
      - avatar / background / media URL plaintext
    allowed_derived_features:
      - field_name
      - count
      - time_range
      - state_distribution
      - operation_type_distribution
      - risk_label
      - exists_or_absent
      - abnormality_flag
      - device_consistency_conclusion
      - content_type_summary
      - repetition_pattern_summary
      - diversion_risk_summary
      - posting_client_type
      - version_delta
      - import_flag
      - path_summary
  boundary:
    no_auto_enforcement:
    no_auto_risk_finalization:
    report_signal_not_strong_alone:
    same_device_mapping_validated_if_type_0_or_1:
    screenshots_not_interface_validation:
```

规则：

- `pending_from_har_or_screenshot_analysis` 不得升级为 `validated`，除非有已解析接口 response 或已实跑 observation。
- `smoke_validated` / `smoke_validated_empty_result` 只代表 v2.6.1 capability 小闭环对观察到的 request / response shape 成功，不代表全量接口回归。
- `empty_result` 不得解释为无行为、无日志、无变更或无风险。
- `/v4/archives/report/photo/search` follow-up 已验证；payload 必须使用 `reportedIds=<user_id>`、`begin/end` 毫秒时间戳、`sort` 字段，以及字符串 `matchType/sort`。旧 500 根因是 payload 字段名和语义错误。
- `/archives/user/message/search` 的 `total` 如出现疑似内部计数器，只能记录 `list_len` 和字段结构。
- `getPunishStatus` 不支持 user-level；photo-level 使用 `{targetId:<photoId>, targetType:"PHOTO"}`，live-level 使用 `{targetId:<liveStreamId>, targetType:"LIVE_STREAM"}`，targetType 必须大写。
- `photo/meta` 缺少 `publishDevice/publishVersion/isImport` 时，可使用 `profile.uploadSource/photoMethod` 等代理字段，但必须标记 proxy。
- 私信 / 评论 / 视频 meta / userRouteTrace 只能输出摘要和派生特征，不输出原文。
- 用户举报 / 视频举报不能单独作为强证据。
- same-device `type=0/type=1` 已验证映射：`type=0` 同设备注册用户，`type=1` 同设备登录用户；不使用旧 `{userId, source, type}` payload。

## 9. User Analysis Selector Profile

用户分析 Tab 可能不是标准表格结构，必须记录 selector profile。

```yaml
user_analysis_tab:
  selector_profile:
    table_structure: standard_ant_table / ks_table / mixed_dom / unknown
    extraction_method: ant_table_selector / ks_table_selector / active_tab_container_selector / row_feature_filter / scoped_snapshot / mixed
    fallback_used: true / false
    selector_noise:
      present:
      source:
      mitigation:
    selector_noise_present:
    selector_noise_mitigation:
    active_tab_container_used:
    row_feature_filter_used:
  table_schema_probe:
    status: validated / failed / skipped
  risk_event_scan:
    status: pending / partial_validated / partial_validated_with_selector_noise / validated / failed
    reason:
    dedupe_policy:
      enabled:
      dedupe_key:
      raw_candidate_rows:
      deduped_rows:
      duplicate_reason:
  row_filter_policy:
    require_time_format:
    require_operation_url_or_operation_type:
    exclude_non_log_sections:
    values_policy:
```

规则：

- `table_schema_probe.status=validated` 不等于 full risk_event_scan 已完成。
- 如果 `risk_event_scan.status=pending`，不得输出完整登录风险研判。
- 如果使用 fallback extraction，必须说明原因和覆盖限制。
- 如果 `selector_noise.present=true`，不得标记 full validated。
- 用户分析 Tab 已发现 `ks-table__row` 非标准表格结构；应优先使用 active tab container，其次使用 row feature filter。
- row feature filter 应优先保留包含时间格式、操作 URL / 操作类型、操作结果、APP 版本、IP 描述、设备字段的日志行，并排除用户信息 Tab 的平台操作、直播功能、电商功能等非日志表格行。
- 如果 DOM 中同一日志行重复渲染，必须启用 dedupe，并记录 raw candidate rows、deduped rows 与 duplicate_reason。
- selector noise 已通过 row feature filter 修复时，可记录 `selector_noise_present=false`、`row_feature_filter_used=true`、`risk_event_scan.status=validated`。
