# Dennis Risk Agent 与 DataAgent 真实可实现性校准说明 v1

## 0. 目的

本文件校准当前 Dennis Risk Agent 与 DataAgent 的真实协同能力，明确：

- v1 可实现的最小闭环是什么。
- 哪些能力已经成立。
- 哪些只是文档上的兼容能力，不是当前平台承诺。
- 如何在 60K chars 启动限制下做最小可用运行态。

边界：

- 不调用 Data Agent。
- 不修改核心 Skill。
- 不编造真实 API、表名、字段名、SQL。
- 不暴露完整 user_id。

## 1. 当前平台能力结论

当前内部平台的真实可实现形态是：

- `dennis-risk-agent` 可以通过 skill 触发机制直接触发 `data-agent` skill。
- Dennis Agent 可以把自己生成的自然语言问题传给 DataAgent。
- DataAgent 返回后，结果会进入 Dennis Agent 当前上下文，Dennis Agent 可以继续推理。
- 当前不支持 DataAgent `running / partial / final` 的流式中间状态回调。
- 当前没有自动暂停和自动续跑的多轮编排能力。
- 如果要用户中途确认，只能通过 session 模式 + 父 Agent 转发，而不是在一次 run 中自动暂停。
- 同一任务中可以多次触发 DataAgent skill，但会受上下文长度限制。
- DataAgent 的“只读 / evidence provider”主要是 prompt 层约束，不是硬性技术隔离。
- 当前有 session history，但没有结构化 audit trace。
- 启动注入有 60K chars 限制，不能把所有 MD 全量注入，必须按需读取。

结论：

- v1 可实现的是“同步只读取证闭环”。
- 不是“流式多轮自动编排型 Agent”。
- Dennis Agent 可以触发 DataAgent skill，并基于返回继续推理。
- DataAgent 返回后才能由 Dennis Agent 解释。
- DataAgent 运行中的中间状态不能被实时监听。

## 2. v1 支持能力

### 2.1 Dennis Agent 识别需要查数

可以：

- 根据用户问题判断是否需要 Data Agent。
- 识别缺哪些证据。
- 判断是否先做单 case、批量分层、证据规划、结果解释、治理设计或复盘沉淀。

### 2.2 Dennis Agent 生成 DataAgent 自然语言问题

可以：

- 把 query intent 编码成可复制给 Data Agent 的自然语言问题。
- 描述查询目标、时间窗、数据域、输出要求和边界提醒。
- 保持只读取证，不写真实 SQL / 表名 / 字段名 / API。

### 2.3 触发 DataAgent skill

可以：

- 由 Dennis Agent 通过 skill 调用机制触发 Data Agent。
- 在同一任务中多次触发 Data Agent skill。
- 通过 session history 承接前一轮上下文。

### 2.4 DataAgent 同步返回

可以：

- 接收 DataAgent 的最终返回文本或 markdown。
- 在返回后继续由 Dennis Agent 推理。
- 把返回当作当前上下文的一部分继续分析。

### 2.5 Dennis Agent 解释返回

可以：

- 区分 data_findings、provider_conclusion_hint、反证、缺失证据、质量风险。
- 对 DataAgent 的返回做证据分层和边界解释。
- 判断当前是否允许阶段性判断。

### 2.6 Dennis Agent 输出 dennis_final_judgement 和 next action

可以：

- 由 Dennis 主 Agent 输出最终或阶段性结论。
- 给出下一步动作。
- 给出是否需要人工确认。

### 2.7 SQL-only / no_permission / partial 的最终返回降级

可以：

- 如果 DataAgent 最终返回 SQL-only / no_permission / partial / empty_result / failed，Dennis Agent 可以降级解释。
- 可以输出 evidence insufficiency、pending evidence、next action 或人工复核要求。

## 3. v1 不支持或不承诺

### 3.1 running / polling 实时状态回调

不支持：

- DataAgent 在运行中的实时回调。
- 实时监听 SQL 执行进度。
- 自动感知“仍在运行”并在同一次 run 中持续刷新。

### 3.2 多 SQL 中间进度实时展示

不支持：

- 多组 SQL 的实时完成度展示。
- 每个 SQL 的渐进式回传。
- 运行中结果的流式拼接。

### 3.3 DataAgent 中途暂停等待用户确认

不支持：

- 在一次 run 中自动暂停并等待用户选择。
- DataAgent 自己卡在中途等待人类确认后再自动续跑。

### 3.4 自动轮询剩余 SQL

不支持：

- 自动轮询剩余 SQL 的实时追踪。
- 自动读取 running SQL 的后续状态变化。

### 3.5 自动 SQL 修复重跑后的实时追踪

不支持：

- 字段名错误修正后的自动追踪。
- 修复后重新提交的实时状态更新。

### 3.6 高成本查询的自动连续执行

不支持：

- 自动连续发起多轮高成本 Hive 查询。
- 自动扩窗后继续大样本回捞。

### 3.7 硬性只读技术隔离

不承诺：

- DataAgent 一定会被硬性技术隔离成只读。
- 只读更多是 prompt / policy 层约束和工作流约束。

### 3.8 结构化 audit trace

不支持：

- 结构化审计链路。
- 标准化可回放 trace。
- 多轮 DataAgent 交互的自动审计面板。

## 4. 对已有设计的影响

### 4.1 `dataagent_interactive_followup` 保留

保留，但 v1 只用于两类情况：

- 解释 DataAgent 最终返回中的 follow-up 信息。
- 解释用户手动贴回的中间结果或过程状态。

它不代表当前平台具备自动流式编排能力。

### 4.2 `running / polling / partial_completed` 保留

保留为 parser 能力和未来兼容能力，但不作为当前平台自动流式能力承诺。

它们表示：

- parser 可以识别这些状态。
- review / eval 可以回归这些状态。
- 未来平台能力可以升级到这些状态。

但当前 v1 不支持：

- 自动监听。
- 自动追踪。
- 自动轮询。

### 4.3 高成本查询仍必须用户确认

仍成立，但确认流程由父 Agent / 用户多轮完成：

- 不是在一次 DataAgent run 中自动暂停。
- 不是 DataAgent 自动向用户发起交互。
- 不是自动编排器在后台帮你续跑。

### 4.4 Data Agent evidence provider 边界仍有效

仍有效，但属于 prompt / policy / workflow 层约束，不是硬性技术隔离。

这意味着：

- Dennis Agent 仍应把 DataAgent 当 evidence provider。
- 但平台层不保证 DataAgent 绝对无法越界。
- 所以需要靠入口层、response contract、parser、review 共同约束。

### 4.5 `dennis_final_judgement` 仍由 Dennis Agent 生成

不变。

DataAgent 不生成最终研判。
parser 不生成最终研判。
最终判断仍由 Dennis 主 Agent 综合证据、反证、风险和业务上下文给出。

## 5. 运行态 MD 加载建议

基于 60K chars 启动限制，建议：

- `AGENTS.md` / `SOUL.md` 只放总控规则和文件索引。
- 不把 `outputs/reviews`、`eval`、历史材料默认注入。
- ATO 运行态只加载最小必要文件。
- Skill / workflow / DataAgent contract 按需 read。
- 防止上下文过载导致路由不稳定。

推荐最小加载顺序：

1. 总控规则。
2. 场景入口层 contract。
3. ATO overlay。
4. Data Agent contract / parser / boundary。
5. 相关 review 样例，仅在需要时加载。

## 6. v1 最小 POC 方案

### Test 1：不调用 Data Agent

用户问题：

“这个用户 5 月 4 日扫码后账号异常，帮我判断缺哪些证据。”

预期：

- 不触发 Data Agent。
- Dennis Agent 直接输出缺失证据、反证和下一步补证动作。
- 结论停留在证据规划或轻量判断，不做强结论。

成功标准：

- 能正确识别这是单 case 判断。
- 能说明缺哪些证据。
- 能保持 ATO 发生方式与下游作恶方式分离。

### Test 2：调用 Data Agent success 返回

用户问题：

“帮我查这个用户 5 月 4 日扫码后是不是被盗。”

预期：

- Dennis Agent 生成 DataAgent 问题。
- 触发 data-agent skill。
- DataAgent 返回后，Dennis Agent 分析 data_findings、provider_conclusion_hint、反证和缺失证据。
- Dennis Agent 输出 dennis_final_judgement。

成功标准：

- 能从返回里抽取数据发现。
- 能把 DataAgent 的提示和 Dennis final judgement 分开。
- 能给出下一步动作。

### Test 3：DataAgent 返回 SQL-only 或 partial

用户问题：

“这批样本帮我查一下扫码盗号共性。”

预期：

- DataAgent 可能只返回 SQL-only 或 partial。
- Dennis Agent 不能强判。
- 必须输出 next action。

成功标准：

- SQL-only 正确降级。
- partial 正确降级。
- 不把执行计划当证据。
- 不把 running 当风险结论。

## 7. 风险与降级方案

### 7.1 如果内部系统不能自动触发 DataAgent

降级为：

- Dennis Agent 先生成 DataAgent 问题。
- 用户或运营复制问题到 DataAgent。
- 返回后再由 Dennis Agent 解释。

### 7.2 如果 DataAgent 返回无法回到上下文

降级为：

- 用户贴回 DataAgent 返回。
- Dennis Agent 重新做解析。

### 7.3 如果上下文太长

降级为：

- 最小运行态加载。
- 只读最相关 contract、workflow、parser 和 case review。

### 7.4 如果只读无法硬控

降级为：

- 依赖 DataAgent 权限层控制。
- 依赖 prompt / policy / workflow 约束。
- 依赖 Dennis 的边界解释和 review 校准。

## 8. 结论

当前不是已经完成全自动 DataAgent 编排。

当前具备的是：

- 同步 skill 调用式最小闭环。
- 可由 Dennis Agent 触发 DataAgent。
- 可在 DataAgent 返回后继续推理。
- 可做阶段性解释和证据分层。

下一步应先做最小 POC，而不是继续扩展文档或大批量 case。

