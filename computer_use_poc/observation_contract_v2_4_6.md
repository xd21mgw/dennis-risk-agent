# v2.4.6 Observation Contract

本文定义 Dennis 子 Agent 调用 browser computer use 完成档案中心只读查询后，如何读取、解释、汇总 browser 返回的 observation，并给出下一步建议。

当前验证状态：

- single-source archives_center focused_login_risk observation digestion validated。
- v2.4.7 end-to-end readonly joint test validated：Dennis 子 Agent 可调用 browser computer use，browser 返回 observation 后 Dennis 可完成证据消化。
- user_login_unified_log 是多源 observation 的第二个 source，当前为 v2.4.8 partially ready。
- user_login_log_api_readonly_hand 是 v2.4.10 新增的统一登录日志 API 优先读取方式，当前为 `get_only_validated / api_readonly_poc`；UI hand 保留为 auth bootstrap / fallback / 字段发现。
- v2.4.8 Run 006 已验证 multi-source entry resolution；该 run 当时被 `agent-browser` 档案中心独立登录态阻断，状态为 `multi_source_e2e_blocked_by_archives_auth`。v2.5.8.1 进一步证明：档案中心独立登录页若账号 / 用户名已预填，可通过点击“下一步”恢复进入档案中心，标记为 `recoverable_preflight_success`。
- v2.4.8 Run 007 已验证同 userId 档案中心 + 用户登录统一日志 focused_login_risk multi-source e2e，状态为 `multi_source_e2e_validated_with_partial_coverage`。
- v2.4.8 Run 008 ~ Run 011 已补充 saved state 复用、档案中心用户分析分页修正、审核 / 打标日志可访问性、统一登录日志 special event detail key extraction。
- v2.5.8.1 已完成云端内部 Agent 三源 E2E 成功运行：`tianshi_strategy_hit_check`、`unified_login_log_check`、`archives_center_profile_check` 均成功。
- 当前 release 状态为 `release_candidate_not_final`。
- 当前已验证单源消化和 focused_login_risk 多源 observation partial coverage；不代表多源联合风险研判或最终定性完成。
- device_sdk_foundation 是 v2.5.0 计划接入的第三个 browser computer use source，当前仅完成 readonly POC / internal playbook 设计，状态为 `design_pending_validation`。
- frontend_activity_profile 是 v2.5.2 计划接入的前端活跃画像只读 source，当前仅完成方法论、URL 模板、schema、test cases 和 run log 模板，状态为 `design_only_pending_browser_validation`。
- tianshi_strategy_platform_rcp 是 v2.5.5 已沉淀的策略命中只读 source，当前仅覆盖 `fastQueryHbase` / `readonly_strategy_hit_check` 极简能力，用于判断 `sourceId` 在指定时间窗口内是否命中生产反作弊 / 风控策略。
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
  - platform: device_sdk_foundation
  - platform: frontend_activity_profile
  - platform: tianshi_strategy_platform_rcp
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
- v2.4.10 API hand 已验证 GET `/rest/unified/log/search` 可直接返回当前查询窗口内完整结果；标准用户查询必须使用 `userId` 参数，不得把用户 ID 放到 `query` 参数中。
- 当前尚未 fully validated；Run 007 仅验证 focused_login_risk multi-source observation partial coverage。
- 当前 POC 仅将页面默认 / backend default 的近 7 天作为实时页面可靠查询窗口；前端时间控件允许选择超过最近 7 天，但超窗“暂无数据”不得解释为历史无记录。
- 本轮页面未显式展示具体 start_time / end_time，但查询结果显示存在默认近 7 天行为；不得写成 UI 明确展示最近 7 天。
- 需要离线补证时建议 DataAgent / Hive。
- `device_sdk_foundation` 后续用于补充设备侧画像、SDK 采集状态、设备风险标签、设备一致性和设备关系摘要；当前未完成 source entry / auth preflight 实跑，不得写成可用能力。
- `frontend_activity_profile` 后续用于补充前端活跃痕迹，只读取“用户属性及时长”区域，不替代完整行为序列、后端日志、登录日志或设备 SDK。
- `tianshi_strategy_platform_rcp` 用于补充策略命中证据，不替代登录链路、设备画像、前端行为或离线数仓取证。

### 2.0.-6 user_login_log_api_readonly_observation

v2.4.10 API hand 用于统一登录日志结构化读取。

```yaml
user_login_log_api_query:
  standard_query_mode:
    userId:
    did:
    query:
  fallback_query_mode:
    query:
    userId:
    did:
  from_timestamp:
  to_timestamp:
  recallSource:
  reliable_window:
  over_reliable_realtime_window:
```

标准查询模式：

```yaml
standard_query_mode:
  user_id_exact_query:
    userId: "{target_user_id}"
    did: ""
    query: ""
```

fallback 查询模式：

```yaml
fallback_query_mode:
  keyword_query:
    query: "{keyword}"
    userId: ""
    did: ""
```

响应结构：

```yaml
user_login_log_api_response:
  status_code:
  code:
  total_count:
  logSearchModels_length:
  api_full_result_loaded:
  index_continuity:
    first_index:
    last_index:
    continuous:
  log_models:
    - date:
      timestamp:
      index:
      userIds:
      dids:
      method:
      logSource:
      logTags:
      logContent_keys:
      normalized_event_type:
      credential_fields_redacted:
```

pagination discovery:

```yaml
unified_log_api_pagination_discovery:
  total_count:
  logSearchModels_length:
  length_equals_totalCount:
  pagination_request_triggered_on_ui_page_change:
  pagination_mode: frontend_pagination
  api_full_result_loaded:
  ui_frontend_pagination:
```

解释规则：

- 标准用户查询必须用 `userId` 参数，不能用 `query` 参数替代。
- `query=用户ID` 只能视为 keyword fallback，不能作为 Dennis Agent 标准用户链路查询方式。
- 若 `logSearchModels.length == totalCount`，可标记 `api_full_result_loaded=true`。
- 若 `logSearchModels.length < totalCount`，才需要继续寻找 page / offset / cursor / searchAfter 等分页参数。
- `index` 不强制从 1 开始，只需判断连续性。
- API full result 只代表当前查询条件和 reliable window 内完整，不代表历史全量。
- API 返回空不等于无风险，也不等于用户无登录记录。
- API 401 / 403 / redirect 不等于无数据。
- UI hand 仍需标记 `ui_visible_page_only=true`；API hand 可标记 `api_full_result_loaded=true`。

`logContent` parse policy：

- `logContent` 是 JSON string，允许 parse key 和非凭证明文 value。
- 保留 userId、deviceId、did、userIp、userIpv6、serverIp、userAgent、appVer、sysVer、uri、method、status、actionType、result、reason、timestamp、dateTime、loginType、deviceModel、osVersion、sdkVersion 等风控字段。
- token、loginToken、tokenId、accessToken、refreshToken、session、sessionId、ticket、authorization、cookie、rawAuthHeader 等凭证明文字段只输出 `present_redacted`。
- 不输出完整 response，不输出完整 `logContent`。

### 2.0.-4 tianshi_strategy_hit_observation

当前为 v2.5.5 validated by internal Agent，范围仅限 `fastQueryHbase` / `readonly_strategy_hit_check`。

```yaml
tianshi_strategy_hit_observation:
  platform: tianshi_strategy_platform_rcp
  platform_display_name: 天狮策略平台 / rcp
  query_type: fastQueryHbase
  capability: readonly_strategy_hit_check
  query_object: sourceId
  query_value_policy: source_id_allowed
  time_window:
  query_status:
  api_response_status:
  api_message:
  raw_record_count:
  has_strategy_hit:
  production_policy_hit_count:
  evidence_strength:
  riskDecision_distribution:
  eventType_distribution:
  riskType_distribution:
  confidence_distribution:
  sample_hits:
    max_items: 3
    value_policy: summarized_without_trace_or_host
  trace_observation:
    has_trace:
    host_value_recorded: false
    port_value_recorded: false
    trace_id_value_recorded: false
    trace_value_policy: not_in_standard_observation
  readonly_safety_check:
  limitations:
```

判断规则：

- `status=200` 且 `message=成功` 时，`query_status=success`。
- `data` 数组非空时，`raw_record_count > 0`。
- 任一 `data[*].hitProductionPolicy=true` 时，`has_strategy_hit=true`。
- `production_policy_hit_count` 统计 `hitProductionPolicy=true` 的记录数。
- `riskDecision`、`eventType`、`riskType` 做简单分布统计。
- `sample_hits` 最多保留 3 条。
- `host`、`port`、`traceId` 不进入标准 observation；如需记录，只记录 `has_trace=true/false`。

解释边界：

- 天狮命中是策略证据，不等于最终作弊定性。
- `riskDecision=阻止/验证` 代表策略返回动作，不代表最终执行成功。
- 无命中不代表无风险。
- 该 source 不替代 DataAgent / Hive、用户登录统一日志、档案中心、前端埋点、设备 SDK / 设备平台。

v2.5.6 observation 消费规则：

```yaml
tianshi_strategy_hit_consumption:
  has_strategy_hit_true:
    evidence_layer: strong_strategy_evidence
    allowed_interpretation: 查询窗口内存在天狮生产策略命中记录。
    forbidden_interpretation:
      - 用户一定作弊
      - 最终风险定性成立
      - 处罚实际执行成功
  has_strategy_hit_false:
    evidence_layer: missing_strategy_hit_in_window
    allowed_interpretation: 查询窗口内未见天狮生产策略命中。
    forbidden_interpretation:
      - 用户无风险
      - 用户未作弊
      - 其他证据源无风险
  query_status_failed_or_permission_blocked_or_unknown:
    evidence_layer: unavailable
    allowed_interpretation: 当前天狮策略命中证据不可用。
    forbidden_interpretation:
      - 无风险
      - 无策略命中
  riskDecision:
    allowed_interpretation: 策略返回动作。
    forbidden_interpretation:
      - 最终执行结果
      - 处罚实际生效状态
```

### 2.0.-4a tianshi_eventlist_api_read_observation

当前为 v2.5.9 validated by internal Agent，范围仅限 `POST /v2/rest/event/eventList` 请求级 / 事件级只读细查。

```yaml
tianshi_eventlist_api_read_observation:
  platform: tianshi_strategy_platform_rcp
  platform_display_name: 天狮策略平台 / rcp
  query_type: eventList
  capability: tianshi_eventlist_api_read
  endpoint: /v2/rest/event/eventList
  method: POST
  source_id:
  source_ids_empty: false
  event_type:
  time_window:
    start:
    end:
    timezone: Asia/Shanghai
    cross_day:
    segmentation:
  query_status:
  auth_status:
  event_list_count:
  eventList_present:
  tableHeaderList_present:
  extracted_events:
    max_items: 3
    value_policy: summarized_without_full_weapon_payload
  sampling_and_completeness:
    hit_policy_events_recorded_100_percent: true
    non_hit_policy_events_sampled: true
  readonly_safety_check:
  blockers:
  limitations:
```

解释规则：

- `eventList API` 成功时，`query_status=success`。
- 401 / 403 / `redirect_to_login` 归为 auth blocker，不得输出 `no_data`。
- `sourceIds` 为空时不得作为用户级证据。
- `event_list_count=0` 只能说明该查询条件下无事件，不能代表用户无风险或行为未发生。
- 命中策略事件 100% 记录，非命中策略事件存在抽样。
- `eventList` 查询窗口原则上不能跨天；如必须查长窗口，应分段，并在 observation 中记录 segmentation。
- `extracted_events` 最多保留 3 条样例。
- `weaponDataMap` / `weaponDecodeDataWeapon` 只做摘要，不全文落盘，避免字段过重。
- 不保存或输出 cookie / token / 完整 header。
- `logged_in_user` 只能作为 run log 样例，不是固定规则。

与 `fastQueryHbase` 的关系：

- 用户只问“是否命中生产策略”时，优先 `fastQueryHbase`。
- 用户明确要求“细查某次具体请求 / 看某个 eventType 明细 / 看注册事件字段 / 看登录事件字段 / 看实时反馈动作 / 看错误码或惩罚动作”时，可选择 `eventList API-read`。
- `fastQueryHbase` 不足以解释请求字段细节时，再补 `eventList API-read`。
- 大范围统计、趋势、历史聚合不使用 `eventList`，应转 DataAgent / Hive 或要求缩小窗口。

### 2.0.-5 e2e_multi_evidence_evidence_summary

v2.5.8 E2E 多手脚只读验证中，Dennis 消费多个 observation 时必须显式列出每个 evidence source 的状态。

```yaml
e2e_multi_evidence_summary:
  source_status:
    tianshi_strategy_hit_check:
      status: success | failed | permission_blocked | no_data | skipped
      coverage:
    unified_login_log_check:
      status: success | failed | permission_blocked | no_data | skipped
      coverage:
    archives_center_profile_check:
      status: success | failed | permission_blocked | user_not_found | skipped
      coverage:
  evidence_readiness:
    completed_sources:
      - tianshi_strategy_hit_check
      - unified_login_log_check
      - archives_center_profile_check
    failed_sources:
  supporting_evidence:
    - source:
      finding:
      strength:
  counter_evidence:
    - source:
      finding:
      interpretation:
  missing_evidence:
    - source:
      reason:
      impact:
  blockers:
    - source:
      blocker:
      next_action:
  boundary_notes:
    - 单源 strong evidence 不得直接输出 definitive conclusion。
    - failed / permission_blocked / no_data 必须进入 missing_evidence 或 blockers。
    - 无命中 / 无结果不等于无风险。
```

消费规则：

- 每个 required source 都必须有 `status`。
- `failed / permission_blocked / no_data / user_not_found` 不得被忽略，必须进入 `missing_evidence` 或 `blockers`。
- 单源 strong evidence 只能提高怀疑等级，不得直接输出 definitive conclusion。
- 未查的 optional source 必须标注为 not_required_in_current_e2e 或 missing_evidence，不能假装已查。
- `independent_login_required` 是 auth blocker，不是 `no_data`。
- `recoverable_preflight_success` 是可恢复认证态，不应计入 `failed_sources`。
- 登录页状态不得作为用户无风险、用户无记录、档案无数据的证据。
- 三源成功时，`evidence_readiness.completed_sources` 应包含 `tianshi_strategy_hit_check`、`unified_login_log_check`、`archives_center_profile_check`。
- 当档案中心 preflight 可恢复成功时，`profile_evidence.query_status=success`。
- 当档案中心 preflight 不可恢复时，`profile_evidence.query_status=blocked_by_independent_login`，并进入 `blockers` / `missing_evidence`。

档案中心 recoverable preflight 输出：

```yaml
archives_center_recoverable_preflight:
  redirected_to_independent_login:
  username_prefilled:
  next_clicked:
  recoverable_preflight_success:
  query_status_after_recovery: success | blocked_by_independent_login | wait_for_manual_login
  fixed_identity_rule: false
  note: 账号 / 用户名已预填时可尝试点击下一步；不得绑定具体账号名作为固定判断条件。
```

### 2.0.-3 frontend_activity_profile_observation_draft

当前为 v2.5.2 design draft，pending browser validation。

```yaml
frontend_activity_profile_observation:
  platform: track_analysis
  module: 用户洞查 / 用户细查详情 / 用户属性及时长
  app_name:
  query_subject_type:
  query_subject_value:
  query_url:
  query_status:
  profile_card:
    user_id:
    register_time:
    active_days_bucket:
    fan_distribution:
    device_attributes:
  usage_duration:
    chart_present:
    time_range_detected:
    active_days_observed:
    total_usage_duration_observed:
    daily_usage_points_observed:
    peak_usage_day:
    peak_usage_duration:
  activity_judgement:
    has_frontend_activity_signal:
    activity_strength:
    judgement_reason:
    evidence_strength:
    evidence_limitations:
  next_evidence_to_collect:
    login_unified_log:
    device_sdk_profile:
    backend_action_log:
    frontend_event_sequence:
    data_agent_hive_check:
  raw_observation_reference:
    screenshot_path:
    url:
    captured_at:
```

解释规则：

- 有使用时长 / 活跃天数，只能说明存在前端活跃信号。
- 不能直接证明是真人操作。
- 不能直接证明是本人操作。
- 不能直接证明没有自动化、脚本、群控。
- 不能证明某个具体业务动作一定发生过。
- 如果要判断具体链路，需要行为序列、后端日志、登录日志、设备 SDK 共同补证。
- 本 source 当前不读取下方行为记录、行为回放、行为序列、单条事件详情、事件参数或页面路径明细。

### 2.0.-2 device_sdk_foundation_observation_draft

当前为 v2.5.0 design draft，pending validation。

```yaml
device_sdk_foundation_observation:
  query:
    input_device_id:
    query_type:
    time_range:
  page_access:
    page_accessible:
    auth_required:
    permission_blocked:
    redirected_to_login:
  device_basic_info:
    device_id:
    did:
    device_type:
    device_model:
    os:
    os_version:
    app_version:
    sdk_version:
  device_risk_profile:
    risk_tags:
    risk_level:
    root_or_jailbreak:
    hook_detected:
    emulator_detected:
    multi_open_detected:
    automation_detected:
    tamper_detected:
  relation_summary:
    related_user_ids:
    related_ips:
    related_apps:
    related_login_events:
  field_visibility:
    visible_fields:
    missing_fields:
  limitations:
  readonly_safety_check:
```

解释规则：

- 设备风险标签是设备侧线索，不是最终风险定性。
- 设备关系聚集不能直接等同群控。
- 设备异常不能直接等同协议上号。
- 登录态阻断不能解释为设备无数据。
- 权限阻断不能解释为设备无风险。
- 未看到字段不能解释为字段不存在，需区分 `field_not_visible` / `permission_blocked` / `query_no_result`。
- deviceId / did / sdkVersion / appVersion / riskTag / deviceModel / osVersion / ip / region 等风控证据字段可以保留；token / session / ticket / authorization / cookie 等认证凭证明文只输出 `present_redacted`。

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
- 档案中心跳转独立登录页时，应先判断账号 / 用户名是否已预填；若已预填，可点击“下一步”尝试恢复会话。
- recoverable preflight 成功时，档案中心 source 应继续执行并记录 `query_status=success`，不得计入 failed source。
- recoverable preflight 不成功时，返回 auth blocker，不得把统一登录日志单源 observation 包装成多源联合结果。
- 下一步应准备 archives saved state、人工登录或在已有认证态环境中重跑，而不是继续猜入口或要求用户手动执行平台查询。

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
- 这是 Run 006 当时执行环境下的认证阻断事实；v2.5.8.1 后续证明，如果独立登录页账号 / 用户名已预填，点击“下一步”可能恢复进入档案中心。
- 通用规则应优先执行 `archives_independent_login_preflight_required_but_recoverable` 判断；不可恢复时再进入 auth blocker。

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
