# Data Agent Running / Polling State Workflow Review v1

## 0. 回归定位

本轮基于 Data Agent interactive follow-up 设计，补充执行中 / polling / 部分 SQL 完成 / SQL 修复重跑等状态支持。

边界：
- 不调用 Data Agent。
- 不修改核心 Skill。
- 不编造真实数据。
- 不写真实表名、字段名、SQL 或 API。
- Data Agent running / polling 只代表执行进度，不代表风险证据。
- Dennis Agent 可以输出阶段性判断，但必须标注 interim，并保留 pending evidence。

## 1. 本轮修改文件

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/adapter_design/dataagent_markdown_response_parser_v1.md`
  - 新增 `provider_status`、`query_execution_summary`、`polling_state`、`sql_repair_state`、`pending_evidence`、`interim_judgement_allowed`。
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/09_scenario_workflows/scenario_workflow_contract_v1.md`
  - 在 `dataagent_interactive_followup` 中补充 running / polling / SQL repair 分支。
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/10_agent_entrypoints/scenario_response_contract_v1.md`
  - 在 `dataagent_interactive_followup_response` 中补充执行进度展示字段和用户可选动作。
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/real_pilot/dataagent_provider_boundary_overlay_v1.md`
  - 补充 running / polling / partial completed 边界。

## 2. Mock Case 回归

### Case 1：4 组 SQL，3 组完成，1 组 running

| 字段 | 内容 |
|---|---|
| Data Agent 返回摘要 | 共 4 组 SQL。登录、设备、账号安全事件已完成；下游行为 SQL 仍 running。 |
| parser 应识别字段 | `provider_status=partial_completed`；`batch_status=polling` 或 `waiting_remaining_queries`；`query_execution_summary.total_queries_count=4`；`completed_queries_count=3`；`running_queries_count=1`；`available_partial_results=[登录, 设备, 账号安全事件]`。 |
| execution progress summary | 3/4 completed，1/4 running。 |
| available data findings | 已完成 SQL 的聚合摘要可以进入 `data_findings`，但只能表示局部证据。 |
| pending evidence | 下游行为证据仍 pending。 |
| Dennis Agent 当前结论上限 | 局部支持 / 整体证据不足，不能输出最终判断。 |
| 是否允许 interim judgement | 允许。原因：已有 3 组结果可支持阶段性解释，但下游行为未闭合。 |
| 用户可选动作 | A 等待剩余 SQL 完成；B 先读已完成结果做阶段性判断；C 停止查询输出阶段性结论；E 缩小下游行为查询范围。 |
| 推荐动作 | B + A：先解释已完成结果，同时继续等待剩余 SQL。 |
| 是否符合 Data Agent evidence provider 边界 | 符合。running 不进入 evidence，已完成结果可进入阶段性 data_findings。 |

### Case 2：Process still running / no new output

| 字段 | 内容 |
|---|---|
| Data Agent 返回摘要 | 返回 “Process still running / no new output”，未给新数据结果。 |
| parser 应识别字段 | `provider_status=running`；`batch_status=polling`；`polling_state.process_still_running=true`；`no_new_output=true`；`next_poll_recommended=true`；`interim_judgement_allowed.allowed=false`。 |
| execution progress summary | 进程仍在运行，暂无新输出。 |
| available data findings | 无新增可用数据发现。 |
| pending evidence | 原 query intent 目标证据全部或大部分仍 pending。 |
| Dennis Agent 当前结论上限 | 无风险结论，只能说明执行状态。 |
| 是否允许 interim judgement | 不允许。原因：没有新结果可解释。 |
| 用户可选动作 | A 等待剩余 SQL 完成；C 停止继续查询并输出“当前无可用证据”；E 缩小查询范围。 |
| 推荐动作 | A：继续轮询一次；如果长时间无输出，再考虑 E。 |
| 是否符合 Data Agent evidence provider 边界 | 符合。process running 不被解释为风险信号。 |

### Case 3：SQL 字段错误，修正后重新提交

| 字段 | 内容 |
|---|---|
| Data Agent 返回摘要 | 某组 SQL 因字段名错误失败，Data Agent 修正字段映射后重新提交，当前 rerun running。 |
| parser 应识别字段 | `provider_status=running`；`batch_status=sql_repaired_rerun`；`sql_repair_state.sql_error_detected=true`；`sql_error_type=field_name_error`；`repair_attempted=true`；`rerun_submitted=true`；`repaired_query_status=running`。 |
| execution progress summary | 原 SQL 失败，已修复重跑，等待新结果。 |
| available data findings | SQL 修复本身不是数据发现；若其他 SQL 已完成，可单独读取。 |
| pending evidence | 修复重跑 SQL 对应证据 pending。 |
| Dennis Agent 当前结论上限 | 证据不足或局部阶段性判断，取决于其他已完成结果。 |
| 是否允许 interim judgement | 条件允许。只有其他已完成结果可解释时才允许，否则不允许。 |
| 用户可选动作 | A 等待重跑完成；D 修正失败 SQL 后重跑；E 缩小查询范围。 |
| 推荐动作 | A：等待 rerun 结果；若再次失败，转 E 或人工检查查询逻辑。 |
| 是否符合 Data Agent evidence provider 边界 | 符合。SQL 修复动作只进入 execution trace，不进入风险证据。 |

### Case 4：登录链路已完成，下游行为 SQL 仍 running

| 字段 | 内容 |
|---|---|
| Data Agent 返回摘要 | 登录/授权链路 SQL 已完成并显示账号接管线索；发布/私信/接口访问 SQL 仍 running。 |
| parser 应识别字段 | `provider_status=partial_completed`；`batch_status=partial_completed`；`available_partial_results=[登录/授权链路]`；`pending_evidence=[下游作恶方式]`；`interim_judgement_allowed.allowed=true`。 |
| execution progress summary | 入口链路完成，下游行为待返回。 |
| available data findings | 登录/授权链路可进入 data_findings。 |
| pending evidence | 发布、私信、接口访问、活动等下游行为仍 pending。 |
| Dennis Agent 当前结论上限 | 可输出“登录链路阶段性支持 ATO 嫌疑”，但下游作恶方式未闭合。 |
| 是否允许 interim judgement | 允许，必须标注 interim。 |
| 用户可选动作 | A 等待下游 SQL 完成；B 先读取登录链路阶段性判断；C 停止下游查询；E 缩小下游查询范围。 |
| 推荐动作 | B + A：先给入口链路阶段性判断，同时等待下游结果。 |
| 是否符合 Data Agent evidence provider 边界 | 符合。入口链路和下游作恶被分层，不把下游 pending 当作无风险。 |

### Case 5：多个 SQL 长时间 running，用户希望节省成本

| 字段 | 内容 |
|---|---|
| Data Agent 返回摘要 | 多个跨域 SQL 长时间 running，Data Agent 提示查询成本较高。用户希望节省成本。 |
| parser 应识别字段 | `provider_status=running`；`batch_status=polling`；`estimated_query_cost.level=high`；`needs_user_confirmation=true`；`polling_state.estimated_remaining_unknown=true`。 |
| execution progress summary | 多组 SQL 长时间运行，剩余时间未知。 |
| available data findings | 取决于是否已有完成结果；没有完成结果则为空。 |
| pending evidence | 跨域 join 相关证据 pending。 |
| Dennis Agent 当前结论上限 | 如果无可用结果，则不能判断；若已有部分结果，只能阶段性判断。 |
| 是否允许 interim judgement | 条件允许。没有可用结果时不允许；有完成结果时允许阶段性。 |
| 用户可选动作 | A 等待；C 停止并输出当前证据上限；E 缩小查询范围；F 扩窗或补域但需确认。 |
| 推荐动作 | E：缩小查询范围，优先查最能影响结论的低成本证据；必要时 C 输出阶段性结论。 |
| 是否符合 Data Agent evidence provider 边界 | 符合。成本控制由用户确认，Dennis 推荐低成本优先。 |

### Case 6：第一批结果足够支持“证据不足”

| 字段 | 内容 |
|---|---|
| Data Agent 返回摘要 | 第一批登录、授权和账号安全事件均未发现异常链路；下游行为查询仍 running，但当前缺少 ATO 入口证据。 |
| parser 应识别字段 | `provider_status=partial_completed`；`batch_status=first_batch` 或 `partial_completed`；`available_partial_results=[登录, 授权, 账号安全事件]`；`pending_evidence=[下游行为]`；`interim_judgement_allowed.allowed=true`。 |
| execution progress summary | 入口证据已完成且未支持 ATO；下游仍 pending。 |
| available data findings | 入口链路未发现异常登录/授权/token/session 线索。 |
| pending evidence | 下游作恶方式仍 pending。 |
| Dennis Agent 当前结论上限 | 阶段性 `insufficient_support`。不能反向断言无风险。 |
| 是否允许 interim judgement | 允许。原因：ATO 入口证据不足已足以支持阶段性证据不足。 |
| 用户可选动作 | B 先输出阶段性判断；C 停止继续查询；A 等待下游结果；E 缩小下游查询范围。 |
| 推荐动作 | B 或 C：如果目标是判断 ATO 入口，当前可输出阶段性证据不足；如还要查下游风险，再等待或缩小范围。 |
| 是否符合 Data Agent evidence provider 边界 | 符合。证据不足是阶段性 Dennis 判断，不是 Data Agent 最终裁判。 |

## 3. running / polling 状态如何被 parser 识别

parser 通过以下字段表达执行进度：

```yaml
provider_status:
batch_status:
query_execution_summary:
polling_state:
sql_repair_state:
pending_evidence:
interim_judgement_allowed:
```

识别重点：
- running / polling 是执行进度，不是风险证据。
- partial_completed 可产生阶段性 data_findings。
- SQL repaired / rerun 只进入 execution trace。
- pending queries 必须进入 pending_evidence 或 missing_evidence。

## 4. Dennis Agent 如何展示执行进度

标准输出包括：
- 当前执行状态。
- 已完成查询。
- 仍在运行查询。
- 已失败 / 已修复查询。
- 当前可用数据发现。
- 仍等待的证据。
- 当前结论上限。
- 是否可以阶段性判断。
- 用户可选动作。

用户可选动作：
- A. 等待剩余 SQL 完成。
- B. 先读取已完成结果，做阶段性判断。
- C. 停止继续查询，基于当前证据输出阶段性结论。
- D. 修正失败 SQL 后重跑。
- E. 缩小查询范围，降低 Hive 成本。
- F. 扩大时间窗或补充数据域，但必须用户确认。

## 5. 哪些情况下可以阶段性判断

可以：
- 部分 SQL 已完成，且结果能解释局部证据。
- 登录链路已完成，下游行为仍 pending，可输出“入口链路阶段性判断”。
- 第一批结果已经足以支持“当前证据不足”，同时保留 pending evidence。

不可以：
- 只有 process still running / no new output。
- 只有 SQL 修复重跑状态，没有任何可用结果。
- pending queries 覆盖关键证据，且当前结果无法解释核心问题。

## 6. 哪些情况下必须等待或用户确认

必须等待：
- 无可用结果，只有 running / polling。
- 关键证据 SQL 仍 running。
- SQL 修复重跑尚未返回结果。

必须用户确认：
- 继续高成本 Hive。
- 长周期扩窗。
- 跨域 join。
- 大样本回捞。
- 权限申请或高敏字段查询。
- 多分支并行查询。

## 7. 是否修改核心 Skill

未修改核心 Skill。

