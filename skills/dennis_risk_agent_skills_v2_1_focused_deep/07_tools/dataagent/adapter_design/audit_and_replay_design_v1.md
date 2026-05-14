# Audit And Replay Design v1

## 0. 定位

本文件设计未来内部平台如何记录、审计和回放 Dennis Agent 与 Data Agent adapter 的交互链路。

目标：

- 可追溯每次风险判断依赖了什么证据。
- 可复盘 Data Agent 返回质量和权限限制。
- 可在权限补齐、数据修复或 schema 升级后重放。
- 可沉淀 Skill、schema、join path、threshold 的改进项。

当前阶段不调用真实 Data Agent，不定义真实审计系统、真实 API 或真实存储表。

## 1. 必须记录的对象

每次 adapter 执行必须记录：

- 用户原问题。
- Skill 路由。
- `query_intent`。
- `dataagent_request`。
- `dataagent_response` 摘要。
- `normalized_evidence`。
- Dennis Agent 结论。
- 人工最终判断。
- 是否回写 Skill / schema / join path / threshold。
- 权限和质量风险记录。
- 是否触发人工确认。

## 2. 审计记录建议结构

```yaml
adapter_audit_record:
  audit_id: "<内部审计标识>"
  created_at: "<未来平台生成>"
  user_question:
    text: "<用户原问题摘要>"
    risk_domain: "<账号安全 | 流量反作弊 | 反爬 | 活动反作弊 | 导流截流 | 其他>"
  skill_routing:
    primary_skill: "<主控 Skill>"
    auxiliary_skills:
      - "<辅助 Skill>"
    routing_reason: "<路由原因>"
  query_intent_snapshot:
    intent_id:
    intent_type:
    target_evidence:
    required_data_domains: []
    join_paths_needed: []
    quality_checks: []
    conclusion_threshold:
  dataagent_request_snapshot:
    request_id:
    task_type:
    data_domains: []
    field_types_needed: {}
    join_paths_needed: []
    safety_boundary: {}
  dataagent_response_summary:
    status: "<success | partial | failed | no_permission | timeout | empty_result | ambiguous_result | data_quality_risk | permission_limited>"
    returned_type: "<sql | table_summary | dashboard_analysis | dataset_analysis | abtest_analysis | profile_tags | audience_package | error | partial | no_permission>"
    evidence_summary: "<不含敏感明细>"
    missing_evidence: []
    quality_risks: []
    permission_notes: []
  normalized_evidence_snapshot:
    evidence_id:
    conclusion_support:
      level:
      reason:
    strong_evidence_count:
    medium_evidence_count:
    weak_evidence_count:
    counter_evidence_count:
    missing_evidence_count:
  dennis_agent_conclusion:
    level: "<明确判断 | 高度疑似 | 证据不足 | 反向排除/暂不支持>"
    reason: "<结论理由摘要>"
    governance_recommendation: "<治理建议摘要>"
    prohibited_actions: []
  human_final_judgement:
    required: "<true | false | 待平台判断>"
    result: "<confirmed | rejected | adjusted | pending | not_required>"
    notes: "<人工备注摘要>"
  feedback_to_assets:
    writeback_skill_required: "<true | false>"
    writeback_schema_required: "<true | false>"
    writeback_join_path_required: "<true | false>"
    writeback_threshold_required: "<true | false>"
    writeback_reason: "<需要回写的原因>"
  replay:
    replayable: "<true | false>"
    replay_blockers:
      - "<权限缺失 | 数据质量 | 输入缺失 | schema 变化 | 平台不支持>"
    replay_trigger:
      - "<权限补齐 | 数据修复 | schema 升级 | join path 升级 | threshold 升级>"
```

## 3. 回放场景

需要支持回放：

- `no_permission` 后权限补齐。
- `permission_limited` 后拿到更完整权限。
- `partial` 后缺失数据补齐。
- `failed` 或 `timeout` 后平台恢复。
- 数据质量问题修复。
- `query_intent_schema_v2` 升级。
- `data_join_paths_v1` 新增 join path。
- `dataagent_conclusion_thresholds_v1` 调整。
- 人工确认发现 Dennis 解释偏差。

## 4. 回放输入

回放时应复用：

- 原用户问题。
- 原 Skill 路由。
- 原 `query_intent`。
- 原 `dataagent_request`。
- 原权限和质量风险记录。

如果 schema 或 join path 已升级，应记录：

- 原版本。
- 新版本。
- 差异摘要。
- 是否需要重新生成 `query_intent`。

## 5. 回放输出

回放应产出：

- 新 `dataagent_response` 摘要。
- 新 `normalized_evidence`。
- 新 Dennis Agent 结论。
- 与旧结论差异。
- 是否需要人工复核。
- 是否需要回写 Skill、schema、join path 或 threshold。

## 6. 权限和质量风险记录

必须记录：

- 权限状态：allowed、permission_limited、no_permission、pending_approval、unknown。
- 受限数据域。
- 受限证据类型。
- 数据质量风险：口径、延迟、覆盖、采样、join、画像更新、策略日志、实验干扰。
- 质量风险对结论等级的影响。

权限不足和数据质量风险不得在审计中被吞掉。

## 7. 人工确认触发条件

以下情况必须触发人工确认或至少标记待确认：

- `manual_review_required: true`。
- `permission_boundary` 为高敏或中高敏且涉及强治理建议。
- `status` 为 partial、failed、no_permission、timeout、ambiguous_result、data_quality_risk 或 permission_limited。
- `conclusion_support.level` 与 Dennis Agent 最终结论不一致。
- 存在处罚、冻结、扣除、封禁、策略上线、扣量、结算调整等高风险动作建议。
- 人工最终判断与 Dennis Agent 结论冲突。

## 8. 回写判断

回写不是默认动作，只有在以下情况触发：

- Skill 路由错误或边界误判：回写 Skill。
- `query_intent_schema_v2` 字段不足：回写 schema。
- 现有 join path 无法表达核心证据链：回写 join path。
- Data Agent 结果解释过度自信或过度保守：回写 threshold。
- 多个 case 重复出现相同缺口：优先沉淀为配置或 playbook。

## 9. 安全边界

审计和回放记录不得用于：

- 绕过权限。
- 批量导出敏感明细。
- 自动处罚、冻结、扣除、封禁。
- 自动策略上线。
- 向非授权方暴露真实样本。

真实存储、脱敏、访问控制、保留周期和审计系统由未来内部平台补充。
