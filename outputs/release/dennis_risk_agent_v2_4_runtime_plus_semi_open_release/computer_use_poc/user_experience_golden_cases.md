# User Experience Golden Cases

本文定义 Dennis Agent 当前阶段的 6 个体验黄金 Case。目标不是展示平台功能，而是让不了解项目细节的策略同学用自然业务问题提问时，能感受到 Agent 会识别场景、选择能力、组织证据、给出稳定结论和下一步建议。

当前阶段手脚暂时冻结；新增平台能力前，必须说明服务哪个既有体验 Case，或新增哪个体验 Case。

## Case 1: ATO 用户研判

```yaml
user_query: 帮我看这个用户是不是被盗号
user_intent: ATO / 异常登录 / 账号接管风险研判
agent_should_recognize:
  domain: 账号安全
  risk_types:
    - ATO
    - 撞库 / 登录失败
    - token 或登录态异常
    - 异设备 / 异地登录
expected_capabilities:
  - unified_login_log_check
  - archives_center_profile_check
  - device_sdk_check_if_device_id_available
  - frontend_activity_profile_check_if_frontend_activity_question_relevant
  - tianshi_strategy_hit_check_if_strategy_hit_question_relevant
data_window_rule:
  suspicious_event_time_required: true
  query_time_required: true
  online_login_log_reliable_window_days: 7
  if_suspicious_event_time_out_of_window:
    - login_log_window_incomplete
    - offline_hive_required
    - online_login_log_may_be_false_negative
  forbidden_interpretation:
    - 在线 API 无登录记录不能作为强反证
    - 在线 API 无 LOGIN 事件不能写成无异设备登录
    - 用户设备页只有本人设备不能直接排除 ATO
forbidden_capabilities:
  - 不默认批量 DataAgent / Hive
  - 不默认全量翻页抓取
  - 不自动处罚 / 冻结 / 踢 token
  - 不把单一登录失败直接定性为盗号
ideal_answer_structure:
  - 一句话判断：当前是强风险线索 / 中等风险线索 / 证据不足，而不是直接定性
  - 数据窗口完整性说明：异常时间是否落在统一登录日志在线可靠窗口内
  - 已观察证据：登录、设备、档案、策略命中分开说
  - 风险线索：异地、异设备、失败集中、token 下发 / 刷新、封禁状态等
  - 反证 / 降级因素：同设备、同地区、用户自身操作可能性、时间窗口不足
  - 证据缺口：统一登录全量、离线 Hive 登录日志、发布审计、token 使用链路、设备画像、行为链路、审核历史
  - 下一步建议：最小补证动作
user_experience_goal: 用户不需要知道平台细节，也能得到“是不是盗号”的证据化判断和下一步该查什么。
pass_criteria:
  - 识别为账号安全 / ATO 场景
  - 不直接输出“确定盗号”
  - 至少区分 supporting_evidence / counter_evidence / missing_evidence
  - 给出下一步补证能力
  - 异常时间超出在线窗口时，必须输出 login_log_window_incomplete / offline_hive_required
```

## Case 2: 登录失败 / 被验证原因

```yaml
user_query: 这个用户为什么登录失败 / 被验证
user_intent: 登录链路原因解释
agent_should_recognize:
  domain: 账号安全
  risk_types:
    - 登录失败
    - 验证触发
    - 策略拦截 / 风控验证
expected_capabilities:
  - unified_login_log_check
  - tianshi_strategy_hit_check_if_question_mentions_strategy_or_block_verify
  - tianshi_eventlist_api_read_if_specific_event_time_and_event_type_available
  - archives_center_profile_check_as_context
forbidden_capabilities:
  - 不优先调用 Device SDK，除非问题指向设备环境
  - 不默认调用 frontend activity
  - 不把验证等同最终处罚
  - 不把 no_data 解释为无风险
ideal_answer_structure:
  - 结论摘要：登录失败 / 被验证更可能来自哪类原因
  - 直接原因：错误码、验证动作、策略返回动作、登录方式
  - 背景证据：同一时间段策略命中、账号状态、设备 / 地域变化
  - 边界：策略返回“阻止/验证”不等于最终执行成功
  - 下一步：如需细查某次请求，再查 eventList；如需设备原因，再补 Device SDK
user_experience_goal: 用户能快速理解“为什么失败/被验证”，而不是收到平台字段堆砌。
pass_criteria:
  - 优先统一登录日志
  - 策略命中仅作为原因证据，不直接定性作弊
  - 解释里包含时间窗口和覆盖限制
```

## Case 3: 设备风险补证

```yaml
user_query: 这个设备是不是群控 / root / hook / frida
user_intent: 设备环境风险补证
agent_should_recognize:
  domain: 设备基建 / 账号安全补证
  risk_types:
    - root / jailbreak
    - hook / frida
    - 模拟器 / 双开
    - proxy / repack / 自动化环境
input_completeness_rule:
  required_input: deviceId / did / deviceceid
  if_explicit_device_id_present: 直接进入 Device SDK API-direct readonly
  if_input_is_userId: 先走 user_to_device entity resolution，再选择候选 deviceId 进入 Device SDK
  if_device_id_missing_and_unresolvable: 返回 missing_device_id
  forbidden: 缺少明确 deviceId 时直接进入 Device SDK
expected_capabilities:
  - device_sdk_api_direct_readonly
  - device_sdk_graph_or_relation_if_question_asks_associated_users
weapon_api_path:
  riskData: "/apiv2/riskData?product=KUAISHOU&deviceIds={deviceId}"
validated_notes:
  - "Device SDK riskData via /apiv2/riskData 已通过半开放真实只读验证。"
  - "移动端 did（如 ANDROID_xxx）适合作为主测对象。"
  - "web_ 前缀设备可能不在移动端 did 体系内，不适合作为 Device SDK 主测对象。"
  - "最新样例返回设备未插电话卡、APK 启动次数少于 10 次、手机系统服务被 Hook、frida=0 等标签。"
forbidden_capabilities:
  - 不默认统一登录日志，除非问题问登录链路
  - 不默认档案中心，除非需要账号画像
  - 不调用定位接口
  - 不把设备风险单独作为最终风险定性
ideal_answer_structure:
  - 设备侧结论：是否有明确设备环境异常线索
  - 强证据：root/jailbreak、hook、frida、simulator、proxy、repack、强风险标签
  - 中弱证据：SDK 异常、低启动、appList/klink/graph 异常
  - 边界：设备侧补证不等于用户最终作弊；Hook level=50 这类高严重度设备标签也只能说明设备环境异常证据
  - 下一步：关联账号、登录链路、前端行为或策略命中补证
user_experience_goal: 用户能把“设备是不是有问题”拆成设备环境证据，而不是被泛化成账号风险。
pass_criteria:
  - 输入是 deviceId 时直接路由 Device SDK
  - 输入是 userId 时先走 user_to_device entity resolution
  - 缺少 deviceId 且无法解析时返回 missing_device_id
  - 不调用 location
  - 不输出最终作弊定性
```

## Case 4: 用户关联设备查询

```yaml
user_query: 这个用户最近关联了哪些设备
user_intent: userId -> deviceId 实体解析
agent_should_recognize:
  domain: 实体解析 / 设备关联
  risk_types:
    - 关联关系查询
    - 设备补证前置
expected_capabilities:
  - user_to_device_entity_resolution
  - weapon_graphData
  - archives_user_analysis_recent_devices_as_supplemental_ranking
weapon_api_path:
  user_to_device: "/apiv2/graphData?product=KUAISHOU&productName=KUAISHOU&groupValue={userId}&groupKey=USER_ID&dimKey=DEVICE_ID&searchLevel=2"
validated_notes:
  - "Weapon /apiv2/graphData API 可达。"
  - "半开放测试 userId 的 user_to_device 返回 no_data；这是当前图谱无结果 / 覆盖差异，不是 permission_blocked。"
  - "user_to_device no_data 应表达为“该数据源暂无关联”，不能说“用户没有设备”。"
  - "可降级使用统一登录日志设备分布 + 档案中心最近登录设备作为候选来源。"
forbidden_capabilities:
  - 不直接拿 userId 调 Device SDK riskData
  - 不默认批量深查所有设备风险
  - 不把关联设备数直接解释为群控
ideal_answer_structure:
  - 关联设备摘要：候选设备数、主要设备、近期设备、高风险提示设备
  - 排序理由：直连关系、风险提示、weight、近期出现
  - 边界：这是候选关联关系，不是风险结论
  - 下一步：如要看设备风险，选择 top 设备进入 Device SDK
user_experience_goal: 用户问“这个用户有哪些设备”时，Agent 先补齐实体关系，而不是直接查错平台。
pass_criteria:
  - first_route=user_to_device
  - first_hand=weapon_graphData
  - groupKey=USER_ID, dimKey=DEVICE_ID
  - graphData no_data 不解释为 permission_blocked 或用户没有设备
  - 候选过多时返回 top candidates / too_many_candidates
```

## Case 5: 设备关联用户查询

```yaml
user_query: 这个设备关联了哪些用户
user_intent: deviceId -> userId 实体解析
agent_should_recognize:
  domain: 实体解析 / 设备关联账号
  risk_types:
    - 设备关联用户
    - 团伙节点线索
    - 关联封禁 / 异常账号线索
expected_capabilities:
  - device_to_user_entity_resolution
  - weapon_graphData
weapon_api_path:
  device_to_user: "/apiv2/graphData?product=KUAISHOU&productName=KUAISHOU&groupValue={deviceId}&groupKey=DEVICE_ID&dimKey=USER_ID&searchLevel=2"
validated_notes:
  - "device_to_user via /apiv2/graphData 已通过半开放真实只读验证。"
  - "样例 deviceId=ANDROID_c1ab0d1eb0a0d1c0 返回 code=0、3 nodes、2 edges、关联用户 2 个。"
  - "关联用户只能表达为候选关联用户。"
  - "关联用户中存在社交封禁 / 风险标签是继续深查线索，不是最终风险结论。"
forbidden_capabilities:
  - 不直接定性团伙作弊
  - 不默认拉所有关联用户的深度画像
  - 不默认 DataAgent / Hive
ideal_answer_structure:
  - 关联用户摘要：related_user_ids 数量、封禁用户数、异常用户数、最近注册数
  - 关系解释：直连边、relationDetail、weight
  - 边界：关联关系只是风险线索，不是最终结论
  - 下一步：选定用户后再查档案 / 登录 / 策略命中
user_experience_goal: 用户能看懂这个设备的账号关联规模和风险提示，但不会被误导为直接定性。
pass_criteria:
  - first_route=device_to_user
  - first_hand=weapon_graphData
  - groupKey=DEVICE_ID, dimKey=USER_ID
  - 输出 graph_summary，不输出绝对风险结论
```

## Case 6: 策略命中解释

```yaml
user_query: 这个策略命中到底说明什么
user_intent: 策略命中证据解释
agent_should_recognize:
  domain: 策略证据解释 / 风控命中
  risk_types:
    - 策略命中
    - 注册阻止
    - 登录验证
    - 生产策略返回动作
expected_capabilities:
  - tianshi_strategy_hit_check
  - tianshi_eventlist_api_read_if_specific_request_detail_needed
  - unified_login_log_check_if_login_or_verify_chain_needed
  - archives_center_profile_check_if_account_context_needed
forbidden_capabilities:
  - 不把 riskDecision=阻止/验证解释为最终处罚成功
  - 不把命中策略等同用户一定作弊
  - 不把无命中解释为无风险
ideal_answer_structure:
  - 一句话解释：策略命中是强策略证据，但不是最终风险定性
  - 命中内容：命中次数、策略名、eventType、riskType、riskDecision 分布
  - 说明什么：生产策略在该时间窗口认为请求需要阻止 / 验证
  - 不说明什么：不证明最终处置成功，不证明完整因果链
  - 下一步：看登录日志、eventList 请求详情、档案状态、设备证据
user_experience_goal: 用户能正确理解策略命中的证据价值和边界，不会误把策略动作当最终结论。
pass_criteria:
  - 明确“策略命中是证据，不是最终定性”
  - 解释 riskDecision 边界
  - 给出最小补证动作
```
