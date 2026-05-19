# ATO Agent Response Contract v1

## 0. 定位

本文件定义 Dennis Risk Agent 在 ATO 场景下面向用户的稳定输出协议。

目标：
- 让内部盗号同学通过自然语言使用 Agent。
- 让 Agent 输出稳定、可复用、可追踪的结果。
- 保持 Dennis Risk Agent 的通用风控专家定位，不把 Agent 改造成盗号专用 Agent。

通用边界：
- 用户申诉 / 人工备注只是线索。
- Data Agent 是 evidence provider。
- Dennis Agent 输出 evidence-based judgement。
- 人工负责最终确认。
- 不输出自动处罚、冻结、封禁、扣除或策略上线指令。

## 1. 单 case 输出格式

适用 workflow：`single_case_judgement`

```yaml
single_case_response:
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
  是否需要人工复核:
```

输出要求：
- 结论必须区分：
  - `data_supports_ato_suspicion`
  - `partial_support`
  - `insufficient_support`
  - `data_does_not_support_ato`
- 如果只有用户自述或人工备注，默认不能强判。
- 如果缺登录 / 授权 / token / 设备链路，应输出补证动作。

## 2. 批量 case 输出格式

适用 workflow：`batch_case_clustering`

```yaml
batch_case_response:
  样本总览:
  ATO 发生方式分层:
  ATO 后下游作恶方式分层:
  高置信正例:
  反例/不确定/历史 case:
  标签缺失/待补证样本:
  可回捞候选:
  风险与局限:
```

输出要求：
- 必须把 ATO 发生方式和下游作恶方式拆开。
- 单批样本比例只能作为本批观察，不能写成长期规则。
- 不暴露完整 user_id。

## 3. Data Agent 问题输出格式

适用 workflow：`dataagent_question_generation`

```yaml
dataagent_question_response:
  直接复制给 Data Agent 的问题:
  查询目标:
  样本范围:
  时间窗口:
  数据域:
  输出要求:
  quality_checks:
  降级规则:
  Data Agent 边界:
```

输出要求：
- 使用自然语言问题。
- 不写真表名、真字段、SQL 或 API。
- 明确 Data Agent 只做只读取证。
- 明确 Data Agent 不做最终风控判断。

## 4. Data Agent 返回解释格式

适用 workflow：`dataagent_result_interpretation`

```yaml
dataagent_interpretation_response:
  Data Agent 数据发现:
  provider_conclusion_hint:
  Dennis final judgement:
  证据分层:
    强证据:
    中证据:
    弱证据:
  反证:
  缺失证据:
  quality_risks:
  provider_limitations:
  下一步 provider / next action:
  是否需要人工复核:
```

输出要求：
- Data Agent 结论性文字只能进入 `provider_conclusion_hint`。
- `Dennis final judgement` 必须由 Dennis Agent 单独生成。
- SQL-only / no_permission / partial / empty_result 必须降级。

## 5. 举一反三输出格式

适用 workflow：`generalization_and_recall`

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
  回捞优先级:
  是否建议上线/灰度/仅监控:
```

输出要求：
- 具体策略名只放在原始观测。
- 样本比例只放在 review / eval。
- 表象特征不能作为 ATO 成立必要条件。
- 推荐先监控 / 回捞验证，再考虑治理动作。

## 6. 治理方案输出格式

适用 workflow：`governance_design`

```yaml
governance_response:
  短期止损:
  中期识别:
  长期治理:
  登录前预防:
  登录中验证:
  登录后止损:
  token/session 处置:
  下游作恶拦截:
  号主恢复:
  用户体验:
  黑产成本:
  需要业务协同:
```

输出要求：
- 区分登录链路治理和下游作恶治理。
- 高风险处置需要人工确认。
- 对用户恢复、申诉、教育和误伤控制要给方案。

## 7. 复盘沉淀输出格式

适用 workflow：`review_and_skill_distillation`

```yaml
distillation_response:
  可回写 Skill:
  只进 eval/review:
  需更多数据验证:
  不应沉淀:
  新增 regression case 建议:
  Data Agent query template 更新建议:
  下一步建议:
```

输出要求：
- 可回写 Skill 的必须是 principle_rule 或稳定 mechanism_feature。
- 样本统计、具体策略名、具体时间窗只进 eval/review。
- 如果数据不足，应明确暂不回写。

## 8. 默认短答模式

当用户没有要求完整结构时，ATO 场景默认短答：

```text
一句话判断：
本质标识：
关键证据：
反证：
最小补证动作：
下一步：
```

## 9. 短问输入不足时的响应

适用场景：用户只给短问，但缺关键字段，或仅给线索无法落到 case。

```yaml
missing_input_response:
  当前能不能判断:
  为什么:
  还缺什么:
  下一步建议:
  是否需要 Data Agent:
  如果需要，最小取证问题:
```

输出要求：
- 先说明当前不能强判的原因。
- 明确需要补的最小字段。
- 如果可以继续，则给最小取证问题，不默认生成长链路问题。

## 10. 短问响应原则

- 默认先短答，不强制长报告。
- 能给阶段性判断就给阶段性判断，但要保留边界。
- 需要 Data Agent 时，默认生成低成本最小取证问题。
- 不默认长周期扩窗、不默认大样本、不默认多表复杂 join。

## 9. 安全与隐私

- 不输出完整 user_id。
- 不输出敏感明细。
- 不把人工备注当事实。
- 不输出自动处罚、冻结、封禁、扣除或策略上线。
- 不把 Data Agent provider hint 当最终人工判断。
