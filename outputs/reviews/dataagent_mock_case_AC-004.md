# Data Agent Mock Case AC-004：群控真机爬取

说明：本文件为离线 mock 回归，不调用真实 Data Agent，不编造真实表名、字段名、API 或真实结果。

## 用户问题

一批真机设备疑似被统一调度爬取内容资产，能否判断为群控真机爬取？

## 触发 Skill

- 主控 Skill：`anti_crawler_expert_skill`
- 辅助 Skill：`group_control_expert_skill`、`risk_chain_reconstruction_skill`

## 需要的证据

- 设备团组：设备、账号、IP、环境是否形成稳定团组。
- 行为路径相似：访问路径、停留、翻页、详情访问是否模板化。
- 同批启动 / 停止：是否存在批次化统一调度。
- 资产获取链路：是否低成本批量获取核心资产。
- 合法矩阵排除：是否为商家/达人/机构/客服合法工具访问。

## query_intent

```yaml
query_intent:
  intent_id: "AC-004_group_control_crawler_001"
  risk_question: "真机设备是否被统一调度进行内容资产爬取"
  target_evidence: "设备团组 + 行为路径相似 + 同批启动/停止 + 资产访问链路"
  applicable_skill:
    primary: "anti_crawler_expert_skill"
    auxiliary:
      - "group_control_expert_skill"
      - "risk_chain_reconstruction_skill"
  minimum_inputs:
    required: ["观测时间窗口", "目标资产或页面语义", "疑似设备/账号集合"]
    optional: ["业务活动日历", "授权工具审计口径"]
    missing: []
  query_dimensions:
    entities: ["设备", "账号", "IP", "资产访问", "页面路径"]
    group_by: ["设备团组", "账号团组", "分钟级启动窗口", "访问路径模板", "资产类型"]
    joins: ["设备环境日志", "页面访问日志", "资产访问日志", "授权矩阵审计信息"]
  time_window:
    baseline: "历史正常访问窗口"
    observation: "异常访问窗口"
    granularity: "分钟或小时"
  expected_outputs:
    - "设备/账号团组连接图摘要"
    - "同批启停同步率"
    - "路径模板命中摘要"
    - "核心资产访问集中度"
    - "合法授权排除摘要"
  interpretation_notes:
    strong_evidence_if:
      - "真机团组、同批调度、路径模板、资产访问集中、无授权解释同时成立"
    weak_signal_if:
      - "只有高频访问或设备聚集"
    counter_evidence_if:
      - "合法运营、热点事件、测试流量、企业网络可解释"
  conclusion_threshold:
    sufficient_for: "明确判断"
    must_combine_with: ["设备团组", "同批启停", "路径相似", "资产访问链路", "合法矩阵排除"]
  safety_boundary:
    false_positive_risks: ["热点流量", "合法运营矩阵", "测试流量", "企业网络"]
    prohibited_actions: ["不得仅凭设备聚集直接判群控"]
```

## mock dataagent response

```yaml
mock_dataagent_response:
  status: "success"
  returned_type: ["团组图摘要", "同步调度摘要", "路径相似摘要", "授权排除摘要"]
  evidence_summary:
    - "疑似设备和账号形成稳定团组。"
    - "多个团组在短时间窗口内同步启动和停止资产访问。"
    - "访问路径高度模板化，目标集中于核心内容资产。"
    - "未命中授权工具、商家/达人/机构运营审计解释。"
  key_findings:
    - "真机链路存在，但行为表现为统一调度。"
    - "访问资产集中且路径重复，符合低成本批量获取资产特征。"
    - "自然热点和业务活动日历未能解释同步峰值。"
  missing_evidence:
    - "外部变现或复用链路未在本轮返回中覆盖。"
  confidence_hint: "high"
  permission_notes:
    - "mock success；结果仅用于解释能力测试。"
```

## 证据解释

- 强证据：稳定设备/账号团组、同批启停、路径模板化、核心资产访问集中、合法矩阵排除。
- 中证据：自然热点和活动日历不能解释同步峰值。
- 弱证据：高频访问只作为背景，不单独构成群控。
- 反证：外部复用/变现链路未覆盖，但不影响“群控真机爬取”链路本身判断，只影响黑产变现闭环强度。

## 结论等级

明确判断。

## 为什么能 / 不能下强结论

能下强结论。群控判断需要真机/账号团组、同批调度、路径相似、收益或目标链路聚集、无合法授权解释。mock 返回已闭合“真机统一调度爬取资产”主链路，并排除主要反证。

## 下一步补证 query_intent

```yaml
query_intent:
  intent_id: "AC-004_group_control_crawler_002"
  risk_question: "群控真机爬取后是否存在外部复用或变现链路"
  target_evidence: "资产外部复用 / 变现链路"
  applicable_skill:
    primary: "anti_crawler_expert_skill"
    auxiliary: ["risk_chain_reconstruction_skill"]
  minimum_inputs:
    required: ["目标资产类型", "异常设备/账号团组", "观测时间窗口"]
    optional: ["外部样本线索", "投诉或业务反馈"]
    missing: ["外部复用样本"]
  query_dimensions:
    entities: ["资产", "设备团组", "账号团组", "外部样本线索"]
    group_by: ["资产类型", "访问团组", "时间差", "外部复用类型"]
    joins: ["资产访问日志", "外部线索回流", "投诉/举报线索"]
  time_window:
    baseline: "历史正常窗口"
    observation: "异常窗口"
    granularity: "小时或天"
  expected_outputs: ["资产访问到外部复用的时间差", "外部复用样本摘要", "团组贡献"]
  interpretation_notes:
    strong_evidence_if: ["资产访问和外部复用时间差稳定且主体链路相关"]
    weak_signal_if: ["只有外部截图或单点样本"]
    counter_evidence_if: ["合作方同步、前端公开信息、人工访问可解释"]
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with: ["已确认群控真机爬取链路"]
  safety_boundary:
    false_positive_risks: ["合作方同步", "公开信息", "人工访问"]
    prohibited_actions: ["不得把外部样本直接当内部爬取证据"]
```

## 治理建议

- 对团组设备/账号做分层限速、验证码/滑块、访问频控和资产页加固。
- 对核心资产增加端侧上下文、访问成本和异常团组识别。
- 保留合法矩阵白名单和业务活动白名单。
- 回流外部复用样本，补齐变现链路。

## 是否需要人工确认

需要。虽然可明确判断群控真机爬取，但上线强策略前需确认业务白名单和误伤影响。

## 是否符合 dataagent_conclusion_thresholds_v1.md

符合。强证据链闭合且关键反证已排除，因此允许明确判断。
