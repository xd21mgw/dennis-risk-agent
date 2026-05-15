# DataAgent Real Response Examples Template v1

## 0. 使用边界

本模板用于记录真实 Data Agent 只读试点返回结果的摘要样例。

- 不记录真实 API、真实 SQL、真实表名、真实字段名。
- 不记录可外泄的敏感明细。
- 不把 Data Agent 返回结果直接等同 Dennis Agent 最终定性。
- `raw_result_reference` 仅保存内部可审计引用，不在材料中展开。

## 1. 单 Case 记录模板

```yaml
case_id:
original_user_question:
query_intent_id:
dataagent_request_id:

dataagent_response_type:
response_status:
response_summary:
key_findings:
  - finding:
    evidence_direction:
    related_evidence_type:
    quality_note:

missing_evidence:
  - missing_item:
    impact_on_conclusion:
    suggested_next_query_intent:

counter_evidence:
  - counter_item:
    related_misjudgment_risk:
    whether_closed:

quality_risks:
  - risk:
    affected_result:
    degrade_rule:

permission_notes:
  access_level:
  restricted_parts:
  whether_affects_conclusion:

raw_result_reference:
  internal_reference_id:
  retention_note:
  sensitive_detail_exported: false

can_convert_to_normalized_evidence:
required_human_supplement:
  - supplement_item:
    owner:
    priority:
```

## 2. 字段说明

### case_id

试点 case 标识。建议与 runbook 中的 case 编号保持一致，例如 `RP-AC-001`。

### original_user_question

原始用户问题。保留业务语义，避免在模板中展开敏感明细。

### query_intent_id

Dennis Agent 生成的 query intent 标识。

### dataagent_request_id

内部平台 adapter 生成的只读请求标识。

### dataagent_response_type

可选类型：

- `sql`
- `table_summary`
- `dashboard_analysis`
- `dataset_analysis`
- `abtest_analysis`
- `profile_tags`
- `audience_package`
- `error`
- `partial`
- `no_permission`
- `empty_result`
- `ambiguous_result`

### response_status

可选状态：

- `success`
- `partial`
- `failed`
- `no_permission`
- `timeout`
- `empty_result`
- `ambiguous_result`
- `data_quality_risk`
- `permission_limited`

### response_summary

Data Agent 返回摘要。只写业务可解释摘要，不粘贴真实 SQL 或敏感明细。

### key_findings

记录 Data Agent 返回的关键发现。

`evidence_direction` 可选：

- `support_protocol`
- `support_cracked_app`
- `support_instrumentation_issue`
- `support_join_issue`
- `support_legal_automation`
- `support_group_control`
- `neutral`
- `unknown`

### missing_evidence

记录缺失证据及其对结论的影响。

要求：

- 缺失破解包排查时，不得给明确协议。
- 缺失官方包埋点排查时，不得给明确协议。
- 缺失合法自动化排查时，不得给明确协议。
- 缺失前后端 join 口径校验时，不得给明确协议。

### counter_evidence

记录反证。重点覆盖：

- 破解包绕 SDK。
- 官方包埋点缺失。
- 前后端 join 口径问题。
- 合法自动化 / 授权工具。
- 群控真机。

### quality_risks

记录可能导致降级的质量风险：

- 前端日志延迟。
- SDK 日志采集延迟。
- 后端日志采样或延迟。
- 设备画像更新延迟。
- join key 不一致。
- 时间窗不一致。
- 权限限制。

### permission_notes

记录权限限制，不展开敏感明细。

### raw_result_reference

仅保存内部引用。不得在对外材料中泄露原始明细。

### can_convert_to_normalized_evidence

可选值：

- `yes`
- `partial`
- `no`

### required_human_supplement

记录需要人工补充的信息，例如业务活动背景、授权工具白名单、版本发布记录、埋点变更记录。

## 3. 降级规则

- `partial`：只允许形成部分证据，结论不得高于高度疑似。
- `failed`：不得形成风险结论，只能输出失败原因和下一步补证。
- `no_permission`：不得绕过权限推断，必须人工确认是否补授权。
- `timeout`：不得用超时替代空结果，必须重试或缩小范围。
- `empty_result`：不能直接解释为无风险。
- `ambiguous_result`：必须列出多种解释路径。
- `data_quality_risk`：必须在 normalized evidence 中保留质量风险。
