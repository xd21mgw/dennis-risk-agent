# v2.4.5.1 档案中心深读性能优化设计

## 1. v2.4.5.1 定位

v2.4.5.1 是档案中心 user profile deep-read 性能优化设计。

范围：

- 不新增平台能力。
- 不扩多入口。
- 不扩多平台。
- 不新增自动研判。
- 只优化档案中心 user profile 深读的执行效率、输出结构和 token 成本。

## 2. 当前瓶颈分析

P0 Tab deep-read 当前约 12 分钟。

主要耗时：

- state 加载失败 + 重新登录：约 2 分钟。
- 用户信息 Tab 快照：约 2 分钟，DOM 最大、元素最多。
- 用户分析 Tab 快照：约 2 分钟，数据量大、响应体长。
- 审核日志 Tab 快照：约 1 分钟。
- 视频作品集 Tab 快照：约 1 分钟。
- 各 Tab 切换等待渲染：约 4 分钟。

判断：

- 固定 wait 3000 不是最大瓶颈。
- 真正瓶颈在 snapshot 输出量大、DOM 解析量大、整理成本高。
- 用户信息 Tab DOM 最大。
- 用户分析 Tab 数据量大。

## 3. execution_mode

当前实跑状态：

- quick mode 已验证，约 22 秒。
- focused_login_risk 结构提取已验证，103 秒完成，低于 3-5 分钟目标。
- focused_login_risk risk_event_scan 已实跑，156 秒完成，低于 3-5 分钟目标。
- risk_event_scan 已能输出派生风险摘要，包括操作类型分布、成功失败分布、时间范围、登录方式序列、IP / 地理 / 设备 / APP 版本一致性、第三方登录和绑定事件可见性、关键事件序列、可疑事件标记、分页和覆盖限制。
- focused_login_risk risk_event_scan selector noise 已修复，row feature filter 已验证有效，63 秒完成。
- 当前状态可标记为 `validated`。
- 用户分析 Tab 表格使用 `ks-table__row`，不是标准 `ant-table`。
- 用户信息 Tab 与用户分析 Tab 的表格行会在同一页面 DOM 中共存；已通过 row feature filter 排除用户信息 Tab 的非日志表格行。
- active tab container 当前不可用，因为档案中心不使用标准 `aria-selected` / `tabpanel` 结构；row feature filter 是当前可用 fallback。
- DOM 中同一日志行可能重复渲染，需要 dedupe。

### 3.1 quick

适用：

- 只想确认档案中心是否可访问。
- 只想快速看用户基础页结构。

读取：

- 用户信息 Tab。
- section 标题。
- 关键入口是否可见。
- 写操作按钮是否存在。

不读取：

- 用户分析。
- 审核日志。
- 视频作品集。
- 表格明细。

目标耗时：1-2 分钟。

### 3.2 focused_login_risk

适用：

- ATO / 异常登录 / 协议上号 / 高危操作初筛。

读取：

- 用户信息 Tab。
- 用户分析 Tab。

用户分析：

- 记录实际 `time_range start/end`。
- 记录 `time_range_source: auto_populated / manual / event_time / default_1y_adjusted`。
- 先做 `table_schema_probe`，确认字段结构。
- 再做 `risk_event_scan`，覆盖当前 `time_range` 内登录 / 高危操作相关记录摘要。
- IP、设备号、手机号、open_id、第三方登录标识、APP 版本、系统版本、地理位置描述、操作 URL path 和结果可在执行态用于一致性、分布、序列等派生判断。
- 上述执行态敏感字段默认不在 run log / 文档 / 对话报告中输出明文，只输出 redacted 标记、计数、分布、一致性判断或关键事件序列。
- cookie、token、session、KIM code、password、access token、refresh token、完整认证票据永远 `never_collect`。
- 如果记录很多，不全量输出；只输出聚合摘要和关键事件序列。
- 如果分页导致当前结果无法覆盖目标窗口，标记 `pagination_required=true`，不得声称已完整覆盖。
- 当前实跑发现用户分析 Tab 表格为非标准结构，初始 ant-table selector 不稳定，需要 fallback extraction。

目标耗时：3-5 分钟。

### 3.3 focused_punishment_review

适用：

- 处罚 / 误伤 / 审核记录核查。

读取：

- 用户信息 Tab。
- 审核日志 Tab。

目标耗时：3-5 分钟。

### 3.4 focused_content_risk

适用：

- 视频 / 内容风险观察。

读取：

- 用户信息 Tab。
- 视频作品集 Tab。

目标耗时：3-5 分钟。

### 3.5 deep

适用：

- 用户明确要求完整档案中心 P0 Tab 深读。

读取：

- 用户信息。
- 用户分析。
- 审核日志。
- 视频作品集。

列表型 Tab：

- 默认先做字段结构探测。
- 用户分析 Tab 如用于登录风险 / ATO / 协议上号 / 高危操作研判，必须追加 `risk_event_scan`。
- 审核日志、视频作品集等其他列表型 Tab 如仅做结构探测，可只取表头 + 前 3 条样例结构。
- 字段值默认 redacted。

目标耗时：5-7 分钟。

## 4. scoped extraction 规则

禁止默认使用整页全量 snapshot 作为主要读取方式。

优先使用结构化定向观察：

- 当前 Tab 是否 selected。
- Tab 名称。
- section 标题。
- table headers。
- filters。
- pagination。
- button texts。
- link texts。
- visible / clickable / disabled 状态。

每个 Tab 只读取当前 Tab 内容区，不读取整页 DOM。

如果必须 snapshot，只允许 scoped snapshot 当前 Tab 容器。

用户分析 Tab selector 规则：

- 优先尝试专属 `user_analysis_tab` selector。
- 如果标准 `ant-table` selector 未命中，进入 fallback extraction。
- fallback 可以使用语义点击 + scoped snapshot + 自定义 selector。
- fallback 使用时必须在 observation 中记录 `selector_profile.fallback_used=true`。
- 当前已发现用户分析 Tab 使用 `ks-table__row`。
- `ks-table__row` 选择器可能混入用户信息 Tab 的非日志表格行，必须配合 row feature filter。

selector 优化策略：

1. 优先定位 active user_analysis tab container，只在当前 active Tab 容器内提取行。
2. 其次使用 row feature filter，仅保留包含时间格式、`/rest/` 操作路径、操作结果、APP 版本、IP 描述、设备字段的日志行。
3. 排除用户信息 Tab 中的平台操作、直播功能、电商功能等非日志表格行。
4. 如果 active tab container 不可用，row feature filter 是当前 validated fallback。
5. selector 噪声未修复前，`risk_event_scan.status` 只能标记为 `partial_validated_with_selector_noise`；本轮 row feature filter 修复后可标记 `validated`。
6. 后续应将 dedupe 逻辑内置到 eval 脚本。

## 5. 列表型 Tab 双层读取策略

### 5.1 table_schema_probe

用途：字段结构探测。

策略：

- 表头。
- 筛选项。
- 是否有数据。
- 前 3 条样例行的字段结构。
- 分页信息。

字段值：redacted。

不得用于完整风险判断。

```yaml
table_schema_probe:
  max_rows_observed: 3
  values_policy: redacted
  purpose: infer_table_schema_only
  pagination_followed: false
```

### 5.2 risk_event_scan

用途：

- 登录风险研判。
- ATO / 账号接管研判。
- 协议上号研判。
- 高危操作研判。

策略：

- 覆盖目标 `time_range` 内相关操作日志的摘要。
- IP、设备、手机号、open_id、第三方登录标识、版本、地理位置、操作 URL path / result 可在执行态用于派生判断，沉淀态默认 redacted。
- 输出操作类型分布、成功失败分布、关键事件序列、时间范围覆盖情况。
- 记录是否需要分页。
- 不输出全量明细。

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
    mode: current_time_range_summary
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
```

默认不读取：

- 全量列表。
- 所有行。
- 翻页内容。
- 明文字段值。

字段值策略：

- 字段名可以输出。
- 字段值默认 redacted；redaction 是输出和沉淀策略，不是执行态研判禁止。
- `table_schema_probe` 只用于判断字段结构，不用于完整取证结论。
- `risk_event_scan` 可使用执行态敏感字段生成派生特征，但仍不输出敏感明文，也不自动定性。
- cookie、token、session、KIM code、password、access token、refresh token、完整认证票据不得读取、不得输出、不得沉淀。

## 6. time_range 记录规则

用户分析 Tab 必须记录实际页面 `time_range`：

```yaml
time_range:
  start:
  end:
  source: auto_populated / manual / event_time / default_1y_adjusted
  adjusted_by_agent: true / false
```

要求：

- 如果页面自动填充的是半年，就记录半年。
- 如果 Agent 未主动调整到近 1 年，不得声称已查近 1 年。
- “默认近 1 年”是 Agent 的目标查询策略，不等于页面天然默认值。
- 如果实际未调整，只能说“当前页面时间范围下观察”。

## 7. 条件等待规则

将固定 wait 3000 优化为语义等待。

每个 Tab 定义关键元素：

- 用户信息：等待“基本信息 / 最近登录 / 注册信息”等 section 出现。
- 用户分析：等待“APP端核心操作日志 / 操作类型筛选 / 时间范围”出现。
- 审核日志：等待“业务领域 / 操作来源 / 操作时间”等列头出现。
- 视频作品集：等待“视频ID / 状态 / 分页 / 视频卡片列表”出现。

如果关键元素出现，即可继续。

如果超时，返回 `tab_status=failed` 或 `timeout`，不无限等待。

## 8. 二级链接处理

二级链接只记录：

- `link_name`
- `visible`
- `clickable`
- `expected_target_page`
- `validation_status=pending`

不点击：

- 详情
- 查重
- 查看更多
- 同设备登录用户
- 同设备注册用户
- 私信 / 评论 / 直播评论等

除非后续单独进入对应入口验证版本。

## 9. batch_js_eval_extraction_plan

目标：

- 尽量通过一次 JS eval 获取当前 Tab 的结构化信息。
- 或在单次脚本中完成：点击 Tab → 等待关键元素 → 提取结构 → 切下一个 Tab。
- 输出 JSON，而不是长文本 snapshot。

提取字段：

- tabs
- selected_tab
- sections
- tables.headers
- filters
- pagination
- buttons
- links
- write_action_candidates
- sensitive_field_candidates

注意：

- JS eval 只能做只读 DOM 读取。
- 不触发写操作。
- 不读取 cookie / localStorage / token / session / KIM code / password / access token / refresh token / 完整认证票据。
- 不输出敏感字段明文；只允许输出字段结构、redacted 标记、派生特征和聚合摘要。

## 10. run report header

所有后续 observation 增加：

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
table_schema_probe:
risk_event_scan:
selector_profile:
sensitive_runtime_evidence_policy:
time_range_policy:
```

### 10.1 user_analysis selector_profile

```yaml
user_analysis_tab:
  selector_profile:
    table_structure: standard_ant_table / non_standard / unknown
    extraction_method: ant_table_selector / scoped_snapshot / custom_selector / mixed
    fallback_used: true / false
  table_schema_probe:
    status: validated / failed / skipped
  risk_event_scan:
    status: pending / partial_validated / partial_validated_with_selector_noise / validated / failed
    reason:
  selector_noise:
    present:
    source:
    mitigation:
  dedupe_policy:
    enabled:
    dedupe_key:
    raw_candidate_rows:
    deduped_rows:
    duplicate_reason:
```

### 10.2 下一步优化目标

- 将 focused_login_risk 压缩到 60 秒内。
- 将 dedupe 逻辑内置到 eval 脚本中。
- 保留 active tab container selector 作为优先路径；当前平台结构下以 row feature filter 为 validated fallback。
- 在不输出敏感明文的前提下，输出操作类型分布、成功失败分布、关键事件序列、IP / 设备 / APP 版本 / 地理一致性判断和 coverage_limitations。

## 11. Smoke Tests

1. quick mode 只读用户信息
   - 预期：只读取用户信息 Tab、section 标题和关键入口。

2. focused_login_risk 只读用户信息 + 用户分析
   - 预期：先做 table_schema_probe；如执行风险研判，再做 risk_event_scan。当前 structure extraction 已实跑验证，full risk_event_scan 仍 pending。

3. focused_punishment_review 只读用户信息 + 审核日志
   - 预期：识别审核日志表头、筛选项、是否空结果。

4. focused_content_risk 只读用户信息 + 视频作品集
   - 预期：识别列表、分页和详情入口 pending。

5. deep mode 读取 P0 Tab
   - 预期：四个 P0 Tab 均观察；用户分析如涉及登录风险，必须输出 risk_event_scan 摘要；其他列表默认 table_schema_probe。

6. time_range 记录实际值和 source
   - 预期：不把 Agent 策略误写成页面默认值。

7. scoped extraction 不输出整页 DOM
   - 预期：只输出当前 Tab 容器结构。

8. 二级链接 pending 不点击
   - 预期：validation_status=pending。

9. write buttons present but untouched
   - 预期：记录按钮存在，不点击。

10. operator account redacted
    - 预期：operator identity 不输出明文。

11. 用户分析前 3 条仅用于 schema probe
    - 预期：不得基于前 3 条样例得出无风险结论。

12. 用户分析日志很多时输出聚合摘要
    - 预期：不输出全量明文，只输出 operation_type_counts、success_failure_counts、key_event_sequence、ip_consistency、device_consistency、app_version_consistency、geo_consistency 等派生判断。

13. 分页未覆盖完整时间窗口
    - 预期：`pagination_required=true`，并记录 coverage_limitations。

14. focused_login_risk non-standard table fallback
    - 预期：标准选择器未命中时，记录 `table_structure=non_standard`、`fallback_used=true`。

15. table_schema_probe does not equal full risk_event_scan
    - 预期：`table_schema_probe.status=validated` 时，`risk_event_scan.status` 仍可为 `pending`。

16. focused_login_risk under 3 minutes
    - 预期：结构提取耗时低于 3 分钟。

17. focused_login_risk risk_event_scan partial validated
    - 预期：156 秒内输出派生摘要；状态为 `partial_validated_with_selector_noise`，不写 full validated。

18. ks-table selector detected
    - 预期：记录 `table_structure=ks_table` 或 `ks-table__row` 相关说明。

19. selector noise from non-user-analysis rows
    - 预期：识别用户信息 Tab 表格行可能混入用户分析日志行。

20. row feature filter required
    - 预期：要求使用时间格式、`/rest/` 路径、操作结果、APP 版本、IP 描述、设备字段等特征过滤日志行。

21. risk_event_scan outputs derived features without raw sensitive values
    - 预期：输出派生摘要，不输出 IP、设备 ID、手机号、open_id、token、请求参数、cookie、session、KIM code 等明文。

22. risk_event_scan not full validated until selector noise removed
    - 预期：selector 噪声未修复前不得标记 full validated。

23. selector noise fixed
    - 预期：row feature filter 后 `selector_noise_present=false`。

24. row feature filter validated
    - 预期：raw mixed rows 可被过滤为日志候选行，并排除用户信息 Tab 的非日志表格行。

25. focused_login_risk risk_event_scan validated
    - 预期：risk_event_scan.status=validated，actual_duration 低于 90 秒。

26. duplicate DOM rows dedupe required
    - 预期：记录 raw_mixed_rows、filtered_log_candidate_rows、deduped_log_rows 和 duplicate_reason。

27. risk_event_scan under 90 seconds
    - 预期：selector 修正后 focused_login_risk risk_event_scan 耗时低于 90 秒。

## 12. 不变边界

- 不修改核心 Skill。
- 不更新 release package。
- 不改变 DataAgent 边界。
- 不提交认证 state / cookie / token / KIM code / 截图。
- 不记录操作者身份明文。
- 不记录目标用户昵称、手机号、IP、设备 ID、视频 ID、视频标题等明文。
- 不把二级链接写成 validated。
- 不把本次设计描述为自动研判完成。
- 不新增平台能力。
- 不扩多入口。
- 不扩多平台。
- 不点击任何写操作。
- 不读取或输出 cookie / token / session / KIM code / password / access token / refresh token / 完整认证票据 / localStorage。
- 不输出敏感明文。
- 不得把 redaction 理解为字段不能参与风控判断；它只约束输出和沉淀。
