# Computer Use Readonly POC

## 1. POC 目标

验证 Dennis Risk Agent 体系中的 Dennis 子 Agent 是否可以调用 browser computer use / browser automation 环境，完成最小只读平台查询动作。

本 POC 只验证一个动作：

输入 `user_id`，打开档案中心，执行只读查询，返回结构化 observation。

## 2. 范围

- 平台：档案中心。
- 查询对象：单个 `user_id`。
- 操作类型：只读页面查询和页面信息观察。
- 输出：结构化 observation，不输出最终风险定性。

## 3. 非目标

- 不做多平台联动。
- 不做批量查询。
- 不做任何写操作、提交、处置、审批、封禁、解封、导出。
- 不绕过权限。
- 不自动形成处罚、冻结、解封、策略上线建议。
- 不替代 Dennis 子 Agent 的风险理解、证据解释和下一步建议。

## 4. 与 v2.4.3 的关系

v2.4.3 internal platform routing patch 负责：

- 判断应该查哪个平台。
- 解释平台字段和边界。
- 给出跨平台取证路径。

computer use readonly POC 负责：

- 验证只读页面操作是否可行。
- 将页面可见信息整理为 observation。
- 把查询失败、权限不足、页面异常等情况结构化返回。

二者关系：

Dennis 子 Agent 先根据用户问题和 `internal_risk_platforms/00_platform_routing_index.md` 判断是否应查档案中心，再生成 readonly plan，并调用 browser computer use 执行档案中心只读查询。browser computer use 返回 observation 后，由 Dennis 子 Agent 消化 observation，输出证据总结、风险线索、证据缺口和下一步建议。

DataAgent / Hive 边界不变：DataAgent 只负责 Hive / 公司数仓取数分析，不替代 browser computer use、在线平台、实时日志、策略平台或设备平台。

## 4-A. Multi-source e2e entry resolution rule

多源 e2e 前，每个 source 必须先完成 `entry_resolution`。

规则：

- `entry_resolution` 必须优先读取已有 playbook / run log / runtime snapshot / README。
- 不允许凭记忆或猜测 URL。
- 不允许从首页菜单随意探索作为正式执行路径。
- 如果 entry 找不到，必须返回 `source_entry_missing`，而不是继续生成半成品联合报告。
- 一个 source 失败时，不能把另一个 source 的 observation 包装成 multi_source observation。
- 不允许要求用户手动执行，除非明确标记为 `human_input_required` 且说明缺失文档项。
- 档案中心入口缺失不等于档案中心无数据。
- 档案中心入口 404 不等于用户无档案记录。
- 统一登录日志单源结果不等于多源 e2e 成功。
- 多源 e2e 必须 `same_user_id_used=true`。

`entry_resolution` 输出格式：

```yaml
source_entry_resolution:
  source_name:
  docs_searched:
  entry_found:
  entry_url:
  validated_execution_path_found:
  selector_or_playbook_found:
  blocker:
  next_action:
```

## 5. 当前状态

当前状态：

```text
v2.4.4-computer-use-readonly-poc-validated
```

最新 P0 深读状态：

```text
v2.4.5 archives center user profile P0 tabs deep-read validated
```

已验证：

- 档案中心 `userId` direct URL 只读查询链路可用。
- 完整认证路径为 SSO KIM Code → 档案中心独立登录 → userId 直达详情页。
- saved state 复用已验证：加载已保存的档案中心认证 state 后，可直接打开 userId direct URL，无重定向，无需重新登录。
- 档案中心 SPA 可完整渲染。
- 页面可识别用户信息、审核日志、打标日志、用户分析、视频作品集、直播作品集、粉丝列表、关注列表、合集列表、收藏列表、动态列表等 Tab。
- 页面可识别基本信息、用户实时负向、最近登录、最近启动、注册信息、账户信息、同设备登录/注册入口等模块。
- target object / operator account 身份信息分层规则已补齐：`user_header` 可用于核验查询目标，`nav_menu` 当前登录操作者信息必须 redacted。
- 敏感字段策略已分层：认证票据类永远 `never_collect`；IP、设备 ID、手机号、open_id、版本、地理位置等字段可在执行态用于派生风控判断，但沉淀态只输出 redacted、计数、分布或一致性结论；字段名、操作类型、时间范围、表头和分布类结构信息可沉淀。
- userId 不存在 / 非法时的预期失败处理已验证：已登录、无重定向、SPA 完整渲染、页面返回“用户不存在”，识别为 `USER_NOT_FOUND`。
- v2.4.5 已验证用户信息、用户分析、审核日志、视频作品集四个 P0 Tab 的只读深读。
- v2.4.5.1 是性能优化设计，不是新能力扩展；目标是通过 quick / focused / deep mode、scoped extraction 和列表采样降低耗时与 token 成本。
- v2.4.5.1 quick mode 已验证，约 22 秒。
- v2.4.5.1 focused_login_risk 结构提取已验证，103 秒；full risk_event_scan 仍待验证。
- v2.4.5.1 focused_login_risk risk_event_scan 已部分验证，约 156 秒；已能输出派生风险摘要，但存在 selector 噪声，状态为 `partial_validated_with_selector_noise`。
- v2.4.5.1 focused_login_risk risk_event_scan selector noise 已修复，约 63 秒；row feature filter 已验证有效，状态可标记为 `validated`。
- quick mode、focused structure extraction、focused risk_event_scan 均已验证。
- v2.4.6 Dennis Agent single-source observation digestion 已验证：能消化档案中心 focused_login_risk observation，并输出证据总结、风险线索、证据缺口和下一步平台建议。
- v2.4.7 end-to-end readonly joint test 已验证：用户问题 → Dennis 子 Agent 生成 readonly plan → browser computer use 执行 → scripts eval 提取 observation → dedupe 生效 → Dennis 消化 observation → 输出证据总结 / 风险线索 / 缺口 / 下一步平台建议。
- v2.4.7.1 已验证档案中心“用户分析 / APP端核心操作日志”API direct POST：`POST /v3/user/log/coreLogs/fetch` 可在已登录档案中心 browser session 内通过 same-origin fetch 成功读取。该能力属于档案中心用户分析 Tab，不是用户登录统一日志；后续 `focused_login_risk` 优先走 API direct POST，DOM scoped JS eval / row feature filter 作为 fallback。API response 中 `requestParam` / `extraParam` 可能包含 token、tokenId、refresh_token、sig、open_id、egid 等敏感字段，只能执行态读取用于派生判断，不得输出明文或沉淀完整 JSON。
- v2.4.8 用户登录统一日志 readonly POC 已完成页面可访问性、部分详情弹窗、边界行为和分页行为实跑，入口为 `https://user-center-workbench.corp.kuaishou.com/create-applications/unified-log-search`，当前状态为 `page_accessibility partially validated; result table partially validated; switchUser detail partially validated; refreshToken detail validated for readonly JSON key extraction; no_result/time_window boundary partially validated; pagination behavior partially validated`。
- v2.4.10 已新增用户登录统一日志 API readonly hand POC。GET `/rest/unified/log/search` 已验证可访问，标准用户查询必须使用 `userId` 参数，不能把 userId 放到 `query` 参数里。样例一次返回 `totalCount=141` 且 `logSearchModels.length=141`，说明 API 可一次性返回当前查询窗口内完整结果；UI 翻页属于前端分页。当前状态：`user_login_log_api_hand=get_only_validated / api_readonly_poc`，final release package 未更新。
- 未点击任何写操作按钮，只读安全检查通过。

未验证：

- 多平台 computer use。
- 多入参查询。
- 批量查询。
- 自动研判。
- 二级链接、详情页、查重页。
- 处置、审批、导出、封禁、解封等任何写操作。
- 多平台 / 多入口风险联动。
- 多源联合 observation digest 已完成 focused_login_risk partial coverage 验证，但不代表 full validation。
- 自动风险定性或自动处置。
- 用户登录统一日志全分页遍历、权限阻断、OAuth / 扫码字段、risk decision 字段。
- 用户登录统一日志分页功能已由人工证据证明可用，但 browser automation 自动翻页仍不稳定；未覆盖全部分页前必须标记 `partial_page_only=true`。
- 用户登录统一日志详情弹窗仍不是 fully validated：`switchUser` detail 只完成 partially validated；`refreshToken` detail 已验证 readonly JSON key extraction，但未验证嵌套 JSON 完整性和 copy button 行为。

后续建议：

- 将 dedupe 逻辑内置到 eval 脚本中。
- 继续保持边界：本阶段只代表档案中心 `userId` direct URL 下的只读派生观察能力，不代表自动风险定性完成。
- v2.4.7 当前仅验证档案中心 focused_login_risk 单平台端到端链路；不代表多平台联合、不代表自动风险定性、不代表自动处置。
- v2.4.8 用户登录统一日志页面前端允许选择超过最近 7 天的历史时间，但当前 POC 仅将默认最近 7 天作为实时页面可靠查询窗口。超出窗口返回“暂无数据”时，不得解释为历史无记录或全量无风险；长周期登录链路应转 DataAgent / Hive 或离线日志能力。当前不得写成 fully validated。
- v2.4.8 分页样例中 total_count 可见，样例 total_count=133、page_size=20；人工证据证明可翻到第 4 页且数据变化。browser automation 未稳定完成自动翻页前，不得声称当前页就是全量结果。
- v2.4.10 API hand 发现：如果 `logSearchModels.length == totalCount`，可标记 `api_full_result_loaded=true`；UI hand 仍需保留 `ui_visible_page_only=true` / `partial_page_only`。API full result 只代表当前查询条件和可靠时间窗口内完整，不代表历史全量。
- v2.4.8 user_login_log_hand_runtime_snapshot 已生成：`outputs/intermediate/dennis_risk_agent_v2_4_8_user_login_log_hand_runtime_snapshot.md`；release package 未更新。
- v2.4.8 Run 006 已验证 multi-source entry resolution：Dennis 在档案中心 + 用户登录统一日志 e2e 前先读取档案中心 playbook / run log / runtime snapshot / README，找到档案中心入口和 selector/playbook。该 run 当时被 `agent-browser` 档案中心独立登录态阻断，状态为 `multi_source_e2e_blocked_by_archives_auth`，不是文档缺失、URL 缺失、页面无数据或统一登录日志失败。
- Run 006 clarification：档案中心 `userId` direct URL 已确认为 `https://admin.p.adm-corp.kuaishou.com/frontend/archives/index.html#/archives/user/profile?userId={userId}`；独立登录域为 `account.p.adm-corp.kuaishou.com`；认证链路为 SSO → 档案中心独立登录 → userId direct URL。旧环境中 `sso_session.py` 可 HTTP 级访问但 `agent-browser` GUI 进程未复用该 cookie，因此 direct URL 被重定向到独立登录页。后续 v2.5.8.1 证明：当独立登录页账号 / 用户名已预填时，点击“下一步”可能恢复进入档案中心，不应立即标记 failed。
- Run 006 中统一登录日志单源查询成功，`user_id=4700398885`、`total_count=133`、`page_size=20`、`visible_row_count=20`、`partial_page_only=true`；该结果只能作为单源 observation，不能包装成 multi-source e2e 成功。
- v2.4.8 Run 007 已完成同 userId 多源 e2e：档案中心 saved state 已解决，档案中心 direct URL 可访问，统一登录日志查询成功，跨源 DID / 历史一键登录 / 退出登录行为可对齐。当前状态为 `multi_source_e2e_validated_with_partial_coverage`，`multi_source_schema_ready=focused_login_risk_observation_only`，`release_status=release_candidate_not_final`。
- v2.4.8 多源 e2e lessons learned 已沉淀：`computer_use_poc/multi_source_e2e_lessons_learned_v2_4_8.md`。
- v2.4.8 Run 008 已验证档案中心 saved state 复用稳定性：`archives_saved_state_reuse=validated`，但只代表 `archives_center_4700398885_20260519` 当前可复用，不泛化为所有账号 / 所有时间。
- v2.4.8 Run 009 已修正档案中心用户分析分页行为：用户分析 / APP端核心操作日志存在分页，样例 `total_count=1181`、`page_size=10`，此前“无分页 / 无限滚动”结论作废。未遍历全部分页前必须保留 `partial_coverage=true`。
- v2.4.8 Run 010 已部分验证档案中心审核日志 / 打标日志可访问性：审核日志有结果，打标日志表头可见；二者只作为补充 source，不替代登录链路证据。
- v2.4.8 Run 011 已验证统一登录日志高危接口 / 多账号登录详情 key extraction：高危接口偏服务端调用链视角，多账号登录偏客户端登录环境视角；凭证明文字段只输出 `present_redacted`。
- v2.4.8 RC plan 已生成：`outputs/intermediate/dennis_risk_agent_v2_4_8_release_candidate_plan.md`，当前仅为 release candidate not final。
- v2.5.0 已启动 Dennis Agent 5 — 设备 SDK 基建手脚设计，新增 `computer_use_poc/device_sdk_foundation_readonly_poc_v2_5_0.md` 和 `computer_use_poc/device_sdk_foundation_internal_agent_playbook_v2_5_0.md`。当前只做 `source_entry_resolution` + `browser_auth_preflight` 设计，不做真实页面执行，状态为 `design_pending_validation`。
- v2.5.2 已新增前端活跃画像只读手脚设计，覆盖“埋点分析 → 用户洞查 → 用户细查详情”页面上方“用户属性及时长”区域。当前只做方法论、URL 模板、schema、test cases 和 run log 模板沉淀，不抓取真实数据，不解析下方行为记录，状态为 `design_only_pending_browser_validation`。
- v2.5.3 已沉淀内部 Agent 返回的前端活跃画像 URL 直联预检结果：URL 可打开，登录态复用成功，无登录跳转 / 权限阻断，目标页面和“用户属性及时长”区域可见。该结果来自内部 Agent，不是 Codex 访问平台；下一步由内部 Agent 读取该区域并输出 observation sample。
- v2.5.3 单点 observation 已由内部 Agent 验证：KUAISHOU + userId + 444946196 可读取“用户属性及时长”区域并形成 observation，前端活跃信号强；该 observation 只能证明前端活跃存在性，不能证明真人、本人与具体业务动作。
- v2.5.4 四组合矩阵已由内部 Agent 验证：KUAISHOU / NEBULA × userId / deviceId 共 4 组全部成功，均可直联查询“用户属性及时长”区域。KUAISHOU 活跃信号强，NEBULA 使用时长几乎为零；deviceId 查询样例自动关联到同一用户，但不能单独证明稳定设备绑定关系。
- v2.5.3 / v2.5.4 extraction_mode 已校准：初始 profile card 与使用时长字段来自 `screenshot_manual_read`；后续已验证 profile card 可通过 `iframe[1].contentDocument → .user-card → innerText` 做 DOM 文本读取。使用时长图表为 canvas 渲染，DOM 只能确认图表存在，峰值和每日点位仍为截图视觉估算，精确数值需后续 tooltip / 图表接口 / network API 验证。
- v2.5.5 已沉淀天狮策略平台 / rcp 极简 readonly 手脚：查询类型为 `fastQueryHbase`，能力为 `readonly_strategy_hit_check`，用于判断 `sourceId` 在指定时间窗口内是否命中生产反作弊 / 风控策略。本轮内部 Agent 已验证 `sourceId=4231737183` 查询成功，`raw_record_count=4`，`has_strategy_hit=true`，`production_policy_hit_count=4`，`riskDecision` 分布为阻止 3 / 验证 1。该结果是策略证据，不等于最终作弊定性，不替代 DataAgent / Hive、登录统一日志、档案中心、前端埋点或设备平台。
- v2.5.6 已新增天狮 `strategy_hit_check` 路由规则：天狮手脚从“可用证据源”升级为“可被 Dennis Agent 查询计划调度的证据源”。当用户询问某个 `sourceId` 是否被风控 / 反作弊 / 生产策略命中过时，Dennis 可生成 `tianshi_strategy_hit_check` 只读查询计划；仍保持 readonly，不做写操作、不做最终风险定性。
- v2.5.7 已新增多手脚证据编排样例：当用户问“某用户是否有风险 / 为什么被拦截或验证”时，Dennis 不应只依赖天狮策略命中，而应生成包含 strategy / login / profile / behavior / device 证据的 `multi_evidence_query_plan`。该版本只新增编排样例，不新增平台能力，不调用真实平台。
- v2.5.8 已新增真实 E2E 多手脚只读验证模板：测试问题为“帮我看下 4231737183 今天是不是风险用户，为什么被阻止/验证？”。本轮只验证天狮策略命中、用户登录统一日志、档案中心三手脚最小闭环，不强制拉前端活跃画像、设备 SDK 或 DataAgent / Hive；当前为模板和 run log 模板，不是实际执行结果。
- v2.5.8.1 已归档云端内部 Agent 真实 E2E 三源成功运行：测试问题为“帮我看下 4231737183 今天是不是风险用户，为什么被阻止/验证？”。`tianshi_strategy_hit_check`、`unified_login_log_check`、`archives_center_profile_check` 三源均成功。档案中心先跳转 `account.p.adm-corp.kuaishou.com` 独立登录页，但账号 / 用户名已预填，点击“下一步”后成功进入档案中心，沉淀为 `archives_independent_login_preflight_required_but_recoverable`。该运行证明 Dennis Agent 可完成多手脚查询计划、多 observation 收集、跨证据汇总和边界说明；仍不代表自动风险定性或自动处置。
- v2.5.9 已新增天狮 `eventList API-read` 请求级细查 POC：内部 Agent 已验证在已认证 rcp 浏览器会话中，`POST /v2/rest/event/eventList` 可用。该能力作为 `fastQueryHbase` 的补充：`fastQueryHbase` 负责策略命中概览，`eventList` 负责具体请求 / 事件明细细查。`eventList` 必须依赖已认证 browser context，查询窗口应尽量小、原则上不能跨天；命中策略事件 100% 记录，非命中事件存在抽样，`eventList no_data` 不代表无风险或行为未发生。

Auth preflight：

- 如果 Dennis 子 Agent 使用的 browser profile / workspace 与前期测试环境不同，可能需要重新扫码 / 登录。
- 这属于认证态环境差异，不代表 browser computer use 能力失败。
- saved state 复用、state 过期、重新登录恢复规则继续有效。
- 如果 `agent-browser` 打开档案中心 direct URL 后跳到 `account.p.adm-corp.kuaishou.com` 独立登录页，应先判断账号 / 用户名是否已预填。若已预填，可点击“下一步”尝试恢复会话；成功进入档案中心时标记 `recoverable_preflight_success`，不得计入 failed source。若点击后仍要求密码 / 扫码 / MFA，或账号 / 用户名未预填，则返回 `archives_independent_login_required` / `wait_for_manual_login`。
- v2.4.9 已新增统一前置检查清单：`computer_use_poc/browser_auth_preflight_checklist_v2_4_9.md`。所有后续平台手脚在读取页面字段前，必须按 `source_entry_resolution → browser_auth_preflight → saved_state_reuse_check → single_browser_session_check → 页面字段探索` 顺序执行。
- 若 `browser_auth_preflight` 未通过，只能返回 blocker；不得把登录态阻断、saved state 缺失、SPA route 污染或 selector 范围不明解释成页面无数据、用户无记录或平台不可用。

v2.4.8 当前汇总状态：

```yaml
user_login_log_hand: partially_ready
multi_source_entry_resolution: validated
archives_saved_state_e2e: validated
archives_saved_state_reuse: validated
multi_source_e2e: validated_with_partial_coverage
archives_user_analysis_pagination: validated_with_correction
archives_audit_label_log_access: partially_validated
unified_log_special_event_detail: validated
release_status: release_candidate_not_final
```

仍未完成：

- unified_log_full_pagination_traversal。
- user_login_log_api_no_result_behavior。
- user_login_log_api_unauthorized_or_expired_auth_behavior。
- user_login_log_api_over_reliable_window_behavior。
- user_login_log_api_logContent_parse_normalization。
- archives_user_analysis_full_pagination_traversal。
- archives_user_analysis_api_direct_post_no_result_behavior。
- archives_user_analysis_api_direct_post_permission_blocked_behavior。
- archives_user_analysis_api_direct_post_response_shape_regression。
- permission_blocked_behavior。
- device_platform_verification。
- audit_label_log_full_validation。
- final_release_package_update。
- device_sdk_foundation_source_entry_resolution。
- device_sdk_foundation_browser_auth_preflight。
- frontend_activity_profile_browser_validation。
- frontend_activity_profile_dom_selector_validation。
- frontend_activity_profile_real_observation_run。
- frontend_activity_profile_user_attribute_duration_observation_sample。
- frontend_activity_profile_behavior_sequence_hand。
- frontend_activity_profile_usage_duration_precise_value_extraction。
- tianshi_strategy_hit_batch_or_long_term_validation。
- tianshi_strategy_hit_final_enforcement_verification。
- tianshi_strategy_hit_routing_live_regression。
- tianshi_eventlist_api_read_routing_live_regression。
- tianshi_eventlist_long_window_segmentation_validation。
- tianshi_eventlist_auth_blocker_validation。
- multi_evidence_orchestration_live_regression。
- e2e_multi_evidence_readonly_real_run。

## 6. SPA / agent-browser guardrail

后台 SPA 页面测试必须遵守：

- 不允许多个 Dennis / agent-browser session 同时访问同一个档案中心 saved state。
- 测试前必须关闭其他 browser session，确保 `single_browser_session=true`。
- Tab 点击前必须确认 click target 属于当前页面内部 Tab 容器，而不是左侧导航、顶部导航或其他应用入口。
- 点击前记录 `current_url`、`source_name`、`user_id`、`target_tab_text`、`target_tab_container_identified`、`click_target_scope`。
- 点击后校验 current_url 是否仍在目标 source 下、是否仍为同一 userId、target_tab 是否 selected、是否出现 `unexpected_route_redirect`。
- 如果点击后跳出目标 source，必须标记 `tab_click_invalid` / `unexpected_route_redirect`。
- unexpected route redirect 不能解释为目标 Tab 不可访问、无结果、无权限或用户无数据。

当前 agent-browser 是单 daemon / 单 Chrome 进程架构，`--session` 无法提供真正并行隔离；`--profile` 在 daemon 已运行时也不能可靠切换。当前阶段默认采用串行锁方案，同一时间只允许一个 agent-browser session 操作内部平台页面。
