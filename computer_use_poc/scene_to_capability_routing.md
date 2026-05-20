# Scene to Capability Routing

本文是体验优先的能力路由说明。用户仍按业务问题提问，系统内部再按 capability routing 选择只读手脚、实体解析或回答模板。

原则：

- 先满足用户体感目标，再选择 capability。
- 不为展示能力而过度查数、过度调平台。
- 不新增真实平台手脚。
- 不把 observation 包装成最终风险定性。
- 新手脚后续必须说明服务哪个体验 Case，或新增哪个体验 Case。

## 0A. 专家认知先判模式 expert_reasoning_first

用户体感目标：

- 用户在查证前需要专家解释现象、梳理候选路径、设计强区分证据时，先得到风控专家对问题本质和后续查询方向的判断。

Capability：

- `expert_reasoning_first`

核心定位：

- `expert_reasoning_first` 不是 case 默认入口。
- `expert_reasoning_first` 不是“研判 / 判断”默认入口。
- 它只处理“查证前的专家先验分析”。
- 明确 case + 明确实体 / 时间 / 查询对象 / 事实验证诉求，默认进入 Plan 模式或 read-only execution。

触发条件：

- 用户明确说“先不查数 / 先从专家视角判断 / 先解释现象 / 先给候选路径 / 先设计证据 / 先给专家先验判断”。
- 用户只提供申诉文本、客服记录、人工备注、模糊现象，且没有明确 `userId / deviceId / workId / IP / token_id / 时间窗口 / 平台名 / 日志对象`。
- 文本中存在明显矛盾，但当前缺少可直接查询条件：
  - 登录设备只有本人，但账号发生非本人发布。
  - 用户称没操作，但存在交易、发布、登录、关注、点赞等行为。
  - 策略命中较强，但用户申诉材料看似正常。
  - 设备无异常，但行为链路异常。
  - 登录无异常，但内容、交易、互动异常。
- 当前问题核心是解释“为什么会这样”、梳理候选路径、设计强区分证据，而不是事实验证。

不触发条件：

- 用户明确要求查平台 / 调用某个手脚 / 看日志结果：进入 Plan 或 read-only execution，不进入 expert_reasoning_first。
- 用户提供 `userId / deviceId / workId / IP / token_id / 时间窗口 / 平台名 / 日志类型 / 查询对象`，并要求“研判下 / 看下 / 查下”：进入 Plan 或 read-only execution。
- 用户已经提供结构化 observation：进入证据归纳 / conclusion boundary，不重新做纯先验。
- 用户要写工程文档、改代码、生成 release 包。
- 用户只是问概念解释。
- 用户要求执行处置、封禁、解封、批量扩散查询。

路由判断顺序：

1. 用户是否明确要求“先不查数 / 先给专家判断 / 先解释现象 / 先给候选路径 / 先设计证据”？
   - 是：进入 `expert_reasoning_first`。
   - 否：继续。
2. 用户是否包含明确实体或事实验证条件，例如 `userId / deviceId / workId / IP / token_id / 时间窗口 / 平台名 / 日志类型 / 查询对象`？
   - 是：进入 Plan 模式或 read-only execution。
   - 否：继续。
3. 用户是否明确要求查日志、查平台、调手脚、看真实数据？
   - 是：进入 Plan 模式或 read-only execution。
   - 否：继续。
4. 用户是否已经提供 observation、日志结果、平台返回？
   - 是：进入 evidence_synthesis / conclusion_generation。
   - 否：继续。
5. 用户是否只有申诉文本、客服记录、人工备注、模糊现象，且缺少可直接查询条件？
   - 是：进入 `expert_reasoning_first`。
   - 否：按普通问答或其他场景处理。

输出要求：

- 只输出专家先验判断和证据规划。
- 不查数、不调内部平台、不读取真实用户数据。
- 必须区分已知事实、高概率推断、待验证假设、反证可能。
- 默认输出“强区分证据卡”，说明每条证据能区分哪些候选路径。
- 下游可衔接 Plan 模式或只读执行模式，但本模式本身不执行。
- 如果进入 Plan 模式，Plan 开头可以有一句简短专家假设，例如“从文本看，可先假设为 token/OAuth 凭证滥用或新设备盗号两类路径”，但主体必须是只读查询计划，不展开完整专家认知模板。

边界：

- 不输出“已确认”“确定就是”。
- 不能把“设备列表无异常”当作排除盗号或 token 复用的充分条件。
- 不能把“API 直调”直接等同协议破解；可能只是合法 token 被复用。

## 0. v2.6 full 半开放自测后的能力状态

主集成入口：

- `outputs/release/dennis_risk_agent_v2_6_full_experience_first_release/`

半开放真实执行范围：

1. 登录失败 / 被验证原因解释。
2. 策略命中解释。
3. ATO 用户研判。
4. 用户关联设备查询。
5. 设备关联用户查询。
6. 设备风险补证。

已校准能力状态：

- `unified_login_log_check`: pass；通过 `sso_session.py + GET /rest/unified/log/search` API direct read 稳定读取。
- `tianshi_strategy_hit_check`: pass；通过 `sso_session.py + GET /v2/rest/event/fastQueryHbase` 稳定读取。
- `archives_center_profile_check`: pass but browser-session-dependent；档案中心底层有 API，但真实执行依赖 SSO + 档案中心独立登录 / browser session。API direct read 若返回 302，应走 agent-browser recoverable_preflight，再在已登录 browser session 内 same-origin fetch 或 DOM read。
- `weapon_graphData_user_to_device`: API pass but test user no_data；`no_data` 代表当前 Weapon 图谱无结果 / 覆盖差异，不是 `permission_blocked`，也不能说用户没有设备。
- `weapon_graphData_device_to_user`: pass；`/apiv2/graphData` 可对移动端 did 返回关联用户候选。
- `weapon_riskData`: pass；`/apiv2/riskData` 可对移动端 did 返回设备侧标签。
- `tianshi_eventList_POST`: partial / TODO；fastQueryHbase 可解释策略命中，具体请求级详情仍需封装 eventList POST。
- `frontend_activity_profile`: not open for real execution；当前只作为 design / TODO，不纳入半开放真实执行能力。

认证态与路径 guardrail：

- `workspace/.ks_sso/sso-state.json` 是主要 SSO state 来源；覆盖 rcp / xz / weapon / track-analysis / rap / user-center-workbench 等域名。
- 不要因为缺少某个平台独立 `*_state.json` 就判断 state 丢失；`archives_auth_state.json`、`weapon_platform_auth_state.json` 可能只是子集备份。
- Weapon 核心只读 API 走 `/apiv2/*`。
- `/anti-device/*` 是前端 UI 路径，可能被 AMC 权限中台拦截；该情况只能标记为 `UI path blocked / path_error`，不能解释为 Weapon API 全站 `permission_blocked`。

仍禁止：

- 批量查询。
- 自动处置。
- 默认 DataAgent / Hive。
- 前端活跃画像强依赖场景。
- 单一证据直接定性作弊 / 盗号。
- 把 `auth_blocked / permission_blocked / api_failed / no_data` 混为一类。

## 1. ATO 用户研判

用户体感目标：

- 用户问“是不是被盗号”，希望拿到证据化判断、反证和下一步，而不是平台字段列表。

Expected capabilities：

- unified_login_log_check
- archives_center_profile_check
- device_sdk_check_if_device_id_available
- tianshi_strategy_hit_check_if_strategy_hit_question_relevant

执行提示：

- 先读取或要求明确 `suspicious_event_time` 与 `query_time`。
- 统一登录日志在线 API 按约 7 天可靠窗口处理。
- 当 `suspicious_event_time` 超过在线登录日志可靠窗口时，统一登录日志只能作为 partial evidence；必须标记 `login_log_window_incomplete`、`offline_hive_required`、`online_login_log_may_be_false_negative`。
- 超窗时，不允许把在线 API `no_data` / 无 LOGIN 事件写成“异常当天零登录记录”“无异设备登录”或 ATO 强反证。
- 默认不直接调用 DataAgent / Hive；如果当前流程未允许离线查询，只提出“转 DataAgent/Hive 或人工离线日志补查”建议。
- 发布类异常必须建议 `publish_audit_log` 作为关键补证。
- 档案中心可用但认证链路较重，Plan 中应标注 `auth/session risk`。
- 档案中心 API direct read 若 302，应走 agent-browser recoverable_preflight；失败时返回 `auth_blocked / permission_blocked`，不是 `no_data`。

不应调用：

- 不默认 DataAgent / Hive。
- 不默认批量拉全量。
- 不自动处罚。
- 不用在线登录日志超窗 no_data 反向排除 ATO。

输出体验：

- 一句话判断 + 支持证据 + 反证 / 降级因素 + 缺口 + 下一步。
- 如果异常时间超窗，结论最多为 `partial_support` 或 `insufficient_support`，直到补齐离线 Hive 登录日志、发布审计或 token 使用链路。

## 2. 登录失败 / 被验证原因

用户体感目标：

- 用户希望知道“为什么失败 / 为什么验证”，需要直接原因和时间线。

Expected capabilities：

- unified_login_log_check
- tianshi_strategy_hit_check
- tianshi_eventlist_api_read_if_specific_request_detail_needed
- archives_center_profile_check_as_context

执行提示：

- 统一登录日志优先 API direct read。
- 天狮策略命中优先 fastQueryHbase。
- 若追问具体请求级字段且 eventList POST 未封装，返回 `partial` 并说明 TODO。

不应调用：

- 不优先 Device SDK，除非问题指向设备环境。
- 不默认 frontend activity。
- 不把 riskDecision 当最终执行结果。

输出体验：

- 直接原因 + 证据链 + 它说明什么 + 它不说明什么 + 下一步。

## 3. 设备风险补证

用户体感目标：

- 用户问设备是否 root/hook/frida/群控，希望得到设备侧证据，而不是账号综合定性。

输入完整性规则：

- Device SDK 的前置输入是 `deviceId / did / deviceceid`。
- 如果用户明确给出 deviceId，直接进入 Device SDK API-direct readonly。
- 如果用户输入的是 userId，但问题问设备风险，先走 `user_to_device` entity resolution，再选择候选 deviceId 进入 Device SDK。
- 如果缺少 deviceId 且无法解析，返回 `missing_device_id`，不允许直接进入 Device SDK。

Expected capabilities：

- device_sdk_api_direct_readonly
- device_sdk_graph_or_relation_if_question_asks_associated_users

执行提示：

- Device SDK riskData 走 Weapon `/apiv2/riskData?product=KUAISHOU&deviceIds={deviceId}`。
- 移动端 did，例如 `ANDROID_xxx`，更适合 Device SDK riskData 查询。
- `web_` 前缀设备可能不在移动端 did 体系内，不适合作为 Device SDK 主测对象。

不应调用：

- 不默认统一登录日志。
- 不默认档案中心。
- 不调用 location。

输出体验：

- 设备侧结论 + 强/中/弱设备证据 + 边界 + 下一步。
- 如果输入不完整，先说明缺少 deviceId 或正在做 user_to_device，不要假装已经完成设备补证。
- Hook / root / frida / simulator / proxy / repack 等标签只是设备侧补证；即使 Hook level=50 这类高严重度标签出现，也不能单独定性用户作弊或盗号。

## 4. 用户关联设备查询

用户体感目标：

- 用户输入 userId，想知道有哪些关联设备，或者后续要查设备风险。

Expected capabilities：

- user_to_device_entity_resolution
- weapon_graphData
- archives_user_analysis_recent_devices_as_supplemental_ranking

执行提示：

- Weapon user_to_device 使用 `/apiv2/graphData?product=KUAISHOU&productName=KUAISHOU&groupValue={userId}&groupKey=USER_ID&dimKey=DEVICE_ID&searchLevel=2`。
- 半开放自测中，Weapon API 可达；测试 userId 返回 `no_data`，应表述为“该数据源暂无关联 / 当前图谱无结果”，不是 `permission_blocked`，也不是“用户没有设备”。
- 若 Weapon 图谱 no_data，可降级使用统一登录日志设备分布 + 档案中心最近登录设备作为候选来源。

不应调用：

- 不直接拿 userId 调 Device SDK riskData。
- 不默认批量深查所有设备。

输出体验：

- 候选设备摘要 + 排序理由 + 关系边界 + 下一步选择哪个设备补证。

## 5. 设备关联用户查询

用户体感目标：

- 用户输入 deviceId，想知道谁在用、关联多少账号、是否有关联封禁账号。

Expected capabilities：

- device_to_user_entity_resolution
- weapon_graphData

执行提示：

- Weapon device_to_user 使用 `/apiv2/graphData?product=KUAISHOU&productName=KUAISHOU&groupValue={deviceId}&groupKey=DEVICE_ID&dimKey=USER_ID&searchLevel=2`。
- 半开放自测中，`deviceId=ANDROID_c1ab0d1eb0a0d1c0` 返回 `code=0`、3 nodes、2 edges、关联用户 2 个。
- 返回用户只能表达为候选关联用户；关联用户中存在社交封禁 / 风险标签是继续深查线索，不是最终风险结论。

不应调用：

- 不直接定性团伙作弊。
- 不默认拉所有关联用户详情。

输出体验：

- 关联用户摘要 + graph_summary + 边界 + 下一步补证。

## 6. 策略命中解释

用户体感目标：

- 用户想知道策略命中“到底说明什么”，需要理解证据价值和边界。

Expected capabilities：

- tianshi_strategy_hit_check
- tianshi_eventlist_api_read_if_specific_request_detail_needed
- unified_login_log_check_if_login_or_verify_chain_needed
- archives_center_profile_check_if_account_context_needed

执行提示：

- 当前 fastQueryHbase 可用，用于策略命中解释。
- eventList POST 仍为 `partial / TODO`；用户追问具体请求级详情时，应说明该能力缺位，不能伪造明细。

不应调用：

- 不把命中写成最终作弊。
- 不把无命中写成无风险。
- 不默认 DataAgent / Hive。

输出体验：

- 策略命中解释 + riskDecision 边界 + 能说明什么 / 不能说明什么 + 最小补证动作。
