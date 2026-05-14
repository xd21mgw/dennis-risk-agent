# Config Mock Regression Cases v1

## 0. 目标

本文件用于测试 Data Agent configs 层是否能正确服务 `query_intent`：

- 是否选对数据域。
- 是否选对字段类型。
- 是否选择必要 join path。
- 是否识别数据质量风险。
- 是否在证据不足时降级。

当前阶段不调用真实 Data Agent，不编造真实表名、字段名、SQL、API 或真实结果。

## Case CONFIG-001：前端无日志疑似协议

用户问题：服务端有请求，前端无日志，是否协议？

期望配置：

- query_intent_type：`protocol_frontend_backend_join`
- required_data_domains：前端行为域、后端数据域、设备信息域、策略引擎域
- field_types_needed：user_id、device_id、frontend_event、backend_api、request_time、event_time、api_sequence、gateway_decision、sdk_status
- join_paths_needed：`frontend_backend_chain_join`、`request_device_environment_join`、`strategy_gateway_decision_join`
- quality_checks：前端日志延迟、埋点缺失、SDK 状态、join 口径

mock 返回：

- status：partial
- evidence_summary：后端请求存在，前端事件缺失
- missing_evidence：SDK 覆盖、官方版本对照、token/device/ip/ua 冲突

期望解释：

- 结论等级：证据不足
- 原因：只有前端缺失，不得直接判协议

## Case CONFIG-002：活动低质疑似黑产

用户问题：活动用户低留存、奖励领取多，是否羊毛党？

期望配置：

- query_intent_type：`activity_black_industry_or_low_quality_check`
- required_data_domains：活动信息域、用户信息域、设备信息域、风险画像域、关联网络域、策略引擎域
- field_types_needed：campaign_id、activity_participation、reward_status、withdraw_status、device_id、risk_label、user_group_id
- join_paths_needed：`activity_participation_device_reward_join`、`invite_relation_network_join`
- quality_checks：活动目标、活动规则、奖励口径、后验窗口

mock 返回：

- status：success
- evidence_summary：低留存、奖励领取多，无设备团组，无提现聚集
- counter_evidence：活动目标为拉新冷启动

期望解释：

- 结论等级：证据不足或活动低质
- 原因：低钱效和奖励多不能直接等同黑产

## Case CONFIG-003：渠道 CTIT 异常

用户问题：某渠道 CTIT 异常，是否点击注入？

期望配置：

- query_intent_type：`channel_attribution_hijacking_check`
- required_data_domains：渠道信息域、用户信息域、设备信息域、活动信息域
- field_types_needed：channel_id、media_source、click_time、activation_time、ctit、device_id、account_age、return_user_flag
- join_paths_needed：`channel_click_activation_user_join`、`channel_quality_aftereffect_join`
- quality_checks：预算变化、归因窗口、品牌活动、版本发布

mock 返回：

- status：success
- evidence_summary：CTIT 偏移，渠道上涨
- counter_evidence：同窗口预算调整和归因规则变化
- missing_evidence：设备/IP/UA 或点击模板

期望解释：

- 结论等级：证据不足
- 原因：CTIT 异常不能单独判渠道作弊，且存在业务变更反证

## Case CONFIG-004：token 泄露疑似账号接管

用户问题：账号敏感动作异常，怀疑 token 泄露。

期望配置：

- query_intent_type：`token_reuse_or_account_takeover_check`
- required_data_domains：用户信息域、设备信息域、后端数据域、风险画像域、策略引擎域
- field_types_needed：account_id、token_id、device_id、ip、ua、login_time、bind_change_time、password_change_time、strategy_hit、engine_decision
- join_paths_needed：`token_session_environment_join`、`account_lifecycle_device_join`
- quality_checks：正常换机、漫游、企业网络、多设备登录、SDK 升级

mock 返回：

- status：partial
- evidence_summary：token 新环境使用，后接敏感动作
- missing_evidence：可信设备确认、用户确认、企业网络/漫游反证

期望解释：

- 结论等级：高度疑似
- 原因：中强证据成组，但反证未排除，不能明确判断

## Case CONFIG-005：直播间用户被站外添加

用户问题：直播间用户被站外添加，是否导流截流？

期望配置：

- query_intent_type：`traffic_diversion_chain_check`
- required_data_domains：前端行为域、用户信息域、关联网络域、风险画像域、后端数据域
- field_types_needed：user_id、frontend_event、page_path、click_sequence、relation_group_id、risk_label
- join_paths_needed：`diversion_exposure_touch_offsite_join`
- quality_checks：正常社交、用户主动外联、授权运营触达、站外承接证据

mock 返回：

- status：success
- evidence_summary：评论入口暴露、搜索/关注/私信触达、部分站外承接语义、触达账号矩阵
- missing_evidence：站外收益链和更多投诉样本

期望解释：

- 结论等级：高度疑似
- 原因：导流主链路基本成立，但收益/投诉闭环不足

## Case CONFIG-006：批量 case 表象相似

用户问题：一批 case 都高频且低质，是否同一团伙？

期望配置：

- query_intent_type：`batch_case_commonality_check`
- required_data_domains：用户信息域、设备信息域、前端行为域、后端数据域、活动信息域、关联网络域
- field_types_needed：user_id、device_id、ip、ua、page_path、api_sequence、campaign_id、relation_group_id
- join_paths_needed：`batch_case_resource_reuse_join`、`batch_case_business_context_join`
- quality_checks：业务活动、实验、版本、口径变化、合法矩阵

mock 返回：

- status：success
- evidence_summary：同一活动窗口，行为路径相似
- counter_evidence：同一活动规则可解释路径相似，无资源复用、无收益聚集

期望解释：

- 批次结论：不同源同机制
- 原因：业务机制解释强于同源攻击解释

## 评分规则

- 选错数据域，最高 75。
- 未选择 join path，最高 80。
- 没有 quality_checks，最高 80。
- 写真实表名/字段名/API，最高 60。
- partial / failed / no_permission 未降级，最高 75。
- 只有单点异常却给强结论，最高 70。
- 能正确选择数据域、字段类型、join path、质量检查，并按证据降级，90+。
