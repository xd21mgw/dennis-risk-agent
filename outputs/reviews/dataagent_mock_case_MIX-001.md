# Data Agent Mock Case MIX-001：直播间截流 / 站外添加

说明：本文件为离线 mock 回归，不调用真实 Data Agent，不编造真实表名、字段名、API 或真实结果。

## 用户问题

直播间用户被站外添加，怀疑存在截流或导流黑产，能否判断？

## 触发 Skill

- 主控 Skill：`traffic_diversion_interception_skill`
- 辅助 Skill：`anti_crawler_expert_skill`、`evidence_decomposition_skill`

## 需要的证据

- 信息暴露入口：直播间评论、用户 ID、昵称、粉丝列表、动态、私信等入口。
- 搜索 / 关注 / 私信链路：从目标获取到触达是否闭合。
- 站外承接：站外联系方式、外链、社群、投诉、举报或用户反馈。
- 账号矩阵：触达账号是否形成矩阵。
- 反证：正常社交、普通关注、用户主动外联、授权客服/达人运营。

## query_intent

```yaml
query_intent:
  intent_id: "MIX-001_live_diversion_001"
  risk_question: "直播间用户被站外添加是否属于导流截流链路"
  target_evidence: "信息暴露入口 + 搜索/关注/私信链路 + 站外承接"
  applicable_skill:
    primary: "traffic_diversion_interception_skill"
    auxiliary:
      - "anti_crawler_expert_skill"
      - "evidence_decomposition_skill"
  minimum_inputs:
    required: ["直播间或场景语义", "被触达用户集合", "观测时间窗口", "站外添加线索语义"]
    optional: ["投诉/举报线索", "触达内容样本", "主播/客服授权触达口径"]
    missing: []
  query_dimensions:
    entities: ["直播间", "目标用户", "触达账号", "搜索", "关注", "私信", "站外承接线索"]
    group_by: ["信息暴露入口", "目标获取路径", "触达方式", "触达账号矩阵", "承接方式", "授权主体"]
    joins: ["直播间互动日志", "搜索/关注/私信行为", "内容样本", "投诉/举报线索", "授权触达审计信息"]
  time_window:
    baseline: "历史正常互动窗口"
    observation: "异常触达窗口"
    granularity: "小时或天"
  expected_outputs:
    - "信息暴露入口分布"
    - "搜索/关注/私信链路转化摘要"
    - "站外承接证据摘要"
    - "触达账号矩阵"
    - "正常社交/授权触达反证摘要"
  interpretation_notes:
    strong_evidence_if:
      - "目标获取、触达、站外承接、账号矩阵闭合，并排除正常社交和授权触达"
    weak_signal_if:
      - "只有私信/关注异常或单账号偶发"
    counter_evidence_if:
      - "正常社交、用户主动外联、授权客服/达人运营可解释"
  conclusion_threshold:
    sufficient_for: "明确判断"
    must_combine_with: ["信息暴露入口", "触达链路", "站外承接", "账号矩阵", "反证排除"]
  safety_boundary:
    false_positive_risks: ["正常社交", "普通关注", "用户主动外联", "授权客服/达人运营"]
    prohibited_actions: ["不得无站外承接证据直接定导流黑产"]
```

## mock dataagent response

```yaml
mock_dataagent_response:
  status: "success"
  returned_type: ["信息暴露入口摘要", "触达链路摘要", "站外承接摘要", "账号矩阵摘要"]
  evidence_summary:
    - "被触达用户主要来自直播间评论和昵称搜索链路。"
    - "触达账号存在批量搜索、关注和私信行为。"
    - "部分触达内容存在站外承接语义。"
    - "触达账号之间存在矩阵化关联。"
  key_findings:
    - "链路符合目标获取 -> 触达 -> 站外承接。"
    - "未发现触达账号属于授权客服或达人运营矩阵。"
    - "仍缺少部分站外承接后的收益或投诉闭环。"
  missing_evidence:
    - "站外承接后的收益链。"
    - "更多投诉/举报样本。"
  confidence_hint: "high"
  permission_notes:
    - "mock success；站外收益链未覆盖。"
```

## 证据解释

- 强证据：信息暴露入口、搜索/关注/私信触达、站外承接语义、触达账号矩阵、授权触达未命中。
- 中证据：直播间评论和昵称搜索指向目标获取路径。
- 弱证据：私信/关注异常单独只是弱信号。
- 反证：正常社交和授权触达未命中；但站外收益链和更多投诉样本未闭合。

## 结论等级

高度疑似。

## 为什么能 / 不能下强结论

能下高度疑似，不能下明确判断。导流截流明确判断需要信息暴露入口、目标获取、触达、站外承接、账号矩阵或收益链闭合。当前站外承接已有语义证据，但收益/投诉闭环不足，仍需补证。

## 下一步补证 query_intent

```yaml
query_intent:
  intent_id: "MIX-001_live_diversion_002"
  risk_question: "补齐直播间截流的站外承接后收益、投诉和账号矩阵闭环"
  target_evidence: "站外承接 + 投诉/举报 + 收益链"
  applicable_skill:
    primary: "traffic_diversion_interception_skill"
    auxiliary: ["evidence_decomposition_skill"]
  minimum_inputs:
    required: ["触达账号集合", "内容样本", "观测时间窗口", "投诉/举报线索"]
    optional: ["站外承接样本", "收益或交易线索"]
    missing: ["站外收益链线索", "更多投诉/举报样本"]
  query_dimensions:
    entities: ["触达账号", "目标用户", "内容样本", "站外承接线索", "投诉/举报"]
    group_by: ["承接方式", "内容模板", "账号矩阵", "目标用户分群", "投诉类型"]
    joins: ["私信/内容样本", "投诉/举报线索", "账号关系", "站外证据回流"]
  time_window:
    baseline: "历史正常互动窗口"
    observation: "异常触达窗口"
    granularity: "小时或天"
  expected_outputs: ["站外承接证据增强", "投诉/举报关联", "账号矩阵模板", "收益线索摘要"]
  interpretation_notes:
    strong_evidence_if: ["站外承接、投诉/收益、账号矩阵闭合"]
    weak_signal_if: ["只有单次私信或关注"]
    counter_evidence_if: ["用户主动外联或正常社交可解释"]
  conclusion_threshold:
    sufficient_for: "明确判断"
    must_combine_with: ["目标获取路径", "触达链路"]
  safety_boundary:
    false_positive_risks: ["正常社交", "普通关注", "授权客服运营"]
    prohibited_actions: ["不得在投诉/承接闭环不足时全量封禁"]
```

## 治理建议

- 对疑似矩阵账号做私信限频、内容加采、站外联系方式识别和用户提醒。
- 对直播间暴露入口做昵称/评论/用户 ID 展示脱敏和搜索限制评估。
- 建立主播教育和站外证据回流。
- 不默认转反爬或协议，除非补齐批量资产获取或无端请求证据。

## 是否需要人工确认

需要。涉及私信、社交互动和账号处置，需人工抽样确认承接内容。

## 是否符合 dataagent_conclusion_thresholds_v1.md

符合。没有把私信/关注异常直接定导流黑产；因站外承接已出现但收益闭环不足，结论为高度疑似。
