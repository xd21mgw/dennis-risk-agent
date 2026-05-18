# Dennis Risk Agent v2.4 Runtime Plus Publish Checklist

- [ ] Git 已提交。
- [ ] release package 已存在。
- [ ] smoke test 已完成，且结果仅按“internal publish 层最小格式与边界回归通过”口径记录。
- [ ] System Prompt 已准备。
- [ ] 必读文件已装载。
- [ ] runtime summary 已装载。
- [ ] ATO 完全体文件已装载。
- [ ] DataAgent 边界已配置。
- [ ] 首次生成 DataAgent 查询建议时符合标准结构。
- [ ] 上架后 5 个问题已测试。
- [ ] 未发现误调 DataAgent。
- [ ] 未发现回答表面化。
- [ ] 可以进入小范围试运行。
- [ ] v2.4.1 加载优化说明已同步。
- [ ] v2.4.1 三问回归结果已按最小格式与边界回归口径完成。
- [ ] 未宣称非 ATO 已具备完全体能力，仍保留内部小范围试运行观察。

## 备注

- ATO 问题必须进入 ATO 完全体。
- 非 ATO 问题默认走 runtime summary。
- 用户明确要求查数时再进入 DataAgent / Hive。
- 高成本查询必须用户确认。
- `dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md` 更适合作为初始化 / 配置期检查，不建议每轮问答常驻加载。
- `dataagent_query_suggestion_contract_v1.md` 是查询建议格式规则，不是 DataAgent 调用器；当用户明确要求查数建议时再加载。
- 查询建议结构不等于可直接执行 SQL；执行前仍需 DataAgent / Hive 根据真实表名、权限、分区、join key 和数据口径转换。
- v2.4.1 的默认常驻不包含 startup checklist、release note、route regression、smoke test。
