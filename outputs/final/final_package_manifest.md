# Final Package Manifest

版本号：`dennis-risk-agent v2.3 executable-deep + Data Agent integration design`

## 1. 必须纳入的文件 / 目录

根目录文件：

- `AGENTS.md`
- `README.md`
- `QUICKSTART_PROMPTS.md`

核心 Skill 包：

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/00_agent_core/`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/01_core_skills/`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/03_attack_skills/`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/04_ai_agent_skills/`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/05_expression_skills/`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/06_templates/`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/08_eval/`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/12_material_distillation/`

评测集：

- `eval/dennis_risk_agent_skills_v2_2_tested/16_test_cases/`
- `eval/dennis_risk_agent_skills_v2_2_tested/17_cross_validation_results/`

最终交付：

- `outputs/final/`

建议纳入的关键回归摘要：

- `outputs/reviews/v2_3_executable_regression_summary.md`
- `outputs/reviews/v2_3_adversarial_regression_summary.md`
- `outputs/reviews/v2_3_adversarial_rerun_summary.md`
- `outputs/reviews/v2_3_self_evolution_crosscheck_summary.md`
- `outputs/reviews/v2_3_mixed_attack_20_case_regression.md`
- `outputs/reviews/v2_3_legal_matrix_5_case_regression.md`
- `outputs/reviews/dataagent_query_intent_10_case_regression.md`
- `outputs/reviews/dataagent_query_intent_4_case_rerun_after_schema_fix.md`
- `outputs/reviews/dataagent_query_intent_8_case_regression.md`
- `outputs/reviews/dataagent_adapter_mock_closed_loop_5_case.md`

## 2. 可选附录

可选纳入完整 review 明细：

- `outputs/reviews/v2_3_case_*.md`
- `outputs/reviews/v2_3_adversarial_case_*.md`
- `outputs/reviews/v2_3_adversarial_rerun_ADV-003.md`
- `outputs/reviews/v2_3_adversarial_rerun_ADV-008.md`
- `outputs/reviews/v2_3_self_evolution_case_*.md`
- `outputs/reviews/dataagent_query_intent_3_case_test.md`
- `outputs/reviews/dataagent_mock_closed_loop_3_case_test.md`
- `outputs/reviews/dataagent_mock_case_*.md`
- `outputs/reviews/dataagent_mock_5_case_summary.md`

可选展示资产：

- `outputs/dennis_risk_agent_flow_poster.svg`

可选历史材料：

- `outputs/reviews/history_docs_deep_distillation.md`
- `outputs/reviews/rta_channel_hijack_distillation.md`

## 3. 明确排除项

必须排除：

- `.git/`
- `.DS_Store`
- `__MACOSX/`
- `outputs/reviews/.dataagent_adapter_mock_closed_loop_5_case.md.swp`
- 任意 `*.swp`
- 任意编辑器临时文件
- 任意系统压缩包残留文件

说明：

- `.swp` 一定不要纳入最终包。
- 若使用 `zip`，需要通过 `-x` 显式排除。
- 若使用 `tar`，需要通过 `--exclude` 显式排除。

## 4. 当前版本号

```text
dennis-risk-agent v2.3 executable-deep + Data Agent integration design
```

内部短名：

```text
dennis-risk-agent-v2.3-dataagent-integration-design
```

## 5. 打包命令

推荐 zip 打包：

```bash
zip -r dennis-risk-agent-v2.3-dataagent-integration-design.zip \
  AGENTS.md \
  README.md \
  QUICKSTART_PROMPTS.md \
  skills/dennis_risk_agent_skills_v2_1_focused_deep/00_agent_core \
  skills/dennis_risk_agent_skills_v2_1_focused_deep/01_core_skills \
  skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills \
  skills/dennis_risk_agent_skills_v2_1_focused_deep/03_attack_skills \
  skills/dennis_risk_agent_skills_v2_1_focused_deep/04_ai_agent_skills \
  skills/dennis_risk_agent_skills_v2_1_focused_deep/05_expression_skills \
  skills/dennis_risk_agent_skills_v2_1_focused_deep/06_templates \
  skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent \
  skills/dennis_risk_agent_skills_v2_1_focused_deep/08_eval \
  skills/dennis_risk_agent_skills_v2_1_focused_deep/12_material_distillation \
  eval/dennis_risk_agent_skills_v2_2_tested/16_test_cases \
  eval/dennis_risk_agent_skills_v2_2_tested/17_cross_validation_results \
  outputs/final \
  outputs/reviews/v2_3_executable_regression_summary.md \
  outputs/reviews/v2_3_adversarial_regression_summary.md \
  outputs/reviews/v2_3_adversarial_rerun_summary.md \
  outputs/reviews/v2_3_self_evolution_crosscheck_summary.md \
  outputs/reviews/v2_3_mixed_attack_20_case_regression.md \
  outputs/reviews/v2_3_legal_matrix_5_case_regression.md \
  outputs/reviews/dataagent_query_intent_10_case_regression.md \
  outputs/reviews/dataagent_query_intent_4_case_rerun_after_schema_fix.md \
  outputs/reviews/dataagent_query_intent_8_case_regression.md \
  outputs/reviews/dataagent_adapter_mock_closed_loop_5_case.md \
  -x ".git/*" \
  -x "*.DS_Store" \
  -x "__MACOSX/*" \
  -x "*.swp"
```

可选 tar 打包：

```bash
tar --exclude='.git' \
  --exclude='.DS_Store' \
  --exclude='__MACOSX' \
  --exclude='*.swp' \
  -czf dennis-risk-agent-v2.3-dataagent-integration-design.tar.gz \
  AGENTS.md \
  README.md \
  QUICKSTART_PROMPTS.md \
  skills/dennis_risk_agent_skills_v2_1_focused_deep \
  eval/dennis_risk_agent_skills_v2_2_tested/16_test_cases \
  eval/dennis_risk_agent_skills_v2_2_tested/17_cross_validation_results \
  outputs/final
```

## 6. 解压后启动方式

建议阅读顺序：

1. `AGENTS.md`
2. `README.md`
3. `QUICKSTART_PROMPTS.md`
4. `outputs/final/dennis_risk_agent_v2_3_dataagent_integration_release_notes.md`
5. `outputs/final/skill_diff_final_review.md`
6. `outputs/final/protocol_attack_dataagent_pilot_readiness_checklist.md`
7. `skills/dennis_risk_agent_skills_v2_1_focused_deep/00_agent_core/skill_execution_contract_v2_3.md`
8. `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/dataagent_tool_contract_v1.md`
9. `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/configs/query_intent_schema_v2.md`
10. `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/adapter_design/query_intent_to_dataagent_request_design_v1.md`
11. `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/pilot_design/protocol_attack_evidence_minimum_pilot_v1.md`

最小使用方式：

```text
1. 先读 AGENTS.md，确认 Dennis 风控 Agent 的角色、工作流和禁止事项。
2. 再读 QUICKSTART_PROMPTS.md，选择要执行的风险研判或回归任务。
3. 若做协议攻击试点，读取 pilot_design/protocol_attack_evidence_minimum_pilot_v1.md 和 readiness checklist。
4. 若做 Data Agent 接入，读取 07_tools/dataagent/configs/ 与 adapter_design/。
5. 当前包只支持设计、研判、query_intent 规划和 mock closed-loop，不真实调用 Data Agent。
```

## 7. 包内边界

本包不包含：

- 真实 Data Agent API。
- 真实认证方式。
- 真实表名。
- 真实字段名。
- 真实 SQL。
- 自动治理执行器。

所有真实数据资产映射、权限、调用、审计和回放能力由未来内部平台补充。
