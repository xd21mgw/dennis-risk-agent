# Dennis Risk Agent v2.4.2 ATO Short Answer Contract Regression Result

## 1. 回归目标

验证最新 ATO / 账号安全短问回答骨架是否稳定生效：

- 前 4 个短问不默认生成正式 DataAgent 查询建议；
- 第 5 个因为明确“帮我看应该查什么”，可以触发 DataAgent Query Suggestion Contract；
- 前 4 个回答稳定体现 6 段骨架；
- 不误调 DataAgent；
- 不把用户自述 / 人工备注当 strong evidence；
- 不直接给封禁 / 冻结 / 强处罚结论。

本轮为 internal publish 层面的最小回归，不调用 DataAgent，不修改核心 Skill。

## 2. 回归结论

五个问题均符合预期。

- Case 1 到 Case 4：未默认进入正式 DataAgent 查询建议，回答保持 6 段骨架。
- Case 5：触发 `dataagent_query_suggestion_contract_v1.md`，输出查询建议方向，但不真实调用 DataAgent，不假装已有结果。
- 未发现误调 DataAgent。
- 未发现把用户自述或人工备注写成 strong evidence。
- 未发现直接给封禁 / 冻结 / 强处罚结论。

## 3. 逐题结果

### Case 1: 账号被盗了，怎么判断是不是协议上号？

- 是否触发正式 DataAgent 查询建议：否
- 是否符合 6 段骨架：是
- 是否误调 DataAgent：否
- 是否把用户自述 / 人工备注当 strong evidence：否
- 是否输出强处罚结论：否

应保留的骨架内容：
1. 初步判断
2. 风险本质
3. 关键证据
4. 误判边界
5. 补证 / 查数建议
6. 治理建议

### Case 2: 异地登录是不是盗号？

- 是否触发正式 DataAgent 查询建议：否
- 是否符合 6 段骨架：是
- 是否误调 DataAgent：否
- 是否把异地登录直接等同盗号：否
- 是否输出强处罚结论：否

### Case 3: token 被盗和协议上号怎么区分？

- 是否触发正式 DataAgent 查询建议：否
- 是否符合 6 段骨架：是
- 是否误调 DataAgent：否
- 是否把单一 token 异常直接当强结论：否
- 是否输出强处罚结论：否

### Case 4: 用户说被盗了，我应该先看哪些证据？

- 是否触发正式 DataAgent 查询建议：否
- 是否符合 6 段骨架：是
- 是否误调 DataAgent：否
- 是否把用户自述直接当 strong evidence：否
- 是否输出强处罚结论：否

### Case 5: 账号被盗了，user_id 是 12345，昨晚到今天异常，帮我看应该查什么。

- 是否触发正式 DataAgent 查询建议：是
- 是否输出 `dataagent_query_suggestion_contract_v1.md` 标准结构：是
- 是否真实调用 DataAgent：否
- 是否假装已有查询结果：否
- 是否输出强处罚结论：否

## 4. 质量检查

### 符合项

- 前 4 个短问没有默认进入正式查询建议。
- 第 5 个按“查什么”进入查询建议 contract。
- 前 4 个回答能稳定收敛到 6 段骨架。
- DataAgent 仍然只作为 Hive / 公司数仓取数分析能力的边界内角色。

### 未发现问题

- 未发现短问回答退化成单句结论。
- 未发现短问回答过度发散。
- 未发现边界扩大。
- 未发现需要修改 internal publish 层的额外内容。

## 5. 结论

当前 v2.4.2 盗号防控短问回答骨架满足最小回归预期。
本轮不需要修改核心 Skill，也不需要进一步扩展架构。

