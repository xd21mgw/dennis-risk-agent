# Scenario Workflow Contract v1

## 0. 定位

本文件定义 Dennis Risk Agent 场景 workflow 的通用输入、输出和边界。

场景 workflow 的职责是调度已有 Skill、证据卡、Data Agent 模板和 response contract，不复制或重写核心 Skill。

ATO workflow 是该 contract 的第一个实现。未来反爬、群控、活动反作弊、渠道抢量等场景可复用本 contract。

## 1. Workflow 标准结构

每个 workflow 必须声明：

```yaml
workflow:
  workflow_name:
  applicable_questions:
  input_information:
  primary_skill:
  auxiliary_skills:
  dataagent_needed:
  manual_review_required:
  output_structure:
  forbidden_behaviors:
```

## 2. 通用 Workflow 定义

### 2.1 single_case_judgement

适用问题：
- 单个用户 / 设备 / 请求 / 活动 / 内容 / 商家是否风险。
- 单个客诉或异常是否可信。

输入信息：
- case_id 或实体标识。
- 用户描述 / 业务描述。
- 异常时间。
- 异常行为。
- 已有证据。
- 人工备注，可选。
- Data Agent 返回，可选。

输出结构：
- 当前结论。
- 支持证据。
- 反证。
- 缺失证据。
- 下一步补证。
- 是否需要 Data Agent。
- 是否需要人工复核。

禁止行为：
- 证据不足强结论。
- 将用户描述或人工备注当事实。
- 自动输出处罚 / 冻结 / 扣除 / 策略上线。

### 2.2 batch_case_clustering

适用问题：
- 批量 case 分层。
- 样本共性分析。
- 正反例和不确定样本拆分。

输入信息：
- case 列表。
- 标签 / 备注。
- 用户描述。
- 已有数据发现。

输出结构：
- 风险场景分层。
- 攻击手法分层。
- 下游作恶分层，如适用。
- 高置信正例。
- 反例 / 不确定 / 历史 case。
- 标签缺失 / 待补证样本。
- 样本统计和边界。

禁止行为：
- 把单批样本比例写成长期规则。
- 只保留正例，不保留反例。
- 自动修正标签为空值的样本。

### 2.3 evidence_planning

适用问题：
- 需要什么证据。
- 证据够不够。
- 如何写证据卡 / 查数卡。

输入信息：
- 风险问题。
- 目标结论。
- 可用样本。
- 已知证据。

输出结构：
- 目标证据。
- 强 / 中 / 弱证据。
- 反证。
- 缺失证据。
- 数据域。
- join path。
- 质量风险。

禁止行为：
- 只列数据，不说明结论阈值。
- 忽略反证。
- 将 Data Agent 计划当数据结果。

### 2.4 dataagent_question_generation

适用问题：
- 生成可复制给 Data Agent 的只读取证问题。

输入信息：
- case_id / batch_id。
- 实体标识。
- time_window。
- 业务场景。
- 目标证据。
- 已知边界。

输出结构：
- Data Agent 自然语言问题。
- 查询目标。
- 样本范围。
- 时间窗口。
- 数据域。
- 输出要求。
- quality_checks。
- 降级规则。

禁止行为：
- 写真实 API。
- 写真实表名、字段名、SQL。
- 要求 Data Agent 给最终处罚或最终定性。

### 2.5 dataagent_result_interpretation

适用问题：
- 解释 Data Agent 返回。
- 判断数据够不够支持结论。

输入信息：
- Data Agent response。
- 原始 query intent / question。
- 预期证据。
- case 范围。

输出结构：
- Data Agent 数据发现。
- provider_conclusion_hint。
- Dennis final judgement。
- 强 / 中 / 弱证据。
- 反证。
- 缺失证据。
- 质量风险。
- 下一步 provider / next action。

禁止行为：
- 将 provider_conclusion_hint 当最终判断。
- SQL-only 进入证据链。
- empty_result 解释为无风险。
- no_permission 时强结论。

### 2.6 dataagent_interactive_followup

适用问题：
- Data Agent 分批返回，只返回第一批结果。
- Data Agent 只生成 SQL，并询问是否执行。
- Data Agent 返回 partial，需要选择继续查哪个数据域。
- Data Agent 仍在运行，提示 process still running / polling / no new output。
- 多组 SQL 部分完成，部分仍 running。
- SQL 字段错误被修复后重新提交。
- Data Agent 建议扩大时间窗。
- Data Agent 需要用户补充 user_id / device_id / session_id / trace_id / risk_event_id / request_id 或 time_window。
- Data Agent 提供多个后续取数方向。

输入信息：
- Data Agent 当前返回。
- 原始 Data Agent question 或 query intent。
- 当前已完成查询。
- 当前数据发现摘要。
- 当前缺失证据。
- Data Agent 提出的 next_data_options，如有。
- 当前执行状态：running / partial_completed / completed / failed / timeout。
- 已完成、仍运行、失败、修复重跑的查询摘要。
- 可用的部分结果和仍待返回的 pending evidence。
- 用户可接受的查询成本 / 时间窗 / 样本范围。

输出结构：
- 当前已完成查询。
- 当前执行状态。
- 已完成查询、仍在运行查询、失败 / 修复查询。
- 当前数据发现摘要。
- 当前可用数据发现。
- 仍等待的证据。
- 当前结论上限。
- 缺失证据。
- Data Agent 给出的可选下一步。
- Dennis Agent 推荐优先级。
- 每个选项的查询成本：低 / 中 / 高。
- 每个选项能验证什么。
- 是否需要用户确认。
- 可复制给 Data Agent 的下一步问题。
- 是否可以先输出阶段性 Dennis 判断。

禁止行为：
- 将 Data Agent 的 next_data_options 直接当最终 next_action。
- 在 SQL-only / running / partial 状态下输出强结论。
- 将 “process still running” 当风险信号。
- 将 SQL 修复 / 重跑动作当风险证据。
- 将仍 running 的查询当作已完成证据。
- 未经用户确认就建议继续高成本 Hive、长周期扩窗、跨域 join 或大样本回捞。
- 将“扩大时间窗”当默认动作，必须先说明成本和能验证什么。
- 将交互式下一步选择写成自动治理或自动策略上线。

运行中 / polling 分支：

- Data Agent 仍在运行且无可用结果时，Dennis Agent 应只展示执行进度、已等待内容和用户选项，不输出风险结论。
- 如果已有部分 SQL 完成，Dennis Agent 可以读取已完成聚合摘要，形成阶段性 `data_findings`。
- 如果未完成 SQL 对关键证据有决定性影响，必须等待最终结果，或明确输出“阶段性判断，不是最终判断”。
- 如果已完成结果足以说明“当前证据不足”，可以停止剩余高成本查询并输出阶段性 Dennis 判断，但要保留 pending evidence。
- 如果用户希望节省成本，Dennis Agent 应提供等待、停止、缩小范围、继续高成本查询等选项，并推荐低成本优先。
- SQL 字段错误修复重跑时，Dennis Agent 只记录 `sql_repair_state` 和执行轨迹，不把修复动作写入证据链。

### 2.7 generalization_and_recall

适用问题：
- 举一反三。
- 回捞建议。
- 特征抽象。

输入信息：
- 单 case / batch findings。
- 正反例。
- 质量风险。

输出结构：
- 原始观测。
- 数据发现。
- 候选特征。
- 机制特征。
- 本质规则。
- 正反例验证方案。
- 误伤风险。
- 回捞优先级。

禁止行为：
- 将具体策略名写成本质特征。
- 将表象特征作为风险成立必要条件。
- 未经反例验证直接建议上线。

### 2.8 governance_design

适用问题：
- 设计治理方案。
- 灰度策略。
- 误伤控制。

输入信息：
- 风险类型。
- 证据强度。
- 业务影响。
- 用户体验约束。

输出结构：
- 短期止损。
- 中期识别。
- 长期治理。
- 用户体验。
- 黑产成本。
- 业务协同。
- 灰度和指标。

禁止行为：
- 自动处罚、冻结、扣除、封禁。
- 不考虑误伤。
- 只有“加强监控”。

### 2.9 review_and_skill_distillation

适用问题：
- 是否回写 Skill。
- 是否新增回归 case。
- 哪些只进 eval。

输入信息：
- case review。
- batch review。
- Data Agent findings。
- regression results。

输出结构：
- 可回写 Skill。
- 只进 eval / review。
- 需更多数据验证。
- 不应沉淀。
- 新增 regression case。
- 下一步建议。

禁止行为：
- 将单批统计写入 Skill。
- 将具体策略名写入本质规则。
- 缺少反例就回写。

## 3. 通用边界

- Data Agent 只作为 evidence provider。
- final judgement 由 Dennis 主 Agent 生成。
- 证据不足必须降级。
- 高风险治理动作不得自动执行。
- 场景 workflow 只能调度已有 Skill / 证据卡 / Data Agent 模板，不应复制重写核心 Skill。

## 4. Scenario Overlay 继承方式

每个场景可以继承通用 workflow，然后补充场景特有内容：

```text
scenario_workflow_contract_v1
→ ato_account_takeover_workflows_v1
→ future anti_crawler_workflows_v1
→ future group_control_workflows_v1
→ future activity_anti_cheating_workflows_v1
```
