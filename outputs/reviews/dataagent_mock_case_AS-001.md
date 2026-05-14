# Data Agent Mock Case AS-001：token 泄露

说明：本文件为离线 mock 回归，不调用真实 Data Agent，不编造真实表名、字段名、API 或真实结果。

## 用户问题

一批账号出现登录态异常和敏感动作，怀疑 token 泄露，能否定性？

## 触发 Skill

- 主控 Skill：`account_security_expert_skill`
- 辅助 Skill：`evidence_decomposition_skill`、`protocol_attack_expert_skill`

## 需要的证据

- token / device / ip / ua 一致性。
- 登录迁移与验证链路。
- 敏感动作后置链路，例如换绑、提现、支付、私信、关键配置变更。
- 正常换机、漫游、企业网络、多设备登录等反证。

## query_intent

```yaml
query_intent:
  intent_id: "AS-001_token_leak_001"
  risk_question: "账号异常是否由 token 泄露或登录态滥用导致"
  target_evidence: "token/device/ip/ua 一致性 + 登录迁移链路 + 敏感动作"
  applicable_skill:
    primary: "account_security_expert_skill"
    auxiliary:
      - "evidence_decomposition_skill"
      - "protocol_attack_expert_skill"
  minimum_inputs:
    required: ["账号集合", "观测时间窗口", "敏感动作语义", "登录事件口径"]
    optional: ["可信设备确认口径", "风控验证口径"]
    missing: []
  query_dimensions:
    entities: ["账号", "token", "设备", "IP", "UA", "登录事件", "敏感动作"]
    group_by: ["环境冲突类型", "敏感动作类型", "登录迁移状态", "验证状态", "账号分群"]
    joins: ["登录态使用记录", "登录事件", "设备环境日志", "敏感动作日志", "验证/确认链路"]
  time_window:
    baseline: "历史正常登录窗口"
    observation: "异常窗口"
    granularity: "小时或天"
  expected_outputs:
    - "token 跨设备/IP/UA 使用摘要"
    - "无登录迁移使用摘要"
    - "敏感动作后置链路"
    - "正常换机/漫游/企业网络反证摘要"
  interpretation_notes:
    strong_evidence_if:
      - "token 在新环境使用且无登录迁移/验证链路，并伴随敏感动作"
    weak_signal_if:
      - "只有异地 IP 或 UA 变化"
    counter_evidence_if:
      - "可信设备确认、正常换机、多设备登录或企业网络可解释"
  conclusion_threshold:
    sufficient_for: "明确判断"
    must_combine_with: ["新环境 token 使用", "无迁移验证", "敏感动作", "正常场景排除"]
  safety_boundary:
    false_positive_risks: ["正常换机", "漫游", "企业网络", "多设备登录", "SDK 升级"]
    prohibited_actions: ["不得仅凭 IP 漫游或 UA 变化冻结账号"]
```

## mock dataagent response

```yaml
mock_dataagent_response:
  status: "partial"
  returned_type: ["登录态环境摘要", "敏感动作摘要", "部分反证摘要"]
  evidence_summary:
    - "部分账号 token 在新设备/IP/UA 环境中被使用。"
    - "异常 token 使用后出现敏感动作。"
    - "部分样本缺少登录迁移和二次验证链路。"
  key_findings:
    - "存在 token 使用环境突变与敏感动作关联。"
    - "可信设备确认结果未完整返回。"
    - "企业网络、漫游和 SDK 升级反证未完全覆盖。"
  missing_evidence:
    - "完整登录迁移链路。"
    - "可信设备确认和用户确认结果。"
    - "企业网络/漫游/SDK 升级排除。"
  confidence_hint: "medium"
  permission_notes:
    - "mock partial；部分验证链路和环境反证未返回。"
```

## 证据解释

- 强证据：暂无闭合强证据。
- 中证据：token 新环境使用、敏感动作后置、部分样本缺少迁移验证。
- 弱证据：IP/UA 变化本身是弱信号。
- 反证：正常换机、漫游、企业网络、SDK 升级和可信设备确认未完整排除。

## 结论等级

高度疑似。

## 为什么能 / 不能下强结论

能下高度疑似，不能明确判断。token 泄露明确判断要求新环境 token 使用、无登录迁移/验证链路、敏感动作、批量模板化和正常场景排除。当前 mock 为 partial，反证未完整排除。

## 下一步补证 query_intent

```yaml
query_intent:
  intent_id: "AS-001_token_leak_002"
  risk_question: "补齐 token 异常使用的登录迁移、可信设备确认和正常环境反证"
  target_evidence: "验证链路 + 正常场景反证排除"
  applicable_skill:
    primary: "account_security_expert_skill"
    auxiliary: ["evidence_decomposition_skill"]
  minimum_inputs:
    required: ["异常账号集合", "异常 token 使用窗口", "敏感动作语义"]
    optional: ["可信设备规则语义", "企业网络口径", "SDK 升级窗口"]
    missing: ["可信设备确认结果", "用户确认结果", "企业网络/漫游排除口径"]
  query_dimensions:
    entities: ["账号", "token", "设备", "IP", "UA", "验证事件", "敏感动作"]
    group_by: ["验证状态", "设备可信状态", "网络环境类型", "敏感动作类型"]
    joins: ["登录态使用记录", "验证/确认链路", "设备环境日志", "敏感动作日志"]
  time_window:
    baseline: "历史正常窗口"
    observation: "异常窗口"
    granularity: "小时或天"
  expected_outputs: ["验证缺失摘要", "正常换机/漫游排除摘要", "敏感动作链路"]
  interpretation_notes:
    strong_evidence_if: ["无验证迁移且正常场景排除，敏感动作链路闭合"]
    weak_signal_if: ["只有异地或 UA 变化"]
    counter_evidence_if: ["可信设备确认或正常换机可解释"]
  conclusion_threshold:
    sufficient_for: "明确判断"
    must_combine_with: ["新环境 token 使用", "敏感动作"]
  safety_boundary:
    false_positive_risks: ["正常换机", "漫游", "企业网络", "多设备登录"]
    prohibited_actions: ["不得在反证未排除前冻结全量账号"]
```

## 治理建议

- 对高度疑似账号做 step-up 验证、敏感动作冷却和登录态刷新。
- 不做全量冻结；优先按敏感动作和环境冲突分层。
- 补用户确认和可信设备回流，建立 token 风险样本。

## 是否需要人工确认

需要。账号安全处置高误伤，且 mock 返回为 partial。

## 是否符合 dataagent_conclusion_thresholds_v1.md

符合。没有把 IP/UA 异常直接定为 token 泄露；在反证未排除时只给高度疑似。
