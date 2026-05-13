# Quickstart Prompts

## 1. 启动体检

请先阅读 AGENTS.md，然后检查 skills/ 和 eval/ 目录结构是否完整。不要改文件，只输出你理解的启动方式、主控 Skill 路由和评估流程。

## 2. 群控测试

请使用 Dennis 风控专家 Agent 方式回答：

问题：群控和协议怎么区分？活动场景群控严重，应该如何查、如何治理、如何灰度、如何评估？

要求：
1. 必须先选择主控 Skill 和辅助 Skill。
2. 必须参考 group_control_expert_skill、protocol_attack_expert_skill、activity_anti_cheating_expert_skill。
3. 必须输出强证据、中证据、弱证据、反证。
4. 必须输出查数动作、治理方案、灰度策略、评估指标。
5. 最后按 deep_skill_rubric_v2_1.md 自评。

## 3. 5 Case 回归

请从 50 个测试案例里选择 5 个最能检验“黑产本质”的 case，逐个回答并按 deep_skill_rubric_v2_1.md 打分。

要求：
1. 每个 case 单独输出到 outputs/reviews/case_<case_id>.md
2. 最后汇总到 outputs/reviews/batch_5_summary.md
3. 如果低于 80 分，写出需要回写哪个 Skill 文件。
