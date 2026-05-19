# ATO Case 001 SQL-only Boundary Update

## 1. 背景

`ATO_CASE_001_PASSWORD_KPN_RESWEEP` 的真实 Data Agent 返回暴露出一个标准中间状态：

- Data Agent 完成表检索。
- Data Agent 生成 5 组只读取证 SQL。
- Data Agent 没有执行查询。
- Data Agent 等待授权执行，或由人工下载 SQL 后执行。

因此该返回不是完整取证 `success`，也不是 `failed`、`no_permission` 或 `empty_result`，而是：

```yaml
status: sql_only
execution_state: pending_execution
returned_type: sql_only + table_search + query_plan
```

## 2. 本轮固化的规则

### 2.1 SQL-only / pending_execution 定义

`sql_only / pending_execution` 是 Data Agent-only 真实试点中的标准中间状态。

适用条件：

- Data Agent 已识别候选数据范围。
- Data Agent 已生成 SQL 或查询计划。
- Data Agent 未返回真实执行结果、样本统计、数据摘要或明细表格。
- Data Agent 明确等待授权执行，或要求人工下载 SQL 后执行。

### 2.2 证据链规则

```yaml
strong_evidence: []
medium_evidence: []
weak_evidence:
  - SQL 取证计划
evidence_plan:
  - 待执行 SQL 覆盖的数据域和证据目标
conclusion_support:
  level: insufficient_support
```

SQL-only 不得进入 `strong_evidence` 或 `medium_evidence`。SQL 取证计划只能进入 `weak_evidence` 或 `evidence_plan`。

### 2.3 下一步动作规则

```yaml
next_action: execute_sql_or_request_execution
manual_review_required: true
```

必须先完成 SQL 执行，才能重新进入 parser evidence 阶段。

### 2.4 连续 SQL-only 的流程含义

ATO 试点第一阶段如果连续返回 SQL-only，应优先解决流程问题：

- Data Agent 是否支持授权后直接执行 SQL。
- 是否需要人工下载 SQL 到数据平台执行。
- 执行结果如何回填到 case 记录。
- SQL 执行前是否需要人工确认只读、时间窗口、user_id 和业务动作范围。

## 3. 已更新文件

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/adapter_design/dataagent_markdown_response_parser_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/real_pilot/ato_account_takeover_real_pilot_runbook_v1.md`
- `eval/dennis_risk_agent_skills_v2_2_tested/18_real_dataagent_ato_pilot_cases/ato_parser_regression_plan_v1.md`

## 4. Case 001 下一步闭环

建议流程：

1. 人工确认 Data Agent 生成的 SQL 是否只读。
2. 确认 SQL 是否限定 `ATO_CASE_001_PASSWORD_KPN_RESWEEP` 的 user_id、推荐时间窗口和 ATO 业务动作范围。
3. 选择授权 Data Agent 执行，或人工下载 SQL 后在数据平台执行。
4. 将执行结果粘贴回 Case 001 记录。
5. parser 重新识别返回状态：
   - 有真实表格 / 数据摘要：进入 evidence 解析。
   - 0 行：进入 `empty_result`，不得解释为无风险。
   - 无权限：进入 `no_permission`。
   - 失败 / 超时：进入 `failed` 或 `timeout`。
6. Dennis Agent 基于新一轮 `unified_normalized_evidence` 输出 evidence-based judgement。

## 5. 是否影响进入 Case 003

当前不建议直接把 Case 001 视为完成并进入 Case 003。

原因：

- Case 001 仍停留在 `sql_only / pending_execution`。
- 尚未验证 parser 对真实执行结果、数据摘要和链路表格的处理能力。
- 如果连续 case 都只返回 SQL-only，试点瓶颈会变成执行授权流程，而不是 ATO 证据解释能力。

可以并行准备 Case 003 的 Data Agent question，但建议先跑通 Case 001 的 SQL 执行结果闭环。

## 6. 是否修改核心 Skill

未修改核心 Skill。

本轮只更新 Data Agent parser、ATO real_pilot runbook、ATO parser regression plan，并新增本 review 文件。
