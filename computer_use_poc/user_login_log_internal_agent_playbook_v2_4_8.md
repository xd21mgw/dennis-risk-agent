# 用户登录统一日志 Internal Agent Playbook v2.4.8

本文面向 Dennis 子 Agent / browser computer use 执行，只定义用户登录统一日志 readonly POC 的运行时规范。

## 一、当前能力范围

平台：

```text
user_login_unified_log
```

默认入口：

```text
https://user-center-workbench.corp.kuaishou.com/create-applications/unified-log-search
```

当前状态：

- partially_ready / release_candidate_not_final。
- Run 011 已验证高危接口 / 多账号登录 special event detail key extraction。
- 当前 POC 仅将页面默认 / backend default 的近 7 天作为实时页面可靠查询窗口。
- 页面前端允许选择超过最近 7 天的历史时间，但超窗结果不能直接解释为历史无记录。
- 默认使用页面自动填充 / backend default 时间范围。
- 除非用户明确要求调整，否则不主动改时间。

不支持：

- 离线全量查询。
- 自动风险定性。
- 处置、导出、复制完整 JSON、批量下载。
- 多平台联合。

## 二、execution_mode

### quick_login_check

- 读取结果列表。
- 观察登录成功 / 失败分布。
- 观察登录方式字段是否可见。
- 目标 1-2 分钟。

### focused_ato_check

- 观察登录方式。
- 观察 OAuth / 扫码字段。
- 观察 token/session 字段是否可见。
- 观察高危接口调用摘要。
- 必要时最多打开前 1-2 条“查看详情”弹窗。
- 目标 2-4 分钟。

### deep_login_trace

- 观察目标时间窗口内登录链路摘要。
- 不输出敏感明文。
- 不复制完整 JSON。
- 目标 3-5 分钟。

## 三、输入字段

必填：

- user_id。
- time_range。如果用户未指定，使用页面默认 / backend default；当前可靠窗口按默认近 7 天处理。

可选：

- did。
- query_keyword。
- log_sources。

## 四、查询前 auth preflight

1. 打开入口 URL。
2. 检查是否重定向到登录页。
3. 如果被重定向到登录页，返回 `LOGIN_REQUIRED`。
4. 如果权限不足，返回 `PERMISSION_BLOCKED`。
5. 如果 browser profile / workspace 与前期测试环境不同，可能需要重新扫码 / 登录。
6. 不记录 password、cookie、token、session、KIM code。

## 五、查询步骤

1. 打开入口 URL。
2. 使用页面自动填充 / backend default 时间范围；不要反复探测日期选择器。
3. 如果用户明确给出 time_range，可以按用户要求调整。
4. 如果用户要求超过最近 7 天，允许选择时间，但必须标记 `over_reliable_realtime_window=true`。
5. 输入 User ID 或 DID。
6. 勾选日志来源：
   - 增长登录相关日志。
   - 账号登录相关日志。
   - 业务鉴权日志。
   - 高危接口调用日志。
7. 可选输入 Query 关键词。
8. 点击查询。
9. 如果首次显示“暂无数据”，等待 3-5 秒后再次点击查询，最多重试 1 次。
10. 如果超出可靠窗口后仍显示“暂无数据”，只能解释为“实时页面未观察到结果 / 数据完整性未验证”，不得解释为历史无登录、全量无记录或用户无风险。
11. 读取结果列表字段。
12. 读取分页信息：`total_count`、`page_size`、`current_page`、上一页 / 下一页按钮状态、页码跳转和 page size selector。
13. 如果 `total_count > visible_row_count`，必须标记 `partial_page_only=true`。
14. 如有必要，最多打开前 1-2 条“查看详情”弹窗。
15. 只读取字段名和派生特征。
16. 不复制完整 JSON。
17. 关闭弹窗。

## 五-A、selector profile / execution shortcut

本节用于减少后续 browser computer use 反复探路。

1. 不再反复探测日期选择器。
2. 不主动改时间，默认使用页面默认 / backend default。
3. 输入 User ID 后点击查询。
4. 若首次显示“暂无数据”，等待 3-5 秒后再次点击查询，最多重试 1 次。
5. 结果出来后，通过行文本 scoped selector 选择目标行：
   - 包含“APP切换账号成功”的行。
   - 包含“快手APP刷新token成功”的行。
6. 在目标行内点击“查看详情”，不要点击全局第一个详情按钮。
7. 打开详情后只提取 JSON key，不提取 value。
8. 字段值策略按“风控分析字段保留、认证凭证明文隐藏”执行：设备、用户、IP、UA、appVer、sysVer、登录时间和 token/session 生命周期类时间字段可作为证据字段保留；token / session / ticket / authorization / cookie 等认证凭证明文只记录 `present_redacted`。
9. 每条详情观察完成后关闭弹窗，再打开下一条。
10. 如果页面白屏，记录 `page_white_screen`，不要无限重试。

## 五-B、time window guardrail

本轮边界测试发现：页面前端允许选择超过最近 7 天的历史时间，超窗查询可以执行，但可能只返回“暂无数据”，且页面没有明确的实时窗口限制提示。

执行规则：

1. 默认不主动改时间，使用页面默认 / backend default。
2. 当前 POC 仅将默认近 7 天作为实时页面可靠查询窗口。
3. 如用户要求查超过最近 7 天，可以选择时间，但必须标记 `over_reliable_realtime_window=true`。
4. 超窗结果即使为“暂无数据”，也只能解释为“实时页面未观察到结果 / 数据完整性未验证”。
5. 不得输出“历史无登录”“全量无记录”“用户无风险”。
6. 长周期登录链路必须建议转 DataAgent / Hive 或离线日志能力。
7. 如果页面未显示明确限制文案，记录 `platform_limit_text=none`，不要自行推断后端真实保留周期。

## 五-C、pagination guardrail

本轮分页测试发现：页面分页功能实际存在，total_count、page_size、上一页 / 下一页、页码跳转和 page size selector 可见；人工证据证明可翻到第 4 页并观察到数据变化。但 browser automation 点击下一页后未稳定观察到页面变化，疑似 AJAX 等待、滚动或点击时机问题。

执行规则：

1. 读取结果表时必须记录 `total_count`、`page_size`、`visible_row_count`、`current_page`。
2. 记录 `prev_button_enabled`、`next_button_enabled`、`page_jump_present`、`page_size_selector_present`。
3. 如果 `total_count > visible_row_count`，必须标记 `partial_page_only=true`。
4. 未逐页覆盖全部结果前，不得输出“全量结果”“已查看全部”“当前页就是全部结果”。
5. 如果下一页可点击但 Agent 未翻页成功，记录 `pagination_automation_unstable=true` 和 `automation_issue`。
6. 点击分页后必须等待 3-5 秒，并确认：
   - `current_page` 是否变化；
   - table row timestamp / tag / method 是否变化；
   - loading 是否结束。
7. 如果分页控件不在可见区域，应先滚动到分页区域。
8. 如果自动化仍失败，不要强行重试超过 1-2 次，记录 `automation_issue`。
9. 页面分页可用但自动化未遍历全量时，输出解释必须包含：`partial_page_only=true`、`full_result_claim_allowed=false`。

Detail modal 当前验证状态：

```yaml
detail_modal_selector_profile:
  validation_status: switch_user_partially_validated_refresh_token_key_extraction_validated
  switch_user_success_detail_modal_openable: true
  refresh_token_success_detail_modal_observation: validated_for_readonly_json_key_extraction
  json_panel_visible: true
  json_key_extraction: readonly_keys_only
  json_value_extraction: false
  copy_button_clicked: false
  known_observed_keys:
    - userId
    - timestamp
    - deviceId
    - userIp
    - userIpv6
    - serverIp
    - sysVer
  refresh_token_stable_keys:
    - serverIp
    - actionType
    - appType
    - userId
    - result
    - userIp
    - userAgent
    - did
    - dateTime
    - uri
    - reason
    - appVer
    - extra
  refresh_token_absent_sensitive_fields_in_current_sample:
    - token
    - session
    - ticket
    - authorization
    - refresh_token
    - access_token
  page_stability_risks:
    - page_white_screen
    - no_data_after_requery
    - query_delay
```

RefreshToken 详情补测规则：

1. 打开详情后，如果 JSON 面板首次只显示 `{`，等待 5 秒后再读取。
2. 只读取 JSON key，不读取 value。
3. `copy` 按钮仅记录 present，不点击。
4. 若 `token` / `session` / `ticket` / `authorization` / `refresh_token` / `access_token` 等认证凭证明文字段出现，只记录 `present_redacted`。
5. 若这些字段未出现，记录 `absent`。
6. 不因无 `request_id` / `trace_id` 或无 `risk_decision` 字段而判定页面无价值，只记录 `missing_field` 或 `not_observed`。

## 五-D、special event detail selector / guardrail

Run 011 已验证高危接口调用和多账号登录详情 key extraction。

高危接口调用详情：

- 视角：服务端调用链。
- 可观察 key 包括 serviceKess、serviceKsn、serviceIp、serviceCatalog、callerKsn、callerIp、method、request、id、timestamp、action、extra、userId、deviceId、`@timestamp` 等。
- 当前样本未发现 token / session / ticket / authorization / refresh_token / access_token。

多账号登录详情：

- 视角：客户端登录环境。
- 可观察 key 包括 userId、timestamp、deviceId、userIp、userIpv6、serverIp、sysVer、appVer、uri、status、params、did_tag、egid、loginType、loginToken、tokenId、token、ksLogId、`@timestamp` 等。
- `token` / `loginToken` / `tokenId` 等凭证明文字段只输出 `present_redacted`。

执行规则：

- “查看详情”按钮可能是 `type=submit`，默认点击可能触发表单提交导致页面跳转。
- 必须使用 scoped row click，并阻止默认 submit 行为，或采用已验证的 modal 打开方式。
- modal 内容异步渲染，若首次仅显示 `{` 或 innerHTML 为空，等待 3-5 秒后再提取 JSON key。
- 只提取 JSON key，不输出 JSON value，不复制完整 JSON。
- 高危接口日志和多账号登录日志 JSON 结构不同，不得强行套用同一字段集合。

## 五-E、agent-browser serial execution guardrail

当前 agent-browser 是单 daemon / 单 Chrome 进程架构，`--session` 无法提供真正并行隔离；`--profile` 在 daemon 已运行时也不能可靠切换。

执行规则：

- 当前阶段默认采用串行锁方案。
- 同一时间只允许一个 agent-browser session 操作内部平台页面。
- 不允许两个 Dennis / browser session 同时访问档案中心、统一登录日志等 SPA 页面。
- 开始 browser computer use 前必须检查是否已有任务在操作 agent-browser。
- 多 session 并发导致的跳转异常不得解释为页面不可用、Tab 不可访问、用户无数据或权限阻断。
- Tab 点击、分页、详情弹窗、saved state 保存等操作必须在 `single_browser_session=true` 条件下执行。

## 六、字段提取策略

结果列表字段：

- 时间。
- 标签。
- User ID。
- DID。
- Method。
- 日志来源。
- 查看详情。

详情弹窗字段：

- 时间。
- 标签。
- User ID。
- DID。
- Method。
- 日志来源。
- JSON 数据字段名。

## 七、字段保留与凭证隐藏策略

统一日志的字段策略不是“隐藏所有设备和用户字段”。登录风险、ATO、协议上号、撞库、OAuth / 扫码和高危接口分析需要保留 user、device、IP、UA、版本、时间、登录态生命周期等风控证据字段。

### retain_fields

以下字段应作为风控分析字段保留，可进入 observation / evidence summary：

- userId / accountId / principal 等用户标识字段。
- did / deviceId / deviceType / deviceModel 等设备字段。
- userIp / serverIp / userIpv6 / region 等网络字段。
- userAgent / appVer / appType / sysVer 等客户端字段。
- actionType / uri / method / result / reason 等行为字段。
- timestamp / dateTime / tokenCreateTime / tokenGenerateTime / tokenExpireTime / sessionCreateTime / sessionExpireTime 等时间字段。

### redact_raw_value_only

以下字段只隐藏认证凭证明文值。如字段存在，只输出 `present_redacted`；不得输出 raw value：

- token。
- accessToken。
- refreshToken。
- session。
- sessionId。
- ticket。
- authorization。
- cookie。
- 其他认证凭证原文。

### semantic disambiguation

- token 明文值必须隐藏。
- token 生成时间、过期时间、状态、类型、来源等非凭证明文字段必须保留。
- deviceId / did 是风控证据字段，应保留，不应默认隐藏。
- userId 是查询对象和证据字段，应保留。
- 如果字段名包含 token 但字段语义是时间、状态、类型、来源，不要 redacted。
- 如果字段名是 accessToken / refreshToken / token value，则只输出 `present_redacted`。

## 八、输出 observation schema

```yaml
platform: user_login_unified_log
execution_mode:
actual_duration:
time_range_policy:
query_form:
result_table:
detail_modal:
risk_event_scan:
sensitive_runtime_evidence_policy:
readonly_safety_check:
failure_reason:
```

## 九、禁止事项

- 不点击复制完整 JSON。
- 不导出。
- 不批量下载。
- 不处置。
- 不输出认证票据明文。
- 不输出操作者账号明文。
- 不把实时页面“暂无数据”解释为全量无记录、历史无登录或用户无风险。
- 超过可靠窗口的查询结果必须降级解释，并建议 DataAgent / Hive 或离线日志补证。
- 不做最终风险定性。

## 十、focused_ato_check 标准执行 Prompt

```text
请通过 browser computer use 执行用户登录统一日志只读查询，execution_mode=focused_ato_check。

入口：
https://user-center-workbench.corp.kuaishou.com/create-applications/unified-log-search

输入：
- user_id: {user_id}
- time_range: 默认使用页面默认 / backend default；当前可靠窗口按默认近 7 天处理，超出需标记 over_reliable_realtime_window
- did: {optional_did}
- query_keyword: {optional_query_keyword}

执行步骤：
1. 打开入口 URL。
2. 做 auth preflight：如登录页，返回 LOGIN_REQUIRED；如权限不足，返回 PERMISSION_BLOCKED。
3. 使用页面默认 / backend default 时间范围；不要主动改时间，不反复探测日期选择器。
4. 如果用户指定超过最近 7 天，可以选择时间，但必须标记 over_reliable_realtime_window=true；超窗“暂无数据”不得解释为历史无记录。
5. 输入 User ID 或 DID。
6. 勾选增长登录相关日志、账号登录相关日志、业务鉴权日志、高危接口调用日志。
7. 点击查询。
8. 如果首次显示“暂无数据”，等待 3-5 秒后再次点击查询，最多重试 1 次。
9. 读取结果列表字段：时间、标签、User ID、DID、Method、日志来源、查看详情。
10. 如有必要，按行文本 scoped selector 选择“APP切换账号成功”或“快手APP刷新token成功”目标行，并在目标行内点击“查看详情”。
11. 只读取 JSON key 和派生特征，不读取 value，不复制完整 JSON。
12. 关闭弹窗后再观察下一条详情。

输出 observation：
- platform
- execution_mode
- actual_duration
- time_range_policy
- query_form
- result_table
- detail_modal
- risk_event_scan
- sensitive_runtime_evidence_policy
- readonly_safety_check
- failure_reason

禁止：
- 不点击复制完整 JSON。
- 不输出 token、accessToken、refreshToken、session、sessionId、ticket、authorization、cookie、KIM code 等认证凭证明文。
- userId、did / deviceId、IP、UA、appVer、sysVer、登录时间、token/session 生命周期时间等是风控分析字段，可以保留。
- 不导出、不批量下载、不处置。
- 不把实时页面“暂无数据”解释为全量无记录、历史无登录或用户无风险。
- 不做最终风险定性。
```
