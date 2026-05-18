# Dennis Risk Agent v2.4.2 DataAgent Query Suggestion Contract Regression Plan

## 1. 目的

验证 Dennis Risk Agent 在第一次生成查数建议时，是否能输出可被 DataAgent / Hive 使用的结构化查询建议，而不是只给维度清单或把建议写成结果。

## 2. 验收原则

- 不真实调用 DataAgent。
- 不虚构查询结果。
- 不输出强处置结论。
- 只验证查询建议格式是否合规。
- DataAgent 仍仅定位为 Hive / 公司数仓取数分析能力。

## 3. 正向触发案例

### Case 1: ATO / 协议上号查询建议

用户问题：
- 账号被盗了，怀疑协议上号，`user_id` 是 12345，时间窗口是昨晚 20:00 到今天 10:00，帮我看应该查什么。

预期：
- 触发 `dataagent_query_suggestion_contract_v1.md`
- 输出 10 段标准结构
- 给出 ATO 查询目标、必要入参、建议字段、强中弱证据、误判边界、预期输出结构
- 不假装已查数

### Case 2: 外部跟价 / 反爬资产泄露查询建议

用户问题：
- 外部站点一直能跟价我们商品，但内部没看到明显高频爬虫。帮我生成 DataAgent 查询建议，不要真的查。

预期：
- 触发 `dataagent_query_suggestion_contract_v1.md`
- 输出 10 段标准结构
- 给出反爬 / 资产保护查询目标、必要入参、建议字段、证据优先级、误判边界
- 不实际调用 DataAgent

## 4. 非触发案例

### Case 3: 只问判断，不问查数建议

用户问题：
- 这个是不是协议攻击？

预期：
- 不触发正式查询建议
- 只给判断框架、证据优先级、误判边界、治理建议

### Case 4: 只问证据，不要求查询建议

用户问题：
- 有哪些证据能看出来是不是群控？

预期：
- 不触发正式查询建议
- 只给证据框架和取证方向

## 5. 关键验收标准

1. 触发场景下必须输出标准结构，不得只给维度清单。
2. 查询建议阶段不得输出虚构数据。
3. 查询建议阶段不得直接输出 `block` / `ignore` 之类强处置结论。
4. 需要动作建议时，只能使用 `recommended_action_candidate`、`manual_review_required`、`need_more_evidence`。
5. 具体阈值必须标注为示例阈值，并注明需按业务历史分布和风控口径校准。
6. DataAgent 仍然只代表 Hive / 公司数仓取数分析能力。

## 6. 预期输出检查点

- 是否识别出“查询建议”而不是“查询结果”。
- 是否包含查询目标、必要入参、建议数据 / 字段、关键证据判断、strong / medium / weak evidence、counter evidence、预期输出结构、用户补充信息。
- 是否避免把查询建议写成最终判定。

