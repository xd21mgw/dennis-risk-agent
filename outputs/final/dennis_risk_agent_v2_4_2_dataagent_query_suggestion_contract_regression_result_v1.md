# Dennis Risk Agent v2.4.2 DataAgent Query Suggestion Contract Regression Result

## 1. 回归目标

验证 `dataagent_query_suggestion_contract_v1.md` 是否能约束 Dennis Risk Agent 在“第一次生成查数建议”时输出可被 DataAgent / Hive 使用的结构化建议，而不是把建议写成查询结果，或退化成维度清单。

本轮不调用 DataAgent，不输出真实查询结果。

## 2. 回归结论

四个案例均符合预期。

- 正向触发案例 1 / 2：能够触发查询建议契约，并输出标准结构。
- 非触发案例 3 / 4：不会生成正式查询建议，只给判断框架、证据方向、误判边界和治理建议。
- 未发现误调 DataAgent。
- 未发现把查询建议写成查询结果。
- 未发现输出强处置结论。

## 3. 正向触发案例

### Case 1: ATO / 协议上号查询建议

用户问题：
- 账号被盗了，怀疑协议上号。user_id 是 12345，时间窗口是昨晚 20:00 到今天 10:00。帮我看应该查什么。

回归结果：
- 是否触发 `dataagent_query_suggestion_contract_v1.md`：通过
- 是否输出标准结构：通过
- 是否真实调用 DataAgent：否
- 是否假装已有结果：否
- 是否直接给强处置结论：否

实际应输出的标准结构覆盖：
1. 查询目标
2. 必要入参
3. 建议查询数据 / 字段
4. 关键证据判断
5. strong evidence
6. medium evidence
7. weak evidence
8. counter evidence / 误判边界
9. 预期输出结构
10. 还需要用户补充的信息

额外符合点：
- 明确阈值只能是示例阈值，需按业务历史分布和风控口径校准。
- 只输出 `recommended_action_candidate`、`manual_review_required`、`need_more_evidence` 级别的建议，不输出 block / ignore。

### Case 2: 外部跟价 / 反爬资产泄露查询建议

用户问题：
- 外部站点一直能跟价我们商品，但内部没看到明显高频爬虫。帮我生成 DataAgent 查询建议，不要真的查。

回归结果：
- 是否触发 `dataagent_query_suggestion_contract_v1.md`：通过
- 是否输出标准结构：通过
- 是否真实调用 DataAgent：否
- 是否假装已有结果：否
- 是否直接给强处置结论：否

实际应输出的标准结构覆盖：
1. 查询目标
2. 必要入参
3. 建议查询数据 / 字段
4. 关键证据判断
5. strong evidence
6. medium evidence
7. weak evidence
8. counter evidence / 误判边界
9. 预期输出结构
10. 还需要用户补充的信息

额外符合点：
- 明确 DataAgent 仅为 Hive / 公司数仓取数分析能力。
- 没有把“帮我生成查询建议”误写成已经查数。

## 4. 非触发案例

### Case 3: 群控和真人众包怎么区分？

回归结果：
- 是否生成正式 DataAgent 查询建议：否
- 是否误调 DataAgent：否
- 是否只给判断框架、证据方向、误判边界、治理建议：通过
- 是否允许后续按需生成查询建议：通过

实际回答应保持：
- 先讲设备、行为、账号、任务链、成本结构差异。
- 再讲证据优先级、误判边界和治理建议。
- 只在用户明确要求查数时，再生成查询建议。

### Case 4: 怎么判断一个攻击是不是单纯协议攻击？

回归结果：
- 是否生成正式 DataAgent 查询建议：否
- 是否误调 DataAgent：否
- 是否只给专家判断框架、证据方向、误判边界、治理建议：通过
- 是否允许后续按需生成查询建议：通过

实际回答应保持：
- 先区分协议攻击、群控、真人众包。
- 再给判断证据和反证。
- 不默认进入查询建议。

## 5. 质量检查

### 符合项

- 触发场景下首次回答必须包含 10 段标准结构。
- 查询建议阶段没有虚构数据。
- 查询建议阶段没有输出强处置结论。
- 非触发场景没有被强行推入正式查询建议。
- DataAgent 仍然只定位为 Hive / 公司数仓取数分析能力。

### 未发现的问题

- 未发现查询建议退化为“维度清单”。
- 未发现查询建议被写成查询结果。
- 未发现边界扩大。

## 6. 结论

`dataagent_query_suggestion_contract_v1.md` 满足 v2.4.2 最小回归预期。
本次无需对核心 Skill 做任何修改。
如后续要继续优化，只建议在 internal publish 层继续做格式约束，不扩展新架构。

