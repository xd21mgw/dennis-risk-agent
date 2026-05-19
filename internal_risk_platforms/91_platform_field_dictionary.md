# 跨平台字段字典

## 1. 统一字段与口径差异

| 统一字段 | 常见平台字段名 | 含义 | 口径差异 | Agent 解释规则 |
|---|---|---|---|---|
| user_id | user_id, User ID, author_id | 用户唯一标识 | 视频 author_id 是内容作者；User ID 是登录日志主体 | 串联平台主锚点，但需确认主体角色 |
| device_id / did | device_id, deviceId, DID, did | 设备标识 | 档案中心/视频 meta/登录日志/设备平台字段名不同；DID 可能为空 | 需跨平台归一，空值不能解释为无设备 |
| phone_number | phone_number, 手机号 | 注册/绑定手机号 | 明文权限受限；可能脱敏 | 只能作为账号归属和关联线索 |
| ip | last_login_ip, user_ip_desc, network_ip, callerIp | IP 地址 | callerIp 多为服务内网；user_ip_desc 是用户侧 IP 描述 | 不同 IP 字段不能混用，先区分用户 IP 和服务 IP |
| timestamp | timestamp, 时间, audit_time, upload_time, log_time | 时间 | 秒级/毫秒级/页面展示时间不同 | 必须对齐时区和精度 |
| operation_type | 操作类型 | APP 端操作类型 | 主要来自档案中心用户分析页 | 仅说明 APP 端操作，不覆盖全端 |
| method | Method, method | 接口/方法名 | 用户登录统一日志和天狮/服务侧含义不同 | 需结合日志来源和 request 解释 |
| action | action, 操作结果 | 操作是否允许/拒绝 | 登录日志中可能为 allow/deny；档案中心可能为成功/失败 | deny 是被拒绝，不是无风险 |
| risk_label | risk_label, 风险标记, 标签 | 风险标签 | 设备风险标签、账号风险标签、策略风险标签口径不同 | 只能作为风险线索，不能单独强结论 |
| punish_status | punish_status, 当前负向, account_status | 当前处罚或账号状态 | 不同平台展示粒度不同 | 处罚状态是事实，风险原因需追溯 |
| mark_code | mark_code, markCode | 风控标注编码 | 需要字典解释 | 不应直接当自然语言结论 |
| strategy_detail | strategy_detail, 策略详情 | 策略命中摘要/明细 | RAP 可能是摘要；天狮是策略配置/归因 | 完整归因以天狮为准 |
| hit_policy | hit_policy, 命中策略 | 命中的策略 | 天狮归因核心字段 | 命中策略不是最终风控结论 |
| feature_value | feature_value, 特征值 | 策略命中特征取值 | 依赖 feature_expression 解释 | 必须结合条件表达式和事件口径 |

## 2. 平台字段映射

| 平台 | 账号锚点 | 设备锚点 | 时间字段 | 风险字段 | 行为字段 |
|---|---|---|---|---|---|
| 档案中心 | user_id, author_id | device_id, deviceId | last_login_time, audit_time, upload_time, timestamp | punish_status, punish_code, mark_code | operation_type, operation_url, operation_result |
| 风险运营中心 | user_id | device_info, related_accounts | 判罚时间、举报时间 | current_risk_status, strategy_detail, mark_code | 评论、搜索、社交数据 |
| 设备攻防基建平台 | user_id | device_id, deviceId | log_time, risk_time, app_install_time | risk_label, risk_level, apk_risk | appLaunchCount, app list |
| 用户登录统一日志 | User ID | DID | timestamp, start_time, end_time | tag, action | method, request, log_source |
| 天狮策略引擎 | user_id | 依事件而定 | event time, policy version time | hit_policy, policy_result | event_id, feature_value |
| 用户行为细查平台 | user_id | device_id | event_time | 无直接风险标签 | event_name, page_url, session_id |

## 3. 解释注意事项

- 同名字段跨平台不一定同口径。例如 `device_id` 可能来自登录、视频 meta、设备 SDK 或前端埋点。
- 策略名、风险标签、mark_code 都是风险线索，不是最终定性。
- 用户自述、人工备注、审核备注不能进入 strong evidence。
- IP 解释必须区分用户侧 IP、服务内网 IP、设备网络 IP。
- 时间字段必须确认时区、精度和数据延迟。

