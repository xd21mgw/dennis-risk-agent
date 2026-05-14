# v2.3 Executable 6 Case 小回归汇总

## 回归范围

| 核心 Skill | Case | 文件 |
|---|---|---|
| group_control_expert_skill | AC-004 | `outputs/reviews/v2_3_case_AC-004.md` |
| protocol_attack_expert_skill | AC-003 | `outputs/reviews/v2_3_case_AC-003.md` |
| anti_crawler_expert_skill | AC-001 | `outputs/reviews/v2_3_case_AC-001.md` |
| account_security_expert_skill | AS-001 | `outputs/reviews/v2_3_case_AS-001.md` |
| activity_anti_cheating_expert_skill | ACT-002 | `outputs/reviews/v2_3_case_ACT-002.md` |
| traffic_anti_cheating_expert_skill | AC-009 | `outputs/reviews/v2_3_case_AC-009.md` |

## 结果

| Case | 主控 Skill | 判断规则命中 | 分数 | 是否需回写 |
|---|---|---|---:|---|
| AC-004 | group_control_expert_skill | 第 3 条 + 第 7 条约束 | 98 | 否 |
| AC-003 | protocol_attack_expert_skill | 第 1 条 + 第 6/7/8/9 条排除约束 | 99 | 否 |
| AC-001 | anti_crawler_expert_skill | 第 1/2 条 + 第 9 条约束 | 99 | 否 |
| AS-001 | account_security_expert_skill | 第 2 条 + 第 7/8 条约束 | 99 | 否 |
| ACT-002 | activity_anti_cheating_expert_skill | 第 2 条 + 第 7 条约束 | 98 | 否 |
| AC-009 | traffic_anti_cheating_expert_skill | 第 2 条 + 第 7 条约束 | 96 | 否 |

平均分：98.2/100。无低于 80 分 case，无需回写 Skill。

## 观察

- v2.3 的“输入是否充分”字段有效防止了强结论：6 个 case 都明确了缺失数据和降级判断。
- 判断规则可执行性较好：每个 case 都能落到具体规则编号，而不是只套专家知识。
- 边界约束有效：AC-004 没有因为真实端行为判正常，AC-003 没有因为高频判协议，ACT-002 没有把低质直接当黑产。
- traffic_anti_cheating_expert_skill 相比其他 Skill 分数略低，原因是 AC-009 更偏机制/SLA，专家风险手法证据少于攻击型 case，但仍达到可用标准。

## 当前仍不足

- 这轮是人工小回归，还没有自动化脚本评分。
- traffic_anti_cheating 的 DAU/DNU case 需要更多真实口径样例，但不能编造表名和字段。
- group_control、protocol、anti_crawler 的混合攻击场景仍需要后续更多组合 case 验证。

## 下一轮建议

- 用 50 case 做批量静态映射校验，检查每个 case 是否能落到 v2.3 的判断规则。
- 继续升级 v2.2 backlog 的 real_user_crowdsourcing、cracked_app、traffic_diversion_interception 三个 Skill。
- 增加一个轻量脚本，检查每个回归文件是否包含主控 Skill、判断规则、自评分和是否回写结论。
