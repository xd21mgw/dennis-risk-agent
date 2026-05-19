# Data Agent SQL Execution Follow-up Template v1

## 0. 定位

本模板用于 Data Agent-only 真实只读试点中，从 `sql_only / pending_execution` 进入 SQL 执行追踪、聚合摘要回填和 parser evidence 的闭环。

Data Agent 负责取数、SQL 执行状态和聚合摘要。Dennis Agent 负责证据解释、结论等级、下一步补证和人工复核。不得输出处罚、冻结、封禁、扣除或策略上线建议。

## 1. SQL execution 状态机

| 状态 | 定义 |
|---|---|
| `sql_only` | Data Agent 只返回 SQL / 查询计划，未执行。 |
| `pending_execution` | SQL 等待授权执行或人工下载执行。 |
| `execution_in_progress` | SQL 已提交到数据平台，至少一个任务 running。 |
| `execution_result_ready` | 单个 SQL 已完成并可返回聚合摘要。 |
| `execution_partial` | 部分 SQL 完成，部分 SQL running / failed / no_permission / timeout。 |
| `execution_failed` | SQL 执行失败。 |
| `execution_no_permission` | SQL 因权限不足、权限裁剪或字段移除影响结果。 |
| `execution_timeout` | SQL 执行超时。 |
| `evidence_ready` | 必要 SQL 均有执行结果或明确空结果，可以进入 parser evidence 阶段。 |

## 2. 每个状态允许做什么 / 禁止做什么

| 状态 | 允许做什么 | 禁止做什么 |
|---|---|---|
| `sql_only` | 记录 evidence_plan、查询目的、待执行 SQL 组 | 进入 strong / medium evidence |
| `pending_execution` | 请求授权执行或人工执行 | 输出 ATO 结论 |
| `execution_in_progress` | 记录 SQL ID、状态、完成/运行中任务 | 将 running 任务当作 evidence |
| `execution_result_ready` | 要求返回聚合摘要、缺失证据、质量风险 | 直接跳过 parser 质量检查 |
| `execution_partial` | 局部解析已完成 SQL，列出未完成 SQL | 做最终判断 |
| `execution_failed` | 记录失败原因、重试方式 | 当作无风险 |
| `execution_no_permission` | 记录权限缺口和影响范围 | 强结论 |
| `execution_timeout` | 建议收窄时间窗、拆分查询 | 当作 empty_result |
| `evidence_ready` | 进入 parser evidence 阶段 | 忽略缺失 SQL 或字段裁剪 |

## 3. SQL ID Follow-up Prompt 模板

```text
请基于以下 SQL ID 做只读取证执行状态跟进，不需要输出处罚、冻结、封禁、扣除或策略上线建议。

case_id:
{case_id}

业务场景：
账号安全 / 盗号申诉 / ATO

SQL ID 列表：
{sql_id_list}

请逐个 SQL ID 返回：
1. SQL ID
2. 查询目的
3. 当前状态：completed / running / failed / no_permission / timeout
4. 返回行数 / 聚合规模
5. 是否发生权限裁剪
6. 是否发生字段移除
7. 权限裁剪或字段移除是否影响结论
8. 聚合摘要
9. 数据发现
10. 缺失证据
11. 权限限制
12. 质量风险

请只输出聚合摘要，不返回全量明细。
请明确哪些是数据发现，哪些是模型推测。
running 的 SQL 不要解释成证据。
如果部分 SQL 完成、部分 running，请标记为 execution_partial。
Data Agent 只做取数和摘要，最终证据解释由 Dennis Agent 完成。
```

## 4. ATO Case 001 当前状态记录

case_id: `ATO_CASE_001_PASSWORD_KPN_RESWEEP`

| SQL ID | 查询目的 | 当前状态 | 是否可进入 evidence |
|---|---|---|---|
| `74733` | 换绑操作 | 已完成 | 等待聚合摘要后可候选进入 evidence |
| `74734` | 登录全景 | 已完成 | 等待聚合摘要后可候选进入 evidence |
| `74735` | 发布行为 | running | 不可进入 evidence |
| `74736` | 安全事件 | running | 不可进入 evidence |
| `74737` | 登录-发布链路关联 | running | 不可进入 evidence |

当前整体状态：

```yaml
execution_state: execution_partial
reason: 部分 SQL 已完成，关键链路 SQL 仍 running。
manual_review_required: true
conclusion_support:
  level: insufficient_support
```

字段权限裁剪情况：

```yaml
field_permission_trimming: unknown
required_followup:
  - 每个 SQL ID 是否发生权限裁剪
  - 是否有字段被移除
  - 裁剪或移除是否影响 ATO 证据链
```

## 5. Evidence 进入规则

- running 不能进入 evidence。
- SQL ID 不能进入 strong / medium evidence。
- SQL-only 不能进入 strong / medium evidence。
- 已完成 SQL 也必须返回聚合摘要、数据发现、缺失证据和质量风险后，才能候选进入 evidence。
- 只有执行结果或明确空结果才能进入 parser evidence 阶段。
- 如果部分 SQL 完成、部分 running，只能生成 `execution_partial`，不能做最终判断。
- 聚合摘要优先，不返回全量明细。
- Data Agent 只取数，Dennis Agent 才解释证据。

## 6. Parser 映射建议

```yaml
normalized_evidence:
  status: execution_partial
  execution_tracking:
    - sql_id:
      query_purpose:
      status:
      row_count_or_aggregate_size:
      permission_trimmed:
      fields_removed:
      impact_on_conclusion:
  data_findings:
    - 仅来自 completed 且有聚合摘要的 SQL
  strong_evidence: []
  medium_evidence: []
  weak_evidence:
    - SQL 执行追踪信息
  missing_evidence:
    - running / failed / no_permission SQL 对应的证据目标
  quality_risks:
    - partial execution
    - permission trimming unknown
  conclusion_support:
    level: insufficient_support
  next_action:
    - wait_for_running_sql
    - request_aggregate_summary_for_completed_sql
  manual_review_required: true
```
