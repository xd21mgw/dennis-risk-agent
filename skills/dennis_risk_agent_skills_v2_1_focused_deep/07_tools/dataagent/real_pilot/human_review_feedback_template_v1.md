# Human Review Feedback Template v1

## 0. 使用边界

本模板用于记录人工复核反馈，并把真实只读试点中的判断经验回流到 Dennis Agent。

- 人工反馈用于改进判断规则、query intent、join path、结论阈值和测试 case。
- 人工反馈不等于自动处罚指令。
- 如涉及线上策略、处罚、冻结、扣除，必须走独立审批和人工确认。

## 1. 单 Case 人工复核模板

```yaml
case_id:
reviewer:
review_date:

dennis_agent_conclusion:
  level:
  one_sentence_judgment:
  main_skill:
  auxiliary_skills:
  key_evidence_used:
  counter_evidence_used:
  missing_evidence_declared:

human_judgment:
  level:
  judgment:
  final_risk_type:
  whether_transfer_skill:
  target_skill_if_transfer:

human_judgment_basis:
  decisive_evidence:
    - evidence:
      reason:
  decisive_counter_evidence:
    - counter_evidence:
      reason:
  business_context:
  quality_or_permission_note:

what_dennis_missed:
  - missed_item:
    impact:
    should_backwrite_to:

what_dennis_misread:
  - misread_item:
    correct_interpretation:
    impact:
    should_backwrite_to:

confidence_review:
  over_confident:
  over_conservative:
  confidence_issue_reason:

rules_to_backwrite:
  - rule:
    target_location:
    priority:
    reason:

new_test_cases_to_add:
  - case_name:
    scenario:
    expected_behavior:
    source_case_id:

online_strategy_impact:
  affects_online_strategy_suggestion:
  impact_description:
  requires_policy_review:
  requires_business_owner_confirmation:
```

## 2. 复核重点

### Dennis Agent 结论

检查 Dennis Agent 是否明确说明：

- 主控 Skill。
- 辅助 Skill。
- 证据强度。
- 反证。
- 缺口。
- 结论等级。
- 下一步补证。
- 人工确认边界。

### 人工判断

人工判断需要给出：

- 是否协议攻击。
- 是否更像破解包。
- 是否更像官方包埋点缺失。
- 是否更像前后端 join 口径问题。
- 是否更像合法自动化 / 授权工具。
- 是否更像群控真机。
- 是否证据不足。

### Dennis 漏掉了什么

常见漏项：

- 未检查官方包同版本埋点。
- 未检查 SDK 日志覆盖率。
- 未检查合法自动化授权主体和账号范围。
- 未检查群控真机统一调度。
- 未检查前后端 join key 或时间窗。
- 未保留权限不足和数据质量风险。

### Dennis 误读了什么

常见误读：

- 把前端无日志直接解释为协议。
- 把 SDK 缺失直接解释为破解包。
- 把高频接口直接解释为攻击。
- 把空结果解释为无风险。
- 把策略命中解释为风险事实。
- 把风险画像解释为事实标签。

### 是否过度自信

以下情况应标记过度自信：

- 关键反证未闭合却输出明确协议。
- Data Agent 返回 `partial`、`no_permission`、`empty_result` 时仍输出强结论。
- 未说明质量风险。
- 未说明人工确认边界。

### 是否过度保守

以下情况可标记过度保守：

- 多项强证据闭合且反证已排除，但仍只输出证据不足。
- 明确 token / device / ip / ua 冲突、接口序列固化、无端链路闭合后，未给高度疑似或明确判断。
- 已明确不是破解包、不是埋点缺失、不是合法自动化、不是群控真机，却没有升级结论等级。

## 3. 回写位置建议

优先级从轻到重：

1. `query_intent_schema_v2`：缺字段、字段不好用、下一步补证表达不足。
2. `data_join_paths_v1`：缺 join path 或 join 风险说明不足。
3. `dataagent_conclusion_thresholds_v1`：结论阈值过松或过严。
4. `normalized_evidence_schema_v1`：无法表达反证、缺失证据、质量风险。
5. Skill 文件：只有当判断规则本身缺失或边界错误时才回写。

## 4. 线上策略影响判断

本模板只记录是否影响线上策略建议，不直接触发策略变更。

需要标记影响线上策略建议的情况：

- 人工确认 Dennis Agent 存在系统性误判。
- 当前证据链支持调整灰度策略。
- 当前证据链提示已有策略存在明显误伤。
- 当前证据链提示只读试点需要扩展到新数据域或新 Skill。

所有线上策略动作必须另行人工审批。
