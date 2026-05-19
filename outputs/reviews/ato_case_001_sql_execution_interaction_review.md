# ATO Case 001 SQL Execution Interaction Review

## 1. 背景

`ATO_CASE_001_PASSWORD_KPN_RESWEEP` 第一次 Data Agent 返回为 `sql_only / pending_execution`：已完成表检索和 5 组 SQL 生成，但没有执行结果。

随后 Data Agent 确认 5 组 SQL 已提交到数据平台：

| SQL ID | 查询目的 | 当前状态 |
|---|---|---|
| `74733` | 换绑 | 已完成 |
| `74734` | 登录全景 | 已完成 |
| `74735` | 发布行为 | running |
| `74736` | 安全事件 | running |
| `74737` | 链路关联 | running |

当前整体状态应识别为：

```yaml
execution_state: execution_partial
reason: 部分 SQL 已完成，关键 SQL 仍 running，尚未返回聚合摘要。
conclusion_support:
  level: insufficient_support
manual_review_required: true
```

## 2. 本轮沉淀内容

已新增 SQL execution follow-up 模板：

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/real_pilot/dataagent_sql_execution_followup_template_v1.md`

已更新：

- `dataagent_markdown_response_parser_v1.md`
- `ato_account_takeover_real_pilot_runbook_v1.md`

## 3. SQL execution 状态机

```text
sql_only
→ pending_execution
→ execution_in_progress
→ execution_result_ready / execution_partial / execution_failed / execution_no_permission / execution_timeout
→ evidence_ready
```

状态含义：

- `sql_only`：只有 SQL / 查询计划。
- `pending_execution`：等待授权执行。
- `execution_in_progress`：SQL 已提交，至少有任务 running。
- `execution_result_ready`：单个 SQL 完成并返回可解析聚合摘要。
- `execution_partial`：部分 SQL 完成，部分 SQL running / failed / no_permission。
- `execution_failed`：执行失败。
- `execution_no_permission`：无权限或字段裁剪影响取证。
- `execution_timeout`：执行超时。
- `evidence_ready`：必要 SQL 均有结果或明确空结果，可进入 evidence。

## 4. 每个状态允许 / 禁止

| 状态 | 允许 | 禁止 |
|---|---|---|
| sql_only | 记录取证计划 | 进入强/中证据 |
| pending_execution | 请求执行授权 | 输出风险结论 |
| execution_in_progress | 记录 SQL ID 和 running 状态 | running 进入 evidence |
| execution_result_ready | 解析聚合摘要 | 跳过质量检查 |
| execution_partial | 局部解析已完成 SQL | 做最终判断 |
| execution_failed | 记录失败原因 | 当作无风险 |
| execution_no_permission | 记录权限缺口 | 强结论 |
| execution_timeout | 收窄查询或拆分 | 当作 empty_result |
| evidence_ready | 进入 parser evidence | 忽略未完成 SQL |

## 5. SQL ID Follow-up Prompt

```text
请基于 ATO_CASE_001_PASSWORD_KPN_RESWEEP 的 SQL ID 做只读取证执行状态跟进。

SQL ID：
- 74733：换绑
- 74734：登录全景
- 74735：发布行为
- 74736：安全事件
- 74737：链路关联

请逐个 SQL ID 返回：
1. SQL ID
2. 查询目的
3. 状态：completed / running / failed / no_permission / timeout
4. 返回行数 / 聚合规模
5. 是否权限裁剪
6. 是否字段移除
7. 是否影响结论
8. 聚合摘要
9. 数据发现
10. 缺失证据
11. 权限限制
12. 质量风险

请只返回聚合摘要，不返回全量明细。
请区分数据发现和模型推测。
running 的 SQL 不要解释成证据。
如果部分 SQL 完成、部分 running，请标记为 execution_partial。
Data Agent 只取数，Dennis Agent 才解释证据。
```

## 6. 当前 Case 001 状态

```yaml
case_id: ATO_CASE_001_PASSWORD_KPN_RESWEEP
execution_state: execution_partial
completed_sql:
  - sql_id: 74733
    purpose: 换绑
  - sql_id: 74734
    purpose: 登录全景
running_sql:
  - sql_id: 74735
    purpose: 发布行为
  - sql_id: 74736
    purpose: 安全事件
  - sql_id: 74737
    purpose: 链路关联
field_permission_trimming: unknown
evidence_ready: false
manual_review_required: true
```

## 7. 当前不能下结论的原因

- 74735 发布行为仍 running，无法判断异常登录后是否发生违规发布。
- 74736 安全事件仍 running，无法确认风险画像、回扫记录或账号安全事件。
- 74737 链路关联仍 running，无法判断登录与发布之间的时间差、设备一致性、IP一致性、地区一致性。
- 已完成的 74733 / 74734 尚未返回聚合摘要，不能进入 evidence。
- 字段权限裁剪情况未知，可能影响登录方式、设备、IP/地区、策略命中等关键证据。

## 8. 下一步需要 Data Agent 返回什么

对每个 SQL ID 返回：

- SQL ID。
- 查询目的。
- 状态。
- 返回行数 / 聚合规模。
- 是否权限裁剪。
- 是否字段移除。
- 是否影响结论。
- 聚合摘要。
- 数据发现。
- 缺失证据。
- 权限限制。
- 质量风险。

优先顺序：

1. 先返回 74733 / 74734 的聚合摘要和权限裁剪情况。
2. 等待 74735 / 74736 / 74737 完成。
3. 如果 74735-74737 长时间 running，返回执行耗时和是否需要拆分/收窄。
4. 所有关键 SQL 有结果或明确失败后，再进入 parser evidence 阶段。

## 9. 是否修改核心 Skill

未修改核心 Skill。

本轮只新增 Data Agent SQL execution follow-up 模板，并更新 Data Agent parser 与 ATO real_pilot runbook。
