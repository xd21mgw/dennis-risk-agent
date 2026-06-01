# Account Security Runtime Summary v1

## 1. 定位

本 summary 支撑半开放 runtime 下的账号安全 / ATO / 盗号判断。重点是避免把批量统计直接解释成攻击本质。

通用研判纪律：本 summary 必须遵守 `computer_use_poc/general_evidence_reasoning_contract_v1.md`。登录日志 no_data、策略命中、模型分、用户反馈、Hive pending 结果都不能单独作为最终定性；必须区分 raw_evidence / strategy_hit / model_score / inference / user_claim / counter_evidence / missing_evidence，并在新证据到达后重算结论。

## 2. ATO 攻击类型识别

### 2.1 撞库 ATO

主线特征：

- 密码尝试、登录失败、CAPTCHA 或验证挑战密集。
- 同 IP / 代理 / 设备对多账号做凭证测试。
- 成功登录后出现敏感动作、资料修改、私信、发布、支付等后置行为。

判断边界：

- `password fail + CAPTCHA + kick_out` 只能提示账号安全异常，不能单独定性撞库。
- 必须看到密码尝试是攻击主线，而不是改密 / 密码验证环节的后置现象。

### 2.2 一键登录 / 三方授权 / 鸿蒙一键登录 ATO

候选触发信号：

- 出现 `HARMONY_` 设备 ID 或鸿蒙设备前缀。
- token issued / token 下发成功。
- 多账号登录成功。
- 同一 IP 集中登录多个用户。
- token revoke / kick out。
- 后续小米 / Android 设备改密或密码验证失败。
- 用户原设备与新 HARMONY 设备明显不一致。

判断：

- 这类 case 应优先识别为“一键登录 / 三方授权接管 / 鸿蒙一键登录 ATO”候选。
- 不应直接归为撞库。
- 大量 password fail / CAPTCHA 可能来自改密环节，不一定是撞库尝试。

## 3. 批量 ATO 逐条时序抽样

批量 ATO case 中出现以下任一信号时，不能只看 totalCount / kick_out 次数 / fail 次数：

- kick_out 密集。
- password fail / CAPTCHA 密集。
- 多设备切换。
- 同 IP 集中。
- 三方登录 / 一键登录 / OAuth / HARMONY 相关字段。

必须抽取 3-5 个代表用户做 timeline：

- 正常登录设备。
- 异常登录设备。
- 登录方式。
- token issued。
- token revoke / kick out。
- password verify / change password。
- IP。
- device model / did prefix。
- event order。

输出必须包含“撞库 ATO vs 一键登录 ATO”的替代解释对比。

### 3.1 Batch ATO cluster lens overlay

批量 ATO 不是“没有分簇”，也不是把每个用户逐个跑单案链路。当前批量框架已有内容相似、设备共性、策略命中、时间聚集、账号画像和行为模式分簇；ATO 需要在这些已有簇上叠加 `ato_cluster_lens`。

标准流程：

1. `existing_cluster_signal_collection`：保留已有分簇依据。
2. `ato_cluster_lens_overlay`：检查 WEB 非可信登录、登录方式异常、`login_to_action_delta`、内容动作闭环、设备身份一致性、共享基础设施和历史行为突变。
3. `compromised_account_cluster_detection`：登录 / 控制链异常 + 后置内容动作异常 + 设备身份异常或历史行为突变同时成立时，标 `compromised_account_cluster` 或 `high_suspected_ato_cluster`。
4. `representative_case_selection`：每个疑似 ATO 簇抽高疑似、中疑似、边界和反例样本。
5. `representative_ato_single_case_deep_dive`：代表样本走单案链路，证明该簇攻击机制。
6. `cluster_level_backfill`：把单案发现回填到簇级 coverage / similarity / confidence / source gap。
7. `batch_conclusion`：只输出簇级结论，不默认全批账号都被盗。

ATO lens 必看：

- `web_untrusted_login_cluster`：WEB / H5 / PC 登录从历史 APP 偏移，或 WEB 登录设备 / IP / UA / browser fingerprint 非历史常用。
- `login_to_action_delta`：WEB / 控制链登录后短时间发布视频、评论、直播、私信或资料修改。
- `device_identity_inconsistency_cluster`：常用 `device_id` 下机型、系统、UA、IP、登录端、登录方式等变量漂移。
- `content_action_deep_dive`：代表样本必须尽量提取 `photo_id` / `live_id` / `comment_id`、发布时间、发布来源、发布设备、IP / UA、四项信息和审核 / 策略 / 导流原因。
- `existing_cluster_plus_ato_lens`：内容导流簇、策略命中簇或设备共性簇可叠加 ATO 盗号投放嫌疑，不互斥。

批量 ATO 边界：

- Track 活跃不能证明本人。
- 常用 `device_id` 不能降低 ATO 置信度，除非 `device_identity_consistency` 完整一致。
- login no_data、`response_too_large`、wrapper mismatch、timeout 只能进入 source gap / Hive required，不得当低风险反证。
- 代表样本单案支持 ATO，只能证明对应簇存在 ATO 模式，不能默认全批账号都被盗。
- 长周期登录补证只生成基于 `account_security_hive_source_registry_v1.md` 的 registry-first query plan，不自由猜表，不实际调用 DataAgent/Hive。

## 4. 禁止结论跳跃

禁止：

- 只凭 `kick_out + password fail + CAPTCHA` 直接输出“撞库 ATO”。
- 只看 totalCount 汇总，不抽样逐条时序。
- 把改密阶段的 password fail / CAPTCHA 当作撞库主线证据。

推荐表述：

```text
当前批量统计显示账号安全异常，但不能直接定性撞库。日志中出现 HARMONY_ 设备、同 IP token 下发、token revoke / kick out，以及后续小米 / Android 改密尝试，更应优先验证一键登录 / 三方授权接管 / 鸿蒙一键登录 ATO 链路。
```

## 5. 单案 evidence card 证据类型分离

单个 user_id / case 的 ATO 研判必须区分：

- `raw_evidence`: 平台日志、发布审计、登录日志、设备画像、策略命中等事实。
- `behavior_event`: 违规内容发布、改密、换绑、私信、关注、支付等动作发生事实。
- `user_claim`: 用户声称被盗、非本人操作、客服备注。
- `inference`: 基于多源证据的解释。
- `hypothesis`: 需要补证的候选路径。
- `missing_evidence`: 未查到、未查询、blocked、timeout、超窗的关键证据。

边界：

- 用户反馈账号被盗只能作为 `user_claim` / weak signal。
- 违规内容发布只能证明违规发生，不能证明被盗。
- 钓鱼页访问、OAuth 授权、前端行为、token 链路、发布审计如果未实际查到，必须写入 `missing_evidence`，不得写“已确认”。
- 发布设备与日常设备不一致通常是 medium evidence，需要登录、设备、行为或发布审计补证；不能单独强判盗号。
- 每条 strong / medium / weak / counter evidence 都必须带 `evidence_type` 和 `strength`。

单案 evidence card 必须包含：

- `conclusion`
- `confidence`
- `strong_evidence`
- `medium_evidence`
- `weak_evidence`
- `counter_evidence`
- `missing_evidence`
- `completed_sources`
- `blocked_or_timeout_sources`
- `source_quality`
- `next_action`

平台 blocked、timeout、browser loop 时，输出 partial evidence card，不裸 timeout。

## 5.1 ATO 单案 source checkpoint 与 deadline

明确 `user_id` 的 ATO 单案允许进入 `single_entity_execution_mode` 并查询只读平台，但必须按 source 编排，不能让后续高耗时 source 吞掉已完成证据。

### 5.0A ATO 单案 suspicious anchor-first

单 user_id 裸问“是不是被盗了 / 是否 ATO”时，first step 必须是 `suspicious_anchor_discovery`。不能在未完成锚点发现前，直接给“证据不足 / 倾向排除 / 不能确认”的松散结论。

默认主动寻找这些锚点：

- `recent_login_anchor`
- `web_login_anchor`
- `scan_or_oauth_anchor`
- `token_or_session_anchor`
- `password_reset_or_account_protection_anchor`
- `abnormal_publish_anchor`
- `live_anchor`
- `comment_or_dm_anchor`
- `profile_change_anchor`
- `four_items_anchor`
- `strategy_hit_anchor`

每个 anchor 至少尝试提取：动作、时间、候选 device_id、机型、系统 / 版本、app 版本、UA、IP / 省市 / ASN、登录端、登录方式、browser fingerprint、session_id / request_id / event_id、content_id / photo_id / live_id / comment_id、source_name、source_status 和 source_quality。

如果未找到 anchor，用户正文写“未完成可疑锚点发现”，再列关键缺口；不得泛化成“证据不足，所以无法判断”。

ATO suspicious source priority：

- P0 登录 / 控制链路：统一登录日志、离线 Hive 登录 registry 表、成功/失败登录、resetPwd / 改密、refreshToken / token issued、kick out / 保护账号、登录端、登录方式、设备、IP、UA、系统、机型、app 版本、browser fingerprint。
- P0 条件内容 / 行为链路：发视频、直播、评论、私信、资料修改、四项信息、发布来源、发布设备、发布 IP / UA、photo_id / live_id / comment_id、内容发布时间、内容命中策略 / 审核 / 导流原因。
- 辅助 source：Track、Weapon、RCP。Track 有活跃不能证明本人；Weapon 只做候选设备关系和设备风险补证；RCP / 策略命中只做行为风险 / 策略旁证。

每个 source 查询结束后必须立即记录 checkpoint：

- `source_name`
- `source_type`
- `source_status`: completed / no_data / blocked / auth_failed / timeout / parse_error / skipped
- `evidence_summary`
- `evidence_time_range`
- `source_quality`
- `raw_reference_safe_id`
- `collected_at`
- `failure_reason`
- `next_source_decision`

source 优先级：

- P0：统一登录日志、档案中心 `archives_user_profile` / `archives_user_analysis`、Weapon graphData、用户明确问策略命中时的天师策略命中摘要。
- P1：Weapon riskData（已解析出可疑 deviceId 后）、track-analysis stats-first、设备 SDK 深层补证。
- P2：RCP browser、档案中心 browser recoverable_preflight、track-analysis SPA 明细。

Track-analysis low-cost补证：

- 当登录日志、Hive、Weapon 或档案中心发现异常手机端设备、非历史设备、新设备登录、扫码后新设备、设备风险标签或策略命中时，默认触发 `track_analysis_activity_profile_api_direct` 作为低成本实时补证。
- 优先检查登录成功日、扫码日、设备切换日、策略命中日的 `getUseDuration`。
- 若后端登录 / 扫码 / 异常设备登录 / 策略命中存在，但对应 userId 或 deviceId 当天前端 duration=0 或无活跃，标记 `front_backend_activity_mismatch`。
- 该信号是协议上号、token/session 使用、非真实客户端行为的中高价值线索，但不能单独定性 ATO；必须与登录链路、设备风险、策略命中、发布 / 行为链路交叉验证。

规则：

- completed source 不得因后续 source timeout / blocked / parse_error 丢失。
- no_data 也算 completed source，但必须标 `no_data_not_risk_exclusion`。
- P0 source completed 后，已具备输出 partial evidence card 的最低条件。
- 默认总预算 180s；任一 P0/P1 source completed 后，在 120s 或 150s checkpoint 应停止扩展 P2 browser source 并输出 partial evidence card。
- P2 browser source 不得阻塞 P0/P1 已完成 evidence 输出。
- execution 开始时先写 observation skeleton；最终 timeout 也必须写 partial / timeout observation。

### 5.1A Browser-Backed Fixed Actions v1 账号安全编排

browser-backed fixed actions v1 已进入 Dennis 母体路由收口，但仍是显式 source plan，不是默认 runtime routing。

裸问表达收敛：

- ATO / 导流 / 扩散类裸问优先按“控制权变化 -> 异常行为闭环 -> 扩散/策略佐证”组织回答。
- 不把回答写成 action 说明书；action 名只作为 source_plan 锚点，正文先讲业务证据要解决什么问题。
- ATO 先看登录 / token / 新设备 / 验证等控制权变化，再看改密、发布、关注、导流等后置行为闭环，最后才看同设备扩散、Track 活跃与数据可用性、策略命中等佐证。
- 导流 / 异常发布先看内容动作与承接链路，再看账号状态和发布前后操作，不因单个 source no_data 排除风险。
- 同设备 / 关联账号只放在扩散或佐证层，不直接写团伙结论。

ATO / 登录异常推荐顺序：

1. `login_logs_search`
2. `archives_user_profile`
3. `archives_user_analysis`
4. `track_analysis_check_data_ready`

controlled parallel 编排口径：

- ATO 单案 source plan 不再只表达线性顺序，必须表达 `execution_group`、`depends_on`、`timeout_class`、`failure_policy`、`source_priority` 和 `expected_observation`。
- ATO 单案 first step 是 `suspicious_anchor_discovery`，之后才进入登录链路、内容动作链路、候选控制端提取、设备身份一致性和历史基线比较。
- `login_logs_search`、`archives_user_profile`、`track_analysis_check_data_ready` 可作为 `independent_parallel` 组并行执行；三者分别覆盖登录侧、账号基线和 Track 数据可用性 / provenance。
- `archives_user_analysis` 作为档案中心后续行为闭环 source，默认在 `archives_user_profile` 后走 `auth_sensitive_serial`；大 pageSize 或大响应时按 `large_response` timeout 处理，输出 partial 不等于完整时间线。
- 合并时 `completed` / `no_data` / `partial` / `auth_failed` / `blocked` / `timeout` / `parse_error` 必须进入 `source_quality_matrix`；completed / partial source 进入 `evidence_card_inputs`，失败或依赖缺口进入 `missing_evidence`。
- 单 source timeout / auth_failed 不阻塞其他 source 的 partial answer；`no_data` / `partial` / `timeout` 不能作为排除 ATO 或低风险反证。

device_identity_consistency：

- 风险设备判断不能等同于 device_id 判断。
- 对每个候选设备 / session，必须比较 device_id 是否历史常用、首次出现时间、近 30/90/180 天出现天数、机型、系统 / 版本、app 版本、UA、browser fingerprint、IP / 省市 / ASN、登录端和登录方式。
- 如果 device_id 历史常用，但机型 / 系统 / UA / IP / 登录端 / 登录方式异常，不得输出“常用设备，风险较低”。应输出：“device_id 看似常用，但设备身份变量不一致，存在伪装常用设备或 session/token 接管嫌疑。”
- 风险标签：`device_identity_inconsistency`、`possible_device_id_spoofing`、`common_device_id_but_abnormal_fingerprint`、`common_device_id_not_sufficient_to_exclude_ato`。

档案中心规则：

- 档案中心是 ATO / 登录异常 / 黑产详情分析的关键证据项，用于补账号状态、改密 / 保护账号、发布、关注、资料变更等登录日志看不到的后置行为闭环。
- 档案中心不是失败即阻塞的硬必跑项。`auth_failed`、`no_data`、`partial_observation_available`、`timeout`、`blocked`、`parse_error` 进入 `source_quality` 和 `missing_evidence`，输出 partial evidence。
- 没有档案中心时，只能说“当前为登录侧或其他已完成 source 的部分观察”，不能只基于登录日志强判或排除 ATO。

解释边界：

- 登录日志 `no_data`、在线窗口不足、parse error、auth failed 都是 `source_quality`，不能排除 ATO。
- `archives_user_profile` 是账号画像底座，不单独定性。
- `archives_user_analysis` 是操作 / 风险日志时间线；大 pageSize 或大响应只能输出 `partial_observation_available` / `large_response_limited`，建议缩窗、降低 pageSize 或分页。
- 当前 v1 表达优先写 `track_analysis_check_data_ready / Track 活跃与数据可用性`；它是 readiness / provenance，不是风险结论，也不能替代前端活跃画像或登录链路证据。
- 若引用历史 `track_analysis_summary` / Track summary 能力，只写成泛化的 Track 活跃画像能力描述，不混成当前 v1 的 action 名。

异常发布 / 色导 / 内容承接：

- 使用 `archives_photo_search -> archives_user_profile -> archives_user_analysis`。
- 这类场景中档案中心更接近必查 source，但仍不因为 `auth_failed` / `timeout` / `blocked` 中断输出；缺口进入 `missing_evidence`。
- `archives_photo_search=no_data` 只表示当前 user/window/source 条件下没有返回记录，不能排除异常发布、内容承接或发布链路风险。

账号扩散 / 同设备：

- 使用 `archives_related_users -> archives_user_profile/login_logs_search/track_analysis_check_data_ready`。
- 关联用户只是扩散线索，不能直接输出团伙结论；必须有登录、设备、行为、策略或发布链路交叉证据。
- private message、资料四件套 / 过往四项、related_devices 等未稳定 live 的 source 不作为默认已验证 source；只能写“如已有稳定接口或用户补充线索，再进一步查看”。

RCP 归因与策略治理：

- 事件归因使用 `rcp_event_detail -> rcp_event_feature_list`。
- `rcp_event_feature_list=partial_observation_available` 时只允许做 feature-group 摘要。
- 策略资产 / 策略树解释使用 `rcp_policy_tree_lookup`；它不是 event hit path，不证明单案命中。
- 策略命中、策略树、事件详情、feature list 和最终风险判断必须分层，策略命中不能单独定性 ATO / 作弊。

字段分层：

- `user_id`、`device_id`、`ip`、`event_id`、`strategy_id`、`photo_id`、`policyCode`、`policyTreeCode` 是风控实体，可在内部研判和 source chaining 保留。
- cookie/token/session/header/password、完整手机号、身份证、姓名、详细地址严禁输出或保存。

输出元数据分级：

- 默认用户回答不展示完整 `routing_metadata` YAML，只给自然语言执行状态摘要。
- 执行状态摘要必须说明：本轮是否查平台、是否调用 DataAgent/Hive、关键 source_quality 边界、缺失字段和下一步。
- boundary flag 默认翻译成用户可读边界，例如 no_data 不反证、partial 可用但不完整、auth_failed 是认证状态、同设备不是团伙结论。
- 只有用户明确要求 debug / `routing_metadata` / run log / YAML / 原始执行元数据，或内部 run log / regression 场景，才输出完整 `routing_metadata`。

## 5.2 ATO 小批量客诉执行与登录日志边界

2-9 个 `user_id` 的 ATO 客诉小批量默认进入 `small_batch_execution_with_checkpoint`，不是纯 plan-only，也不是 10+ 的 batch clustering。

执行规则：

- 允许逐个查 P0 source，优先统一登录日志。
- 只对异常用户补 P1 source：Weapon、天师策略命中、设备 SDK、档案中心画像等。
- 默认不进入 P2 browser source。
- 每个 user/source 独立 checkpoint。
- 单用户 auth_failed / timeout / blocked / parse_error 不得导致整体无输出。

统一登录日志 source boundary：

- 在线 API 约 7 天可靠窗口。
- admin / user-center-workbench 主要覆盖 APP 登录、refresh token、密码验证等登录侧行为，不能覆盖完整 WEB / H5 / PC / token / OAuth / 扫码控制链。
- 客诉时间不在在线窗口内时，必须标 `login_log_window_incomplete` 与 `source_time_range_gap`。
- APP 登录日志 no_data、单 DID、IP 稳定，只能写“登录日志侧可见窗口内未见强异常，ATO 证据不足”。
- 不得仅凭 APP 登录日志输出“低风险 / 无风险 / 排除 ATO”。
- 扫码 / OAuth / 地推欺诈 / 陌生链接诱导 / 发布违规 / 好友删除类客诉，必须标 `app_login_only_source_gap`、`missing_oauth_or_scan_chain`、`missing_publish_audit`、`missing_device_sdk`、`missing_strategy_hit`。
- 当风险动作是 WEB 登录后发导流视频、评论、直播、私信或资料修改，但实时登录源只覆盖 APP 或窗口不完整，必须标 `admin_app_log_only_gap`、`web_control_chain_missing`、`offline_hive_required`，并在用户正文证据缺口 / 下一步补证中强提醒 Hive 长周期补证。
- 不允许输出“实时源无异常，所以倾向不是盗号”，除非登录链路、内容动作链路、设备身份一致性和历史基线均已闭合。

## 6. ATO 离线 Hive 数据源运行态规则

在线统一登录日志只按近 7 天可靠窗口处理。历史 ATO / 盗号 case、超窗 case、批量 ATO case 不能把在线 no_data / 超窗 no_data 写成“无登录异常”或“无 ATO 风险”反证。

必须标记：

- `login_log_window_incomplete`
- `admin_app_log_only_gap`
- `web_control_chain_missing`
- `offline_hive_required`
- `hive_required_hint`
- `online_login_log_may_be_false_negative`

ATO 实时源不完整时，Hive 不是“可选增强”，而是定性闭环所需的关键补证；但调用 Hive 必须用户逐次明确授权。用户正文推荐表达：

```text
当前实时源无法定性。统一登录日志存在窗口限制，admin 侧主要覆盖 APP 日志，不能覆盖完整 WEB/H5/PC/token/OAuth 控制链。若要判断是否 ATO，需要补 Hive 长周期登录日志和发布动作链路。
```

触发强提醒的典型条件：

- 统一登录日志超过在线可靠窗口，或异常时间不在当前可见窗口内。
- admin 侧仅有 APP 日志，而风险动作来自 WEB / H5 / PC 或 token / OAuth / 扫码控制链。
- 风险动作是 WEB 登录后发导流视频、评论、直播、私信或资料修改。
- 在线登录日志 no_data、`response_too_large`、wrapper mismatch、`source_contract_gap`。
- 批量 ATO 中部分账号存在 WEB 非可信登录，但实时登录 / 控制源覆盖不足。

### 6.1 选表规则

| 用户问题 | runtime 选表 | 关键约束 |
|---|---|---|
| 有没有异设备成功登录 / 成功登录轨迹 | `ks_rc_bs.ks_account_login_basic_info` | 成功登录专用，9999 天，全量历史；只查成功登录。 |
| 是否被撞库 / 登录失败 / 暴力破解 | `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info` | 表名必须是 `orign`；`p_action_type='login'`；`finalloginresult=1` 成功，其他失败，null 不确定。 |
| 有没有改密 / resetPwd | `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info` | `p_action_type='resetPwd'`。 |
| Web/H5 端风控拦截 | `ks_rc_arch.antispam_feature_map_default_partitioned` | 生命周期 30 天；必须限制 `p_date + p_hourmin + p_action_type`。 |
| App 发布 / 登录 / 互动 / 协议风险命中 | `ks_raw_log_v2.antispam_feature_map_partitioned` | 生命周期 50 天；必须限制 `p_date + p_hourmin + p_action_type`；禁止全表扫描。 |

### 6.2 标准输出

如果在线数据缺失或窗口不足，不能只说“建议补充登录日志”，必须输出 Hive query plan：

```yaml
query_goal:
selected_table:
reason_for_table_selection:
partition_filters:
entity_filters:
key_fields:
expected_signal:
risk_if_missing:
fallback_table:
no_data_interpretation:
```

示例边界：

- `ks_account_login_basic_info` 无数据，只能说明该日期分区未发现成功登录，不代表没有失败登录、未走完流程或改密。
- `dwd_risk_usr_accnt_login_orign_info` 中 `finalloginresult is null` 是流程未完成 / 状态不确定，不得简单写成失败。
- Web RCP 超过 30 天、App RCP 超过 50 天时，必须标记 `source_gap`，不得作为无风险反证。
- DataAgent 只作为 Hive / 数仓取数分析能力，不是万能风控执行器。

在线登录日志 wrapper 边界：

- `response_too_large` 只能说明 wrapper 无法解析 / 传输，不是“登录很多”，也不是 completed 登录证据。
- 人工 UI 无数据但 wrapper 返回 `response_too_large` 时，标记 `wrapper_response_mismatch`、`source_contract_gap`、`actual_ui_no_data_unverified_by_wrapper`、`login_log_evidence_unusable`。
- 有 anchor_time 时，优先缩到前后 2-6 小时补查；无 anchor_time 时，先做 `suspicious_anchor_discovery`，不要盲目扩大窗口。
- 在线窗口不足、wrapper 失败或 UI/wrapper 不一致时，生成基于 `computer_use_poc/batch_risk_clustering/account_security_hive_source_registry_v1.md` 的 Hive query plan；真实 DataAgent/Hive 调用仍需用户逐次授权。
