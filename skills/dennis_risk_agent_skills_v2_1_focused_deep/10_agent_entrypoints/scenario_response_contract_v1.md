# Scenario Response Contract v1

## 0. 定位

本文件定义 Dennis Risk Agent 的通用场景输出协议。

ATO response contract 是该通用协议的第一个场景实现。未来反爬、群控、活动反作弊、渠道抢量、导流截流等场景应按该协议扩展。

目标：
- 用户通过自然语言获得稳定答案。
- Agent 能根据 intent 自动选择合适输出结构。
- 保持证据、反证、缺口、治理和沉淀的一致性。

## 1. 通用最小输出

当用户没有要求完整结构时，默认输出：

```yaml
scenario_short_response:
  当前结论:
  为什么:
  关键证据:
  反证:
  最小补证动作:
  下一步:
```

## 2. 完整输出字段

完整输出协议覆盖：

```yaml
scenario_full_response:
  当前结论:
  为什么:
  支持证据:
    强证据:
    中证据:
    弱证据:
  反证:
  缺失证据:
  下一步补证:
  是否需要 Data Agent:
  可复制给 Data Agent 的问题:
  Data Agent 返回解释:
    data_findings:
    provider_conclusion_hint:
    dennis_final_judgement:
  举一反三:
  治理建议:
  是否建议回写 Skill:
```

## 3. 单 case 输出格式

```yaml
single_case_response:
  当前结论:
  为什么:
  支持证据:
  反证:
  缺失证据:
  下一步补证:
  是否需要 Data Agent:
  是否需要人工复核:
```

## 4. 批量 case 输出格式

```yaml
batch_case_response:
  样本总览:
  风险发生方式分层:
  下游作恶方式分层:
  高置信正例:
  反例/不确定/历史 case:
  标签缺失/待补证样本:
  可回捞候选:
  风险与局限:
```

说明：
- 具体场景可将“风险发生方式”替换成 ATO 发生方式、爬取路径、群控调度方式、活动套利路径等。

## 5. Data Agent 问题输出格式

```yaml
dataagent_question_response:
  直接复制给 Data Agent 的问题:
  查询目标:
  样本范围:
  时间窗口:
  数据域:
  输出要求:
  降级规则:
  Data Agent 边界:
```

## 6. Data Agent 返回解释格式

```yaml
dataagent_interpretation_response:
  Data Agent 数据发现:
  provider_conclusion_hint:
  Dennis final judgement:
  强/中/弱证据:
  反证:
  缺失证据:
  quality_risks:
  provider_limitations:
  下一步 provider / next action:
```

边界：
- Data Agent 返回中的结论性文字只进入 provider_conclusion_hint。
- Dennis final judgement 由 Dennis 主 Agent 生成。

## 7. Data Agent 交互式下一步输出格式

适用 workflow：`dataagent_interactive_followup`

```yaml
dataagent_interactive_followup_response:
  当前已完成查询:
  当前数据发现摘要:
  当前结论上限:
  缺失证据:
  Data Agent 给出的可选下一步:
    - option_id:
      option_summary:
      source: dataagent_next_data_option
  Dennis Agent 推荐优先级:
    - priority:
      option_id:
      reason:
  每个选项的查询成本:
    - option_id:
      cost: 低 / 中 / 高
      cost_reason:
  每个选项能验证什么:
    - option_id:
      target_evidence:
      possible_result_impact:
  是否需要用户确认:
  可复制给 Data Agent 的下一步问题:
  是否可以先输出阶段性 Dennis 判断:
```

边界：
- Data Agent 可以提出 `next_data_options`，但不决定最终 `next_action`。
- Dennis Agent 负责把选项转成用户可理解、可选择的动作。
- SQL-only、running、partial、no_permission 状态下，阶段性判断必须降级。
- 高成本 Hive、长周期扩窗、跨域 join、大样本回捞必须显式确认。
- 可复制给 Data Agent 的下一步问题仍然只能要求只读取证，不要求最终定性或治理动作。

## 8. 举一反三输出格式

```yaml
generalization_response:
  可回捞候选特征:
  原始观测:
  数据发现:
  候选特征:
  机制特征:
  不建议使用的表象特征:
  正反例验证方案:
  误伤风险:
  是否建议上线/灰度/仅监控:
```

## 9. 治理建议输出格式

```yaml
governance_response:
  短期止损:
  中期识别:
  长期治理:
  用户体验:
  黑产成本:
  需要业务协同:
  灰度策略:
  评估指标:
```

## 10. 复盘沉淀输出格式

```yaml
distillation_response:
  可回写 Skill:
  只进 eval/review:
  需更多数据验证:
  不应沉淀:
  下一步建议:
```

## 11. 通用禁止行为

- 不证据不足强结论。
- 不把 Data Agent 返回当最终判断。
- 不把用户自述 / 人工备注当事实。
- 不把单批样本统计写入 Skill。
- 不自动输出处罚、冻结、封禁、扣除或策略上线。
- 不把具体策略名 / 规则名当作本质特征。

## 12. 场景实现关系

```text
scenario_response_contract_v1
→ ato_agent_response_contract_v1
→ future anti_crawler_response_contract_v1
→ future group_control_response_contract_v1
→ future activity_anti_cheating_response_contract_v1
```
