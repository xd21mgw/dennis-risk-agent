# Scenario Intent Router Contract v1

## 0. 定位

本文件定义 Dennis Risk Agent 的通用场景入口层 intent router contract。

它不绑定 ATO。ATO 是第一个 scenario overlay，用来验证“场景入口层 → 工作流 → 证据规划 → Data Agent → Dennis 解释 → 治理 / 回归沉淀”的模式。

未来以下场景均可复用该 contract：

- anti_crawler
- group_control
- activity_anti_cheating
- traffic_diversion
- channel_hijack
- protocol_attack
- cracked_app
- account_security / ATO

边界：
- scenario router 只负责识别用户意图和选择 workflow。
- scenario router 不替代核心 Skill。
- scenario router 不调用真实 Data Agent。
- scenario router 不生成最终风控定性。

## 1. 通用 Intent 类型

### 1.1 single_case_judgement

单 case 研判。

典型问题：
- 这个 case 是不是风险？
- 这个用户 / 设备 / 请求 / 样本能不能定性？
- 这个客诉是否可信？

输出目标：
- 当前结论。
- 支持证据。
- 反证。
- 缺失证据。
- 下一步补证。

### 1.2 batch_case_clustering

批量样本分层。

典型问题：
- 这批样本帮我分层。
- 哪些是正例，哪些是反例，哪些是不确定？
- 这些 case 有什么共性？

输出目标：
- 风险类型分层。
- 手法 / 场景分层。
- 高置信正例。
- 反例 / 不确定 / 标签缺失样本。
- 待补证样本。

### 1.3 evidence_planning

证据规划 / 证据卡 / 查数卡。

典型问题：
- 这个问题需要哪些证据？
- 怎么判断证据够不够？
- 证据卡怎么写？

输出目标：
- 目标证据。
- 强 / 中 / 弱证据。
- 反证。
- 数据域。
- join path。
- 质量风险。

### 1.4 dataagent_question_generation

生成 Data Agent 只读取证问题。

典型问题：
- 帮我生成 Data Agent 查询问题。
- 这批样本要怎么取数？
- 给我一个可复制给 Data Agent 的问题。

输出目标：
- 自然语言 question。
- 数据域。
- 字段类型。
- 关联关系。
- 输出要求。
- 降级规则。

### 1.5 dataagent_result_interpretation

解释 Data Agent 返回。

典型问题：
- 这是 Data Agent 返回，帮我解释。
- 这些数据够不够下结论？
- 哪些是数据发现，哪些只是提示？

输出目标：
- data_findings。
- provider_conclusion_hint。
- strong / medium / weak evidence。
- counter_evidence。
- missing_evidence。
- dennis_final_judgement。

### 1.6 generalization_and_recall

举一反三 / 回捞建议。

典型问题：
- 怎么回捞同类风险？
- 哪些特征能用？
- 哪些特征不要用？

输出目标：
- 原始观测。
- 数据发现。
- 候选特征。
- 机制特征。
- 本质规则。
- 正反例验证方案。
- 回捞优先级。

### 1.7 governance_design

治理方案。

典型问题：
- 这类风险怎么治理？
- 应该拦、验、限、教育，还是监控？
- 怎么控制误伤？

输出目标：
- 短期止损。
- 中期识别。
- 长期治理。
- 用户体验。
- 黑产成本。
- 业务协同。

### 1.8 review_and_skill_distillation

复盘沉淀 / 是否回写 Skill。

典型问题：
- 这批 case 能沉淀什么？
- 要不要回写 Skill？
- 哪些只进 eval？

输出目标：
- 可回写 Skill。
- 只进 eval / review。
- 需更多数据验证。
- 不应沉淀。
- 下一步回归建议。

## 2. 每个 Scenario Overlay 必须补充

每个场景 overlay 应声明：

```yaml
scenario_overlay:
  scenario_name:
  trigger_keywords:
  typical_user_questions:
  primary_skill:
  auxiliary_skills:
  intent_mapping:
  dataagent_needed_rules:
  response_contract:
  scenario_specific_boundaries:
```

## 3. 通用路由输出

```yaml
scenario_route:
  triggered:
  scenario:
  intent:
  primary_workflow:
  secondary_workflows:
  primary_skill:
  auxiliary_skills:
  dataagent_needed:
  minimum_inputs_needed:
  response_contract:
  boundary_warnings:
```

## 4. 通用边界

- 用户输入、人工备注、标签、样本统计都不是事实。
- Data Agent 返回不是最终风控判断。
- 证据不足必须降级。
- 具体策略名 / 规则名不能作为长期本质特征。
- 单批样本统计不能直接写入 Skill。
- 高风险治理动作不得自动执行。

## 5. ATO Overlay 的关系

`ato_intent_router_v1.md` 是本 contract 的第一个场景实现。

ATO overlay 可以保留自己的触发关键词、场景边界、响应格式和 Data Agent 取证模板，但应遵守本通用 contract：

```text
scenario_intent_router_contract_v1
→ ato_intent_router_v1
```
