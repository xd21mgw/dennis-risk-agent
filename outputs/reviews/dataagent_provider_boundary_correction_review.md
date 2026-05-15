# Data Agent Provider Boundary Correction Review

## 1. 当前偏差点

近期 Data Agent 模拟返回和回归样例中出现较多：

- 结论等级。
- recommended_next_provider。
- parser 期望识别。
- 强 / 中 / 弱证据预期。
- 类似最终研判的表达。

风险：

- Data Agent 被误当成最终风控裁判。
- Router 的工具选择职责被 Data Agent 侵入。
- Dennis 主 Agent 的 final judgement owner 角色被削弱。
- 真实 Data Agent question 可能夹带 parser 测试要求。

## 2. 修正后的职责边界

Data Agent：

- 输出数据发现、覆盖范围、缺失证据、权限限制、口径风险。
- 结论性文字只能作为 `provider_conclusion_hint`。

Parser：

- 抽取数据发现。
- 抽取 provider_conclusion_hint。
- 抽取 missing evidence、counter evidence、quality risks。
- 不输出 final judgement。

Router：

- 根据 missing_evidence 和 provider_limitations 生成 recommended_next_provider。

Dennis 主 Agent：

- 输出 `dennis_final_judgement`。
- 输出结论等级、治理建议、人工确认边界。

## 3. 修正前后字段流转对比

| 字段 / 内容 | 修正前风险 | 修正后归属 |
|---|---|---|
| Data Agent “高度疑似” | 可能被当最终结论 | `provider_conclusion_hint` |
| dennis_final_judgement | 可能被 provider 侵入 | 只能 Dennis 主 Agent 生成 |
| recommended_next_provider | 可能由 Data Agent 直接给 | Router / Dennis 生成 |
| parser 期望识别 | 可能进入真实 question | 仅 mock / 回归 / 校准使用 |
| 缺失证据 | Data Agent / parser 均可输出 | normalized evidence 输入 |
| 口径风险 | Data Agent / parser 均可输出 | quality_risks |

## 4. 案例演示：后端有请求、前端无日志

### Data Agent 输出什么

Data Agent 应输出：

- 后端请求是否存在。
- 前端日志是否有匹配。
- 查询覆盖了哪些数据域。
- 哪些数据域无权限或未覆盖。
- SDK / 版本 / 包类型是否有数据发现。
- 缺失的策略引擎、实时日志、关系网络、授权运营证据。
- join 口径风险。
- 数据侧提示，例如“存在协议疑点”，但只能作为 provider_conclusion_hint。

Data Agent 不应输出：

- Dennis 最终判断。
- recommended_next_provider。
- 处罚 / 冻结 / 策略上线建议。
- parser 期望识别。

### Parser 映射什么

Parser 映射：

- key_findings：后端请求、前端匹配情况、SDK / 版本 / 包线索。
- missing_evidence：实时日志、策略引擎、群控标签、授权工具白名单。
- counter_evidence：埋点缺失、join 口径、合法自动化、群控真机。
- quality_risks：权限、时效、口径、SQL-only、empty_result。
- provider_limitations：Data Agent-only、缺 realtime / device / risk engine。
- provider_conclusion_hint：Data Agent 的“疑似协议”等文字。

Parser 不映射：

- dennis_final_judgement。
- Router 决策。
- 自动治理动作。

### Dennis 主 Agent 最终判断什么

Dennis 主 Agent 基于 normalized evidence 输出：

- 结论等级：明确判断 / 高度疑似 / 证据不足 / 反向排除。
- 为什么不能强结论。
- 下一步 provider。
- 治理建议。
- 人工复核边界。

示例：

```text
当前最多支持协议疑点；若缺 realtime log、device fingerprint、risk engine、授权白名单和群控反证，则不能明确协议攻击。
```

## 5. 本轮修改

新增：

- `dataagent_provider_boundary_overlay_v1.md`
- `dataagent_response_to_unified_evidence_mapping_v1.md`
- `dataagent_sse_markdown_parser_rules_v1.md`
- `dataagent_provider_boundary_correction_review.md`

更新：

- `query_intent_to_question_encoder_v1.md`
- `dataagent_markdown_response_parser_v1.md`

## 6. 是否修改核心 Skill

否。本轮只修改 Data Agent real_pilot / adapter_design / parser 相关文档和 review 输出。

