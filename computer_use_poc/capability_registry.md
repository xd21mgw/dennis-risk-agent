# Capability Registry

本文记录 Dennis Risk Agent 在 `computer_use_poc` 阶段沉淀的能力类型。能力不等于平台手脚；部分能力只属于大脑认知层。

## Current Formal Capability Index

以下按 capability 而不是平台列出当前正式能力。平台只是适配器或数据来源，主 Agent 应先识别业务场景和证据需求，再选择 capability。

诊断类能力：

| capability | purpose | mode | status | key_boundary |
|---|---|---|---|---|
| `plan_only_diagnostic` | 对 plan-only 输出做 Codex 评分，区分 intent/routing、source plan、orchestration、evidence reasoning、output contract | diagnostic / no platform call | documented | 只能证明脑子 / 路由 / 编排设计是否合理，不能证明 runtime config、auth、safeBins 或 source wrapper 可用；默认输出自然语言执行状态摘要，完整 `routing_metadata` 仅在 debug / run log / regression 或用户明确要求时展示 |
| `failure_triage_card` | 对失败 case 做分层归因：config/runtime、intent/routing、source_orchestration、evidence_reasoning、output_contract、no_issue | post-failure diagnostic | documented | 不调用平台，不调用 DataAgent；用于决定 fix owner 和 regression |

通用风险研判能力：

| capability | purpose | mode | status | key_boundary |
|---|---|---|---|---|
| `universal_risk_evidence_workflow` | 所有风险研判共用的工作模式：实时 readonly source 优先，实时能闭合就给 evidence-based 结论，不能闭合则输出 partial evidence / missing evidence / 分场景离线补证计划，批量问题再进入共性分簇 | orchestration contract | documented | 不是新平台手脚，不自动调用 DataAgent/Hive，不把离线计划伪装成已执行；每个 source 必须有 source_quality 和时间窗口边界 |

全局输出字段分层：

- 所有 capability 的输出必须遵守 `computer_use_poc/field_output_classification_policy_v1.md`。
- token / cookie / session / password / authorization / storageState / header 等认证凭证明文永远不得明文输出。
- IP / UID / DID / deviceId / requestId / sourceId / strategyId / adminaction 等是风控实体字段；内部可信分析可作为 evidence card、pattern summary、case table 的分析实体，KIM 半开放和跨团队分享需按受众范围选择原值、safe_ref、partial mask、count 或 distribution。
- `tokenId` 若只是事件标识符，不等于 token secret；默认 `token_id_ref` 或 partial mask。
- `no_sensitive_plaintext` 不能一刀切覆盖所有风控实体字段；KIM E2E / runtime validation 必须按字段分层判定。

| capability | purpose | primary adapters / sources | default_scope | status | key_boundary |
|---|---|---|---|---|---|
| `user_profile_read` | 读取用户基础画像、账号状态、历史风险、档案补证 | 档案中心 home/profile/risk/label/punish APIs 或 browser fallback | single_user readonly summary | formal_readonly | 不做自动风险定性，不输出敏感明文 |
| `archives_profile_readonly` | 档案中心用户分析 P0 只读 source，读取用户画像、账号状态、封禁 / 降权、注册设备、登录设备摘要 | browser-backed `archives_user_profile` / `archives_user_analysis` via `runtime_case_execution_runner.py` controlled batch；`bin/archives_profile_runner` is manual diagnostic only | single_user account baseline | browser_backed_passthrough_source | 支持 `user_id`；只读；不输出 cookie/token/session/header；不做 auth repair；`body_missing` / auth gap / source gap 进入 Dennis-generated source_quality；不得 fallback legacy runner；无 publish_device_id 时不能判断发作品设备异常 |
| `login_log_read` | 读取登录、验证、token 生命周期、登录失败原因 | 用户登录统一日志 API / UI fallback | single_user_or_did reliable window | formal_readonly | 必须先做 `reliable_window_precheck`；`recallSource=2,0,1,3` 必须出现在 online URL；over-window no_data 是 data_gap，不是 counter_evidence |
| `frontend_activity_read` | 读取前端活跃画像和使用时长信号 | 埋点分析“用户属性及时长”区域 | single_user_or_device profile summary | validated_but_not_default_real_execution | 只能说明前端活跃信号，不证明真人/本人/具体动作 |
| `track_analysis_activity_profile_api_direct` | 读取 user_id / device_id 的近 30 天活跃、画像、设备关联和事件日活跃对齐信号 | track-analysis `getLastestDateTime` / `getDeviceIds` / `getUseDuration` / `profile` | platform_source; single user/device realtime readonly | api_direct_confirmed; cost=low; execution_mode=realtime_readonly_api | 输入支持 `user_id` / `device_id` / `appName=KUAISHOU|NEBULA`；不需要用户确认，不需要 DataAgent；输出 profile_card / device_ids / latest_datetime / uid_did_relation_latest_datetime / daily_duration_rows / total_duration / peak_duration / first_active_date / register_time / fan_distribution / active_days_bucket；活跃信号不能单独定性 |
| `user_device_resolution` | 做 user ↔ device 双向实体转译，并在 ATO 中作为 Dennis-side `user_device_entity_resolution` 桥接层 | login_logs_search、archives_user_analysis、archives_photo_search、Weapon graphData、Track readiness | single_entity candidates | formal_readonly / Dennis-generated entity layer | 关联关系是候选实体关系，不是风险结论；缺 candidate device 进入 missing_evidence，不让 batch 失败 |
| `device_risk_read` | 读取设备环境风险、hook/root/frida/模拟器/多开等设备侧补证 | Device SDK / Weapon riskData | single_device readonly summary | formal_readonly | 设备异常不能单独定性用户作弊或盗号 |
| `strategy_hit_read` | 判断 source/request 在窗口内是否命中生产风控策略；作为 strategy_hit_inventory 首选批量入口 | 天狮 fastQueryHbase HTTP+SSO | single_source bounded window | formal_readonly | `eventTypeCodes=""` 表示全事件类型；策略命中是证据，不等于最终作弊定性 |
| `tianshi_eventlist_read` | 对具体 eventType / 小时间窗口做请求级细查 | 天狮 eventList API-read / browser same-origin | specific_event small window | partial_design_and_poc | eventList 是补查入口，不是 strategy_hit_inventory 首选命中概览入口；no_data 不代表行为未发生 |
| `tianshi_strategy_platform_contracts` | 固化天狮 fastQueryHbase / eventList 的 contract、schema、routing 和 observation 边界 | `computer_use_poc/tianshi_strategy_platform_contracts/` | contract layer only | documented | C 包不解析策略树；策略配置理解属于未来 D 包 |
| `tianshi_strategy_hit_inventory` | 从 user/source_id 维度盘点策略命中概览、TOP 策略、TOP 节点、TOP 条件、策略共现和代表事件 | fastQueryHbase HTTP+SSO → eventList supplement → representative event attribution | single_source bounded window inventory | documented_ready_for_runtime | 策略命中盘点是风险感知线索，不等于最终风险定性，不自动处置 |
| `tianshi_live_attach_attribution_candidate` | 解释直播长连接 attach / `SYNC_LIVE_ATTACH_REQUEST` 为什么被策略阻止，以及直播人气防刷相关策略路径 | fastQueryHbase → eventList / rcpEventDetail → getPolicyVersionListByEvent → nodePolicyAttribution | live_attach single_source beta partial | runtime_candidate_beta_partial | beta / partial candidate，不是 full success；eventDetail timeout 只能标 `event_detail_partial` |
| `business_security_scene_asset_mapping` | 回答业务安全有哪些场景、eventType / policyTree 候选和后续验证优先级 | `business_security_scene_asset_mapping_poc_v1.md` | asset index / query plan only | asset_index_only_query_plan_only | 资产地图不是可执行研判能力，不触发平台查询，不输出风险定性 |
| `tianshi_anticrawl_family_candidate` | 解释 ANTICRAWL 家族候选 eventType 和反爬查询计划 | asset map + future hit sample required | candidate query plan only | candidate_only_query_plan_only | 不注册为可执行 runtime；缺真实命中 source_id / eventId 时只输出 query plan |
| `real_name_feature_service_partial_contract` | 记录 EB_USER_REAL_NAME_VERILY__1 testCase bridge 调用方式、参数映射、字段可用性和脱敏输出边界 | `real_name_feature_service_partial_contract_v1.md` | partial contract / redaction schema / query plan | partial_contract_redaction_schema_only_query_plan_only | 不是完整实名画像能力，不是本人 / 盗号判断，不注册可执行 identity runtime |
| `tianshi_strategy_governance_readonly` | 解释策略是什么、挂在哪、为什么命中、何时上线/终止 | `computer_use_poc/strategy_governance/` readonly governance docs | strategy governance readonly plan / observation | documented_ready_for_runtime | 不做最终作弊定性，不自动处置，不写操作、不上线、不审批 |
| `universal_risk_evidence_workflow` | 把单案和批量风险研判统一到“实时 source 优先 -> 证据链闭合检查 -> partial/missing evidence -> 分场景离线补证计划 -> 必要时分簇扩展”的 Dennis 大脑工作模式 | `source_orchestration_plan_v1.yaml`、`multi_entry_runtime_guard_v1.md`、runtime summaries、answer templates | orchestration contract | documented | 不新增平台 action，不默认查 Hive/DataAgent，不把 ATO/Hive 登录表口径泛化成唯一补证路径；source_quality 边界适用于所有风险场景 |
| `multi_evidence_orchestration_contracts` | 综合风险研判时编排天狮、登录日志、档案中心等多源证据，输出 evidence summary | `computer_use_poc/multi_evidence_orchestration_contracts/` | planner / template only | documented | 不新增真实查询，不因单源强证据给 definitive conclusion |
| `batch_analysis_framework` | 抽象不同 batch 场景共用流程：registry、evidence card、pattern summary、missing evidence、strategy draft | `eval/dennis_risk_agent_skills_v2_2_tested/batch_analysis_framework_v1.md` | framework only | documented | 不是执行能力，不调用 DataAgent / 平台，不自动上线策略 |
| `batch_risk_clustering_analysis` | 对一批 user/device/event/interface/channel/alert case 做分簇、异常相关性矩阵、代表样本抽样、证据缺口和策略建议 | `computer_use_poc/batch_risk_clustering/` templates | batch_plan_mode | documented | 不默认逐个在线查大批量实体，不自动调用 DataAgent，不基于相似性直接判断同团伙 |
| `batch_ato_cluster_lens` | 在已有 batch clustering 之上叠加 compromised-account / ATO 盗号投放 lens，识别 WEB 非可信登录、login_to_action_delta、设备身份漂移、代表样本单案深挖和簇级回填 | `computer_use_poc/batch_risk_clustering/batch_ato_cluster_lens_v1.md` | batch_clustering_mode overlay | documented | 不是从零分簇，不逐用户 for-loop，不把代表样本无脑泛化到全批；实时登录 / 控制链不完整时只生成账号安全 Hive registry-first 补证计划，不调用 DataAgent/Hive |
| `batch_case_analysis` | 对 5-20 个 ATO case 做半自动归因、证据卡聚合、模式总结、缺口识别和候选策略方向 | `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/` templates | 5-20 cases offline template analysis | mvp_template_ready | 不调用真实 DataAgent，不自动上线策略，不自动处置 |
| `ato_case_expansion_planning` | 对单个或少量 ATO case 设计举一返三扩展路径和 Hive 取数问题 | `ato_case_expansion_plan_v1.md` | plan only | documented | 围绕账号控制权异常和攻击链路扩展，不按昵称/简介扩展，不执行真实查询 |
| `black_market_account_matrix_batch_analysis` | 对黑产账号矩阵 / 导流互动 / 互粉互动 / 养号账号池做批量归因和候选策略方向 | `eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/` templates | small batch offline template analysis | mvp_template_ready | 不是 ATO，不调用真实 DataAgent，不自动上线策略 |
| `batch_case_analysis_planned` | 多 case 批量研判的规划能力 | 后续 batch case registry / DataAgent only when scene allows | planned only | planned | 不默认批量扩散，不绕过审批，不替代单案证据闭环 |
| `learning_candidate_capture` | 收集用户真实问题、识别能力缺口、生成候选队列和 case learning note | `computer_use_poc/question_collection/` schemas / templates | post-answer accounting only | documented | 不是风险研判手脚，不访问平台，不调用 DataAgent，不自动改 Skill / release |

正式能力与平台适配器关系：

- Source priority and access method must be expressed separately:
  - `source_priority: P0 | P0-explicit | P0-conditional | P1 | P2 | conditional`
  - `access_method: api_direct | controlled_runner | browser_cookie_activation | same_origin_fetch | manual_gap | hive_authorized`
  - 证据价值决定 source priority，执行方式决定 access method。API direct first 是采集路径优先，不是 P0/P1/P2 的唯一判定标准。
- `user_profile_read` / 档案中心用户分析在 ATO、account_security、abnormal publish、user state analysis 中是 P0 account-baseline source。即使需要 `browser_cookie_activation` / `same_origin_fetch`，也不得因非纯 API direct 自动降为 P1/P2。
- `archives_profile_readonly` 是档案中心用户分析的 P0 手脚别名，用于恢复 ATO / 发作品 / 处罚链路 case 的账号侧底座证据。case execution 以 `runtime_case_execution_runner.py` controlled batch 为入口；`bin/archives_profile_runner` 仅 manual diagnostic，不得在 browser-backed gap 后作为 fallback。执行时 `body_missing` / source gap / auth gap 必须显式进入 Dennis-generated source_quality。
- 发布作品 / 发布设备 / 发布来源链路是 ATO 默认 P0 内容承接 capability：裸问被盗也要通过 `archives_photo_search` 检查近期作品/发布承接；`photo_search no_data` 不排除异常发布或 ATO。发布设备可作为后续 `device_risk_read` 和 `device_identity_consistency` 的 raw_reference_safe_id 来源。
- `device_risk_read` / Weapon riskData 是 conditional device-level follow-up，输入依赖 `deviceId`，可来自 graphData、login_log、publish_chain、track_analysis 或其他 current-task source 的 raw_reference_safe_id。没有 deviceId 时必须标 `missing_device_reference`，不得假装 riskData 已覆盖。
- `strategy_hit_read` 在用户明确问“策略命中 / 有没有命中策略 / 策略命中能否辅助判断”时是 `P0-explicit` target source；策略命中只能作为辅助风险信号，不是 final judgement。
- Browser / cookie activation 是 access method，不是 source priority。main agent 不得以 browser / curl / cookie fallback 形式 direct exec 接管平台查询。
- P0 source capability 的 wrapper-first 是 runtime 约束，不只是文档建议。`login_log_read`、`strategy_hit_read`、`user_device_resolution` / Weapon read 等 P0 source 需要 dedicated dennis runtime config、`safeBins`、source wrapper 和 `tools.deny` 同时生效。
- 如果 live `openclaw.json` 没有独立 `dennis-risk-agent` entry，或 dennis 继承 full-profile defaults，必须标 `runtime_config_not_applied`，不得宣称 wrapper-first 已 runtime 生效。
- Browser fallback 必须显式记录 `access_method=browser_same_origin_fetch` 或 `browser_ui_observation`；不得把 browser fallback 成功包装成 wrapper-first 成功。
- `user_profile_read` 可由档案中心 API-first 或 browser fallback 实现。
- `login_log_read` 优先 API direct read，UI hand 作为 fallback / 字段发现。
- `login_log_read` 的 online URL 必须保留 `recallSource=2,0,1,3`；缺失可能导致 `code=10045`，这属于 wrapper URL 映射缺口，不应误判为登录行为不存在。
- `user_device_resolution` 以 Weapon graphData 为主入口，不使用 Device SDK riskData 做实体解析主入口。
- `device_risk_read` 在拿到 deviceId / did / deviceceid 后做设备侧风险补证。
- `strategy_hit_read` 用于策略命中概览，也是 `strategy_hit_inventory` 的首选批量入口；`tianshi_eventlist_read` 用于 eventType 级具体请求补证，尤其是允许 / `ec=1` 事件补查。
- `tianshi_strategy_hit_inventory` 是天狮策略命中盘点能力，子能力包括：
  - `strategy_hit_overview_lookup`：首选 fastQueryHbase，输入 `source_id + time_window`，输出 `eventId` / `eventType` / `riskDecision` / `hitPolicies` / `hitProductionPolicies` / `confidenceLevel` / `riskType`。
  - `event_type_detail_supplement`：使用 eventList，对允许事件、`ec=1` 事件和请求级字段做 eventType 级补查；eventList 需要 browser same-origin。
  - `representative_event_attribution`：使用 `rcpEventDetail` + `nodePolicyAttribution` + `nodeBindPolicyAttribution` 对代表 event 深挖，不默认对所有事件全量归因。
  - 盘点输出可包含 `policy_topn`、`node_topn`、`condition_topn`、`policy_cooccurrence` 和 `representative_events`；这些都是风险感知线索，不是用户级风险定性。
- `tianshi_live_attach_attribution_candidate` 是 `SYNC_LIVE_ATTACH_REQUEST` / 直播长连接 attach 的非注册 / 登录 runtime candidate beta，子能力包括：
  - `attach_hit_overview_lookup`：首选 fastQueryHbase，输入 `source_id + time_window`，输出 attach 相关 eventId / riskDecision / hitPolicies / confidenceLevel / riskType。
  - `attach_event_detail_supplement`：使用 eventList / rcpEventDetail；rcpEventDetail 对阻止事件可能 timeout，必须标 `event_detail_partial`，不得当 no_data。
  - `attach_policy_attribution`：使用 getPolicyVersionListByEvent + nodePolicyAttribution，支持代表事件条件级归因；已验证 `BS_antibrush_attach_user_multi_loc_block_policy` 和 `BS_antibrush_attach_not_same_startup_block_policy`。
- `business_security_scene_asset_mapping` 只做资产地图 / query plan，覆盖 account_security、traffic_security、anti_crawler_antibrush、interaction_anti_abuse、activity_anti_cheating；找到 eventType / policyTree 不代表已可归因或正在命中。
- `tianshi_anticrawl_family_candidate` 只做 candidate_only / query_plan_only；已知候选包括 `ANTICRAWL`、`ANTICRAWL_LIVE`、`ANTICRAWL_BASE`、`ANTICRAWL_SEARCH`、`ANTICRAWL_COMMON`、`ANTICRAWL_RPC_SIGN`、`ANTICRAWL_PLATFORM_SYNC`、`LIVE_STREAM_ANTICRAWL`；没有命中样本时不得假装可完整归因。
- `real_name_feature_service_partial_contract` 只做 EB_USER_REAL_NAME_VERILY__1 的 partial contract / redaction schema / query plan，不注册可执行 identity runtime：
  - 关键调用参数：`access_path=/v2/rest/testCase/run`，`foreignKey=EB_USER_REAL_NAME_VERILY__1`，`sourceId=userId`，`activityName=call_condition`，`required_activityName=MERCHANT_NEWSHOP_OPEN_AWARD`，`sid=kuaishou.api` 由 feature config 自动填充。
  - 当前可用信息：`idNo` 存在性、idNo 派生省份摘要、城市级可用性、年龄段、性别摘要、敏感字段 redacted 标记。
  - 禁止输出：姓名、身份证号、身份证前 6 位、完整生日、手机号、完整 IP、详细地址。
  - 已实名不等于一定本人操作，未实名不等于一定黑产；实名省份与发布 IP 一致不能单独排除盗号，不一致也不能单独判定盗号。
- `tianshi_strategy_platform_contracts` 是 `strategy_hit_read` 和 `tianshi_eventlist_read` 的契约索引；它定义 source_id 非空、小窗口、eventList 不跨天、sampling / no_data / auth blocker 边界，以及未来 D 包策略树边界。
- `tianshi_strategy_governance_readonly` 是天狮策略治理只读能力，子能力包括：
  - `policy_detail_lookup`：解释策略定义、条件表达式、版本历史、绑定树。
  - `policy_tree_asset_lookup`：解释策略树结构、节点路径、节点绑定策略、全树策略 code。
  - `single_event_policy_attribution`：解释某次事件为什么命中 / 生效，包括事件详情、特征快照、条件级归因、节点级归因。
  - `policy_release_record_lookup`：解释策略发布流程、实验 / 审批 / 灰度 / 上线 / 终止和版本变更追溯。
  - 它不同于 `strategy_hit_read`：后者只回答是否命中策略；策略治理能力回答策略定义、策略树资产、事件归因和发布记录。
  - 用户风险研判只把天狮作为 `strategy_hit_evidence` 候选；只有具备 `eventId` + `eventType` + `queryTime` + `policyCode`，或可从事件详情解析出 `policyCode` 时，才进入 `single_event_policy_attribution`。
- `multi_evidence_orchestration_contracts` 是完整风险研判问题的 planner 层：默认三源为 `tianshi_strategy_hit_check`、`unified_login_log_check`、`archives_center_profile_check`；只有请求级字段问题才触发 `tianshi_eventlist_api_read`。
- `browser_backed_fixed_actions_v1` 是 `multi_evidence_orchestration_contracts` 的已登记 browser-backed source action 层，不是新默认路由。它覆盖：
  - ATO / 登录异常：`login_logs_search`、`archives_user_profile`、`archives_user_analysis`、`archives_photo_search`、`track_analysis_check_data_ready`。可疑锚点由这些实时 P0 source 共同定位，不是独立前置 action。
  - 异常发布 / 色导 / 内容承接：`archives_photo_search`、`archives_user_profile`、`archives_user_analysis`。
  - 账号扩散 / 同设备：`archives_related_users`，并按需交叉 `archives_user_profile` / `login_logs_search` / `track_analysis_check_data_ready`。
  - RCP 事件归因：`rcp_event_detail -> rcp_event_feature_list`。
  - 策略资产治理 / 策略树解释：`rcp_policy_tree_lookup`。
  - 注册状态：Node service allowlist、Dennis Python client endpoint、README / ONLINE_SOURCE_SUMMARY / inventory 已对齐。
  - source 状态：`login_logs_search`、`track_analysis_check_data_ready`、`archives_user_profile`、`archives_user_analysis`、`archives_related_users`、`rcp_event_detail`、`rcp_policy_tree_lookup` 为 `live_smoke_verified`；`archives_photo_search` 为 live path `no_data`；`rcp_event_feature_list` 为 `partial_observation_available`。
  - 边界：所有 action 均 `default_runtime_routing=false`，必须由显式 source plan 选择；`no_data` 不是无风险反证，`partial_observation_available` 是可用部分观察，`large_response_limited` 进 source_quality，Archives 302 归为 `auth_flow_not_completed_in_bound_context`。
  - 档案中心编排：ATO / 登录异常必须把 `archives_user_profile` + `archives_user_analysis` + `archives_photo_search` 纳入 source plan，用来补账号状态、改密 / 保护账号、发布、关注、资料变更和作品 / 发布承接闭环；`archives_photo_search no_data` 不能排除 ATO / 异常发布 / 导流。黑产扩散 / 同设备计划 `archives_related_users` + profile，并交叉登录日志和 Track 活跃与数据可用性。
  - 档案中心是关键证据项但非硬阻塞项：`auth_failed`、`no_data`、`partial_observation_available`、`timeout`、`blocked`、`parse_error` 必须进入 `source_quality` / `missing_evidence` / partial evidence，不能中断回答，也不能作为低风险或无风险反证。
  - 扩散边界：`archives_related_users` / 同设备关系只说明候选扩散链路，不能直接定性团伙；必须再看行为、策略、设备和时间线一致性。
  - 策略命中 / 策略树 / 事件详情 / feature list 不能混用：策略命中只是辅助线索，`rcp_policy_tree_lookup` 只解释策略资产，不证明单案命中路径。
  - controlled parallel 编排：Dennis source plan 可显式下发 `/actions/batch` / `/actions/multi_source_plan` 所需的 `execution_group`、`depends_on`、`timeout_class`、`failure_policy`、`source_priority` 和 `expected_observation`。支持组为 `independent_parallel`、`dependency_serial`、`large_response_serial`、`auth_sensitive_serial`；这只是显式编排能力，不改变任一 action 的 `default_runtime_routing=false`。
  - controlled parallel 典型场景：ATO 中 `login_logs_search`、`archives_user_profile`、`track_analysis_check_data_ready` 可 `independent_parallel`，`archives_photo_search` 和 `archives_user_analysis` 后续 `auth_sensitive_serial`；RCP `rcp_event_detail -> rcp_event_feature_list` 是 `dependency_serial`；`archives_user_analysis` / `rcp_event_feature_list` 大响应进入 `large_response_serial`；Archives 同源链路进入 `auth_sensitive_serial`。
  - pure passthrough 边界：browser-backed service 只输出 passthrough envelope、transport metadata、capped body 和 batch transport status；Dennis 负责生成 observation、`source_quality_matrix`、evidence card、`missing_evidence` 和 `final_answer_boundary`。不得依赖 service-side `normalized_observation`、`source_card`、`source_quality`、`evidence_card_inputs` 或 `compat_summary`。
  - Dennis-side ATO 解释层：`user_device_entity_resolution` 从登录、档案用户分析、作品搜索、Weapon 和 Track 中提取候选设备；evidence card 按控制权入口、账号状态与后置行为、内容/发布承接、前后端活跃、设备/IP/扩散、策略/风控信号、反证与缺口组织；实时不闭合时输出 1-5 离线补证授权模块，不默认请求全量 DataAgent/Hive。
  - controlled parallel 合并边界：service 的 `transport_status_matrix` / `source_results` 由 Dennis 合并；`completed` / `no_data` / `partial` / `auth_failed` / `blocked` / `timeout` / `parse_error` 分类进入 Dennis `source_quality_matrix`；completed 或 partial passthrough observation 进入 Dennis evidence card，失败或依赖缺口进入 `missing_evidence`。单 source 失败不阻塞其他 source，且 no_data / partial / timeout 不得当低风险反证。
  - ATO single-case realtime P0：`browser_backed_fixed_actions_v1` 在 ATO 裸问中必须先收集登录 / 档案画像 / 档案用户分析 / 作品发布 / Track readiness 五类实时 P0 source，再由 Dennis 从多源观察中推导可疑锚点、候选控制端、`device_identity_consistency` 和历史基线。不能把 `suspicious_anchor_discovery` 当独立 source，也不能把 Track / RCP / Weapon / 登录日志 / 档案中心平铺 source 状态当成 ATO 研判主线。
  - ATO suspicious source priority：登录链路和内容 / 行为链路是可疑来源发现主入口；Track / Weapon / RCP 是补证 source。在线统一登录日志不可用、窗口不足、admin 侧仅 APP 日志、WEB/H5/PC/token/OAuth/扫码链路缺失、`response_too_large` 或 UI/wrapper 不一致时，只能生成基于 `account_security_hive_source_registry_v1.md` 的 Hive query plan，等待用户逐次授权，不得让 DataAgent 自由猜表。
  - `device_identity_consistency` 是 ATO 设备判断能力：比较 `device_id`、首次出现、30/90/180 天出现天数、机型、系统、app 版本、UA、browser fingerprint、IP/省市/ASN、登录端和登录方式。风险标签包括 `device_identity_inconsistency`、`possible_device_id_spoofing`、`common_device_id_but_abnormal_fingerprint`、`common_device_id_not_sufficient_to_exclude_ato`。
  - Track 表述：当前 v1 裸问优先写 `track_analysis_check_data_ready / Track 活跃与数据可用性`；历史 `track_analysis_summary` 只作为 Track 活跃画像泛化能力描述，避免混成当前 action 名。
  - 未稳定 source：private message、资料四件套 / 过往四项、related_devices 等不作为默认已验证 source；只有已有稳定接口、显式 source plan 或用户补充线索时，才写“可进一步查看”。
  - 风控实体字段 `user_id`、`device_id`、`ip`、`event_id`、`strategy_id`、`photo_id`、`policyCode`、`policyTreeCode` 可在内部研判和 source chaining 保留；cookie/token/session/header/password、手机号、身份证、姓名、地址严禁输出或保存。
- `frontend_activity_read` 是早期 stats-first / frontend activity 抽象；当前优先使用 `track_analysis_activity_profile_api_direct` 作为低成本 realtime readonly platform source。
- `track_analysis_activity_profile_api_direct` 支持：
  - actions：`getLastestDateTime`、`getDeviceIds`、`getUseDuration`、`profile`。
  - input：`user_id` / `device_id` / `appName=KUAISHOU|NEBULA`。
  - observation：`profile_card`、`device_ids`、`latest_datetime`、`uid_did_relation_latest_datetime`、`daily_duration_rows`、`total_duration`、`peak_duration`、`first_active_date`、`register_time`、`fan_distribution`、`active_days_bucket`。
  - event-day alignment：登录成功日、扫码日、设备切换日、策略命中日若后端有登录 / 扫码 / 命中但对应 userId/deviceId 前端 duration=0 或无活跃，应标 `front_backend_activity_mismatch`。
  - boundary：`front_backend_activity_mismatch` 是协议上号、token/session 使用、非真实客户端行为的中高价值线索，但不得单独定性；必须与登录链路、设备风险、策略命中、发布 / 行为链路交叉验证。
  - execution boundary：能力合同为 `api_direct_confirmed` 不等于当前 runtime source 已 completed。只有 live wrapper / playbook 中存在已验证可执行 endpoint 时才可标 completed；否则执行输出必须降级为 `pending_api_direct_confirmation` / `source_gap`，不得阻塞账号安全 P0 evidence card。
- ATO / account_security 场景中，如果登录日志、Hive、Weapon 或档案中心发现异常手机端设备、非历史设备、新设备登录、扫码后新设备或设备风险标签，默认触发 `track_analysis_activity_profile_api_direct` 作为低成本补证 source，优先检查登录成功日 / 扫码日 / 设备切换日 / 策略命中日的 `getUseDuration`。
- 单例 case 风险研判输出必须使用 `single_case_evidence_card`，每条 strong / medium / weak / counter evidence 都要带 `evidence_source` / `source_quality`；该口径与 ATO batch evidence source schema 对齐。
- `batch_analysis_framework` 是 batch 方法论抽象，不是新平台手脚，不直接执行 observation。
- `batch_risk_clustering_analysis` 是跨场景批量风险分簇研判包，用于 10+ 标准批量分簇、50+ aggregation / DataAgent-Hive query plan、异常相关性矩阵和代表样本抽样；不表示已开放大批量在线查询。
- `batch_case_analysis` 当前是 ATO 批量 case 半自动归因的文档与模板闭环，服务 5-20 个 case 的 case 标准化、证据卡聚合、模式总结和候选策略方向；不表示已接真实 DataAgent 或自动策略上线。
- `ato_case_expansion_planning` 服务单个或少量 ATO case 的举一返三扩展设计，核心锚点是凭证 / token / OAuth / 登录态异常、改密 / 换绑 / 安全操作、基础设施和后置动作回连，不按相同昵称 / 简介扩展。
- `black_market_account_matrix_batch_analysis` 当前是非 ATO 的账号矩阵 / 导流互动 / 养号池归因样板，不应污染 ATO 的账号控制权异常定义。
- `batch_case_analysis_planned` 保留为更大范围批量研判的未来规划，不表示已开放批量执行。
- `learning_candidate_capture` 只负责用户问题收集、能力缺口识别和学习候选材料生成；Agent 可以自动记账，但不能自动改脑，所有 Skill / Prompt / routing / regression / release 改动都必须经过人工审核和 Codex 后续任务。

## Semi-open Experience Patch v1 Modes

这些 mode 是入口路由和回答体验约束，不一定对应新的平台 capability。

| mode | trigger | default behavior | boundary |
|---|---|---|---|
| `single_entity_execution_mode` | 明确单个 `user_id` / `device_id` / case 查询；“帮我查 / 帮我看 / 看近期登录 / 看设备关联 / 看策略命中” | 在线只读 observation，输出 evidence card 或 partial evidence card；每条证据带 `evidence_type` / `strength`；ATO 单案 source timeout / auth blocked / parse error 时仍输出 completed / blocked / timeout / parse_error / missing evidence、source_quality 和 next_action | 不默认 DataAgent，不空研判；不把 user_claim / behavior_event / inference 写成 raw_evidence；不把 no_data / timeout / blocked 当无风险反证 |
| `single_ato_source_checkpoint` | ATO 单案多 source 编排；已有 source completed 但后续 source 可能 timeout / blocked | 每个 source 结束即记录 checkpoint；P0/P1 completed 后可输出 partial evidence card；P2 browser 不阻塞已完成 evidence | completed source 不得丢失；no_data 标 `no_data_not_risk_exclusion`；默认 180s，总 deadline 前必须输出 |
| `unified_login_auth_bridge_guard` | 统一登录日志认证态桥接、子 agent timeout 后 main agent 行为 | 统一登录日志只读查询走受控 wrapper / dennis source orchestration；main agent 只记录 timeout 并返回 partial / retry plan | 禁止 main agent direct exec curl/cookie/browser 查询；302 / same-origin / profile lock / auth_failed 进入 source_quality |
| `small_batch_execution_with_checkpoint` | 2-9 个 ATO 客诉用户 | 默认允许逐个查 P0 source，优先统一登录日志；异常用户再补 P1 source；每个 user/source 独立 checkpoint | 不是纯 plan-only；不默认 P2 browser；不因单用户 auth 失败导致整体无输出；登录日志窗口和 APP-only source gap 必须显式标注 |
| `evidence_boundary_mode` | no_data / timeout / blocked / 设备关联 / 模型分 / 用户反馈是否能定性 | 纯分析，30s 内短答 | 不自动查平台，不把弱信号当强证据 |
| `strategy_recommendation_plan_mode` | 灰度验证、误伤控制、策略推荐、举一返三、监控指标、治理方案 | 输出策略框架、补证字段、DataAgent/Hive query plan | 即使带 user_id 也不自动 execution |
| `batch_plan_mode` | 3+ 用户 / 设备、批量、共性归因、分层判断 | 输出 batch plan、case registry 字段、证据分层框架 | 不逐个在线查，确认后才 batch execution |
| `non_ato_expert_mode` | 反爬、协议、导流截流、活动作弊、渠道套利、群控泛化 | 专家分析 + 取证计划 + 策略建议 | 不默认 browser / 档案中心 |
| `partial_evidence_card_fallback` | source timeout / blocked / parse error / auth issue | 输出 completed / blocked / timeout / missing evidence 和 next action | 不裸 timeout，不把失败当反证 |
| `browser_spa_loop_guard` | track-analysis / 档案中心 / 天狮同一 SPA 操作失败超过 3 次 | 停止该 source，标 `operation_loop_detected` / `platform_access_partial` / `browser_overuse`，输出 partial evidence card | 不无限点击 / 截图 / 下拉 / 导入 |

DataAgent/Hive 仅在超出在线可靠窗口、批量、长窗口、复杂 SQL、跨表分析或用户明确要求生成取数问题时进入 plan 或等待确认；不得泛化成默认执行底座。

## learning_candidate_capture

```yaml
capability_id: learning_candidate_capture
chinese_name: 用户问题收集与学习候选队列
layer: learning_candidate_infrastructure
status: documented
purpose: 收集半开放用户真实问题和反馈，识别全场景高频需求、能力缺口、路由问题、证据模板缺口和安全绕过问题，生成 question_record / candidate_queue / case_learning_note 候选材料
input:
  - sanitized_user_question
  - answer_mode
  - agent_observed_quality_risk_signals
  - user_feedback
  - suggested_scene
  - suggested_capability
output:
  - question_record
  - learning_candidate_queue_row
  - case_learning_note_candidate
boundaries:
  - full_scenario_capability_not_ato_only
  - not_a_risk_judgement_hand
  - no_real_platform_access
  - no_dataagent_call
  - no_sensitive_plaintext_output_or_storage
  - no_cookie_token_session_header_recording
  - no_auto_skill_update
  - no_auto_prompt_update
  - no_auto_routing_update
  - no_auto_release_update
  - reviewer_decision_pending_by_default
recommended_followup_only_after_review:
  - add_to_faq
  - add_golden_case
  - add_bad_case
  - update_skill_summary
  - update_routing
  - update_evidence_template
  - add_regression_case
  - generate_dataagent_query_plan
  - add_asset_extraction_guard_case
templates:
  - computer_use_poc/question_collection/README.md
  - computer_use_poc/question_collection/question_record_schema_v1.md
  - computer_use_poc/question_collection/question_learning_policy_v1.md
  - computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv
  - computer_use_poc/question_collection/user_feedback_capture_v1.md
  - computer_use_poc/question_collection/case_learning_note_template_v1.md
  - computer_use_poc/question_collection/question_collection_text_regression_cases_v1.yaml
  - computer_use_poc/question_collection/question_collection_text_regression_run_v1.md
  - computer_use_poc/question_collection/runtime_append_only_logging_contract_v1.md
  - computer_use_poc/question_collection/runtime_question_record_sample_v1.jsonl
  - computer_use_poc/question_collection/runtime_logging_smoke_test_v1.md
  - computer_use_poc/question_collection/runtime_question_record_collector_stub_v1.py
```

## batch_analysis_framework

```yaml
capability_name: batch_analysis_framework
chinese_name: Batch Analysis 通用框架
layer: methodology
status: documented
purpose: 抽象不同 batch analysis 场景共用流程，避免每个场景重复设计 registry、evidence card、pattern summary 和 strategy draft
common_flow:
  - case_intake
  - case_registry
  - entity_normalization
  - single_case_evidence_card
  - cross_case_pattern_summary
  - missing_evidence_aggregation
  - strategy_direction_draft
  - manual_review_boundary
scene_specific_replace:
  - risk_definition
  - scene_specific_fields
  - evidence_priority
  - pattern_dimensions
  - strategy_direction_boundary
boundaries:
  - framework_only
  - no_real_dataagent_call
  - no_real_platform_query
  - no_auto_strategy_launch
  - dataagent_only_for_hive_or_warehouse_analysis_when_scene_allows
  - internal_agent_is_observation_executor_not_final_reasoning_brain
```

## batch_risk_clustering_analysis

```yaml
capability_name: batch_risk_clustering_analysis
chinese_name: 批量风险分簇研判包
capability_type:
  - analysis_planning
  - batch_reasoning
  - evidence_structuring
layer: evidence_orchestration
status: documented
default_mode: batch_plan_mode
supported_modes:
  - single_entity_execution_mode
  - small_multi_case_execution_mode
  - small_batch_mode
  - batch_clustering_mode
  - large_batch_aggregation_mode
  - alert_batch_or_population_analysis_mode
purpose: 对多 case / 多实体 / 告警批次 / 接口请求激增 / 渠道异常 / 设备群控 / ATO 批量 / 活动套利 / 策略召回批次做分簇、异常相关性矩阵、代表样本抽样、证据缺口识别、举一返三和策略建议
threshold_policy:
  1_2_entities: single_entity_execution_mode
  3_4_entities: small_multi_case_execution_mode
  5_9_entities: small_batch_mode
  10_49_entities: batch_clustering_mode
  50_499_entities: large_batch_aggregation_mode
  500_plus_entities: alert_batch_or_population_analysis_mode
requires:
  - batch input schema
  - account risk data source registry
  - batch L1 feature query contract
  - top dimension drilldown
  - frequent pattern contribution analysis
  - ATO cluster lens overlay when compromised-account / stolen-account posting is suspected
  - evidence source metadata
  - representative sampling
  - abnormal correlation matrix
  - pattern summary
does_not_do:
  - no_default_large_batch_online_lookup
  - no_auto_dataagent_call
  - no_real_internal_platform_access
  - no_auto_disposition
  - no_auto_strategy_launch
  - no_same_gang_judgement_from_similarity_only
  - no_historical_case_evidence_as_current_batch_fact
boundaries:
  - 5 个以下可全量深查
  - 10+ 强制 batch_clustering_mode / plan_mode，不逐个在线查
  - 50+ 强制 aggregation / DataAgent-Hive query plan
  - explicit_per_entity_online_execution_required_for_10_plus
  - strategy_recommendation_or_expansion_with_ids_stays_plan_mode
  - DataAgent only for Hive / warehouse query planning when needed
  - no_data cannot be no-risk counter evidence
  - blocked_timeout_partial_source_must_be_source_gap
  - batch_ato_lens_additive_to_existing_clusters
  - common_device_id_not_sufficient_to_exclude_ato
  - representative_sample_not_global_proof
workflow:
  - batch_input
  - L1_wide_table_profile_shallow_query_plan
  - batch_feature_table
  - top_dimension_summary
  - frequent_pattern_contribution_score
  - A_to_B_directed_abnormal_correlation
  - cluster_hint
  - ato_cluster_lens_overlay_when_relevant
  - compromised_account_cluster_detection
  - representative_sampling
  - representative_ato_single_case_deep_dive_when_relevant
  - cluster_level_backfill
  - cluster_evidence_card
  - expansion_and_strategy_recommendation
required_output_fields_for_10_plus:
  - batch_clustering_mode
  - relation_family
  - evidence_basis
  - denominator_status
  - relationship_strength
  - reverse_check_result
  - confounder_risk
  - cannot_conclude_boundary
  - representative_cases
  - pattern_summary
  - required_validation
  - candidate_strategy_direction
  - batch_feature_table
  - top_dimension_summary
  - frequent_pattern
  - contribution_score
  - ato_cluster_lens_when_relevant
  - cluster_level_backfill_when_relevant
templates:
  - computer_use_poc/batch_risk_clustering/account_risk_data_source_registry_v1.md
  - computer_use_poc/batch_risk_clustering/account_security_hive_source_registry_v1.md
  - computer_use_poc/batch_risk_clustering/account_security_hive_query_plan_templates_v1.md
  - computer_use_poc/batch_risk_clustering/batch_l1_feature_query_contract_v1.md
  - computer_use_poc/batch_risk_clustering/batch_top_dimension_drilldown_template_v1.md
  - computer_use_poc/batch_risk_clustering/batch_frequent_pattern_contribution_template_v1.md
  - computer_use_poc/batch_risk_clustering/README.md
  - computer_use_poc/batch_risk_clustering/batch_risk_case_schema_v1.md
  - computer_use_poc/batch_risk_clustering/batch_risk_threshold_policy_v1.md
  - computer_use_poc/batch_risk_clustering/batch_risk_clustering_methodology_v1.md
  - computer_use_poc/batch_risk_clustering/batch_ato_cluster_lens_v1.md
  - computer_use_poc/batch_risk_clustering/abnormal_correlation_matrix_v1.md
  - computer_use_poc/batch_risk_clustering/batch_risk_representative_sampling_v1.md
  - computer_use_poc/batch_risk_clustering/batch_risk_evidence_card_template_v1.md
  - computer_use_poc/batch_risk_clustering/batch_risk_pattern_summary_template_v1.md
  - computer_use_poc/batch_risk_clustering/batch_risk_response_template_v1.md
  - computer_use_poc/batch_risk_clustering/batch_risk_runtime_validation_cases_v1.yaml
```

Account-security Hive source boundary:

- ATO / 盗号 / 登录链路离线补证应使用 `account_security_hive_source_registry_v1.md` 和 `account_security_hive_query_plan_templates_v1.md`。
- 成功登录优先 `ks_rc_bs.ks_account_login_basic_info`。
- 登录失败 / 撞库 / 暴力破解 / 改密优先 `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info`；表名拼写为 `orign`，不得改成 `origin`。
- Web RCP 使用 `ks_rc_arch.antispam_feature_map_default_partitioned`，30 天窗口。
- App RCP 使用 `ks_raw_log_v2.antispam_feature_map_partitioned`，50 天窗口，必须限制 `p_date + p_hourmin + p_action_type`。
- DataAgent 仅作为 Hive / 数仓取数分析计划或确认后的离线执行能力，不是万能风控执行器。

Batch ATO cluster lens boundary:

- `batch_ato_cluster_lens` 是 `batch_risk_clustering_analysis` 的 overlay，不推翻已有内容相似、设备共性、策略命中、时间聚集、账号画像和行为模式分簇。
- 识别 `web_untrusted_login_cluster`、`login_to_action_cluster`、`device_identity_inconsistency_cluster`、`compromised_account_cluster`、`content_abuse_only_cluster`、`mixed_cluster` 和 `insufficient_evidence_cluster`。
- ATO / 账号接管分簇特征库已注册维度：控制权入口、设备共性、IP / 网络、时间序列、行为承接、前端活跃、策略 / 风控信号、用户反馈 / 反证。
- 控制权入口必须区分撞库 / 密码型 ATO、OAuth / 扫码 / 一键登录接管、token / session / 协议上号、异常发布 / 导流承接型 ATO、误伤 / 用户自身异常行为 / 灰色用户；HARMONY、OAuth、quickLogin、token issued、kickout、reset_login_type 等线索不能被简单归为撞库。
- 分簇输出必须包含 `cluster_key`、`shared_features`、`representative_users`、`strong_evidence`、`weak_evidence`、`counter_evidence` 和 `missing_evidence`。
- 每个疑似 ATO 簇抽代表样本做 `representative_ato_single_case_deep_dive`，再用 `cluster_level_backfill` 回填 coverage / similarity / confidence / source gap；不得默认全批账号都被盗。
- Track 活跃、策略命中、内容命中、常用 `device_id`、在线登录 no_data / `response_too_large` / wrapper mismatch 都不能作为排除 ATO 的强反证。
- 当批量 ATO 的实时登录 / 控制链不完整，或 admin 仅 APP 日志无法覆盖 WEB/H5/PC/token/OAuth/扫码链路时，必须提示 `offline_hive_required` 并使用账号安全 Hive registry-first query plan；未获用户逐次授权不得调用 DataAgent/Hive。

## batch_case_analysis

```yaml
capability_name: batch_case_analysis
chinese_name: ATO 批量 case analysis / 批量归因最小闭环
layer: evidence_orchestration
status: mvp_template_ready
purpose: 面向 5-20 个 ATO / 盗号申诉 case，完成 case 标准化、单 case 证据卡、跨 case 模式聚合、缺口识别和候选策略方向
input:
  - ato_batch_case_registry
  - case_id
  - user_id
  - device_id
  - event_time
  - abnormal_action
  - user_claim
  - available_evidence
  - missing_evidence
output:
  - standardized_case_registry
  - single_case_evidence_cards
  - cross_case_pattern_summary
  - missing_evidence_summary
  - candidate_strategy_direction
contract:
  input_contract: eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_input_contract_v1.md
  output_contract: eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_output_contract_v1.md
  status_transition: eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_status_transition_v1.md
  user_interaction_examples: eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_user_interaction_examples_v1.md
  real_case_pilot_checklist: eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_real_case_pilot_checklist_v1.md
should_trigger_when:
  - user_provides_5_to_20_ato_cases
  - user_asks_for_batch_attribution
  - user_asks_for_common_pattern_summary
  - user_asks_for_strategy_direction_draft_from_cases
should_not_trigger_when:
  - user_asks_for_single_case_execution
  - user_requests_auto_strategy_launch
  - user_requests_batch_platform_query_without_approval
  - user_requests_real_dataagent_execution
boundaries:
  - no_real_dataagent_call
  - no_real_platform_query
  - no_auto_disposition
  - no_auto_strategy_launch
  - dataagent_only_for_future_hive_or_warehouse_analysis_when_scene_allows
  - real_case_pilot_is_validation_stage_not_auto_disposition
  - case_aggregation_is_pattern_hypothesis_not_final_risk_conclusion
  - input_contract_required_before_evidence_card
  - output_contract_required_for_user_facing_result
  - status_transition_must_be_visible_for_missing_or_partial_cases
  - evidence_source_trace_required
  - model_inference_cannot_be_treated_as_raw_evidence
  - stale_partial_blocked_source_must_be_visible_in_output
templates:
  - eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_case_schema_v1.md
  - eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_case_registry_template_v1.csv
  - eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_workflow_v1.md
  - eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_evidence_card_template_v1.md
  - eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_pattern_summary_template_v1.md
  - eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_strategy_direction_template_v1.md
  - eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_input_contract_v1.md
  - eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_output_contract_v1.md
  - eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_status_transition_v1.md
  - eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_user_interaction_examples_v1.md
  - eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_real_case_pilot_checklist_v1.md
```

## ato_case_expansion_planning

```yaml
capability_name: ato_case_expansion_planning
chinese_name: ATO / 盗号 case 举一返三扩展方案
layer: planning_and_methodology
status: documented
purpose: 针对单个或少量 ATO case，设计如何扩展发现同类受害账号、同类攻击链路和同类黑产基础设施
input:
  - single_or_few_ato_cases
  - known_event_time
  - abnormal_action
  - available_evidence_card
  - missing_evidence
output:
  - expansion_anchor_list
  - query_scope_control
  - candidate_account_discovery_plan
  - evidence_card_backfill_plan
  - pattern_summary_plan
  - dataagent_hive_question_templates
should_trigger_when:
  - user_asks_how_to_expand_from_one_ato_case
  - user_asks_for_similar_victim_discovery_plan
  - user_asks_for_same_attack_chain_or_infra_expansion
  - user_has_one_or_few_ato_cases_and_wants_hive_questions
should_not_trigger_when:
  - user_asks_for_black_market_profile_matrix_expansion
  - user_asks_for_same_nickname_or_intro_cluster_as_ato
  - user_requests_real_dataagent_execution
  - user_requests_auto_disposition
boundaries:
  - no_real_dataagent_call
  - no_real_platform_query
  - no_auto_disposition
  - no_auto_strategy_launch
  - expansion_is_plan_not_observation
  - post_action_is_not_ato_root_cause_without_control_change_evidence
  - online_login_log_over_window_requires_offline_hive_required
template:
  - eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_case_expansion_plan_v1.md
```

## black_market_account_matrix_batch_analysis

```yaml
capability_name: black_market_account_matrix_batch_analysis
chinese_name: 黑产账号矩阵 / 导流互动 batch case analysis
layer: evidence_orchestration
status: mvp_template_ready
purpose: 面向同一波黑产账号样本，完成账号矩阵、导流互动、互粉互动、养号账号池的资料聚类、证据卡、模式摘要和候选策略方向
not_ato_boundary:
  - ato_is_account_control_abnormality
  - this_capability_is_account_matrix_and_diversion_interaction_abuse
input:
  - account_matrix_registry
  - account_ref
  - uid_segment
  - nickname_pattern
  - intro_pattern
  - adminaction_code
  - registration_age_days
  - observed_behavior
output:
  - account_matrix_evidence_cards
  - common_intro_pattern_summary
  - common_adminaction_summary
  - nickname_template_summary
  - registration_age_cohort
  - uid_segment_cohort
  - behavior_evidence_missing
  - candidate_strategy_direction
should_trigger_when:
  - user_provides_black_market_account_matrix_samples
  - user_asks_for_diversion_interaction_batch_analysis
  - user_asks_for_mutual_follow_or_account_pool_attribution
should_not_trigger_when:
  - user_asks_for_ato_account_takeover_judgement
  - user_asks_for_single_user_login_or_token_control_analysis
  - user_requests_auto_strategy_launch
boundaries:
  - no_real_dataagent_call
  - no_real_platform_query
  - no_auto_disposition
  - no_auto_strategy_launch
  - contact_uid_device_ip_must_be_redacted
  - profile_cluster_is_recall_signal_not_disposition_basis
templates:
  - eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/black_market_account_matrix_case_schema_v1.md
  - eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/black_market_account_matrix_registry_template_v1.csv
  - eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/black_market_account_matrix_evidence_card_template_v1.md
  - eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/black_market_account_matrix_pattern_summary_template_v1.md
  - eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/black_market_account_matrix_strategy_direction_template_v1.md
  - eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/black_market_account_matrix_dry_run_sample_v1.md
```

## plan_mode

```yaml
capability_name: plan_mode
chinese_name: Plan 模式 / 研判计划能力
layer: main_agent_orchestration
status: new_capability_from_zero
purpose: 在用户显式要求计划、边界不清、批量/关联扩展或高风险动作不适合直接执行时，生成用户可理解、可选择、可确认的只读研判计划
mode_boundary:
  - plan_mode_is_pre_execution_explanation
  - execution_mode_is_real_query_and_judgement
  - real_judgement_queries_should_default_to_execution_when_scope_is_clear
  - plan_is_not_default_for_every_query
input:
  - user_query
  - detected_entities
  - inferred_scene
  - available_capabilities
  - risk_context
output:
  - problem_understanding
  - judgement_goal
  - query_path_with_evidence_cards
  - evidence_strength_explanation
  - readonly_boundary
  - expected_output
  - user_choices
should_trigger_when:
  - user_explicitly_asks_for_plan
  - user_asks_how_to_investigate
  - unclear_entity_or_scope
  - large_batch_or_association_expansion_needed
  - high_risk_action_or_sensitive_boundary
  - method_or_path_design_question
should_not_trigger_when:
  - pure_concept_explanation
  - single_field_lookup
  - user_explicitly_requests_direct_query
  - clear_scope_real_judgement_query
  - normal_readonly_execution_can_answer
default_execution_examples:
  - 帮我看下这个用户是不是风险用户
  - 这个账号是不是盗号
  - 这批账号是不是一伙的
  - 这个用户是不是误伤
  - 这个 request_id 为什么被拦
  - 这个 device_id 有没有问题
boundaries:
  - readonly_only
  - no_disposition
  - no_default_batch_expansion
  - association_is_candidate_not_conclusion
  - no_fabricated_evidence
  - too_many_candidates_stop_expansion
  - missing_entity_requires_clarification_or_generic_plan
  - auth_or_permission_error_must_be_explicit
  - safety_framework_not_yet_integrated
downstream_capabilities:
  - archives_center
  - user_login_logs
  - device_sdk_or_device_profile
  - tianshi_strategy_hit
  - frontend_activity_profile
  - weapon_graph_or_entity_relation_when_needed
  - data_agent_only_when_scene_allows
```

### 定位

`plan_mode` 是执行前解释层，不是真实查询结果。它不调用接口、不生成 observation、不输出最终风险结论。

真实研判问题默认进入执行模式；Plan 只在用户显式要求“先说怎么查 / 先给计划 / 先不要执行”，或边界不清、批量 / 关联扩展、高风险动作不适合直接执行时触发。

Data Agent 不能被泛化成所有数据源底座。只有当场景允许，且确实需要 Hive / 公司数仓取数分析时，才可能进入 Data Agent。

### 输出模板

Plan 标准结构见 `computer_use_poc/plan_mode_capability_v1.md`，固定包含：

1. 我理解的问题。
2. 本次研判目标。
3. 查询路径与强区分证据卡。
4. 证据强弱说明。
5. 查询边界。
6. 预期输出。
7. 你可以选择。

## expert_reasoning_first

```yaml
capability_name: expert_reasoning_first
mode_name: expert_reasoning_first
display_name: 专家认知模式 / 专家认知先判模式
type: brain_capability
platform_call: false
real_data_read: false
write_action: false
downstream_can_connect_to:
  - plan_mode
  - read_only_execution_mode
input:
  - case_text
  - appeal_text
  - customer_service_record
  - manual_note
  - risk_phenomenon_description
output:
  - expert_prior_judgment
  - known_facts
  - core_contradiction_explanation
  - candidate_attack_paths
  - distinguishing_evidence_cards
  - suggested_query_path
  - confidence_and_boundaries
```

### 定位

`expert_reasoning_first` 是 Dennis Risk Agent 的专家认知先判模式，不是新平台手脚，也不是 v2.5 内部平台执行能力。

它复用 v2.1 大脑提示词、账号安全认知、风险路径判断、证据拆解和回复话术，用于“查证前的专家先验分析”。它不是所有 case 的默认入口，也不是所有“研判 / 判断”请求的默认入口。

适用前提：

- 先不查数。
- 先解释现象。
- 先判断可能路径。
- 先设计强区分证据。
- 暂时缺少可直接查数的实体或时间窗口，或用户明确要求“先不查平台”。

在这些前提下，先完成：

1. 看懂问题。
2. 提炼核心矛盾。
3. 给出候选风险路径。
4. 解释表面矛盾为什么可能成立。
5. 设计强区分证据。
6. 输出后续可选查询路径。
7. 标注置信度和边界。

该模式只输出“专家先验判断”和“证据规划”，不是事实结论。

### 触发条件

满足以下任一条件时，进入 `expert_reasoning_first`：

- 用户明确说：
  - 先不查数。
  - 先从专家视角判断。
  - 先解释现象。
  - 先给候选路径。
  - 先设计强区分证据。
  - 先给专家先验判断。
- 用户只提供申诉文本、客服记录、人工备注、模糊现象，且没有明确 `userId / deviceId / workId / IP / token_id / 时间窗口 / 平台名 / 日志对象`。
- 输入中有明显矛盾现象，但当前缺少可直接查询条件：
  - 登录设备只有本人，但账号发生非本人发布。
  - 用户称没操作，但存在交易、发布、登录、关注、点赞等行为。
  - 策略命中较强，但用户申诉材料看似正常。
  - 设备无异常，但行为链路异常。
  - 登录无异常，但内容、交易、互动异常。
- 当前问题核心是解释“为什么会这样”、梳理候选路径、设计强区分证据，而不是事实验证。

### 不触发条件

不要进入 `expert_reasoning_first`：

- 用户明确要求“查一下平台”“调用某个手脚”“看日志结果”。
- 用户提供了 `userId / deviceId / workId / IP / token_id / 时间窗口 / 平台名 / 日志类型 / 查询对象`，并要求“研判下 / 看下 / 查下”。这种场景默认进入 read-only execution；只有用户显式要求计划，或边界不清、批量扩展、高风险动作时才进入 Plan。
- 用户已经给出结构化平台 observation，需要做证据归纳或结论生成。
- 用户要写工程文档、改代码、生成 release 包。
- 用户只是问概念解释，例如“token 是什么”“OAuth 是什么”。
- 用户要求执行处置、封禁、解封、批量扩散查询。

### 路由优先级

- 明确 case + 明确实体 / 时间 / 查询对象 / 事实验证诉求：默认进入 read-only execution；Plan 只用于显式计划请求或边界不清场景。
- case 文本 + 明确 `userId` 和时间窗口，但用户没有显式说“先不查数”：默认进入 read-only execution；只有边界不清、批量扩展、高风险动作或用户显式要求计划时才进入 Plan。
- Plan 模式可以在开头给一句简短专家假设，但不要展开完整 `expert_reasoning_first` 模板。
- 用户明确要求“先从专家视角判断，不查平台”：即使有明确实体，也进入 `expert_reasoning_first`。

### 核心边界

- 不查数。
- 不调内部平台。
- 不访问真实用户数据。
- 不输出“已确认”“确定就是”这类事实结论。
- 可以输出“高度疑似 / 当前最可能 / 需要日志确认 / 证据不足”。
- 必须区分：已知事实、高概率推断、待验证假设、反证可能。
- 不能把关联关系直接等同于风险定性。
- 不能把“设备列表无异常”误解为“账号一定没被盗”。
- 不能把“API 直调”直接等同于“协议破解”。很多场景可能只是复用合法 token 调合法接口。

## expert_reasoning_first answer contract

输出必须包含：

1. 一句话判断。
2. 已知事实。
3. 核心矛盾解释。
4. 候选攻击路径排序。
5. 强区分证据卡。
6. 查询路径建议。
7. 结论置信度与边界。
8. 下一步建议。

强区分证据卡必须能区分至少两个候选路径，不能只写“建议查日志”。

## Capability Security Overlay v1

本节是安全执行框架 v1 的 capability registry 增量字段，不替代上文的业务能力定义。

通用安全字段：

```yaml
capability_security_fields:
  capability_name:
  description:
  mode: readonly / write / system
  capability_level:
  allowed_inputs:
  denied_inputs:
  max_default_scope:
  batch_allowed:
  approval_required_if:
  sensitive_fields:
  output_redaction:
  audit_required:
  fallback_policy:
  current_status:
```

通用边界：

- 所有业务查询能力默认 `readonly`。
- `api_direct_read` 不能是任意接口访问，只能是已登记 endpoint / capability。
- `browser_dom_read` 不能执行任意 JS，只能读取已登记页面模块。
- `write` / `system` 类型当前版本 `prohibited`。
- 用户 prompt 不能决定底层工具；主 Agent 必须根据 scene + entity + evidence_need 选择 capability。

### Registered capability security profile

```yaml
capabilities:
  - capability_name: user_to_device_resolution
    description: "将 userId 转译为候选 deviceId / did / deviceceid"
    mode: readonly
    capability_level: readonly_sensitive
    allowed_inputs: [single_user_id, bounded_time_context_optional]
    denied_inputs: [bulk_user_list_without_approval, arbitrary_graph_expansion]
    max_default_scope: single_user_top_candidates
    batch_allowed: false
    approval_required_if: [many_users, multi_hop_expansion, too_many_candidates]
    sensitive_fields: [device_id, relation_detail]
    output_redaction: device_id_partial_mask_or_reference
    audit_required: true
    fallback_policy: missing_device_id_or_too_many_candidates
    current_status: registered_readonly

  - capability_name: device_to_user_resolution
    description: "将 deviceId 转译为候选关联用户"
    mode: readonly
    capability_level: readonly_sensitive
    allowed_inputs: [single_device_id]
    denied_inputs: [bulk_device_list_without_approval, multi_hop_expansion]
    max_default_scope: single_device_direct_users
    batch_allowed: false
    approval_required_if: [many_devices, multi_hop_expansion, sensitive_user_details_requested]
    sensitive_fields: [user_id, relation_detail, risk_tags]
    output_redaction: user_id_reference_or_partial_mask
    audit_required: true
    fallback_policy: no_related_user_or_too_many_candidates
    current_status: registered_readonly

  - capability_name: device_risk_read
    description: "读取设备侧风险标签和设备环境摘要"
    mode: readonly
    capability_level: readonly_sensitive
    allowed_inputs: [single_device_id]
    denied_inputs: [location_query_by_default, bulk_device_export, raw_device_fingerprint_output]
    max_default_scope: single_device_risk_summary
    batch_allowed: false
    approval_required_if: [many_devices, raw_fingerprint_requested, location_requested]
    sensitive_fields: [device_id, device_fingerprint, ip, app_list]
    output_redaction: derived_risk_tags_and_partial_device_id
    audit_required: true
    fallback_policy: platform_not_applicable_or_no_data
    current_status: registered_readonly

  - capability_name: user_profile_read
    description: "读取单用户画像、状态、历史风险和补证摘要"
    mode: readonly
    capability_level: readonly_sensitive
    allowed_inputs: [single_user_id]
    denied_inputs: [bulk_user_export, raw_personal_info_output]
    max_default_scope: single_user_profile_summary
    batch_allowed: false
    approval_required_if: [many_users, sensitive_identity_fields_requested]
    sensitive_fields: [phone, ip, device_id, operator_account, personal_info]
    output_redaction: summary_and_redacted_identifiers
    audit_required: true
    fallback_policy: auth_required_or_permission_blocked
    current_status: registered_readonly

  - capability_name: login_log_read
    description: "读取登录链路、验证链路、token 生命周期摘要"
    mode: readonly
    capability_level: readonly_sensitive
    allowed_inputs: [single_user_id_or_single_did, bounded_time_range]
    denied_inputs: [raw_token_output, unbounded_history_query, bulk_user_query]
    reliable_window_precheck_required: true
    reliable_window_days: 7
    max_default_scope: single_entity_reliable_window
    batch_allowed: false
    approval_required_if: [over_reliable_window, many_users, raw_log_content_requested]
    sensitive_fields: [token, session, ip, device_id, user_agent, log_content]
    output_redaction: credential_present_redacted_and_derived_features
    audit_required: true
    fallback_policy: login_log_window_incomplete_or_offline_hive_required
    over_window_no_data_interpretation: data_gap_not_counter_evidence
    over_window_behavior: skip_or_warn_and_return_offline_hive_required
    current_status: registered_readonly

  - capability_name: strategy_hit_read
    description: "读取策略命中摘要和策略证据"
    mode: readonly
    capability_level: readonly_sensitive
    allowed_inputs: [single_source_id, bounded_time_range]
    denied_inputs: [raw_response_dump, batch_source_ids_without_approval]
    max_default_scope: single_source_bounded_window
    batch_allowed: false
    approval_required_if: [many_source_ids, raw_event_detail_requested, long_time_window]
    sensitive_fields: [request_payload, raw_response, internal_trace]
    output_redaction: strategy_summary_and_sample_hits_limited
    audit_required: true
    fallback_policy: partial_if_eventlist_unavailable
    current_status: registered_readonly

  - capability_name: frontend_activity_read
    description: "读取前端活跃画像摘要"
    mode: readonly
    capability_level: readonly_sensitive
    allowed_inputs: [single_user_id_or_device_id]
    denied_inputs: [raw_event_sequence_by_default, behavior_replay_export]
    max_default_scope: profile_top_area_summary
    batch_allowed: false
    approval_required_if: [event_sequence_requested, many_entities]
    sensitive_fields: [device_id, usage_detail, screenshots]
    output_redaction: activity_signal_summary
    audit_required: true
    fallback_policy: design_only_or_not_open_for_real_execution
    current_status: limited_or_design_only

  - capability_name: api_direct_read
    description: "对已登记 endpoint / capability 执行 API direct readonly"
    mode: readonly
    capability_level: readonly_sensitive
    allowed_inputs: [registered_endpoint, registered_payload_shape, bounded_scope]
    denied_inputs: [arbitrary_url, arbitrary_api, raw_header_export, credential_export]
    max_default_scope: registered_single_entity_read
    batch_allowed: false
    approval_required_if: [new_endpoint, many_entities, raw_json_requested]
    sensitive_fields: [cookie, token, session, headers, raw_json, requestParam, extraParam]
    output_redaction: schema_summary_and_derived_features
    audit_required: true
    fallback_policy: api_failed_or_response_shape_changed
    current_status: registered_readonly_only

  - capability_name: browser_dom_read
    description: "在已登记页面模块内执行只读 DOM / scoped extraction"
    mode: readonly
    capability_level: readonly_sensitive
    allowed_inputs: [registered_page_module, scoped_selector, readonly_extract]
    denied_inputs: [arbitrary_js, localStorage_dump, cookie_read, mutation_clicks]
    max_default_scope: registered_page_module_read
    batch_allowed: false
    approval_required_if: [new_page_module, broad_snapshot, sensitive_raw_text_requested]
    sensitive_fields: [operator_account, page_sensitive_text, storage, token_like_values]
    output_redaction: scoped_summary_and_redacted_values
    audit_required: true
    fallback_policy: selector_unstable_or_auth_required
    current_status: registered_readonly_only
```

### Prohibited capability classes

```yaml
prohibited_current_version:
  write_or_mutation:
    mode: write
    current_status: prohibited
    examples:
      - ban_user
      - unban_user
      - change_strategy
      - submit_approval
      - delete_data
  system_or_logic_modification:
    mode: system
    current_status: prohibited
    examples:
      - modify_agent_prompt
      - modify_skill
      - modify_routing
      - modify_release
      - change_tool_registry
```
