# v2.3 自我进化交叉 Case：SE-003

## 对抗点

DAU/DNU 指标异常，但缺少协议、群控、真人众包、账号设备团组或站外任务证据。

## 交叉 Skill

- 主控候选：traffic_anti_cheating_expert_skill
- 辅助候选：risk_governance_design_skill、evidence_decomposition_skill

## 修改前误判风险

DAU/DNU 异常容易被写成黑产污染，但缺攻击证据时更可能是口径、埋点、数据任务、版本、去重逻辑或回补问题。

## 回写动作

- traffic_anti_cheating_expert_skill 第 2 条增加“缺攻击证据不得定性黑产污染，只能按数据治理/口径异常待排查处理”。
- 补 DAU/DNU 专项补证和数据治理降级策略。

## 复核结论

当前最多下“指标口径异常或风险待排查”。不能直接剔除核心指标，也不能定黑产。

## 需要补证

口径定义、去重逻辑、端版本、埋点变更、任务依赖、实时/离线 diff、回补记录、业务使用方确认、攻击证据。

## 评分

修改后 91/100。仍依赖数据平台任务链路和业务口径 owner 确认。
