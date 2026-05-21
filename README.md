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

## ATO 批量 Case Analysis 最小闭环

当前已新增 ATO 批量 case analysis 管理目录：

`eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/`

用途：

- 面向 5-20 个 ATO / 盗号申诉 case 做半自动批量归因。
- 把 case 标准化为 registry、单 case 证据卡、批量模式摘要和候选策略方向。
- 重点输出证据聚合、缺口识别、模式总结和后续补证建议。

边界：

- 不调用真实 DataAgent。
- 不执行真实内部平台查询。
- 不做自动策略上线。
- DataAgent 仅作为未来 Hive / 数仓取数分析能力，不是默认万能数据底座。
- 批量分析是半自动归因，不是自动处置系统。

推荐入口：

- `ato_batch_case_schema_v1.md`：标准 case 字段。
- `ato_batch_case_registry_template_v1.csv`：脱敏样例 registry。
- `ato_batch_workflow_v1.md`：批量分析流程。
- `ato_batch_evidence_card_template_v1.md`：单 case 证据卡。
- `ato_batch_pattern_summary_template_v1.md`：批量模式聚合。
- `ato_batch_strategy_direction_template_v1.md`：候选策略方向。
- `ato_batch_input_contract_v1.md`：批量 case 输入契约，定义必填字段、缺字段状态和 5-20 cases 推荐规模。
- `ato_batch_output_contract_v1.md`：批量分析固定输出结构，要求核心结论引用 evidence_source / source_quality。
- `ato_batch_status_transition_v1.md`：case_status / batch_status 流转，防止缺字段或弱来源直接进入强结论。
- `ato_batch_user_interaction_examples_v1.md`：3 类用户交互样例，覆盖字段完整、缺字段、登录日志超窗。
- `ato_case_expansion_plan_v1.md`：单个或少量 ATO case 的举一返三扩展方案，围绕账号控制权异常、攻击链路和黑产基础设施扩展，而不是按相同昵称 / 简介扩展。

## Batch Analysis 通用框架

当前已新增轻量通用 batch analysis framework：

`eval/dennis_risk_agent_skills_v2_2_tested/batch_analysis_framework_v1.md`

用途：

- 抽象 ATO batch 与黑产账号矩阵 batch 的共用流程。
- 固化 case intake、case registry、entity normalization、single-case evidence card、cross-case pattern summary、missing evidence aggregation、strategy direction draft、manual review boundary。
- 明确不同风险场景只替换 risk definition、scene-specific fields、evidence priority、pattern dimensions 和 strategy direction boundary。

边界：

- Batch analysis 当前是半自动归因，不是自动策略上线。
- DataAgent 仍只作为 Hive / 数仓取数分析能力，不是默认万能数据底座。
- 内部 Agent 后续只作为真实只读 observation 执行层，不作为最终研判大脑。

## 黑产账号矩阵 / 导流互动 Batch Analysis 样板

当前已新增非 ATO 的黑产账号矩阵 batch analysis 管理目录：

`eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/`

用途：

- 面向同一波黑产账号样本做账号矩阵、导流互动、互粉互动、养号账号池归因。
- 聚合简介签名、联系方式归一化、adminaction、昵称模板、注册天数 cohort、UID 号段 cohort 和行为链路缺口。
- 输出 evidence card、pattern summary 和候选策略方向。

边界：

- 不是 ATO。ATO 是账号控制权异常；本能力是账号矩阵 / 导流 / 互动作弊 / 黑产养号池归因。
- 不调用真实 DataAgent。
- 不执行真实内部平台查询。
- 不做自动策略上线。
- 不输出微信号、UID、device、IP 等敏感明文。

推荐入口：

- `black_market_account_matrix_case_schema_v1.md`
- `black_market_account_matrix_registry_template_v1.csv`
- `black_market_account_matrix_evidence_card_template_v1.md`
- `black_market_account_matrix_pattern_summary_template_v1.md`
- `black_market_account_matrix_strategy_direction_template_v1.md`
- `black_market_account_matrix_dry_run_sample_v1.md`

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
