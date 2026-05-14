# Data Agent Mock Case ACT-003：渠道抢量

说明：本文件为离线 mock 回归，不调用真实 Data Agent，不编造真实表名、字段名、API 或真实结果。

## 用户问题

某渠道转化突然上涨，怀疑点击注入或归因抢量，能否判断为渠道作弊？

## 触发 Skill

- 主控 Skill：`traffic_anti_cheating_expert_skill`
- 辅助 Skill：`evidence_decomposition_skill`、`risk_chain_reconstruction_skill`

## 需要的证据

- CTIT / 渠道归因。
- 自然量跷跷板。
- 新客真实性与后验质量。
- 设备/IP/UA 或点击行为模板。
- 预算、活动、版本、归因规则变化反证。

## query_intent

```yaml
query_intent:
  intent_id: "ACT-003_channel_hijack_001"
  risk_question: "目标渠道是否存在点击注入或归因抢量"
  target_evidence: "CTIT / 渠道归因 + 自然量跷跷板 + 后验质量"
  applicable_skill:
    primary: "traffic_anti_cheating_expert_skill"
    auxiliary:
      - "evidence_decomposition_skill"
      - "risk_chain_reconstruction_skill"
  minimum_inputs:
    required: ["目标渠道集合", "异常时间窗口", "归因口径", "转化动作语义"]
    optional: ["预算调整记录语义", "活动排期语义", "版本发布语义", "归因规则变更语义"]
    missing: []
  query_dimensions:
    entities: ["渠道", "点击", "安装", "激活", "新客", "设备", "IP", "UA"]
    group_by: ["渠道", "媒体或广告位", "CTIT 时间桶", "自然/付费来源", "设备分群", "新客质量分层"]
    joins: ["点击日志", "安装/激活日志", "归因结果", "自然量与渠道量指标", "后验质量指标", "业务变更信息"]
  time_window:
    baseline: "历史对照窗口"
    observation: "异常窗口"
    granularity: "小时或天"
  expected_outputs:
    - "CTIT 分布"
    - "渠道份额变化"
    - "自然量跷跷板"
    - "后验质量"
    - "设备/IP/UA 或点击模板异常"
    - "业务变更反证"
  interpretation_notes:
    strong_evidence_if:
      - "CTIT 异常、自然量跷跷板、后验质量差、设备/IP/UA 或点击模板异常同时成立，并排除业务变更"
    weak_signal_if:
      - "只有渠道上涨或 CTIT 偏移"
    counter_evidence_if:
      - "预算、活动、版本或归因规则变化可解释"
  conclusion_threshold:
    sufficient_for: "明确判断"
    must_combine_with: ["CTIT 异常", "自然量跷跷板", "后验质量异常", "点击/设备异常", "业务变更排除"]
  safety_boundary:
    false_positive_risks: ["预算调整", "活动排期", "版本发布", "归因规则变化", "媒体策略变化"]
    prohibited_actions: ["不得仅凭 CTIT 或渠道上涨拒付"]
```

## mock dataagent response

```yaml
mock_dataagent_response:
  status: "success"
  returned_type: ["CTIT 摘要", "渠道份额趋势", "后验质量摘要", "业务变更对照"]
  evidence_summary:
    - "目标渠道 CTIT 分布存在偏移。"
    - "目标渠道份额上涨，同期自然量下降。"
    - "后验质量略弱于对照。"
    - "异常窗口存在预算调整和归因口径变化。"
  key_findings:
    - "CTIT 和自然量结构支持归因异常假设。"
    - "设备/IP/UA 或点击模板异常未返回。"
    - "预算和归因口径变化可解释部分渠道份额变化。"
  missing_evidence:
    - "设备/IP/UA 聚集。"
    - "点击行为模板。"
    - "归因链路可复现证据。"
  confidence_hint: "medium"
  permission_notes:
    - "mock success；点击行为模板数据未在本轮返回范围内。"
```

## 证据解释

- 强证据：暂无。
- 中证据：CTIT 偏移、渠道份额上涨、自然量下降、后验质量略弱。
- 弱证据：渠道上涨和后验略弱，单独不构成作弊。
- 反证：预算调整和归因口径变化可解释部分异常；缺设备/IP/UA 和点击模板。

## 结论等级

证据不足。

## 为什么能 / 不能下强结论

不能下强结论。渠道抢量明确判断需要 CTIT 异常、自然量跷跷板、后验质量异常、设备/IP/UA/点击行为异常和归因链路可复现，同时排除预算、活动、版本、归因规则变化。当前存在明确业务变更反证，且点击/设备异常缺失。

## 下一步补证 query_intent

```yaml
query_intent:
  intent_id: "ACT-003_channel_hijack_002"
  risk_question: "排除预算和归因口径变化后，目标渠道是否仍存在点击模板或设备/IP/UA 异常"
  target_evidence: "点击行为模板 + 设备/IP/UA 异常 + 业务变更分层"
  applicable_skill:
    primary: "traffic_anti_cheating_expert_skill"
    auxiliary: ["evidence_decomposition_skill"]
  minimum_inputs:
    required: ["目标渠道集合", "异常窗口", "预算/归因变更窗口", "点击链路口径"]
    optional: ["媒体广告位语义", "新客质量对照口径"]
    missing: ["点击行为模板口径", "设备/IP/UA 聚集口径"]
  query_dimensions:
    entities: ["渠道", "点击", "设备", "IP", "UA", "新客"]
    group_by: ["渠道", "媒体或广告位", "变更前后", "CTIT 时间桶", "设备分群", "IP/UA 模板"]
    joins: ["点击日志", "归因结果", "设备/IP/UA 环境信息", "业务变更信息", "后验质量指标"]
  time_window:
    baseline: "变更前窗口"
    observation: "变更后异常窗口"
    granularity: "小时或天"
  expected_outputs: ["变更分层后的 CTIT", "点击模板摘要", "设备/IP/UA 聚集", "后验质量对照"]
  interpretation_notes:
    strong_evidence_if: ["排除业务变更后仍有点击模板和设备/IP/UA 异常"]
    weak_signal_if: ["只有 CTIT 偏移"]
    counter_evidence_if: ["业务变更能解释异常"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["自然量跷跷板", "后验质量异常"]
  safety_boundary:
    false_positive_risks: ["预算调整", "归因规则变化", "媒体策略变化"]
    prohibited_actions: ["不得在反证未排除前拒付或扣减结算"]
```

## 治理建议

- 暂不拒付或扣减结算，先做渠道归因异常监控和结算复核。
- 将预算/归因变更窗口单独分层，避免把业务变更当作弊。
- 补点击行为模板和设备/IP/UA 异常后再决定是否灰度限量。

## 是否需要人工确认

需要。存在业务变更反证，渠道结算影响高。

## 是否符合 dataagent_conclusion_thresholds_v1.md

符合。CTIT 异常和自然量跷跷板未自动升级为作弊，因反证存在而降级为证据不足。
