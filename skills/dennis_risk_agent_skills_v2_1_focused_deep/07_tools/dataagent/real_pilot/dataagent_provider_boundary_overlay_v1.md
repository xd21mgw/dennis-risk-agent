# Data Agent Provider Boundary Overlay v1

## 0. 目标

本文件用于校正 v2.4 Data Agent-only 只读试点边界。

核心原则：

- Data Agent 是 evidence provider。
- Dennis 主 Agent 是 final judgement owner。
- Evidence Tool Router 负责工具选择和 recommended_next_provider。
- Parser 负责把 Data Agent markdown 映射为 normalized evidence，不负责最终风控裁判。

## 1. Data Agent 定位：Evidence Provider

Data Agent 在当前架构中只负责数据平台侧取证和数据发现。

Data Agent 可以作为：

- Hive / 离线取数 provider。
- BI / 看板 / 数据集分析 provider。
- SQL 生成 provider。
- 表检索 / 字段口径 provider。
- AB 实验分析 provider。
- 画像标签 / 人群圈选 provider。
- 离线趋势 / 聚合 / 归因 / 复盘 provider。

Data Agent 不是：

- 最终风控裁判。
- 策略决策器。
- 处罚执行器。
- provider 路由器。
- 线上治理系统。

## 2. Dennis 主 Agent 定位：Final Judgement Owner

Dennis 主 Agent 负责：

- 风险理解。
- Skill 路由。
- 证据强弱解释。
- 反证和误判识别。
- 结论等级输出。
- 治理建议。
- 灰度和人工确认边界。
- `dennis_final_judgement`。

只有 Dennis 主 Agent 可以输出：

- 明确判断 / 高度疑似 / 证据不足 / 反向排除。
- 是否进入治理。
- 是否需要人工确认。
- 是否需要回写 Skill / schema / router / parser。

## 3. Data Agent 可以输出什么

真实 Data Agent question 只能要求 Data Agent 输出：

- 数据发现。
- 查询覆盖范围。
- 查询时间窗。
- 可见数据域。
- 未覆盖数据域。
- 缺失证据。
- 权限限制。
- 口径风险。
- 数据质量风险。
- SQL / 查询逻辑，如 Data Agent 只能生成查询方案。
- 数据侧提示，即 `provider_conclusion_hint`。

Data Agent 的数据侧提示可以包括：

- “从已查数据看存在异常线索”。
- “当前数据不足以判断”。
- “需要补充某类证据”。
- “该结果可能受口径影响”。

## 4. Data Agent 不应该输出什么

真实 Data Agent question 不应要求 Data Agent 输出：

- `dennis_final_judgement`。
- 最终风控定性。
- 处罚、冻结、扣除、封禁建议。
- 策略上线建议。
- `recommended_next_provider`。
- Router 决策。
- parser 期望识别。
- 强 / 中 / 弱证据的最终风险裁判口径。
- 自动治理动作。

如果 Data Agent markdown 中自然出现“疑似协议攻击”“高度疑似”等结论性文字，parser 只能把它抽取为 `provider_conclusion_hint`。

## 5. provider_conclusion_hint 与 dennis_final_judgement

### provider_conclusion_hint

来源：

- Data Agent markdown 中的数据侧判断倾向。

含义：

- provider 基于当前可见数据给出的提示。
- 可能受权限、口径、数据域覆盖、SQL 是否执行、markdown 推测影响。
- 只能辅助 Dennis 主 Agent 判断。

限制：

- 不等于最终结论。
- 不得直接触发治理。
- 不得直接进入线上策略。
- 不得覆盖 missing_evidence、counter_evidence、quality_risks。

### dennis_final_judgement

来源：

- Dennis 主 Agent 综合 normalized evidence、Skill 边界、业务上下文、反证、误伤风险后输出。

含义：

- 风控研判结论。
- 需要明确证据强度、反证、缺口和人工确认边界。

限制：

- 不由 Data Agent 直接填充。
- 不由 parser 直接填充。
- 不由单一 provider 自动生成。

## 6. recommended_next_provider 的归属

`recommended_next_provider` 由 Evidence Tool Router / Dennis 主 Agent 生成。

生成依据：

- `missing_evidence`
- `provider_limitations`
- `quality_risks`
- `permission_notes`
- 当前 query intent 的目标证据
- 当前试点阶段 active provider

Data Agent 可以输出“缺失什么证据”，但不负责决定“下一步接哪个 provider”。

示例：

- Data Agent 输出：缺少实时前端日志。
- Router / Dennis 输出：recommended_next_provider = `realtime_log_provider`。

## 7. parser 期望识别的归属

“parser 期望识别”只属于：

- mock 样例。
- parser 单元测试。
- 回归评测。
- 校准报告。

真实 Data Agent question 中不得包含：

- parser 期望识别。
- status 期望。
- returned_type 期望。
- strong_evidence / medium_evidence / weak_evidence 期望。
- recommended_next_provider 期望。

真实链路应为：

```text
Data Agent 输出自然语言 / markdown
→ parser 映射为 normalized evidence
→ Router / Dennis 生成 recommended_next_provider
→ Dennis 主 Agent 输出 dennis_final_judgement
```

## 8. 真实 Data Agent question 的写法边界

真实 question 应要求：

- 做只读取证。
- 输出数据发现。
- 输出覆盖范围。
- 输出缺失证据。
- 输出权限限制。
- 输出口径风险。
- 区分数据发现和推测。
- 不要给处罚、冻结、扣除、封禁、策略上线建议。
- 不要把前端无日志直接判协议。
- 不要把低钱效直接判黑产。
- 不要把策略命中直接当风险事实。

真实 question 不应要求：

- 输出最终结论等级。
- 决定下一步 provider。
- 填写 parser schema。
- 输出治理处置。
- 直接替 Dennis 主 Agent 做研判。

## 9. 前后端缺口案例边界

对于“后端有请求、前端无日志”：

Data Agent 应输出：

- 后端请求是否存在。
- 前端日志是否覆盖。
- 可见 SDK / 版本 / 包类型线索。
- 查询覆盖范围。
- 缺失的实时日志、策略、关系、授权证据。
- join 口径风险。
- 权限限制。
- provider_conclusion_hint，如“存在数据侧疑点”。

Parser 应映射：

- key_findings。
- missing_evidence。
- counter_evidence。
- quality_risks。
- provider_limitations。
- provider_conclusion_hint。

Dennis 主 Agent 才输出：

- 是否协议攻击。
- 结论等级。
- 为什么不能强结论。
- 下一步 provider。
- 治理建议和人工确认边界。

