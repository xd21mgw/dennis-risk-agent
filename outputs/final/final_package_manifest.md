# Final Package Manifest

版本号：`dennis-risk-agent v2.3 executable-deep + Data Agent integration design`

当前 release addendum：

```text
dennis-risk-agent v2.6.0 User ↔ Device Entity Resolution Layer
```

本 addendum 仅吸收 `computer_use_poc` 中已完成一致性检查的实体解析层文档，不修改核心 Skill，不新增接口，不包含真实查询结果。

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

Computer Use POC / Entity Resolution addendum：

- `computer_use_poc/entity_resolution_user_device_layer_v2_6_0.md`
- `computer_use_poc/entity_resolution_user_device_contract_v2_6_0.md`
- `computer_use_poc/entity_resolution_user_device_routing_rules_v2_6_0.md`
- `computer_use_poc/entity_resolution_user_device_smoke_tests_v2_6_0.md`
- `computer_use_poc/run_logs/entity_resolution_user_device_text_regression_run_v2_6_0.md`
- `computer_use_poc/device_sdk_api_routing_rules_v2_5_3.md`
- `computer_use_poc/smoke_tests.md`

这些文件构成 v2.6.0 User ↔ Device Entity Resolution Layer 的 release package 增量：主 Agent 在 intent routing 与具体 hand 之间，先补齐 `userId ↔ deviceId / did / deviceceid` 入参映射，再进入 Device SDK、用户登录统一日志、档案中心等后续只读 hand。

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

## 4.1 v2.6.0 Entity Resolution Addendum

### 能力摘要

`User ↔ Device Entity Resolution Layer v2.6.0` 位于主 Agent intent routing 和具体 hand 之间，只负责 `userId ↔ deviceId / did / deviceceid` 的实体转译：

- 不直接查风险。
- 不直接做风险定性。
- 不替代 Device SDK、用户登录统一日志、档案中心、前端活跃画像或 DataAgent。
- 只为后续 hand 补齐必要入参。

### 双向解析主入口

`user_to_device`：

- 主入口：Weapon `graphData`。
- `groupValue={userId}`。
- `groupKey=USER_ID`。
- `dimKey=DEVICE_ID`。
- 解析 `pointInfoMap` 中 `DEVICE_ID` 节点，以及 `relationEdgeList` 中 `source=userId`、`target=DEVICE_ID` 的直连边。

`device_to_user`：

- 主入口：Weapon `graphData`。
- `groupValue={deviceId}`。
- `groupKey=DEVICE_ID`。
- `dimKey=USER_ID`。
- 解析 `pointInfoMap` 中 `USER_ID` 节点，以及 `relationEdgeList` 中 `source=deviceId`、`target=USER_ID` 的直连边。

### 与其他 hand 的职责切分

- Device SDK hand / `riskData`：不作为实体解析主入口；只在拿到 deviceId 后做 hook / frida / root / jailbreak / proxy / simulator / repack 等设备侧风险补证。
- 用户登录统一日志：登录失败、登录流水、登录原因类问题直接走登录日志，不应触发 graphData / Device SDK。
- 档案中心用户分析 API：只作为近期关联设备补充排序来源，不作为 `user_to_device` 主入口。
- DataAgent / Hive：只用于批量、长周期、历史聚合，不替代 graphData 在线实体解析。

### 路由边界

- `userId + 设备风险`：先 `user_to_device` graphData，再 Device SDK 设备补证。
- `userId + 登录流水`：直接用户登录统一日志，不走 graphData / Device SDK。
- `deviceId + 设备风险`：直接 Device SDK，不做实体转译。
- `deviceId + 关联用户`：走 `device_to_user` graphData。
- 关联关系不是风险结论。
- 候选过多不默认批量深查。
- 缺失设备返回 `missing_device_id`。
- 缺失关联用户返回 `no_related_user / missing_user_id`。
- 候选过多返回 `too_many_candidates`。

### Runtime Error Semantics

已吸收的运行态状态：

- `graphdata_error`
- `auth_required`
- `permission_denied`
- `no_related_entity`
- `no_direct_relation`
- `missing_device_id`
- `no_related_user / missing_user_id`
- `too_many_candidates`
- `parse_error`

这些运行态错误语义已文档化；`no_data` / `auth_required` / `permission_denied` 等真实接口返回形态仍未做真实运行验证。

### 验证状态

- v2.6.0 文本回归：10/10 pass。
- graphData error semantics：已补充 8 个 error case。
- release package 更新前一致性检查：已完成，未发现口径冲突。
- 本 addendum 未真实查询、未新增接口、未批量、未修改核心 Skill。

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
12. `computer_use_poc/entity_resolution_user_device_layer_v2_6_0.md`
13. `computer_use_poc/entity_resolution_user_device_contract_v2_6_0.md`
14. `computer_use_poc/entity_resolution_user_device_routing_rules_v2_6_0.md`
15. `computer_use_poc/run_logs/entity_resolution_user_device_text_regression_run_v2_6_0.md`

最小使用方式：

```text
1. 先读 AGENTS.md，确认 Dennis 风控 Agent 的角色、工作流和禁止事项。
2. 再读 QUICKSTART_PROMPTS.md，选择要执行的风险研判或回归任务。
3. 若做协议攻击试点，读取 pilot_design/protocol_attack_evidence_minimum_pilot_v1.md 和 readiness checklist。
4. 若做 Data Agent 接入，读取 07_tools/dataagent/configs/ 与 adapter_design/。
5. 当前包只支持设计、研判、query_intent 规划和 mock closed-loop，不真实调用 Data Agent。
6. 若问题涉及 `userId ↔ deviceId` 入参不一致，先读取 v2.6.0 Entity Resolution addendum；该层只补齐实体，不给风险定性。
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
