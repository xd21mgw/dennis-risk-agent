# v2.4.5 档案中心 User Profile 深读模板设计

## 一、v2.4.5 定位

v2.4.5 = 档案中心 user profile 深读模板设计。

范围：

- 仅针对档案中心 `userId` direct URL 用户详情页。
- 仅做只读观察模板。
- 重点拉齐 Tab、模块、二级链接、时间范围、字段 redaction、失败模式。

非目标：

- 不扩多平台。
- 不扩多入参。
- 不做批量查询。
- 不做自动风险定性。
- 不做处置动作。
- 不把二级入口写成已验证能力。

validated 范围仍只来自 v2.4.4：

- `userId` direct URL。
- saved state 复用。
- 多 `userId` 成功访问。
- `USER_NOT_FOUND` 预期失败。
- target object / operator account 身份分层。
- 只读安全边界。

v2.4.5 已实跑验证：

- 用户信息 Tab。
- 用户分析 Tab。
- 审核日志 Tab。
- 视频作品集 Tab。
- saved state 过期后重新登录并保存新 state。
- P0 Tab 切换和只读观察。
- operator account redacted。
- sensitive fields redacted。
- readonly_safety_check=PASSED。

## 二、Tab 优先级

P0 深读 Tab：

1. 用户信息
2. 审核日志
3. 用户分析
4. 视频作品集

P1 后续观察：

1. 直播作品集
2. 粉丝列表
3. 关注列表
4. 动态列表
5. 同设备登录 / 注册入口

暂缓：

1. 合集列表
2. 收藏列表
3. 导出 / 批量 / 处置类入口
4. 语义不明的跳转入口

## 三、统一 Tab Observation Schema

```yaml
tab_observation:
  tab_name:
  tab_priority:
  entry_condition:
  tab_status:
    visible:
    clickable:
    loaded:
    empty:
    permission_blocked:
  core_sections:
  list_or_table_present:
  filters_present:
  pagination_present:
  safe_read_fields:
  sensitive_fields:
  write_action_buttons_present:
  readonly_safe_actions:
  failure_reason:
  next_possible_observation:
```

说明：

- 点击 Tab、等待加载、读取模块名称属于只读安全动作。
- 点击封禁、解封、打标、保存、提交、审批、导出、批量操作不属于只读安全动作，禁止点击。
- 如果按钮或链接语义不明，默认只记录存在，不点击。

## 四、用户信息 Tab 深读模板

用户信息 Tab 是 P0 深读对象。

从截图和已验证页面看，用户信息 Tab 不是简单基础资料页，而是包含多个高价值风控模块和二级入口。

需要覆盖模块：

1. 基本信息
2. 相关链接
3. 最近登录
4. 最近启动
5. 注册信息
6. 账户信息
7. 用户实时负向
8. 用户设置
9. 同设备登录用户入口
10. 同设备注册用户入口
11. 头像查重 / 背景查重入口

```yaml
user_info_tab:
  tab_status:
    visible:
    loaded:
  sections:
    basic_info:
      visible:
      target_object_fields:
      sensitive_fields:
      write_action_buttons_present:
    related_links:
      visible:
      link_items:
        - link_name:
          link_type:
          clickable:
          direct_url_candidate:
          validation_status: pending / validated / blocked
          risk_use_case:
    recent_login:
      visible:
      fields_visible:
      sensitive_fields_policy:
    recent_launch:
      visible:
      fields_visible:
      sensitive_fields_policy:
    registration_info:
      visible:
      fields_visible:
      sensitive_fields_policy:
    account_info:
      visible:
      fields_visible:
      sensitive_fields_policy:
    realtime_negative_status:
      visible:
      fields_visible:
      interpretation_boundary:
    device_relation_entries:
      same_device_login_users:
        visible:
        clickable:
        direct_url_candidate:
        validation_status: pending
      same_device_register_users:
        visible:
        clickable:
        direct_url_candidate:
        validation_status: pending
    image_similarity_entries:
      avatar_similarity:
        visible:
        clickable:
        direct_url_candidate:
        validation_status: pending
      background_similarity:
        visible:
        clickable:
        direct_url_candidate:
        validation_status: pending
```

注意：

- 最近登录、最近启动、注册信息里的 IP、设备号、手机号、经纬度、设备型号等在执行态可用于派生判断，输出和沉淀时默认 redacted。
- target object 的 `user_header` 可用于核验 `query_value`，但敏感字段仍按字段级策略处理。
- operator account，例如右上角登录账号、导航栏用户名，必须 redacted。
- 实跑确认用户信息 Tab 包含高价值风控模块，也存在写操作按钮风险；写操作按钮只能记录语义和存在状态，禁止点击。

## 五、相关链接 / 二级入口候选

```yaml
secondary_link_candidate:
  link_name:
  source_tab:
  source_section:
  object_type:
  expected_target_page:
  clickable:
  direct_url_candidate:
  validation_status: pending / validated / blocked
  risk_use_case:
  safety_level:
  notes:
```

候选入口包括但不限于：

- 私信
- 评论
- 直播评论
- 说说评论
- 说说作品集
- 用户名搜索
- 同设备登录用户
- 同设备注册用户
- 第三方注册原始信息
- 头像查重
- 背景查重

重要要求：

- 当前这些二级链接只能标记为 `direct_url_candidate / pending`。
- 不能写成 `validated`，除非已有实跑记录。
- 不要因为页面上有链接，就认为可安全直达。
- 如果链接语义不明，只记录存在，不点击。

## 六、审核日志 Tab 深读模板

审核日志是 P0。

需要覆盖：

- Tab 是否可点击。
- 是否有新版 / 旧版切换。
- 是否有日志列表。
- 是否有筛选条件。
- 是否有时间、审核人、页面、操作、备注等字段。
- 是否为空。
- 是否权限不足。

```yaml
audit_log_tab:
  tab_status:
    visible:
    clickable:
    loaded:
    empty:
    permission_blocked:
  version_switch:
    new_version_visible:
    old_version_visible:
    switch_click_allowed:
    validation_status: pending
  filters_present:
  list_or_table_present:
  fields_visible:
    audit_time:
    auditor:
    page:
    operation:
    remark:
  sensitive_fields_policy:
  readonly_safe_actions:
  write_action_buttons_present:
  failure_reason:
```

注意：

- 日志字段默认摘要化，不输出人员、备注中的敏感明文。
- 如果旧版信息更全，也只能先标记为 `pending`，等实跑确认后再 `validated`。

## 七、用户分析 Tab 深读模板

用户分析是 P0，但必须显式处理 `time_range`。

重要时间范围规则：

- 用户分析 Tab 查询必须显式记录 `time_range`。
- 如果用户问题有明确事件时间，优先围绕事件时间设置查询窗口。
- 如果用户没有给时间范围，Agent 查询策略可目标设为近 1 年，但这不等于页面天然默认值。
- 实际执行时必须读取并记录页面控件当前 `start/end`。
- 如果页面默认时间范围不是 1 年，observation 必须如实记录。
- 如需改成近 1 年，应明确作为 `readonly filter adjustment`，并记录 `readonly_safe_actions_taken`。
- 如果未调整筛选条件，只能说“当前页面时间范围下的观察结果”。
- 如果用户要求超过 1 年，需要用户确认。
- 如果近 1 年查不到记录，不能直接解释为“没有行为”，只能说明“在当前查询范围和筛选条件下未见记录”。
- observation 必须记录 `time_range_source`：
  - `user_provided`
  - `event_time`
  - `default_1y`
  - `manually_confirmed`

```yaml
user_analysis_tab:
  tab_status:
    visible:
    clickable:
    loaded:
    empty:
    permission_blocked:
  time_range_required: true
  default_time_range_policy: default_1y
  time_range:
    provided:
    start:
    end:
    source: user_provided / event_time / default_1y / manually_confirmed / missing
    actual_page_value_recorded:
    adjusted_by_agent:
  filters_visible:
  operation_type_filter_visible:
  sub_tabs_visible:
    - APP端核心操作日志
  list_or_table_present:
  table_schema_probe:
    max_rows_observed: 3
    values_policy: redacted
    purpose: infer_table_schema_only
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
      values_policy:
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
  safe_read_fields:
    operation_type:
    timestamp:
    operation_url:
    operation_result:
    app_version:
  sensitive_runtime_evidence_policy:
    raw_value_access:
    raw_value_persistence:
    raw_value_display:
    derived_feature_output:
  sensitive_fields:
    user_ip_desc:
    device_id:
    did:
    egid:
    phone:
    open_id:
    third_party_login_identifier:
    app_version:
    system_version:
    location:
    operation_url_path:
    operation_result:
  sensitive_fields_policy:
  no_result_interpretation:
  readonly_safe_actions_taken:
  readonly_safe_actions:
  write_action_buttons_present:
  failure_reason:
```

注意：

- IP、设备 ID / did / egid、手机号、open_id、第三方登录标识、APP 版本、系统版本、地理位置描述、操作 URL path 和结果可以在执行态用于风控判断，但默认不在 run log / 文档 / 普通 observation 中输出明文。
- 操作 URL 可以使用 path 和结果生成派生判断，但不输出完整敏感参数。
- cookie、token、session、KIM code、password、access token、refresh token、完整认证票据永远 `never_collect`。
- 不能把无结果直接解释为无风险。
- 实跑确认用户分析 Tab 存在时间范围、操作类型筛选、APP端核心操作日志、子 Tab 和结果列表字段。
- `table_schema_probe` 仅用于字段结构探测，不得用于完整风险判断。
- ATO / 异常登录 / 协议上号 / 高危操作研判必须启用 `risk_event_scan`，覆盖目标 `time_range` 内相关操作日志摘要。
- 如果日志很多，不输出全量明文；输出操作类型分布、成功失败分布、关键事件序列、IP / 设备 / APP 版本 / 地理一致性判断和覆盖限制。
- 如果分页导致当前结果无法覆盖目标窗口，必须标记 `pagination_required=true`，不得声称已完整覆盖。

## 八、视频作品集 Tab 深读模板

视频作品集是 P0。

需要覆盖：

- Tab 是否可点击。
- 是否有视频列表。
- 是否为空。
- 是否有分页。
- 是否有详情入口。
- 是否有视频 ID、标题、状态、播放、点赞、评论、分享等列。

```yaml
video_portfolio_tab:
  tab_status:
    visible:
    clickable:
    loaded:
    empty:
    permission_blocked:
  list_or_table_present:
  pagination_present:
  fields_visible:
    photo_id:
    title:
    status:
    publish_time:
    view_count:
    like_count:
    comment_count:
    share_count:
  detail_entry:
    visible:
    clickable:
    validation_status: pending
  sensitive_fields_policy:
  readonly_safe_actions:
  write_action_buttons_present:
  failure_reason:
```

注意：

- 视频标题默认摘要或 redacted。
- `photo_id` 是否输出，按后续字段策略控制。
- 详情入口当前只能 `pending`，不写 `validated`。
- 实跑确认视频作品集存在列表、分页、详情、查重、查看更多入口；详情 / 查重 / 查看更多仍为 `pending`。

## 九、敏感字段与身份分层策略

必须复用 v2.4.4 规则：

```yaml
identity_context:
  target_object:
    description: 查询目标对象，可用于核验 query_value
    examples: user_header, target user ID
    policy: 可保留必要匹配信息，但敏感字段按字段级策略处理
  related_object:
    description: 页面中出现的关联对象
    examples: 同设备用户、粉丝、关注、视频作者等
    policy: 默认 redacted
  operator_account:
    description: 当前登录操作者账号
    examples: nav_menu、右上角用户名
    policy: 必须 redacted
  system_metadata:
    description: 页面状态、模块、字段名、按钮名
    policy: 可以记录
```

字段 redaction 规则：

- 手机号：`visible_masked_value_redacted`
- IP：`visible_value_redacted`
- 设备 ID：`visible_value_redacted`
- open_id / 第三方登录标识：`visible_value_redacted`
- APP 版本 / 系统版本：可用于一致性判断，输出原值需 redacted 或聚合化
- 操作 URL path / 操作结果：可用于派生判断，不输出完整敏感参数
- 昵称 / 用户名：target object 可用于匹配，其他默认 redacted
- 操作者账号：`operator_identity_redacted`
- cookie / token / session / KIM code / password / access token / refresh token / 完整认证票据：`never_collect`
- redaction 是输出和沉淀策略，不是执行态风控判断禁止。

## 十、只读安全规则

允许：

- 点击 Tab。
- 等待页面加载。
- 展开只读详情。
- 切换明确只读筛选项。
- 记录字段是否可见。

禁止：

- 点击封禁。
- 点击解封。
- 点击打标。
- 点击保存。
- 点击提交。
- 点击审批。
- 点击导出。
- 点击批量操作。

如果按钮语义不明，默认不点击。

如果页面进入写操作流程，立即停止并返回 `failure_reason`。

## 十一、v2.4.5 Smoke Tests

1. 用户信息 Tab 深读成功
   - 预期：识别 basic_info、related_links、recent_login、recent_launch、registration_info、account_info、realtime_negative_status。

2. 用户信息 Tab 二级链接候选识别成功
   - 预期：候选链接只标记 `pending`，不写 `validated`。

3. 用户信息 Tab 识别同设备登录 / 注册入口
   - 预期：识别入口存在，`validation_status=pending`。

4. 审核日志 Tab 加载成功
   - 预期：识别日志列表、筛选条件、字段可见性。

5. 审核日志为空
   - 预期：`empty=true`，不解释为无风险。

6. 用户分析 Tab 默认近 1 年查询
   - 预期：`time_range.source=default_1y`。

7. 用户分析 Tab 使用事件时间查询
   - 预期：`time_range.source=event_time`。

8. 用户分析 Tab 无结果但不解释为无行为
   - 预期：`no_result_interpretation=only_no_record_under_current_range_and_filters`。

9. 视频作品集加载成功
   - 预期：识别列表、分页、字段可见性。

10. 出现写操作按钮但不点击
    - 预期：记录按钮存在，`readonly_safety_check=PASSED` 或停止。

11. Tab 权限不足
    - 预期：`permission_blocked=true`，不绕过权限。

12. operator account 出现但 redacted
    - 预期：`operator_account.value_policy=operator_identity_redacted`。

## 十二、输出要求

深读 observation 输出时必须包含：

- P0 Tab 状态。
- 已加载模块。
- 字段可见性。
- 敏感字段策略。
- 二级入口候选及 validation_status。
- time_range 和 time_range_source。
- readonly_safety_check。
- failure_reason，如有。

不得输出：

- 明文手机号、IP、设备 ID、操作者账号。
- cookie、token、session、KIM code、password、access token、refresh token、完整认证票据。
- 未验证二级入口的 validated 结论。
- 自动风险定性。
- 处置建议作为已执行动作。
