# Data Agent Mock Case AC-003：单纯协议判定

说明：本文件为离线 mock 回归，不调用真实 Data Agent，不编造真实表名、字段名、API 或真实结果。

## 用户问题

一批请求命中关键接口，疑似单纯协议攻击，能否直接定性为脱端协议？

## 触发 Skill

- 主控 Skill：`protocol_attack_expert_skill`
- 辅助 Skill：`evidence_decomposition_skill`、`cracked_app_expert_skill`

## 需要的证据

- 前后端链路一致性：是否缺少合理页面、事件、端上下文。
- 接口序列固化：接口顺序、间隔、参数模式是否模板化。
- token / device / ip / ua 一致性：是否存在批量环境冲突。
- SDK / 包证据：排除破解包绕采集、官方埋点缺失。
- 合法矩阵：排除授权工具、官方工具或商家接口化运营。

## query_intent

```yaml
query_intent:
  intent_id: "AC-003_protocol_pure_001"
  risk_question: "一批关键接口请求是否属于脱端协议攻击"
  target_evidence: "前后端链路一致性 + 接口序列固化 + token/device/ip/ua 一致性"
  applicable_skill:
    primary: "protocol_attack_expert_skill"
    auxiliary:
      - "evidence_decomposition_skill"
      - "cracked_app_expert_skill"
  minimum_inputs:
    required:
      - "观测时间窗口"
      - "关键接口或业务动作语义"
      - "风险请求集合"
      - "正常端链路口径"
    optional:
      - "客户端版本/渠道"
      - "SDK 覆盖口径"
      - "授权工具审计口径"
    missing: []
  query_dimensions:
    entities: ["请求", "用户", "账号", "设备", "token", "IP", "UA", "前端事件"]
    group_by: ["接口动作", "调用序列", "时间间隔", "客户端版本", "渠道", "环境冲突类型"]
    joins: ["服务端请求日志", "前端事件日志", "端侧上下文日志", "登录态环境日志", "授权工具审计信息"]
  time_window:
    baseline: "历史正常窗口"
    observation: "异常请求窗口"
    granularity: "小时"
  expected_outputs:
    - "端链路覆盖摘要"
    - "接口序列重复度"
    - "token/device/ip/ua 冲突摘要"
    - "SDK/官方版本反证摘要"
    - "授权工具排除摘要"
  interpretation_notes:
    strong_evidence_if:
      - "无端链路、接口直达、序列固化、环境冲突同时成立，并排除埋点/破解包/授权工具"
    weak_signal_if:
      - "只有高频或只有前端无日志"
    counter_evidence_if:
      - "官方工具授权调用、官方包同样缺日志、埋点口径变化可解释"
  conclusion_threshold:
    sufficient_for: "明确判断"
    must_combine_with: ["端链路缺失", "接口序列固化", "环境冲突", "反证排除"]
  safety_boundary:
    false_positive_risks: ["埋点缺失", "破解包绕采集", "官方工具", "合法接口化运营"]
    prohibited_actions: ["不得仅凭高频或前端无日志直接定协议"]
```

## mock dataagent response

```yaml
mock_dataagent_response:
  status: "success"
  returned_type: ["链路覆盖摘要", "接口序列摘要", "环境一致性摘要", "反证排除摘要"]
  evidence_summary:
    - "风险请求缺少正常端侧页面和事件链路。"
    - "关键接口调用顺序和间隔高度模板化。"
    - "token/device/ip/ua 组合存在批量冲突。"
    - "未发现可解释该请求集合的授权工具调用。"
  key_findings:
    - "风险请求更像接口直达，而不是正常端行为。"
    - "异常不集中于单一官方版本采集缺失。"
    - "未返回破解包工件级证据，但 SDK/包异常不是主要解释。"
  missing_evidence:
    - "方法级短链和签名细节未在本轮 mock 返回中展开。"
  confidence_hint: "high"
  permission_notes:
    - "mock success；结果仅用于解释能力测试。"
```

## 证据解释

- 强证据：端链路缺失、接口直达倾向、接口序列固化、token/device/ip/ua 批量冲突、授权工具未命中。
- 中证据：异常不集中于单一官方版本，弱化埋点缺失解释。
- 弱证据：高频请求本身只作为背景信号。
- 反证：未发现授权工具解释；仍缺少方法级签名细节和完整破解包工件证据。

## 结论等级

高度疑似。

## 为什么能 / 不能下强结论

可以下高度疑似，但不打明确判断。协议关键证据已成组，但 mock 返回仍缺少方法级短链、签名细节和完整包工件排除；按阈值不能把“高度疑似”强行升级为明确判断。

## 下一步补证 query_intent

```yaml
query_intent:
  intent_id: "AC-003_protocol_pure_002"
  risk_question: "补齐协议攻击的方法级短链、签名异常和破解包排除证据"
  target_evidence: "方法级短链 + 签名/token 参数异常 + 包工件排除"
  applicable_skill:
    primary: "protocol_attack_expert_skill"
    auxiliary: ["cracked_app_expert_skill"]
  minimum_inputs:
    required: ["风险请求集合", "观测时间窗口", "签名/token 校验口径"]
    optional: ["包签名状态语义", "安全模块状态语义"]
    missing: ["方法级短链口径", "完整包工件口径"]
  query_dimensions:
    entities: ["请求", "账号", "设备", "token", "客户端包"]
    group_by: ["签名校验状态", "参数模板", "包状态", "安全模块状态"]
    joins: ["服务端请求日志", "签名校验结果", "客户端包信息", "安全模块信息"]
  time_window:
    baseline: "历史正常窗口"
    observation: "异常请求窗口"
    granularity: "小时"
  expected_outputs: ["签名/token 异常摘要", "参数模板摘要", "包工件排除摘要"]
  interpretation_notes:
    strong_evidence_if: ["协议短链与签名异常闭合，且包工件反证排除"]
    weak_signal_if: ["只有参数相似"]
    counter_evidence_if: ["异常由破解包或官方版本问题解释"]
  conclusion_threshold:
    sufficient_for: "明确判断"
    must_combine_with: ["端链路缺失", "接口序列固化", "环境冲突"]
  safety_boundary:
    false_positive_risks: ["破解包", "官方版本问题", "授权工具"]
    prohibited_actions: ["不得绕过复核直接上线强拦截"]
```

## 治理建议

- 先对高置信请求做灰度限速、二次校验和样本复核。
- 补齐方法级短链和签名异常后，再考虑关键接口强校验。
- 保留授权工具白名单、官方版本反证和回滚机制。

## 是否需要人工确认

需要。涉及协议强拦截，且明确判断证据尚未完全闭合。

## 是否符合 dataagent_conclusion_thresholds_v1.md

符合。没有因为“成功返回”直接打明确判断，而是依据协议攻击阈值保留在“高度疑似”。
