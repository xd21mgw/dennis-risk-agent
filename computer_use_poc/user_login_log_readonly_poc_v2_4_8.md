# v2.4.8 用户登录统一日志 Readonly POC

## 一、v2.4.8 定位

v2.4.8 是第二个 browser computer use readonly 平台 POC。

平台名称：

- 用户中心智能工作台 / 账号问题排查 / 统一日志查询

默认入口 URL：

```text
https://user-center-workbench.corp.kuaishou.com/create-applications/unified-log-search
```

服务场景：

- ATO。
- 异常登录。
- 协议上号。
- 撞库尝试。
- OAuth / 扫码异常。
- 高危接口调用核查。

边界：

- 当前入口和能力均为 pending validation，不得写成 validated。
- 不替代档案中心。
- 不替代设备平台。
- 不替代埋点 / 用户行为细查。
- 不替代 DataAgent / Hive 离线取数。
- 不做自动定性。
- 不做处置。

## 二、真实页面结构

页面左侧：

- 用户中心智能工作台。
- 账号问题排查。
- 工具中心等菜单。

查询条件区：

- 开始时间。
- 结束时间。
- User ID。
- DID。
- 日志来源 checkbox：
  - 增长登录相关日志。
  - 账号登录相关日志。
  - 业务鉴权日志。
  - 高危接口调用日志。
- Query 关键词。
- 查询按钮。
- 重置按钮。

查询结果列表字段：

- 时间。
- 标签。
- User ID。
- DID。
- Method。
- 日志来源。
- 日志内容 / 查看详情。

详情弹窗：

- 点击“查看详情”后出现“日志详情”弹窗。
- 弹窗包含时间、标签、User ID、DID、Method、日志来源、JSON 数据、复制按钮、关闭按钮。

JSON 数据中可能出现：

- userId。
- timestamp。
- deviceId。
- userIp。
- userIpv6。
- serverIp。
- sysVer。
- appVer。
- uri。
- status。
- phoneModel。
- params。
- token / session / 认证相关字段可能出现在 params 或 extra 字段中。

## 三、time_range 限制

必须明确：

- 实时系统只能查询最近 7 天登录记录。
- 默认使用页面自动填充的最近 7 天时间范围。
- 除非用户明确要求调整，否则 Dennis / browser computer use 不主动修改时间。
- 如果用户给的 time_range 超过最近 7 天，不能在实时页面直接查询。
- 应返回 `TIME_RANGE_OUT_OF_REALTIME_WINDOW`。
- 需要离线补证时，建议 DataAgent / Hive 或离线日志能力。
- 不得把“超过 7 天查不到”解释为“没有登录记录”。
- 不得将实时页面无结果解释为全量无记录。

```yaml
time_range_policy:
  realtime_window_days: 7
  default_use_page_autofilled_recent_7d: true
  requested_range:
  effective_range:
  range_status:
    - within_realtime_window
    - out_of_realtime_window
    - adjusted_to_recent_7d
```

## 四、输入参数

最小输入：

- `user_id`
- `time_range`，必须在最近 7 天内；如果用户未指定，默认使用页面自动填充最近 7 天。

可选输入：

- `did`
- `login_method`
- `operation_type`
- `client_type / platform_type`
- `result_status`
- `query_keyword`
- `log_sources`

## 五、execution_mode

### quick_login_check

目标：

- 只看登录成功失败分布、登录方式字段是否可见。
- 读取结果列表字段。

目标耗时：1-2 分钟。

### focused_ato_check

目标：

- 登录方式。
- OAuth / 扫码。
- token/session 字段可见性。
- 高危接口调用摘要。

动作：

- 必要时打开前 1-2 条“查看详情”只读弹窗。

目标耗时：2-4 分钟。

### deep_login_trace

目标：

- 目标时间窗口内登录链路摘要。
- 不输出敏感明文。
- 不复制完整 JSON。

目标耗时：3-5 分钟。

## 六、标准 observation schema

```yaml
user_login_log_observation:
  platform: user_login_unified_log
  platform_display_name: 用户中心智能工作台 / 账号问题排查 / 统一日志查询
  entry_url:
  query_object:
  query_value_policy:
  execution_mode:
  actual_duration:
  state_reuse_status:
  page_status:
  time_range_policy:
    realtime_window_days:
    default_use_page_autofilled_recent_7d:
    requested_range:
    effective_range:
    range_status:
  query_form:
    start_time_filled:
    end_time_filled:
    user_id_filled:
    did_filled:
    log_sources_checked:
    query_keyword_filled:
  filters_visible:
  result_table:
    table_or_list_present:
    row_count:
    fields_visible:
      time:
      label:
      user_id:
      did:
      method:
      log_source:
      detail_entry:
    methods_observed:
    log_sources_observed:
    pagination:
  detail_modal:
    opened:
    max_detail_rows_opened:
    detail_rows_opened:
    fields_visible:
      time:
      label:
      user_id:
      did:
      method:
      log_source:
      json_data:
    copy_button_clicked: false
    detail_values_policy: derived_features_only
  field_visibility:
    login_time:
    login_method:
    login_result:
    oauth_fields:
    scan_fields:
    token_session_fields:
    high_risk_operation_fields:
    ip_fields:
    device_fields:
    app_version_fields:
    client_type_fields:
  risk_event_scan:
    status:
    total_records_visible:
    operation_type_counts:
    success_failure_counts:
    login_method_counts:
    method_counts:
    oauth_or_scan_visible:
    token_session_field_visible:
    high_risk_operation_sequence:
    earliest_event_time:
    latest_event_time:
    ip_consistency:
    device_consistency:
    app_version_consistency:
    geo_consistency:
    suspicious_event_markers:
    pagination_required:
    coverage_limitations:
    values_policy:
  sensitive_runtime_evidence_policy:
  readonly_safety_check:
  failure_reason:
```

## 七、详情弹窗读取策略

“查看详情”是允许的只读动作，但需要严格限制。

允许：

- 点击“查看详情”打开只读弹窗。
- 读取字段名。
- 读取字段是否存在。
- 读取派生特征。
- 读取 method / uri path / status 等结构信息。

禁止：

- 点击复制按钮复制完整 JSON。
- 输出完整 JSON。
- 输出 IP、deviceId、userIpV6、serverIp、params、token、session 等明文。
- 输出认证票据。
- 导出、批量下载、处置。

```yaml
detail_scan_policy:
  max_detail_rows_opened: 1-2
  detail_values_policy: derived_features_only
  copy_button_clicked: false
```

## 八、敏感字段三层策略

### never_collect

- cookie。
- token 原文。
- session 原文。
- KIM code。
- password。
- access token / refresh token。
- 完整认证票据。
- 完整 JSON 中的认证凭据。

### runtime_readable_but_not_persisted

- IP。
- deviceId / did / egid。
- 手机号。
- open_id。
- OAuth 标识。
- 扫码相关字段。
- APP 版本。
- 系统版本。
- 地理位置。
- uri path / method / status。
- token/session 字段“是否可见”的结构信息。

### persistable_structure

- 字段名。
- Method。
- 标签。
- 日志来源。
- 登录方式。
- 操作类型。
- 成功失败。
- 时间范围。
- 表头。
- 分布。
- 计数。
- 是否有 OAuth / 扫码 / token/session 字段。

## 九、只读安全规则

允许：

- 打开入口 URL。
- 输入 user_id / DID / time_range。
- 使用页面自动填充最近 7 天时间。
- 选择日志来源 checkbox。
- 点击查询按钮。
- 切换只读筛选。
- 点击“查看详情”打开只读弹窗。
- 关闭弹窗。

禁止：

- 点击复制完整 JSON。
- 导出。
- 批量下载。
- 处置。
- 输出认证票据明文。
- 输出操作者账号明文。

## 十、selector / extraction 策略

- 不默认 full snapshot。
- 优先 scoped extraction / structured JS eval。
- 先做字段结构探测，再做 risk_event_scan。
- 结果列表不全量输出明文，只输出摘要 / 分布 / 派生特征。
- 详情弹窗只提取字段名和派生特征。
- 如果表格不是标准 ant-table，需要记录 selector_profile。
- 如果分页导致覆盖不全，标记 pagination_required / coverage_limitations。

## 十一、failure modes

- `LOGIN_REQUIRED`
- `PERMISSION_BLOCKED`
- `USER_NOT_FOUND_OR_NO_LOG`
- `TIME_RANGE_REQUIRED`
- `TIME_RANGE_OUT_OF_REALTIME_WINDOW`
- `TABLE_NOT_FOUND`
- `LOADED_EMPTY_OR_NO_ROWS`
- `SELECTOR_UNSTABLE`
- `STATE_EXPIRED_RELOGIN_REQUIRED`
- `DETAIL_MODAL_NOT_OPENED`
- `DETAIL_JSON_TOO_SENSITIVE`
- `NO_RESULT_IN_REALTIME_WINDOW`

## 十二、smoke tests

全部 pending validation：

- recent 7d query success。
- out of 7d range returns `TIME_RANGE_OUT_OF_REALTIME_WINDOW`。
- user_id + time_range 查询成功。
- 无结果但页面正常。
- 权限不足。
- state 过期重新登录。
- 登录成功 / 失败分布可见。
- OAuth / 扫码字段可见性识别。
- token/session 字段不输出明文。
- IP / 设备字段只输出派生特征。
- result table fields detected。
- detail modal opens readonly。
- detail JSON values redacted。
- copy button not clicked。
- token/session fields never collected。
- pagination_required 正确标记。
- readonly_safety_check 通过。

