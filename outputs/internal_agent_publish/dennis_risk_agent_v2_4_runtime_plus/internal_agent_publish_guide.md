# Dennis Risk Agent v2.4 Runtime Plus Internal Publish Guide

## 1. Agent 名称建议

建议名称：
- `Dennis Risk Agent`
- `Dennis 风控专家`
- `Dennis Risk Agent v2.4 Runtime Plus`

不建议把名称写成单场景专用，例如 `ATO Agent`，因为当前定位是通用业务风控专家，ATO 只是第一个深度样板。

## 2. Agent 定位

Dennis Risk Agent 是通用业务风控专家 Agent。

- ATO 是深度完全体样板。
- 非 ATO 默认走 runtime summary。
- 默认不调用 DataAgent。
- 只有用户明确要求查数 / 拉样本 / 看日志 / 看画像 / 验证数据时，才生成 DataAgent / Hive 取证请求。
- DataAgent 仅定位为 Hive / 公司数仓取数分析能力，不是全能数据底座。
- v2.4.1 将默认常驻进一步收紧：startup checklist 建议仅在初始化 / 配置期使用，不建议每轮常驻。

## 3. 默认 System Prompt 装载建议

建议默认装载：

1. 总控 system prompt / working guide / routing rules。
2. `dennis_risk_agent_v2_4_runtime_plus_manifest_v1.md`
3. `scenario_intent_router_contract_v1.md` 摘要。
4. `scenario_workflow_contract_v1.md` 摘要。
5. `scenario_response_contract_v1.md` 摘要。

不要默认把所有 deep skill 全量注入。
不要默认把 `dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md` 放到每轮常驻；它更适合初始化 / 配置期检查。
`dataagent_query_suggestion_contract_v1.md` 是“查询建议格式规则”，不是 DataAgent 调用器；只有用户明确要求“查数建议 / query intent / Hive 取证路径”时才加载。

## 4. Knowledge / Skill 文件装载顺序

### 4.1 ATO 命中时

先识别 ATO / 账号安全 / 申诉 / 登录异常 / 批量 case / 账号被盗，再加载 ATO 完全体：

- `account_security_expert_skill.md`
- `dataagent_markdown_response_parser_v1.md`
- `query_intent_schema_v2.md`
- `data_join_paths_v1.md`
- `dataagent_result_interpretation_rules_v1.md`
- `dataagent_conclusion_thresholds_v1.md`
- `dataagent_provider_boundary_overlay_v1.md`
- `dataagent_timeout_policy_review_v1.md`
- `ato_short_question_entrypoint_adaptation_v1.md`
- `ato_runtime_slimming_plan_v1.md`
- `ato_runtime_slim_manifest_v1.md`
- `dennis_dataagent_poc_auto_sync_loop_result_v1.md`

### 4.2 非 ATO 命中时

默认只加载对应 runtime summary：

- 反爬 → `anti_crawler_runtime_summary_v1.md`
- 协议 → `protocol_attack_runtime_summary_v1.md`
- 群控 → `group_control_runtime_summary_v1.md`
- 破解包 → `cracked_app_runtime_summary_v1.md`
- 真人众包 → `real_user_crowdsourcing_runtime_summary_v1.md`
- 活动反作弊 → `activity_anti_cheating_runtime_summary_v1.md`
- 导流截流 → `traffic_diversion_runtime_summary_v1.md`
- 流量反作弊 → `traffic_anti_cheating_runtime_summary_v1.md`

## 5. ATO 场景触发规则

用户问题涉及以下关键词时，优先判断 ATO：

- 账号被盗 / 账号接管 / ATO。
- 申诉 / 解封 / 可信度判断。
- 扫码 / OAuth / 授权登录 / 异步登录。
- 登录异常 / token / session / 账号控制权变化。
- 批量 case / 批量盗号 / 批量申诉。

命中 ATO 后，应进入 ATO 完全体，不要只停留在 runtime summary。

## 6. 非 ATO runtime summary 触发规则

用户只问以下类型时，默认只加载 runtime summary：

- 怎么看。
- 是不是。
- 怎么防。
- 难点在哪。
- 怎么区分。

这些问题默认先给：

- 判断框架。
- 攻击路径。
- 证据优先级。
- 误判边界。
- 治理建议。
- 下一步动作。

## 7. DataAgent / Hive 触发边界

只有用户明确要求以下内容时，才进入 DataAgent：

- 查数。
- 拉样本。
- 看日志。
- 看画像。
- 验证数据。
- 生成查询问题。

高成本查询必须用户确认。
DataAgent 仅代表 Hive / 公司数仓取数分析能力。

## 8. 必须常驻的文件

建议常驻：

- 总控 system prompt / working guide / routing rules
- `dennis_risk_agent_v2_4_runtime_plus_manifest_v1.md`
- `scenario_intent_router_contract_v1.md`
- `scenario_response_contract_v1.md`
- `dataagent_provider_boundary_overlay_v1.md`
- `dataagent_timeout_policy_review_v1.md`

## 9. 按需召回的文件

按需读取：

- `dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md`（初始化 / 配置期优先，不建议每轮常驻）
- `dataagent_query_suggestion_contract_v1.md`（查询建议格式规则，高优先级按需召回）
- ATO 完全体 Skill 与解释文件
- 非 ATO runtime summary
- 深度 Skill 全文
- interpretation / threshold / parser / join path 细则
- POC / regression / walkthrough 结果

## 10. 不要默认全量注入的文件

不建议默认注入：

- 全量 review
- 全量 eval
- 全量 history
- walkthrough 全文
- 过往大批量 regression 结果

## 11. 测试问题与验收标准

建议先测：

1. ATO 短问是否进入 ATO 完全体。
2. 反爬 / 协议 / 群控 / 活动反作弊是否命中对应 runtime summary。
3. 默认是否不误调 DataAgent。
4. 用户明确要求查数时是否能转入 DataAgent 取证方向。
5. 是否能保持短答优先、本质优先、证据优先。

验收标准：

- 路由正确。
- 不表面化。
- 不误调 DataAgent。
- 不削弱 ATO 完全体。
- 不把非 ATO 推成深度闭环。
- v2.4.1 加载优化后，startup checklist 不再每轮常驻。
- 首次生成 DataAgent 查询建议时，必须符合 `dataagent_query_suggestion_contract_v1.md` 的标准结构。
