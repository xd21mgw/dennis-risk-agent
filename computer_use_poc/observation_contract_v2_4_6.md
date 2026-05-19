# v2.4.6 Observation Contract

本文定义 Dennis 子 Agent 调用 browser computer use 完成档案中心只读查询后，如何读取、解释、汇总 browser 返回的 observation，并给出下一步建议。

当前验证状态：

- single-source archives_center focused_login_risk observation digestion validated。
- v2.4.7 end-to-end readonly joint test validated：Dennis 子 Agent 可调用 browser computer use，browser 返回 observation 后 Dennis 可完成证据消化。
- user_login_unified_log 是多源 observation 的第二个 source，当前为 v2.4.8 partially ready。
- v2.4.8 Run 006 已验证 multi-source entry resolution；multi-source e2e 当前被 `agent-browser` 档案中心独立登录态阻断，状态为 `multi_source_e2e_blocked_by_archives_auth`。
- v2.4.8 Run 007 已验证同 userId 档案中心 + 用户登录统一日志 focused_login_risk multi-source e2e，状态为 `multi_source_e2e_validated_with_partial_coverage`。
- v2.4.8 Run 008 ~ Run 011 已补充 saved state 复用、档案中心用户分析分页修正、审核 / 打标日志可访问性、统一登录日志 special event detail key extraction。
- 当前 release 状态为 `release_candidate_not_final`。
- 当前已验证单源消化和 focused_login_risk 多源 observation partial coverage；不代表多源联合风险研判或最终定性完成。
- Dennis Agent 输出必须保留“线索 / 证据 / 结论边界”三层区分。

## 1. 三方分工

### Dennis 子 Agent / 编排 Agent

职责：

- 理解用户问题。
- 生成只读查询计划。
- 调用 browser computer use 执行档案中心只读查询。
- 消化 browser 返回的 observation。
- 输出证据总结、风险线索、证据强度、缺口和下一步平台建议。

不负责：

- 直接替代 observation 伪造平台结果。
- 自动处置。
- 在证据不足时输出最终风险定性。

### browser computer use

职责：

- 在只读边界内执行页面操作。
- 返回结构化 observation。
- 遵守敏感字段 redaction、operator account redaction、readonly safety。

不负责：

- 理解业务问题。
- 生成最终风险判断。
- 自动处置。

### Codex

职责：

- 沉淀 schema。
- 沉淀 playbook。
- 沉淀 run log。
- 维护 POC 文档和边界。

不负责：

- 直接操作内部平台。
- 替代 Dennis 子 Agent 或 browser computer use 实时执行。

### DataAgent / Hive

职责：

- Hive / 公司数仓取数分析。

不负责：

- 替代 browser computer use。
- 覆盖在线平台、实时日志、策略平台、设备平台的页面只读查询。

## 2. Observation 输入结构

browser computer use 返回 observation 时，建议使用以下最小结构：

```yaml
platform:
query_object:
query_value_policy:
execution_mode:
actual_duration:
state_reuse_status:
tabs_observed:
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
limitations:
```

输入解释：

- `platform`：当前只支持 `archives_center`。
- `query_object`：当前只支持 `user_id`。
- `query_value_policy`：不得输出额外敏感明文。
- `execution_mode`：如 `quick`、`focused_login_risk`、`deep`。
- `risk_event_scan`：只读派生摘要，不是最终登录全量事实。
- `limitations`：必须保留，不得在解释时忽略。

未来多源 observation 可增加：

```yaml
source_observations:
  - platform: archives_center
  - platform: user_login_unified_log
same_user_id_used:
source_entry_resolutions:
  - source_name:
    docs_searched:
    entry_found:
    entry_url:
    validated_execution_path_found:
    selector_or_playbook_found:
    blocker:
    next_action:
```

说明：

- `user_login_unified_log` 后续用于补强档案中心 `focused_login_risk` 的登录链路证据。
- 当前已完成页面可访问性、认证态复用、基础 User ID 查询、默认日志来源 checkbox、结果表可见性和只读安全边界的 partially validated。
- `refresh_token_detail_observation` 已验证 readonly JSON key extraction；这只代表 refreshToken 详情弹窗字段名可安全观察，不代表统一登录日志 fully validated。
- 当前尚未 fully validated；Run 007 仅验证 focused_login_risk multi-source observation partial coverage。
- 当前 POC 仅将页面默认 / backend default 的近 7 天作为实时页面可靠查询窗口；前端时间控件允许选择超过最近 7 天，但超窗“暂无数据”不得解释为历史无记录。
- 本轮页面未显式展示具体 start_time / end_time，但查询结果显示存在默认近 7 天行为；不得写成 UI 明确展示最近 7 天。
- 需要离线补证时建议 DataAgent / Hive。

### 2.0.-1 multi_source_e2e_entry_resolution_rule

多源 e2e 前，每个 source 必须先完成 entry resolution。

```yaml
multi_source_e2e_entry_resolution_rule:
  required_before_execution: true
  docs_priority:
    - playbook
    - run_log
    - runtime_snapshot
    - README
  no_guess_url: true
  no_homepage_menu_exploration_as_formal_path: true
  on_missing_entry: source_entry_missing
  no_partial_single_source_wrapped_as_multi_source: true
  human_input_required_only_if_missing_docs_explained: true
  same_user_id_used_required: true
```

解释规则：

- 不允许凭记忆或猜测 URL。
- 如果 entry 找不到，必须返回 `source_entry_missing`，不得继续生成半成品联合报告。
- 一个 source 失败时，不能把另一个 source 的 observation 包装成 multi_source observation。
- 不允许要求用户手动执行，除非明确标记为 `human_input_required` 且说明缺失文档项。
- 档案中心入口缺失不等于档案中心无数据。
- 档案中心入口 404 不等于用户无档案记录。
- 统一登录日志单源结果不等于多源 e2e 成功。
- 多源 e2e 必须 `same_user_id_used=true`。
- 档案中心独立登录态缺失时，应返回 `multi_source_e2e_blocked_by_archives_auth`，不得把统一登录日志单源 observation 包装成多源联合结果。
- 下一步应准备 archives saved state 后重跑 e2e，而不是继续猜入口或要求用户手动执行。

Run 006 当前验证结果：

```yaml
multi_source_e2e_run_006:
  target: archives_center + user_login_unified_log focused_login_risk e2e
  user_id: "4700398885"
  archives_center_entry_resolution: validated
  archives_entry_found: true
  archives_selector_or_playbook_found: true
  archives_direct_url: "https://admin.p.adm-corp.kuaishou.com/frontend/archives/index.html#/archives/user/profile?userId={userId}"
  archives_independent_login_domain: account.p.adm-corp.kuaishou.com
  archives_auth_path: SSO → 档案中心独立登录 → userId direct URL
  sso_session_py_http_access: true
  agent_browser_reused_sso_cookie: false
  archives_blocker:
    - archives_browser_auth_blocked
    - archives_independent_login_required_for_agent_browser
  user_login_unified_log_query_success: true
  user_login_unified_log_total_count: 133
  user_login_unified_log_page_size: 20
  user_login_unified_log_visible_row_count: 20
  partial_page_only: true
  e2e_joint_observation_success: false
  validation_status: multi_source_e2e_blocked_by_archives_auth
```

Run 006 clarification:

- 当前不是 entry missing / URL missing。
- 当前不是档案中心无结果或用户无档案。
- `sso_session.py` 可 HTTP 级访问，但 `agent-browser` GUI 进程未复用该 cookie。
- 下一步是人工在 `agent-browser` 中完成档案中心独立登录并保存 state，或在已有档案中心认证态的 Dennis Risk Agent 环境中重跑，再执行 Run 007：`multi_source_e2e_with_archives_saved_state`。

Run 007 当前验证结果：

```yaml
multi_source_e2e_run_007:
  validation_status: multi_source_e2e_validated_with_partial_coverage
  user_id: "4700398885"
  same_user_id_used: true
  archives_saved_state: archives_center_4700398885_20260519
  archives_center:
    accessible: true
    query_success: true
    result_present: true
    user_profile_visible: true
    user_analysis_tab_visible: true
    app_core_operation_log_visible: true
    time_range: "2025-11-20 ~ 2026-05-19"
    partial_coverage: true
  user_login_unified_log:
    accessible: true
    query_success: true
    result_present: true
    total_count: 133
    page_size: 20
    visible_row_count: 20
    partial_page_only: true
  cross_source_alignment:
    did_consistent: true
    aligned_behaviors:
      - 历史一键登录
      - 退出登录
  multi_source_schema_ready: focused_login_risk_observation_only
  e2e_joint_observation_success: true
  blockers: []
```

Run 007 输出命名规则：

```yaml
observation_categories:
  high_confidence_observations:
  medium_confidence_observations:
  weak_or_contextual_observations:
  missing_observations:
```

说明：

- 不使用 `strong_evidence` / `medium_evidence` / `weak_evidence` 命名，避免被误解为风险定性。
- `high_confidence_observations` 只代表观察可靠性较高，不代表风险强证据或最终结论。
- `multi_source_schema_ready=true` 必须限定为 `focused_login_risk_observation_only`。
- Run 007 不代表自动风险定性完成、全量历史数据已查看、设备攻防平台已验证、审核 / 打标日志已查看或最终风险结论已生成。

Run 008 ~ Run 011 状态补充：

```yaml
v2_4_8_followup_status:
  archives_saved_state_reuse: validated
  archives_user_analysis_pagination: validated_with_correction
  archives_audit_label_log_access: partially_validated
  unified_log_special_event_detail: validated
  release_status: release_candidate_not_final
```

### 2.0.3 archives_user_analysis_pagination_observation

```yaml
archives_user_analysis_pagination_observation:
  validation_status: archives_user_analysis_pagination_behavior_validated_with_correction
  total_count_visible:
  total_count:
  page_size:
  current_page:
  next_button_present:
  next_button_enabled:
  page_jump_present:
  page_range_visible:
  partial_coverage:
  table_container_scroll_required:
  forbidden_interpretation:
    - 已查看6个月全量
    - 当前页就是全部历史
    - 没有更多登录记录
    - 用户分析无更多数据
```

解释规则：

- 未观察到分页控件不等于没有分页。
- 必须区分 page body scroll 和 table container scroll。
- 若 `total_count > visible_row_count`，必须 `partial_coverage=true`。

### 2.0.4 archives_audit_label_log_observation

```yaml
archives_audit_label_log_observation:
  validation_status: archives_audit_label_log_access_partially_validated
  audit_log:
    accessible:
    result_present:
    visible_columns:
    pagination_present:
    limitations:
  label_log:
    accessible:
    result_present:
    empty_state_text:
    visible_columns:
    pagination_present:
    limitations:
```

解释规则：

- 打标日志表头可见不等于有数据。
- 审核日志有结果不等于登录风险定性完成。
- 审核 / 打标日志只作为补充 source，不替代登录链路证据。

### 2.0.5 user_login_unified_log special event detail observations

```yaml
user_login_unified_log:
  high_risk_api_detail_observation:
    validation_status: validated
    perspective: service_side_call_chain
    visible_json_keys:
    key_count:
    credential_fields:
      token:
      session:
      ticket:
      authorization:
      refresh_token:
      access_token:
  multi_account_login_detail_observation:
    validation_status: validated
    perspective: client_login_environment
    representative_json_keys:
    key_count:
    credential_fields:
      token:
      loginToken:
      tokenId:
      session:
      ticket:
      authorization:
      refresh_token:
      access_token:
  credential_fields_present_redacted_policy:
    token: present_redacted_if_found
    loginToken: present_redacted_if_found
    tokenId: present_redacted_if_found
    session: present_redacted_if_found
    ticket: present_redacted_if_found
    authorization: present_redacted_if_found
```

解释规则：

- 高危接口调用日志偏服务端调用链视角。
- 多账号登录日志偏客户端登录环境视角。
- 本轮只提取 JSON key，不输出 JSON value，不做风险定性。
- `token` / `loginToken` / `tokenId` 等凭证明文字段如出现，只输出 `present_redacted`。
- “查看详情”按钮可能是 `type=submit`，必须使用 scoped row click，并阻止默认 submit 行为，或采用已验证的 modal 打开方式。
- modal 内容异步渲染时，若首次仅显示 `{` 或 innerHTML 为空，等待 3-5 秒后再提取 JSON key。

### 2.0.6 spa_route_and_tab_click_guardrail

```yaml
spa_tab_click_observation:
  source_name:
  user_id:
  single_browser_session:
  before_click:
    current_url:
    target_tab_text:
    target_tab_container_identified:
    click_target_scope:
  after_click:
    current_url:
    still_in_target_source:
    same_user_id:
    target_tab_selected:
    unexpected_route_redirect:
  interpretation:
    click_valid:
    blocker:
    forbidden_interpretation:
      - 目标 Tab 不可访问
      - 用户无数据
      - 无权限
      - 页面无结果
```

规则：

- 后台 SPA 页面测试时，多 session 并发可能污染路由状态。
- 测试前必须确保 `single_browser_session=true`。
- Tab 点击前必须确认 click target 属于当前页面内部 Tab 容器。
- 如果 `click_target_scope=unknown`，不允许点击，应先返回 blocker。
- 如果点击后跳出目标 source，标记 `tab_click_invalid` / `unexpected_route_redirect`。
- unexpected route redirect 不能解释为目标 Tab 不可访问、无结果、无权限或用户无数据。

### 2.0.7 agent_browser_serial_execution_guardrail

```yaml
agent_browser_serial_execution_guardrail:
  single_browser_session_required: true
  concurrent_internal_platform_sessions_allowed: false
  recommended_short_term_solution: lock_file_or_task_mutex
  future_solution:
    - each_session_independent_chrome_process
    - each_session_independent_user_data_dir
    - each_daemon_independent_cdp_port
```

规则：

- 当前 agent-browser 是单 daemon / 单 Chrome 进程架构，`--session` 无法提供真正并行隔离。
- `--profile` 在 daemon 已运行时也不能可靠切换。
- 多 session 同时操作同一 browser / cookie / SPA 状态，可能导致路由污染、Tab 点击异常、页面跳转异常。
- 当前阶段默认采用串行锁方案。
- 多 session 并发导致的跳转异常不得解释为页面不可用、Tab 不可访问、用户无数据或权限阻断。

### 2.0.0 user_login_unified_log boundary observations

```yaml
user_login_unified_log:
  no_result_observation:
    empty_state_text:
    query_condition_retained:
    correct_interpretation:
    forbidden_interpretation:
      - 用户无风险
      - 用户无登录记录
      - 全量无记录
  time_window_observation:
    frontend_over_7_days_selectable:
    platform_limit_text:
    over_window_query_result:
    auto_truncate_observed:
    reliable_window_assumption:
    fallback_required:
      - DataAgent / Hive
      - 离线日志能力
    forbidden_interpretation:
      - 超过 7 天无记录
      - 历史无登录
      - 全量无风险
```

解释规则：

- `empty_state_text=暂无数据` 只能表示当前查询条件下实时页面无结果。
- `frontend_over_7_days_selectable=true` 不等于后端历史数据完整可查。
- 如果 `platform_limit_text=none`，不得自行推断真实后端保留周期。
- 超过可靠窗口的空结果必须进入 `limitations` / `missing_evidence`，并建议 DataAgent / Hive 或离线日志补证。

### 2.0.1 user_login_unified_log.refresh_token_detail_observation

当前 refreshToken 详情补测已验证字段名只读提取，状态为 `refresh_token_detail_modal_validated`。该状态仅覆盖单类记录的 detail modal，不代表无结果、分页、权限阻断、多源联合或完整 JSON 嵌套字段已验证。

```yaml
user_login_unified_log:
  refresh_token_detail_observation:
    validation_status: refresh_token_detail_modal_validated
    stable_keys:
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
    field_categories:
      user_identifier_fields:
        - userId
      time_fields:
        - dateTime
      network_fields:
        - userIp
        - serverIp
      client_fields:
        - userAgent
        - appVer
        - appType
      device_fields:
        - did
      api_fields:
        - uri
      action_fields:
        - actionType
      result_fields:
        - result
        - reason
      extension_fields:
        - extra
    missing_or_not_observed:
      - request_id
      - trace_id
      - oauth
      - scan
      - risk_label
      - risk_decision
      - effective_fail_reason
    field_policy:
      retain_fields:
        user_identifier_fields:
          - userId
          - accountId
          - principal
        device_fields:
          - did
          - deviceId
          - deviceType
          - deviceModel
        network_fields:
          - userIp
          - serverIp
          - userIpv6
          - region
        client_fields:
          - userAgent
          - appVer
          - appType
          - sysVer
        action_fields:
          - actionType
          - uri
          - method
          - result
          - reason
        time_fields:
          - timestamp
          - dateTime
          - tokenCreateTime
          - tokenGenerateTime
          - tokenExpireTime
          - sessionCreateTime
          - sessionExpireTime
      redact_raw_value_only:
        - token
        - accessToken
        - refreshToken
        - session
        - sessionId
        - ticket
        - authorization
        - cookie
      current_refreshToken_sample:
        token: absent
        session: absent
        ticket: absent
        authorization: absent
        refreshToken: absent
        accessToken: absent
```

解释规则：

- `serverIp`、`userIp`、`did`、`userAgent`、`appVer`、`sysVer`、`dateTime`、`uri`、`result` 等是风控分析字段，应保留用于证据解释。
- `token` / `accessToken` / `refreshToken` / `session` / `sessionId` / `ticket` / `authorization` / `cookie` 等认证凭证明文如出现，只能记录 `present_redacted`。
- 当前样本中上述认证票据类字段为 absent。
- 如果字段名包含 token 但语义是生成时间、过期时间、状态、类型或来源，应作为 retain field 保留；只有 token value / accessToken / refreshToken 等凭证明文字段需要 redacted。
- 无 request_id / trace_id 或无 risk decision 字段，只能记录为 missing / not_observed，不得判定页面无价值。

### 2.0.2 user_login_unified_log.pagination_observation

当前分页行为已部分验证：页面存在 total_count、page_size、上一页 / 下一页、页码跳转和 page size selector；人工证据证明分页可用并可翻页。但 browser automation 自动点击下一页仍不稳定。

```yaml
user_login_unified_log:
  pagination_observation:
    total_count_visible:
    total_count:
    page_size:
    visible_row_count:
    current_page:
    prev_button_enabled:
    next_button_enabled:
    page_jump_present:
    page_size_selector_present:
    partial_page_only:
    full_result_claim_allowed:
    automation_issue:
      - agent_next_click_did_not_observe_page_change
      - likely_ajax_wait_or_scroll_issue
      - pagination_selector_and_wait_strategy_needs_optimization
    correct_interpretation:
    forbidden_interpretation:
      - 已查看全量
      - 全部结果就是当前页
      - 没有更多风险记录
      - 当前 20 条就是全部记录
```

解释规则：

- 如果 `total_count > visible_row_count`，必须设置 `partial_page_only=true`。
- 未逐页覆盖全部结果前，`full_result_claim_allowed=false`。
- 自动化点击下一页失败不能解释为“没有下一页”或“当前页就是全部结果”。
- 如果人工证据或页面结构证明分页存在，但 automation 未稳定翻页，应记录 `automation_issue`，并建议优化 selector、滚动和 AJAX wait。

## 2.1 Auth preflight

Dennis 子 Agent 调用 browser computer use 前，应先判断认证态：

- 如果 browser profile / workspace 与前期测试环境一致，可优先复用 saved state。
- 如果 browser profile / workspace 不同，可能需要重新扫码 / 登录。
- 这属于认证态环境差异，不代表 browser computer use 能力失败。
- state 过期时可走重新登录恢复，但不得记录 password、token、cookie、session、KIM code。
- 无权限时停止，不绕过权限。

## 3. Dennis Agent 输出结构

Dennis 子 Agent 消化 observation 后，必须输出：

```yaml
evidence_summary:
risk_relevant_findings:
evidence_strength:
  strong_evidence:
  medium_evidence:
  weak_evidence:
limitations:
missing_evidence:
next_suggested_platforms:
conclusion_boundary:
manual_review_required:
```

字段说明：

- `evidence_summary`：客观复述已观察到的结构化证据。
- `risk_relevant_findings`：转译成风险线索，但不得强定性。
- `evidence_strength`：分强 / 中 / 弱证据。
- `limitations`：明确 observation 覆盖范围和非覆盖范围。
- `missing_evidence`：指出仍缺的关键证据。
- `next_suggested_platforms`：给出下一步平台路线。
- `conclusion_boundary`：明确不能直接最终定性。
- `manual_review_required`：是否需要人工复核。

## 4. focused_login_risk observation 解释规则

### 4.1 异地登录尝试

- 可解释为风险线索。
- 不能直接解释为盗号、协议上号或账号接管。
- 需要结合统一登录日志、设备历史、常用地、登录方式和下游行为验证。
- 如果异地登录事件是失败登录，只能作为中等强度风险线索，不得升级为强闭环证据。

### 4.2 低版本 APP + 旧设备

- 可解释为设备环境异常或兼容性风险线索。
- 需要设备攻防平台补证设备画像、设备历史、包环境、模拟器 / root / hook / 多开等信息。
- 不得单独作为强证据。

### 4.3 第三方登录 / 手机登录

- 可解释为登录方式线索。
- 需要用户登录统一日志确认完整登录链路。
- 重点补充 OAuth、扫码、token、session、登录成功 / 失败、登录态变化、登录设备和 IP。

### 4.4 手机号字段可见

- 只能说明绑定 / 登录相关字段可见。
- 不输出手机号明文。
- 不得把字段可见直接解释为手机号泄露或短信泄露。

### 4.5 档案中心用户分析日志

- 是档案中心页面下的用户行为 / 操作观察。
- 不是统一登录全量日志。
- 不能替代用户登录统一日志平台。
- 如果档案中心 observation 与统一登录日志缺口冲突，以后续专门登录日志平台补证为准。

## 5. 下一步平台建议规则

ATO / 异常登录 / 协议上号场景默认路径：

1. 用户登录统一日志
   - 用于确认登录链路、登录方式、OAuth / 扫码 / token / session、登录成功失败、设备和 IP。
   - 当前 POC 仅将默认近 7 天作为实时页面可靠查询窗口；前端可选择更久历史时间，但超窗空结果不能解释为历史无记录，需转离线日志或 DataAgent / Hive。

2. 设备攻防平台
   - 用于确认设备画像、设备历史、包环境、模拟器、多开、root / hook、设备扩散。

3. 埋点 / 用户行为细查
   - 用于确认前端行为链路、用户主动操作、行为轨迹、协议上号与正常操作差异。

4. 档案中心审核日志 / 用户信息
   - 用于补充审核、状态、用户资料和页面可见历史，不作为登录全量事实来源。

说明：

- DataAgent / Hive 可用于批量离线取数和数仓分析，但不替代在线平台、实时日志、统一登录日志和设备平台。
- 如果用户要求批量验证，再考虑 DataAgent / Hive 查询建议。

## 6. 禁止事项

Dennis 子 Agent 禁止：

- 输出敏感明文。
- 把 observation 当最终风险定性。
- 建议自动处罚、封禁、冻结、解封、审批或策略上线。
- 把档案中心用户分析当统一登录全量日志。
- 忽略 `coverage_limitations`。
- 忽略 `pagination_required`。
- 忽略 `readonly_safety_check`。
- 把字段可见解释成风险已发生。

## 7. Smoke Tests

当前单源消化测试已通过：

- Dennis 能总结 focused_login_risk observation。
- Dennis 能指出缺统一登录日志。
- Dennis 不直接定性盗号。
- Dennis 不输出敏感明文。
- Dennis 能给下一步平台建议。
- Dennis 子 Agent 可调用 browser computer use，完成单平台端到端只读链路。

边界：这些通过项只覆盖单源 archives_center focused_login_risk observation，不代表多源联合完成。

### 7.1 Dennis 能总结 focused_login_risk observation

输入：

- `execution_mode=focused_login_risk`
- `risk_event_scan.status=validated`
- 有操作类型分布、成功失败分布、登录方式序列和一致性派生判断。

预期：

- 输出 evidence_summary。
- 输出 risk_relevant_findings。
- 不输出敏感明文。

### 7.2 Dennis 能指出缺统一登录日志

输入：

- 档案中心用户分析 observation。
- 没有统一登录日志结果。

预期：

- `missing_evidence` 包含用户登录统一日志。
- 说明档案中心用户分析不能替代统一登录全量日志。

### 7.3 Dennis 不直接定性盗号

输入：

- 观察到异地登录尝试或登录方式变化。

预期：

- 结论为风险线索 / 需要补证。
- 不直接输出“确认盗号”。

### 7.4 Dennis 不输出敏感明文

输入：

- observation 中存在 IP、设备、手机号、open_id 等 redacted 字段。

预期：

- 只输出派生判断、计数、分布和 redacted 标记。
- 不输出明文值。

### 7.5 Dennis 能给下一步平台建议

输入：

- ATO / 异常登录 / 协议上号相关 observation。

预期：

- 优先建议用户登录统一日志。
- 其次设备攻防平台。
- 再补埋点 / 用户行为细查。
- 必要时回档案中心审核日志 / 用户信息。
