# Dennis 风控专家 Skills v2.2 测试包

## 内容

本目录是独立测试包，用于后续人工检测和自动回归。

包括：

- `16_test_cases/json/dennis_50_test_cases_v2_2.json`：50 个测试案例；
- `16_test_cases/markdown_by_domain/`：按领域拆分的 Markdown 版；
- `16_test_cases/golden_expectations/`：通用黄金标准；
- `17_cross_validation_results/`：交叉验证结果；
- `18_regression_review/`：回归复核；
- `19_skill_update_backlog/`：从测试反推的 Skill 更新清单。

## 测试案例来源

- 历史对话记忆；
- 2023/2024/2025 年度述职；
- 业务领域大图；
- 成功策略图；
- v2.1 Focused Deep 的 Skill 边界；
- 聚焦外部案例：账号安全、流量反作弊、反爬、活动反作弊。

## 使用方式

1. 随机抽一个 case；
2. 让 Codex/Agent 基于 v2.1 Skill 回答；
3. 对照 must_have / must_not；
4. 用 deep_skill_rubric 打分；
5. 将不通过项回写到 Skill。
