# Integration Quick Start

## 1. 默认加载

先加载：

1. `README.md`
2. `dennis_risk_agent_v2_4_runtime_plus_manifest_v1.md`

再按场景加载对应内容。

`dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md` 建议作为初始化 / 配置期文件使用，不建议每轮问答都常驻加载。
v2.4.1 的默认常驻已进一步收紧，不建议把 release note、route regression、smoke test 放到每轮运行态。

## 2. 用户问 ATO 怎么走

加载 ATO 完全体：

- `account_security_expert_skill.md`
- DataAgent parser / schema / join / interpretation / threshold
- DataAgent boundary / timeout
- ATO short question adaptation
- ATO runtime slim / POC 结果

然后按 ATO 路由、workflow、response contract 走。

## 3. 用户问非 ATO 怎么走

默认只加载对应 runtime summary，优先单一 summary；只有问题明确跨域时最多加载 2 个 summary：

- 反爬 → `anti_crawler_runtime_summary_v1.md`
- 协议 → `protocol_attack_runtime_summary_v1.md`
- 群控 → `group_control_runtime_summary_v1.md`
- 破解包 → `cracked_app_runtime_summary_v1.md`
- 真人众包 → `real_user_crowdsourcing_runtime_summary_v1.md`
- 活动反作弊 → `activity_anti_cheating_runtime_summary_v1.md`
- 导流截流 → `traffic_diversion_runtime_summary_v1.md`
- 流量反作弊 → `traffic_anti_cheating_runtime_summary_v1.md`

默认先给判断、证据拆解、取证方向和治理建议，不默认查数。

## 4. 用户明确要求查数时怎么走

如果用户明确说：

- 查数
- 拉样本
- 看日志
- 看画像
- 验证数据
- 生成查询问题

才进入 DataAgent 取证方向。

DataAgent 只定位为 Hive / 公司数仓取数分析能力。

如果用户要的是“查数建议 / query intent / Hive 取证路径”，先按 `dataagent_query_suggestion_contract_v1.md` 输出标准结构，再决定是否进入后续取数方向。
其中入参要分层表达：最小必要入参、建议补充入参、可选上下文；只要最小必要入参具备，建议补充入参或可选上下文缺失都不应阻断初步查询建议。
查询建议结构不等于可直接执行 SQL；执行前仍需 DataAgent / Hive 根据真实表名、权限、分区、join key 和数据口径转换。

## 5. 平台路由和取证知识库接入方式

`internal_risk_platforms/` 是平台路由和取证知识库 v1，用于帮助 Agent 判断应该查哪个平台、怎么看字段、怎么解释、查不到下一步去哪。

不建议全量注入。推荐按需读取顺序：

1. 平台路由索引：`internal_risk_platforms/00_platform_routing_index.md`
2. 对应平台卡：`01_archives_center_platform_card.md` 到 `06_user_behavior_trace_platform_card.md`
3. 跨平台链路：`internal_risk_platforms/90_cross_platform_investigation_paths.md`
4. 字段字典：`internal_risk_platforms/91_platform_field_dictionary.md`
5. 待确认项：`internal_risk_platforms/99_todo_unknown_fields.md`

`92_platform_routing_smoke_tests.md` 和 `93_platform_knowledge_quality_report.md` 只作为测试/质量资产，常规回答不加载。

DataAgent / Hive 仍只负责 Hive / 公司数仓取数分析，不替代内部在线平台、实时日志、策略平台和设备平台。

## 6. 哪些情况不要调 DataAgent

- 只是问“怎么看 / 是不是 / 怎么防”。
- 只是问方法论。
- 只是要边界判断。
- 只是要治理建议。
- 当前 summary 已能覆盖的问题。
- 只是要“查询建议格式”但没有明确要求生成查询问题时，也不要直接调用 DataAgent；先按 `dataagent_query_suggestion_contract_v1.md` 输出建议结构。

## 7. 高成本动作

以下情况必须用户确认：

- 长周期扩窗。
- 多表 join。
- 大样本回捞。
- 预计较慢的 Hive 查询。

正式接入前，可以先用 5 个 smoke test 问题验证路由是否按预期命中 ATO 完全体或对应 runtime summary。
v2.4.1 接入时，建议先确认 startup checklist 未被放入每轮常驻。
smoke test 通过只代表 internal publish 层最小格式与边界回归通过，仍需内部小范围试运行验证真实回答质量；非 ATO 不因此视为完全体能力。
