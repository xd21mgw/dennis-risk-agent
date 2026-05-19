# Data Agent Timeout Policy Review v1

## 0. 本轮目标

本轮补充 Data Agent timeout policy，解决“查询慢、失败、无权限、没有风险”之间的边界混淆。

边界：
- 不调用 Data Agent。
- 不修改核心 Skill。
- 不编造真实数据。
- 不写真实表名、字段名、SQL 或 API。
- timeout 只代表取证未完成，不代表没有风险。

## 1. 新增 / 修改文件

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/real_pilot/dataagent_provider_boundary_overlay_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/09_scenario_workflows/scenario_workflow_contract_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/10_agent_entrypoints/scenario_response_contract_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/adapter_design/dataagent_markdown_response_parser_v1.md`
- `outputs/reviews/dataagent_timeout_policy_review_v1.md`

## 2. Timeout Policy 摘要

### 2.1 三档阈值

- `quick_wait_threshold`: 60~120 秒。
  - 作用：提示用户查询可能较慢。
  - 不是 timeout。

- `single_call_timeout`: 5~10 分钟。
  - 作用：停止当前等待，标记 timeout。
  - 进入 pending_evidence / missing_evidence。

- `high_cost_confirmation_threshold`: 预计超过 10 分钟、长周期、多表 join、大样本回捞。
  - 作用：必须用户确认，不能自动连续执行。

### 2.2 基本规则

- timeout 只代表取证未完成，不代表没有风险。
- timeout 不能作为反证。
- timeout 后不得生成明确低风险结论。
- timeout 后应进入 `pending_evidence` / `missing_evidence`。
- 高成本查询、长周期扩窗、多表 join、大样本回捞必须用户确认。
- 同步调用模式下，不承诺自动轮询和自动等待剩余 SQL。

## 3. parser / workflow / response 一致性

### 3.1 parser

必须识别：

- `provider_status: timeout`
- `timeout_type`
- `elapsed_time`
- `partial_results_available`
- `pending_queries`
- `retry_recommended`
- `retry_with_smaller_scope`
- `user_confirmation_required`

### 3.2 workflow

`dataagent_interactive_followup` 在 timeout 场景下应：

- 说明当前只是取证未完成。
- 只展示已完成结果和 pending evidence。
- 提供等待、缩小范围、减少 join 复杂度、停止查询、换低成本问题等选项。
- 不把 timeout 当风险信号。

### 3.3 response

`dataagent_interactive_followup_response` 应展示：

- timeout 状态。
- 已完成结果。
- 仍等待的证据。
- 当前结论上限。
- timeout 不是反证的原因。
- 用户可选动作。

## 4. Mock Case 回归

### Case 1：60 秒无返回

| 字段 | 内容 |
|---|---|
| DataAgent 状态 | `provider_status=running`，未进入 timeout。 |
| parser 应识别字段 | `elapsed_time≈60s`；必要时 `timeout_type=quick_wait_exceeded`；`user_confirmation_required=false`。 |
| Dennis Agent 应输出 | 提示查询可能较慢，建议短暂等待。 |
| 当前结论上限 | 不能下结论。 |
| 用户可选动作 | A 继续等待；E 缩小范围；F 换更低成本问题。 |
| 推荐动作 | A。 |
| 是否符合 evidence provider 边界 | 符合。 |

### Case 2：5~10 分钟仍无最终结果

| 字段 | 内容 |
|---|---|
| DataAgent 状态 | `provider_status=timeout`。 |
| parser 应识别字段 | `timeout_type=single_call_timeout` 或 `query_execution_timeout`；`pending_evidence` 非空；`missing_evidence` 非空。 |
| Dennis Agent 应输出 | 标记 timeout，但不能把它当反证或无风险。 |
| 当前结论上限 | `insufficient_support` 或阶段性判断上限。 |
| 用户可选动作 | A 继续等待；B 缩小时间窗；C 减少数据域 / 降低 join 复杂度；E 停止查询并阶段性判断。 |
| 推荐动作 | B / C。 |
| 是否符合 evidence provider 边界 | 符合。 |

### Case 3：已有部分结果，剩余查询 timeout

| 字段 | 内容 |
|---|---|
| DataAgent 状态 | `provider_status=partial_completed` + 部分 pending timeout。 |
| parser 应识别字段 | `partial_results_available` 非空；`pending_queries` 非空；`interim_judgement_allowed.allowed=true`。 |
| Dennis Agent 应输出 | 允许 interim judgement，并明确哪些结果已完成，哪些仍 pending。 |
| 当前结论上限 | 阶段性结论可出，最终结论仍待闭合。 |
| 用户可选动作 | A 继续等待；B 先做阶段性判断；E 停止剩余查询；F 换低成本问题。 |
| 推荐动作 | B + A。 |
| 是否符合 evidence provider 边界 | 符合。 |

### Case 4：长周期扩窗预计成本高

| 字段 | 内容 |
|---|---|
| DataAgent 状态 | `waiting_user_choice` 或高成本预警。 |
| parser 应识别字段 | `user_confirmation_required=true`；`retry_recommended=true`；`retry_with_smaller_scope=true`。 |
| Dennis Agent 应输出 | 必须用户确认，不能自动继续。 |
| 当前结论上限 | 不变。 |
| 用户可选动作 | B 缩小时间窗；C 减少 join 复杂度；F 扩窗但需确认。 |
| 推荐动作 | B 或 C。 |
| 是否符合 evidence provider 边界 | 符合。 |

### Case 5：大样本回捞 timeout

| 字段 | 内容 |
|---|---|
| DataAgent 状态 | `provider_status=timeout`。 |
| parser 应识别字段 | `timeout_type=query_execution_timeout`；`user_confirmation_required=true`；`retry_with_smaller_scope=true`。 |
| Dennis Agent 应输出 | 建议缩小样本或先抽样，不要继续放大查询。 |
| 当前结论上限 | 不变。 |
| 用户可选动作 | B 缩小样本；D 只生成 SQL 查询计划；E 停止查询做阶段性判断。 |
| 推荐动作 | B。 |
| 是否符合 evidence provider 边界 | 符合。 |

### Case 6：只返回 SQL，没有执行结果

| 字段 | 内容 |
|---|---|
| DataAgent 状态 | `sql_only / pending_execution`。 |
| parser 应识别字段 | `batch_status=sql_only` 或 `waiting_user_choice`；`provider_status=waiting_user_choice`；`pending_evidence` 非空。 |
| Dennis Agent 应输出 | SQL-only 是取证计划，不进入证据链。 |
| 当前结论上限 | `insufficient_support`。 |
| 用户可选动作 | A 等待执行；D 只生成 SQL 查询计划；E 停止查询。 |
| 推荐动作 | D 或 A。 |
| 是否符合 evidence provider 边界 | 符合。 |

## 5. 哪些情况必须用户确认

必须用户确认：

- 预计超过 10 分钟的高成本查询。
- 长周期扩窗。
- 多表 join。
- 大样本回捞。
- 可能触及权限审批的查询。
- 需要继续执行 SQL 的场景。

## 6. timeout 是否能作为反证

不能。

timeout 只表示：

- 当前取证未完成。
- 结果未闭合。
- 需要继续等待、缩小范围或停止。

不能表示：

- 无风险。
- 风险已排除。
- 低风险成立。

## 7. 是否修改核心 Skill

未修改核心 Skill。

