# Data Agent Mock Response Schema v1

## 0. 说明

本文件只定义未来 Data Agent 返回结构的抽象 schema，不模拟真实数据，不编造真实表名、字段名、接口路径、看板内容、实验结果或画像标签。

当前 Codex 阶段可用该 schema 设计解释逻辑和单元测试，但不得声称已真实调用 Data Agent。

## 1. 标准响应结构

```yaml
dataagent_response:
  request_meta:
    intent_id: "<对应 query_intent.intent_id>"
    intent_type: "<查询意图类型>"
    execution_stage: "<mock | future_platform | manual_export>"
    generated_at: "<时间占位，不代表真实执行时间>"
    data_access_status: "<not_executed | executed | permission_denied | partial | failed>"
  input_echo:
    risk_question: "<原始风险问题>"
    target_evidence: "<目标证据类型>"
    applicable_skill:
      primary: "<主控 Skill>"
      auxiliary:
        - "<辅助 Skill>"
    time_window:
      baseline: "<历史基线窗口>"
      observation: "<观测窗口>"
      granularity: "<粒度>"
    query_dimensions:
      entities:
        - "<实体粒度>"
      group_by:
        - "<聚合维度>"
      joins:
        - "<关联数据类型>"
  data_outputs:
    metric_summaries:
      - metric_name: "<指标语义名，不写真字段>"
        metric_role: "<risk_signal | counter_evidence | quality_metric | governance_metric>"
        value_shape: "<scalar | trend | distribution | ratio | list | graph>"
        comparison_basis: "<baseline | peer_group | control_group | historical | none>"
        observation: "<结果摘要占位，不填真实值>"
    segment_breakdowns:
      - segment_name: "<分层语义>"
        segment_role: "<risk_cluster | normal_cluster | authorized_cluster | unknown>"
        observation: "<分层摘要占位>"
    sample_descriptions:
      - sample_type: "<abnormal_sample | normal_sample | counter_sample>"
        sample_scope: "<样本范围语义>"
        sample_note: "<样本说明占位，不含真实ID>"
    lineage_or_assets:
      candidate_assets:
        - asset_type: "<table | dashboard | dataset | experiment | tag>"
          asset_description: "<资产语义说明，不写真实资产名>"
          confidence: "<high | medium | low>"
      caveats:
        - "<资产口径或权限限制>"
  quality_and_limits:
    coverage_status: "<complete | partial | insufficient | unknown>"
    missing_inputs:
      - "<缺失输入>"
    data_quality_risks:
      - "<埋点缺失 | 口径差异 | 权限不足 | 样本偏差 | SLA延迟 | 实验干扰>"
    permission_or_access_notes:
      - "<权限或访问状态说明>"
  interpretation_hints:
    supports_hypotheses:
      - hypothesis: "<支持的风险假设>"
        evidence_strength: "<strong | medium | weak>"
        reason: "<为什么支持>"
    counter_hypotheses:
      - hypothesis: "<反证或业务合理解释>"
        reason: "<为什么构成反证>"
    not_enough_for:
      - "<当前结果不足以支持的结论>"
  recommended_next_queries:
    - next_intent_id: "<下一轮 query_intent 占位>"
      target_evidence: "<下一步要补的证据>"
      reason: "<为什么需要补>"
```

## 2. Dennis 风控 Agent 解释输出结构

Data Agent 返回后，Dennis 风控 Agent 应转换为：

```yaml
risk_interpretation:
  risk_question: "<风险问题>"
  primary_skill: "<主控 Skill>"
  auxiliary_skills:
    - "<辅助 Skill>"
  data_summary: "<数据返回摘要>"
  evidence_assessment:
    strong_evidence:
      - "<强证据>"
    medium_evidence:
      - "<中证据>"
    weak_evidence:
      - "<弱证据>"
    counter_evidence:
      - "<反证>"
  current_max_conclusion: "<明确判断 | 高度疑似 | 证据不足 | 反向排除/暂不支持>"
  why_not_stronger: "<不能下更强结论的原因>"
  required_next_evidence:
    - "<下一步补证>"
  governance_recommendation:
    immediate_action: "<当前可做动作>"
    gray_strategy: "<灰度策略>"
    prohibited_action: "<不得直接做的动作>"
  evaluation_metrics:
    - "<评估指标>"
```

## 3. 字段约束

- `metric_name` 只能写语义名，例如“端链路覆盖率”“奖励聚集度”“后验留存差异”，不得写真实字段名。
- `asset_description` 只能写资产语义，例如“端侧 SDK 日志候选资产”，不得写真实表名或看板名。
- `sample_note` 不得包含真实用户 ID、账号 ID、设备 ID、token、手机号或其他敏感标识。
- `observation` 不填真实数值，除非来自未来真实 Data Agent 返回。
- `interpretation_hints` 不能直接替代 Dennis 风控 Agent 的最终解释。

## 4. 失败响应结构

```yaml
dataagent_response:
  request_meta:
    intent_id: "<对应 query_intent.intent_id>"
    data_access_status: "<permission_denied | failed | not_supported | insufficient_input>"
  failure:
    failure_type: "<permission | missing_input | unsupported_platform | data_quality | execution_error>"
    failure_reason: "<失败原因>"
    required_fix:
      - "<需要补充的信息或权限>"
  safe_fallback:
    dennis_agent_action: "<输出补证清单 / 降级判断 / 人工查数说明>"
    conclusion_limit: "证据不足"
```
