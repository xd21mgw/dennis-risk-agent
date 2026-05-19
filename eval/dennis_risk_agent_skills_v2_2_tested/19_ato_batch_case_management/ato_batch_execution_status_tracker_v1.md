# ATO Batch Execution Status Tracker v1

## 1. 目标

定义批量 ATO case 从导入、生成 Data Agent question、SQL 执行、聚合摘要、parser evidence 到人工复核的状态机。

本文件不调用 Data Agent，不定义真实 API。

## 2. Case 级状态机

```text
imported
→ minimum_input_ready
→ question_ready
→ dataagent_submitted
→ sql_only
→ pending_execution
→ execution_in_progress
→ execution_partial
→ execution_result_ready
→ evidence_ready
→ manual_review_required
→ manual_review_done
→ archived
```

异常分支：

```text
blocked_by_missing_input
no_permission
failed
timeout
```

## 3. 状态定义

| 状态 | 含义 | 允许动作 | 禁止动作 |
|---|---|---|---|
| `imported` | case 已进入 registry | 校验最小输入 | 输出风险结论 |
| `minimum_input_ready` | user_id/time_window 等齐备 | 生成 Data Agent question | 进入 evidence |
| `blocked_by_missing_input` | 缺 user_id 或 time_window | 向用户要补充信息 | 调用 Data Agent |
| `question_ready` | 自然语言 question 已生成 | 人工提交或内部平台提交 | 当作取证完成 |
| `dataagent_submitted` | 已提交 Data Agent | 等待返回 | 输出结论 |
| `sql_only` | 只返回 SQL / 查询计划 | 请求执行 SQL 或人工执行 | 进入强 / 中证据 |
| `pending_execution` | SQL 已提交待执行 | 轮询状态 | 进入证据链 |
| `execution_in_progress` | 部分 SQL running | 继续轮询 | final judgement |
| `execution_partial` | 部分完成、部分未完成 | 解析已完成部分为 partial evidence | 关闭 case |
| `execution_result_ready` | SQL 均完成或有明确空结果 | 进入 parser evidence | 忽略权限限制 |
| `evidence_ready` | unified evidence 已生成 | Dennis Agent 解释 | 自动处置 |
| `no_permission` | 核心域无权限 | 权限申请 / 降级 | 强结论 |
| `failed` | 执行失败 | 优化查询 / 重试 | 解释为无风险 |
| `timeout` | 查询超时 | 收窄窗口 / 拆分查询 | 解释为无风险 |
| `manual_review_required` | 需要人工复核 | 分派复核 | 自动关闭为事实结论 |
| `manual_review_done` | 人工复核完成 | 归档或入回归 | 覆盖数据发现 |

## 4. SQL 级跟踪字段

```yaml
sql_execution_item:
  sql_id:
  purpose:
  status:
  row_count_or_aggregate_size:
  permission_trimmed:
  removed_field_types:
  impact_on_conclusion:
  aggregate_summary:
  missing_evidence:
  quality_risks:
  updated_at:
```

SQL 状态枚举：

- `created`
- `submitted`
- `running`
- `success`
- `empty_result`
- `partial`
- `no_permission`
- `failed`
- `timeout`

## 5. Evidence 准入规则

- SQL-only / 查询计划不进入 strong_evidence 或 medium_evidence。
- running / pending 的 SQL 不进入 evidence。
- success 且有聚合摘要，可以进入 evidence。
- empty_result 可以进入 evidence，但只能说明“查询结果为空”，不能解释为无风险。
- no_permission 必须进入 permission_notes 和 missing_evidence。
- partial execution 只能输出 partial evidence，不能关闭 case。

## 6. 批量看板建议字段

```yaml
batch_status:
  total_cases:
  minimum_input_ready_count:
  blocked_by_missing_input_count:
  sql_only_count:
  execution_in_progress_count:
  execution_result_ready_count:
  evidence_ready_count:
  no_permission_count:
  failed_or_timeout_count:
  manual_review_required_count:
  long_term_regression_count:
```

## 7. 已有样例状态

| case_id | 当前状态 | 说明 |
|---|---|---|
| ATO_CASE_001_PASSWORD_KPN_RESWEEP | `evidence_ready` | 5 组 SQL 完成，支持密码登录型 ATO 嫌疑 |
| ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP | `evidence_ready` | 登录授权、安全事件、设备 IP、发布行为完成，支持扫码/OAuth 型 ATO 嫌疑 |
| ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE | `evidence_ready` | 数据完整但支持不足，作为反例 / 证据不足样本 |

## 8. 批量推进优先级

P0：
- `execution_partial`
- `sql_only`
- `no_permission`
- 与人工备注冲突的 case

P1：
- 正例链路清晰但缺人工复核的 case
- 反例 / 证据不足样本

P2：
- 重复类型、低信息量、缺少关键输入的 case
