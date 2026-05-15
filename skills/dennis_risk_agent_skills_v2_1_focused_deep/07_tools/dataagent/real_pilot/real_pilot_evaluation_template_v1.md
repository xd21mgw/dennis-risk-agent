# Real Pilot Evaluation Template v1

## 0. 使用边界

本模板用于评估真实 Data Agent 只读试点是否成功。

- 不记录真实 API、真实 SQL、真实表名、真实字段名。
- 不把 Data Agent 返回结果直接当作最终风控定性。
- 不把试点评估结果直接转为处罚、冻结、扣除或策略上线。

## 1. 单 Case 评估模板

```yaml
case_id:
case_type:
pilot_batch:
review_date:

query_intent_completeness:
  is_complete:
  missing_parts:
  comments:

dataagent_request_executability:
  is_executable:
  blocker:
  comments:

dataagent_response_parseability:
  is_parseable:
  response_status:
  response_type:
  parse_risks:
  comments:

normalized_evidence_completeness:
  is_complete:
  missing_evidence_sections:
  quality_risks_preserved:
  counter_evidence_preserved:
  comments:

dennis_agent_conclusion_level:
  level:
  reason:
  whether_degraded_correctly:

human_final_judgment:
  judgment:
  judgment_basis:
  required_followup:

consistency_check:
  consistent_or_not:
  inconsistency_reason:
  dennis_agent_issue:
  dataagent_result_issue:
  adapter_issue:
  human_review_note:

backwrite_needed:
  query_intent_schema:
    needed:
    reason:
  data_join_paths:
    needed:
    reason:
  conclusion_thresholds:
    needed:
    reason:
  normalized_evidence_schema:
    needed:
    reason:
  skill:
    needed:
    target_skill:
    target_section:
    reason:

next_batch_decision:
  enter_next_batch:
  condition:
  blockers:
```

## 2. 评估项说明

### query_intent 是否完整

检查是否包含：

- 风险问题。
- 目标证据。
- 主控 Skill 和辅助 Skill。
- 最小输入。
- 数据域。
- 字段类型。
- join path。
- 查询维度。
- 时间窗。
- 预期输出。
- 解释规则。
- 结论阈值。
- 质量检查。
- 时效要求。
- 权限边界。
- 人工确认。
- 安全边界。
- 证据不足时的下一步 query intent。

### dataagent_request 是否可执行

检查：

- 是否能被内部平台 adapter 转换。
- 是否只包含抽象数据域、字段类型和 join path。
- 是否有明确时间窗和查询维度。
- 是否明确只读边界。
- 是否没有真实 API、真实 SQL、真实表名、真实字段名。

### dataagent_response 是否可解析

检查：

- 状态是否可识别。
- returned type 是否可识别。
- 关键发现是否能映射到证据类型。
- 缺失证据、反证、质量风险是否保留。
- 权限限制是否可解释。

### normalized_evidence 是否完整

检查：

- 是否拆分强 / 中 / 弱证据。
- 是否保留反证。
- 是否保留缺失证据。
- 是否保留质量风险和权限说明。
- 是否给出结论支持等级。
- 是否生成下一步 query intent。
- 是否标记人工确认。

### Dennis Agent 结论等级

允许四档：

- 明确判断。
- 高度疑似。
- 证据不足。
- 反向排除 / 转其他 Skill。

要求：

- `partial`、`failed`、`no_permission`、`timeout`、`empty_result`、`ambiguous_result` 不得输出明确判断。
- 缺少破解包、官方包埋点缺失、join 口径问题、合法自动化、群控真机排除时，不得输出明确协议。

### 人工最终判断

人工判断用于校验 Dennis Agent 是否：

- 过度自信。
- 过度保守。
- 漏掉关键反证。
- 误读数据质量风险。
- 错误转交 Skill。

## 3. 是否进入下一批试点

进入下一批的最低条件：

- 本批 case 均有完整审计记录。
- query intent 可稳定生成。
- dataagent request 可由内部平台执行或明确失败原因。
- normalized evidence 能表达强 / 中 / 弱证据、反证、缺口、质量风险。
- 人工复核未发现系统性强结论误判。

暂停下一批的条件：

- 连续出现前端无日志直接判协议。
- 反证无法在 normalized evidence 中表达。
- 权限不足被错误解释为无风险。
- 空结果被错误解释为无风险。
- 自动处置边界不清。

## 4. 汇总模板

```yaml
pilot_batch_summary:
  total_cases:
  completed_cases:
  failed_cases:
  degraded_cases:
  consistent_cases:
  inconsistent_cases:
  major_failure_modes:
    - failure_mode:
      affected_cases:
      backwrite_target:
  recommendation:
  next_batch_scope:
```
