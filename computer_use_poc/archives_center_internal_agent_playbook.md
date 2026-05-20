# 档案中心 Computer Use 只读执行 Playbook

本文是 Dennis 子 Agent 调用 browser computer use 执行档案中心只读查询时的运行时规范。它不是设计文档，也不是风险定性规则。

端到端链路：

用户问题 → Dennis 子 Agent 生成 readonly plan → Dennis 调用 browser computer use → browser 返回 observation → Dennis 消化 observation → 输出证据总结 / 风险线索 / 证据缺口 / 下一步建议。

## 1. 当前能力范围

已支持：

- 档案中心 `userId` direct URL。
- saved state 复用。
- quick mode。
- focused_login_risk mode。
- P0 Tab deep-read。

不支持：

- 多平台。
- 多入参。
- 二级链接 validated。
- 批量查询。
- 自动风险定性。

Auth preflight：

- 档案中心 `userId` direct URL 已确认：
  `https://admin.p.adm-corp.kuaishou.com/frontend/archives/index.html#/archives/user/profile?userId={userId}`。
- 档案中心独立登录域：`account.p.adm-corp.kuaishou.com`。
- 认证链路：SSO → 档案中心独立登录 → userId direct URL。
- 如果 Dennis 子 Agent 使用的 browser profile / workspace 与前期测试环境不同，可能需要重新扫码 / 登录。
- 这属于认证态环境差异，不代表 browser computer use 能力失败。
- `sso_session.py` 可 HTTP 级访问不代表 `agent-browser` GUI 进程已复用该 cookie。
- 如果 `agent-browser` 打开 direct URL 后仍被重定向到 `account.p.adm-corp.kuaishou.com`，应标记 `archives_browser_auth_blocked` / `archives_independent_login_required_for_agent_browser`。
- saved state 复用、state 过期、重新登录恢复规则继续有效。
- 重新登录过程中不得记录 password、token、cookie、session、KIM code。
- 处置、审批、导出、封禁、解封等任何写操作。

## 1-A. Entry resolution before execution

档案中心 source 在任何单源或多源 e2e 执行前，必须先完成 `entry_resolution`。

规则：

- 优先读取本 playbook、既有 run log、README、runtime snapshot。
- 不允许凭记忆或猜测 archives-center URL。
- 不允许从首页菜单随意探索作为正式执行路径。
- 如果 entry 找不到，返回 `source_entry_missing`，不要继续执行 browser computer use。
- 档案中心入口 404 只能说明入口解析失败或路径无效，不等于用户无档案记录。
- 多源 e2e 中，如果档案中心 source 失败，不得把用户登录统一日志单源 observation 包装成 multi_source observation。
- 当前已确认入口 URL，不得再将 Run 006 解释为 entry missing / URL missing。
- 如果 entry 已找到但 `agent-browser` 缺少档案中心独立登录态，返回 auth blocker；下一步是完成 agent-browser 档案中心独立登录并保存 state，或在已有认证态环境中重跑。
- 当前已验证 saved state：`archives_center_4700398885_20260519`。该 state 当前可复用，但不得泛化为所有账号 / 所有时间均可复用。

输出格式：

```yaml
source_entry_resolution:
  source_name: archives_center
  docs_searched:
  entry_found:
  entry_url:
  validated_execution_path_found:
  selector_or_playbook_found:
  blocker:
  next_action:
```

## 2. execution_mode 定义

### quick

用途：快速确认用户详情页是否可访问，以及用户信息 Tab 的基础结构。

读取：

- 用户信息 Tab。
- section 标题。
- 关键入口是否可见。
- 写操作按钮语义。

目标耗时：1-2 分钟。

### focused_login_risk

用途：账号安全、异常登录、ATO、协议上号、高危操作初筛。

读取：

- 用户信息 Tab。
- 用户分析 Tab。

用户分析要求：

- 必须记录实际页面 time_range。
- 优先使用 API direct POST `/v3/user/log/coreLogs/fetch` 读取 APP 端核心操作日志。
- API direct POST 不可用时，再回退 DOM scoped JS eval / row feature filter。
- 必须先确认字段结构或 response shape。
- 如用于登录 / 高危操作研判，必须做 risk_event_scan。

### focused_login_risk API direct POST 优先路径

v2.4.7.1 已验证档案中心用户分析 Tab 背后的 API direct POST。

```yaml
api_direct_post_priority:
  endpoint: /v3/user/log/coreLogs/fetch
  method: POST
  auth_context:
    browser_session_required: true
    same_origin_fetch: true
    auth_header_export_required: false
    csrf_required: false
  fallback:
    - DOM scoped JS eval
    - row feature filter
```

执行规则：

- API direct POST 属于档案中心用户分析 Tab，不属于用户登录统一日志平台。
- 不导出 cookie / token / session。
- 不输出 requestParam / extraParam 明文。
- 不输出 token / tokenId / refresh_token / sig / open_id 明文。
- API response 可直接生成 `risk_event_scan`。
- API 失败、认证失效、响应结构变化或敏感 JSON 过重时，回退 DOM fallback。

## 2-A. 用户分析分页 guardrail

Run 009 已修正此前错误结论：档案中心用户分析 / APP端核心操作日志存在分页。

执行规则：

- 不得再默认认为用户分析是无分页 / 无限滚动模式。
- 未观察到分页控件不等于没有分页。
- 必须区分 page body scroll 和 table container scroll。
- 分页控件可能位于表格底部 / 表格容器底部，不一定随 body scroll 暴露。
- 若 `total_count > visible_row_count`，必须标记 `partial_coverage=true`。
- 未逐页遍历前，禁止输出：
  - 已查看6个月全量。
  - 当前页就是全部历史。
  - 没有更多登录记录。
  - 用户分析无更多数据。

## 2-B. 审核日志 / 打标日志 guardrail

Run 010 已部分验证审核日志 / 打标日志可访问性。

执行规则：

- 权限系统升级通知弹窗可能遮挡 Tab 点击，点击 Tab 前应先关闭弹窗。
- Tab 点击后必须确认 `current_url` 仍在档案中心 direct URL 下。
- Tab selected 状态和页面实际内容都要确认，不能只看 click 成功。
- 打标日志表头可见不等于有数据。
- 审核日志有结果不等于登录风险定性完成。
- 审核 / 打标日志只作为补充 source，不替代登录链路证据。

## 2-C. SPA route / Tab click guardrail

后台 SPA 页面测试时，多 session 并发可能污染路由状态。

执行规则：

- 不允许多个 Dennis / agent-browser session 同时访问同一个档案中心 saved state。
- 测试前必须关闭其他 browser session，确保 `single_browser_session=true`。
- Tab 点击前必须确认 click target 属于当前页面内部 Tab 容器，而不是左侧导航、顶部导航或其他应用入口。
- 点击前必须记录：`current_url`、`source_name`、`user_id`、`target_tab_text`、`target_tab_container_identified`、`click_target_scope`。
- 点击后必须校验：current_url 是否仍在目标 source 下、是否仍为同一 userId、target_tab 是否 selected、是否出现 `unexpected_route_redirect`。
- 如果点击后跳出目标 source，必须标记 `tab_click_invalid` / `unexpected_route_redirect`。
- unexpected route redirect 不能解释为目标 Tab 不可访问、无结果、无权限或用户无数据。
- 若 `click_target_scope=unknown`，不允许点击，应先返回 blocker。

## 2-D. agent-browser serial execution guardrail

当前 agent-browser 是单 daemon / 单 Chrome 进程架构，`--session` 无法提供真正并行隔离；`--profile` 在 daemon 已运行时也不能可靠切换。

执行规则：

- 当前阶段默认采用串行锁方案。
- 同一时间只允许一个 agent-browser session 操作内部平台页面。
- 不允许两个 Dennis / browser session 同时访问档案中心、统一登录日志等 SPA 页面。
- 开始 browser computer use 前必须检查是否已有任务在操作 agent-browser。
- 如果已有任务在运行，应等待或停止当前任务。
- 多 session 并发导致的跳转异常不得解释为页面不可用、Tab 不可访问、用户无数据或权限阻断。
- Tab 点击、分页、详情弹窗、saved state 保存等操作必须在 `single_browser_session=true` 条件下执行。

目标耗时：3-5 分钟。

当前状态：

- structure extraction 已验证。
- risk_event_scan selector noise 已修复并 validated。
- 当前 validated 范围仅限档案中心 userId direct URL 的 focused_login_risk 只读派生观察，不代表自动风险定性。

### deep

用途：用户明确要求档案中心 P0 Tab 完整深读。

读取：

- 用户信息。
- 用户分析。
- 审核日志。
- 视频作品集。

目标耗时：5-7 分钟。

## 3. 用户分析 Tab 特殊规则

用户分析 Tab 不能默认按标准表格处理。

规则：

- 默认优先尝试 API direct POST `/v3/user/log/coreLogs/fetch`，避免 DOM selector noise。
- 不要默认使用 `ant-table` 选择器。
- 档案中心用户分析表格可能使用 `ks-table__row`。
- 不要全页面直接 `querySelectorAll('.ks-table__row')`。
- 优先定位 active user_analysis tab container。
- 如果无法定位 active container，使用 row feature filter。
- 当前 active tab container 不可用时，row feature filter 是 validated fallback。
- selector noise 未修复时，`risk_event_scan.status` 只能写 `partial_validated_with_selector_noise`；row feature filter 修复成功后可写 `validated`。

## 4. row feature filter

只保留符合日志特征的行。

保留条件：

- 有时间格式。
- 有操作 URL path 或操作类型。
- 有操作结果。
- 有 APP 版本、IP 描述、设备字段之一。

排除条件：

- 平台操作。
- 直播功能。
- 电商功能。
- 行为封禁。
- 流量调控。
- 账户信息。
- 其他用户信息 Tab 中的非日志表格行。

## 5. table_schema_probe 与 risk_event_scan

### table_schema_probe

用途：字段结构探测。

规则：

- 只看表头 + 前 3 条样例结构。
- 字段值默认 redacted。
- 不用于风险判断。
- 不得基于 table_schema_probe 得出无风险、无异常或无行为结论。

### risk_event_scan

用途：登录 / 高危操作摘要。

必须输出：

- 操作类型分布。
- 成功失败分布。
- 登录方式序列。
- IP 一致性派生判断。
- 设备一致性派生判断。
- APP 版本一致性派生判断。
- 地理位置一致性派生判断。
- 第三方登录是否可见。
- 手机号 / 绑定事件是否可见。
- 关键事件序列。
- 可疑事件标记。
- 分页是否影响覆盖。
- coverage_limitations。

禁止：

- 输出 IP、设备 ID、手机号、open_id、token、请求参数、cookie、session、KIM code 等明文。
- 把 risk_event_scan observation 写成最终风险定性。

## 6. 敏感字段三层策略

### never_collect

不得读取、不得输出、不得沉淀：

- cookie。
- token。
- session。
- KIM code。
- password。
- access token / refresh token。
- 完整认证票据。

### runtime_readable_but_not_persisted

可在执行态用于风控派生判断，但不得明文沉淀：

- IP。
- 设备 ID / did / egid。
- 手机号。
- open_id。
- 第三方登录标识。
- APP 版本。
- 系统版本。
- 地理位置。
- 操作 URL path / result。

允许输出：

- redacted 标记。
- 计数。
- 分布。
- 一致性判断。
- 关键事件序列摘要。
- hash，如后续安全规范允许。

### persistable_structure

可沉淀：

- 字段名。
- 操作类型。
- 成功 / 失败。
- 时间范围。
- 表头。
- 分布。
- 计数。
- Tab / 模块名。

## 7. 统一 observation 输出

browser computer use 必须输出以下 observation 结构，供 Dennis 子 Agent 消化：

```yaml
execution_mode:
actual_duration:
state_reuse_status:
tabs_observed:
selector_profile:
  table_structure:
  extraction_method:
  fallback_used:
  selector_noise:
    present:
    source:
    mitigation:
risk_event_scan:
  status:
  operation_type_counts:
  success_failure_counts:
  earliest_event_time:
  latest_event_time:
  login_method_sequence:
  ip_consistency:
  geo_consistency:
  device_consistency:
  app_version_consistency:
  third_party_login_visible:
  phone_or_binding_event_visible:
  key_event_sequence:
  suspicious_event_markers:
  pagination_required:
  coverage_limitations:
sensitive_runtime_evidence_policy:
  raw_value_access:
  raw_value_persistence:
  raw_value_display:
  derived_feature_output:
readonly_safety_check:
```

## 8. 禁止事项

禁止：

- 点击封禁、解封、打标、保存、提交、审批、导出、批量操作。
- 点击二级链接，除非后续专门验证。
- 输出操作者账号明文。
- 输出 token / cookie / session / KIM code。
- 输出 IP、设备 ID、手机号、open_id、请求参数等敏感明文。
- 把 observation 当成最终风险结论。
- 把 `partial_validated_with_selector_noise` 写成 `validated`。
- 把二级入口写成 validated。
- 把无结果解释为无风险。

## 9. focused_login_risk 标准 Prompt 模板

```text
请在档案中心执行 userId direct URL 只读查询，execution_mode=focused_login_risk。

输入：
- user_id: {user_id}
- target_url: {archives_center_userid_direct_url}

执行范围：
1. 使用已保存 state，直接打开 userId direct URL。
2. 如果 state 失效，停止并返回 state_reuse_status，不记录任何认证信息。
3. 只读取用户信息 Tab 和用户分析 Tab。
4. 用户分析 Tab 优先使用 same-origin API direct POST `/v3/user/log/coreLogs/fetch`。
5. API response shape 正常时，直接从 response 生成 risk_event_scan。
6. API 不可用时，再做 table_schema_probe + DOM fallback risk_event_scan。
7. DOM fallback 不要默认使用 ant-table 选择器；用户分析表格可能是 ks-table__row。
8. DOM fallback 不要全页面直接 querySelectorAll('.ks-table__row')。
9. DOM fallback 优先定位 active user_analysis tab container；如果失败，使用 row feature filter。
10. row feature filter 只保留有时间格式、操作 URL path 或操作类型、操作结果、APP 版本 / IP 描述 / 设备字段之一的日志行。
11. 排除平台操作、直播功能、电商功能、行为封禁、流量调控、账户信息等非日志表格行。

敏感字段策略：
- cookie、token、session、KIM code、password、access token、refresh token 永远 never_collect。
- IP、设备 ID、手机号、open_id、APP 版本、系统版本、地理位置、操作 URL path / result 可在执行态用于派生判断，但不得明文输出或沉淀。
- 只输出 redacted 标记、计数、分布、一致性判断、关键事件序列摘要。

输出 observation：
- execution_mode
- actual_duration
- state_reuse_status
- tabs_observed
- selector_profile
- risk_event_scan
- sensitive_runtime_evidence_policy
- readonly_safety_check

禁止：
- 不点击任何写操作按钮。
- 不点击二级链接。
- 不输出操作者身份明文。
- 不输出任何认证票据或敏感字段明文。
- 不输出最终风险定性。
- 如果 selector noise 仍存在，risk_event_scan.status 必须写 partial_validated_with_selector_noise，不能写 validated。
- 如果 row feature filter 已确认 selector_noise_present=false，可写 risk_event_scan.status=validated，但仍不得输出最终风险定性。
```
