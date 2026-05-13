# dennis-risk-agent

这是一个可直接给 Codex 使用的 Dennis 风控专家 Agent 项目。

## 目录结构

```text
dennis-risk-agent/
├── AGENTS.md
├── skills/
│   └── dennis_risk_agent_skills_v2_1_focused_deep/
├── eval/
│   └── dennis_risk_agent_skills_v2_2_tested/
├── outputs/
│   ├── drafts/
│   ├── reviews/
│   └── final/
└── README.md
```

## 启动方式

在本目录下启动 Codex：

```bash
cd dennis-risk-agent
codex
```

第一次启动建议输入：

```text
请先阅读 AGENTS.md，然后检查 skills/ 和 eval/ 目录结构是否完整。不要改文件，只输出你理解的启动方式、主控 Skill 路由和评估流程。
```

## 第一次体检 Prompt

```text
请基于 AGENTS.md 启动 Dennis 风控专家 Agent。

第一步：读取 skills/dennis_risk_agent_skills_v2_1_focused_deep/ 下的核心说明文件。
第二步：读取 eval/dennis_risk_agent_skills_v2_2_tested/16_test_cases/json/dennis_50_test_cases_v2_2.json。
第三步：输出：
1. 当前 Skill 总数
2. 五类 Skill 边界
3. 50 个测试案例覆盖的领域
4. 你认为当前最强的 5 个 Skill
5. 当前最弱的 5 个 Skill
6. 后续如何用测试集做回归
不要修改文件。
```

## 群控测试 Prompt

```text
请使用 Dennis 风控专家 Agent 方式回答：

问题：群控和协议怎么区分？活动场景群控严重，应该如何查、如何治理、如何灰度、如何评估？

要求：
1. 必须先选择主控 Skill 和辅助 Skill。
2. 必须参考 group_control_expert_skill、protocol_attack_expert_skill、activity_anti_cheating_expert_skill。
3. 必须输出强证据、中证据、弱证据、反证。
4. 必须输出查数动作、治理方案、灰度策略、评估指标。
5. 最后按 deep_skill_rubric_v2_1.md 自评。
```

## 50 个测试案例回归 Prompt

```text
请读取 eval/dennis_risk_agent_skills_v2_2_tested/16_test_cases/json/dennis_50_test_cases_v2_2.json。

请生成一个 50 case 回归计划：
1. 按领域分组
2. 每组抽 1 个代表 case
3. 说明每个 case 应触发哪些 Skill
4. 说明评分方式
5. 输出到 outputs/reviews/regression_plan.md
```

## 小批量测试 Prompt

```text
请从 50 个测试案例里选择 5 个最能检验“黑产本质”的 case，逐个回答并按 deep_skill_rubric_v2_1.md 打分。

要求：
1. 每个 case 单独输出到 outputs/reviews/case_<case_id>.md
2. 最后汇总到 outputs/reviews/batch_5_summary.md
3. 如果低于 80 分，写出需要回写哪个 Skill 文件。
```

## Skill 回写计划 Prompt

```text
请根据 outputs/reviews/ 下的测试结果，生成 Skill 回写计划。

要求：
1. 不要直接修改 Skill 文件。
2. 列出低分 case。
3. 说明低分原因。
4. 指定需要修改的 Skill 文件。
5. 给出每个文件的修改大纲。
6. 输出到 outputs/reviews/skill_update_plan.md。
```

## 确认后回写 Prompt

```text
请根据 outputs/reviews/skill_update_plan.md 修改对应 Skill 文件。

要求：
1. 保持原目录结构。
2. 不要新增无关 Skill。
3. 每个修改都要补充：认知、证据、边界、治理、指标、反例。
4. 修改后重新跑对应低分 case。
```

## 使用原则

这个项目的核心不是“让 Codex 聊天”，而是让 Codex 按以下流程工作：

```text
读取 AGENTS.md
→ 选择 Skill
→ 生成答案
→ 按测试集 / Rubric 自评
→ 输出结果到 outputs/
→ 生成回写计划
→ 人工确认后再修改 Skill
```
