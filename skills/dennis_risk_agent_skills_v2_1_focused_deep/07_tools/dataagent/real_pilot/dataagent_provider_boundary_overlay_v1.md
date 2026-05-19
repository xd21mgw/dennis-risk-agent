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

## 7. 交互式下一步选项边界

Data Agent 可以提出 `next_data_options`，用于表达“还可以继续查什么”。

Data Agent 可以输出：

- 下一批可查询数据域。
- 是否需要用户补充实体标识或时间窗。
- 是否建议执行已生成 SQL。
- 是否建议扩大时间窗。
- 是否建议继续查询某个下游行为分支。
- 查询成本或耗时的粗略提示，如低 / 中 / 高。

Data Agent 不负责：

- 决定最终 `next_action`。
- 决定 `recommended_next_provider`。
- 决定是否继续高成本 Hive 查询。
- 决定是否进入治理、处罚、冻结、扣除、封禁或策略上线。
- 把交互式选项升级为最终风险结论。

Dennis 主 Agent / Router 负责：

- 将 Data Agent 的 `next_data_options` 转成用户可选择的动作。
- 说明每个选项能验证什么证据。
- 标注查询成本：低 / 中 / 高。
- 给出推荐优先级和原因。
- 判断是否可以先输出阶段性 Dennis 判断。
- 在用户确认后，才生成下一步 Data Agent 问题。

必须显式确认的动作：

- 长周期扩窗，例如从 1 天扩到 7-10 天。
- 跨域 join，例如登录、发布、私信、内容、活动、关系网络联合查询。
- 大样本回捞或批量人群验证。
- 高成本 Hive 查询。
- 可能触及高敏字段或需要权限审批的查询。

如果用户未确认，高成本动作只能作为待选项，不得默认继续执行。

## 8. Running / Polling / Partial Completed 边界

Data Agent running / polling 状态只代表执行进度，不代表风险证据。

Data Agent 可以输出：

- process still running。
- no new output。
- 多组 SQL 的执行进度。
- 已完成 / running / failed / repaired / rerun 的任务状态。
- 已完成查询的聚合摘要。
- 剩余查询预计仍需等待或无法估计。

Dennis 主 Agent 可以：

- 向用户解释执行进度。
- 读取已完成查询的聚合摘要，形成阶段性 data_findings。
- 将仍 running 的查询写入 `pending_evidence`。
- 判断是否允许阶段性 Dennis 判断。
- 提供等待、停止、缩小范围、修复重跑、扩窗或补充数据域等选项。

Dennis 主 Agent 不得：

- 把“正在跑 / 轮询中”解释成风险信号。
- 把 SQL 字段错误、修复或重跑当作风险证据。
- 把部分完成结果包装成完整证据链。
- 在关键证据仍 pending 时输出最终判断。

阶段性判断边界：

- 如果没有可用结果，只能输出执行状态，不能输出风险判断。
- 如果部分结果可用，可以输出 interim judgement，但必须标注“阶段性”。
- 如果 pending queries 涉及关键证据，结论上限必须降级。
- 如果第一批结果已经足以支持“证据不足”，可以输出阶段性 Dennis 判断，同时说明继续查询能补什么。
- 最终判断必须等待关键证据闭合，或明确说明当前只基于已完成结果。

## 9. Timeout 边界

timeout 只代表取证未完成，不代表没有风险。

timeout 不得被解释为：

- 无风险。
- 反证成立。
- 风险已排除。
- 可以输出明确低风险结论。

timeout 后应进入：

- `pending_evidence`
- `missing_evidence`
- `quality_risks`

timeout 的处理原则：

- 当前同步调用模式下，不承诺自动轮询和自动等待剩余 SQL。
- 如果查询超过可接受阈值，应由 Dennis Agent 提示用户选择等待、缩小范围、减少 join 复杂度、只生成 SQL、停止查询或换低成本问题。
- 高成本查询、长周期扩窗、多表 join、大样本回捞必须用户确认。
- `timeout` 只能表示当前证据未闭合，不得作为反证或低风险依据。
- 如果已完成部分结果，可保留这些结果进入阶段性 data_findings，但未完成部分仍为 pending。
- timeout 后不得生成明确低风险结论。

### 9.1 超时阈值建议

建议在 Dennis Agent 侧采用三档阈值解释：

- `quick_wait_threshold`：60~120 秒，用于提示用户查询可能较慢。
- `single_call_timeout`：5~10 分钟，用于停止当前等待并标记 timeout。
- `high_cost_confirmation_threshold`：预计超过 10 分钟、长周期、多表 join、大样本回捞时，必须用户确认。

## 9. parser 期望识别的归属

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

## 10. 真实 Data Agent question 的写法边界

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

## 11. 前后端缺口案例边界

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
