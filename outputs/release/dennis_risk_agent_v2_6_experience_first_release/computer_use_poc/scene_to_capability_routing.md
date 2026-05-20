# Scene to Capability Routing

本文是体验优先的能力路由说明。用户仍按业务问题提问，系统内部再按 capability routing 选择只读手脚、实体解析或回答模板。

原则：

- 先满足用户体感目标，再选择 capability。
- 不为展示能力而过度查数、过度调平台。
- 不新增真实平台手脚。
- 不把 observation 包装成最终风险定性。
- 新手脚后续必须说明服务哪个体验 Case，或新增哪个体验 Case。

## 1. ATO 用户研判

用户体感目标：

- 用户问“是不是被盗号”，希望拿到证据化判断、反证和下一步，而不是平台字段列表。

Expected capabilities：

- unified_login_log_check
- archives_center_profile_check
- device_sdk_check_if_device_id_available
- tianshi_strategy_hit_check_if_strategy_hit_question_relevant

不应调用：

- 不默认 DataAgent / Hive。
- 不默认批量拉全量。
- 不自动处罚。

输出体验：

- 一句话判断 + 支持证据 + 反证 / 降级因素 + 缺口 + 下一步。

## 2. 登录失败 / 被验证原因

用户体感目标：

- 用户希望知道“为什么失败 / 为什么验证”，需要直接原因和时间线。

Expected capabilities：

- unified_login_log_check
- tianshi_strategy_hit_check
- tianshi_eventlist_api_read_if_specific_request_detail_needed
- archives_center_profile_check_as_context

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

不应调用：

- 不默认统一登录日志。
- 不默认档案中心。
- 不调用 location。

输出体验：

- 设备侧结论 + 强/中/弱设备证据 + 边界 + 下一步。
- 如果输入不完整，先说明缺少 deviceId 或正在做 user_to_device，不要假装已经完成设备补证。

## 4. 用户关联设备查询

用户体感目标：

- 用户输入 userId，想知道有哪些关联设备，或者后续要查设备风险。

Expected capabilities：

- user_to_device_entity_resolution
- weapon_graphData
- archives_user_analysis_recent_devices_as_supplemental_ranking

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

不应调用：

- 不把命中写成最终作弊。
- 不把无命中写成无风险。
- 不默认 DataAgent / Hive。

输出体验：

- 策略命中解释 + riskDecision 边界 + 能说明什么 / 不能说明什么 + 最小补证动作。
