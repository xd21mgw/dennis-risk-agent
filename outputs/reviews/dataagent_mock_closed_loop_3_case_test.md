# Data Agent Mock 闭环 3 Case 测试

说明：本文件只测试 Dennis 风控 Agent 对 mock Data Agent 返回的解释能力。所有 `mock dataagent response` 都是结构化假设返回，不代表真实查询结果；本轮不调用真实 Data Agent，不编造 API，不编造真实表名、字段名、接口路径或真实数据。

## Case 1：协议攻击但前端无日志

### 1. 用户问题

怀疑一批请求是协议攻击，但前端无日志，能否判断为脱端协议请求？

### 2. 触发 Skill

- 主控 Skill：`protocol_attack_expert_skill`
- 辅助 Skill：`cracked_app_expert_skill`、`evidence_decomposition_skill`

### 3. query_intent 摘要

- intent_id：`case_001_protocol_frontend_missing_001`
- target_evidence：前后端链路一致性
- 期望返回：端链路覆盖率、无前端事件请求占比、版本/渠道/包分布、接口序列重复度、token/device/ip/ua 冲突摘要、官方版本对照。
- 安全边界：不得仅凭前端无日志直接定协议；必须排除埋点缺失、SDK 采样、日志延迟、官方版本问题、破解包绕采集和授权接口化运营。

### 4. mock dataagent response

```yaml
mock_dataagent_response:
  status: "partial"
  returned_type:
    - "链路覆盖摘要"
    - "接口序列摘要"
    - "版本/渠道分布摘要"
  evidence_summary:
    - "目标请求集合存在端侧事件缺失现象。"
    - "部分业务动作存在接口序列相似。"
    - "异常样本在少数客户端版本和渠道上更集中。"
  key_findings:
    - "服务端请求与前端事件链路存在明显不一致。"
    - "接口顺序存在模板化迹象，但尚未确认是否接口直达。"
    - "未返回完整 token/device/ip/ua 一致性结果。"
    - "未返回官方包同版本对照和 SDK 覆盖完整结果。"
  missing_evidence:
    - "SDK 日志覆盖与官方版本对照。"
    - "包签名、版本、渠道、安全模块状态。"
    - "token/device/ip/ua 批量冲突结果。"
    - "合法工具或授权矩阵排除结果。"
  confidence_hint: "medium"
  permission_notes:
    - "部分端侧包信息和 SDK 覆盖数据未返回，mock 状态为 partial。"
```

### 5. Dennis Agent 证据解释

强证据：

- 暂无。mock 返回没有排除官方埋点缺失、SDK 采样、破解包绕采集和授权工具调用，也没有完整 token/device/ip/ua 证据。

中证据：

- 服务端请求与前端事件链路不一致，支持“链路冲突”。
- 部分接口序列相似，支持“可能存在自动化或协议化调用”的假设。
- 异常集中于少数版本和渠道，提示需要排查破解包、SDK 覆盖或版本口径。

弱证据：

- 前端无日志本身只是弱信号。
- 接口序列相似但未确认接口直达，只能作为自动化嫌疑。

反证：

- 反证尚未返回，尤其缺官方包同版本对照、SDK 采样/埋点口径、合法工具授权范围。
- 异常集中于少数版本和渠道，本身也可能是破解包或官方版本采集问题的线索，而不是协议强证据。

### 6. 结论等级

证据不足。

### 7. 为什么能或不能下强结论

不能下强结论。根据 `dataagent_conclusion_thresholds_v1.md`，协议攻击明确判断需要“无正常端链路 + 接口直达 + 接口序列固化 + token/device/ip/ua 异常 + 排除埋点缺失、官方工具、破解包绕采集”。当前 mock response 是 partial，缺少 token/device/ip/ua、SDK 覆盖、包完整性和授权工具排除，因此最多只能判断为“链路冲突 + 协议嫌疑待补证”。

### 8. 下一步补证 query_intent

```yaml
query_intent:
  intent_id: "case_001_protocol_frontend_missing_002"
  risk_question: "前端无日志是否由破解包绕采集、官方包埋点缺失或 SDK 覆盖异常导致"
  target_evidence: "SDK 日志覆盖与客户端包异常"
  applicable_skill:
    primary: "cracked_app_expert_skill"
    auxiliary:
      - "protocol_attack_expert_skill"
  minimum_inputs:
    required:
      - "异常请求集合"
      - "观测时间窗口"
      - "客户端版本和渠道语义"
    optional:
      - "包签名状态语义"
      - "安全模块状态语义"
    missing:
      - "官方版本对照口径"
      - "合法工具/授权矩阵排除口径"
  query_dimensions:
    entities:
      - "设备"
      - "账号"
      - "客户端包"
      - "SDK 日志"
      - "风险请求"
    group_by:
      - "版本"
      - "渠道"
      - "包签名状态"
      - "SDK 模块状态"
      - "安全模块状态"
    joins:
      - "端 SDK 日志"
      - "客户端包信息"
      - "服务端风险请求"
      - "授权工具审计信息"
  time_window:
    baseline: "待补充历史对照窗口"
    observation: "待补充异常观测窗口"
    granularity: "天"
  expected_outputs:
    - "SDK 覆盖率"
    - "日志缺失分布"
    - "风险请求与异常包关联"
    - "官方版本对照"
    - "授权工具排除结果"
  interpretation_notes:
    strong_evidence_if:
      - "风险请求集中于签名、版本、SDK 或安全模块异常包，并排除官方版本采集问题"
    weak_signal_if:
      - "只看到 SDK 日志缺失，没有包或版本证据"
    counter_evidence_if:
      - "官方包同版本同样缺失"
      - "授权工具调用可解释"
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with:
      - "包签名/版本/安全模块异常"
      - "token/device/ip/ua 一致性异常"
      - "接口直达证据"
  safety_boundary:
    false_positive_risks:
      - "官方埋点缺失"
      - "日志延迟"
      - "采样口径变化"
      - "合法接口化运营"
    prohibited_actions:
      - "不得把 SDK 缺失直接等同协议攻击"
```

### 9. 治理建议

- 当前只做监控、加采和样本复核，不做强拦截。
- 对异常版本/渠道加采 SDK 覆盖、包完整性和端侧上下文。
- 对高风险请求可做低准灰度限速或二次校验，但需保留回滚和白名单。
- 若后续确认破解包，治理转向包完整性校验、风险版本限制、强制升级和样本库回流。

### 10. 是否需要人工确认

需要。因为 mock response 为 partial，且缺少关键反证排除项。

### 11. 自评：是否符合 dataagent_conclusion_thresholds_v1.md

符合。partial 返回被降级为“证据不足”，没有因前端无日志和接口相似直接定协议；结论严格遵守“只有前端无日志或高频请求不足以判断协议攻击”的阈值。

## Case 2：活动场景群控抢奖励

### 1. 用户问题

怀疑活动场景存在群控抢奖励，能否判断为活动黑产或群控？

### 2. 触发 Skill

- 主控 Skill：`activity_anti_cheating_expert_skill`
- 辅助 Skill：`group_control_expert_skill`、`real_user_crowdsourcing_skill`、`evidence_decomposition_skill`

### 3. query_intent 摘要

- intent_id：`case_002_activity_group_control_001`
- target_evidence：设备团组 + 同批启动/停止 + 活动奖励/提现
- 期望返回：设备/账号团组、同批启停、行为路径相似、奖励提现聚集、后验质量、合法矩阵或活动自然高峰对照。
- 安全边界：不得仅凭奖励领取多、设备聚集、低留存或高频参与直接定群控。

### 4. mock dataagent response

```yaml
mock_dataagent_response:
  status: "success"
  returned_type:
    - "设备/账号团组摘要"
    - "行为路径相似摘要"
    - "奖励/提现聚集摘要"
    - "后验质量摘要"
  evidence_summary:
    - "目标活动参与对象存在稳定设备/账号团组。"
    - "多个团组在活动关键时间窗口内出现同步参与。"
    - "任务路径相似，奖励领取后后验质量偏弱。"
    - "奖励结果存在聚集，但提现或最终收益主体未完全闭合。"
  key_findings:
    - "设备/账号聚集和批次同步同时存在。"
    - "行为路径模板化明显。"
    - "后验留存、复访或业务价值表现偏弱。"
    - "合法矩阵/活动运营授权排除项未返回。"
    - "真人众包任务平台、教程话术证据未返回。"
  missing_evidence:
    - "合法商家/达人/机构活动运营授权排除。"
    - "提现或最终收益主体完整链路。"
    - "外部任务平台或教程话术证据。"
    - "活动自然高峰和业务日历解释。"
  confidence_hint: "high"
  permission_notes:
    - "mock 状态为 success，但授权矩阵和提现主体链路不在本次返回范围内。"
```

### 5. Dennis Agent 证据解释

强证据：

- 暂不作为强证据闭环。虽然返回为 success，但缺少合法矩阵排除和最终收益主体闭合，不能直接“明确判断”群控或活动黑产。

中证据：

- 设备/账号团组稳定，支持群控或组织化参与假设。
- 同批参与和路径模板化，支持统一调度或任务化执行。
- 奖励聚集和后验质量偏弱，支持活动套利或低质参与假设。

弱证据：

- 后验质量偏弱本身只能说明钱效或质量问题，不等于黑产。
- 行为路径相似可能由活动规则、教程传播或真实用户模仿造成。

反证：

- 尚未排除合法商家/达人/机构运营。
- 尚未排除活动自然高峰、开抢机制、业务日历。
- 尚未区分群控和真人众包；设备团组偏群控，但缺最终收益链，任务化线索也可能指向众包。

### 6. 结论等级

高度疑似。

### 7. 为什么能或不能下强结论

可以下“高度疑似”，不能下“明确判断”。根据阈值，群控明确判断需要设备/账号团组、同批启动停止、行为路径高度相似、收益聚集、无合法矩阵授权且链路稳定复现。当前 mock 返回已覆盖设备团组、同批同步、路径模板和奖励聚集，但缺少合法矩阵排除、提现/最终收益主体闭合、活动自然高峰排除，因此不能打明确判断。

### 8. 下一步补证 query_intent

```yaml
query_intent:
  intent_id: "case_002_activity_group_control_002"
  risk_question: "活动异常参与是否存在合法运营解释、真人众包解释或最终收益链闭合"
  target_evidence: "授权主体/合法矩阵 + 收益聚集 + 任务化完成"
  applicable_skill:
    primary: "activity_anti_cheating_expert_skill"
    auxiliary:
      - "group_control_expert_skill"
      - "real_user_crowdsourcing_skill"
  minimum_inputs:
    required:
      - "活动场景或活动 ID 语义"
      - "异常团组集合"
      - "观测时间窗口"
      - "奖励和提现口径"
    optional:
      - "活动运营授权主体语义"
      - "业务活动日历"
      - "任务平台或教程线索"
    missing:
      - "授权主体/账号范围/工具来源审计口径"
      - "提现或最终收益主体口径"
  query_dimensions:
    entities:
      - "账号"
      - "设备"
      - "活动任务"
      - "奖励"
      - "提现主体"
      - "授权主体"
    group_by:
      - "授权主体"
      - "账号范围"
      - "操作目的"
      - "任务完成窗口"
      - "收益主体"
      - "后验质量分层"
    joins:
      - "活动参与日志"
      - "奖励发放记录"
      - "提现或核销记录"
      - "授权矩阵审计信息"
      - "业务活动日历"
      - "后验质量指标"
  time_window:
    baseline: "待补充历史活动或活动前对照窗口"
    observation: "待补充活动异常窗口"
    granularity: "小时或天"
  expected_outputs:
    - "合法授权匹配情况"
    - "超范围动作摘要"
    - "最终收益主体聚集"
    - "任务窗口集中度"
    - "活动自然高峰对照"
  interpretation_notes:
    strong_evidence_if:
      - "无合法授权，设备团组、同批调度、路径模板、最终收益聚集闭合"
    weak_signal_if:
      - "只有低质量或奖励聚集"
    counter_evidence_if:
      - "合法矩阵授权和活动运营排期可解释"
      - "活动规则导致自然同步"
  conclusion_threshold:
    sufficient_for: "明确判断"
    must_combine_with:
      - "合法矩阵排除"
      - "最终收益链闭合"
      - "活动自然高峰排除"
  safety_boundary:
    false_positive_risks:
      - "合法活动运营"
      - "活动开抢自然高峰"
      - "真人众包而非群控"
      - "活动低质而非黑产"
    prohibited_actions:
      - "不得在授权和收益链未查清前全量扣奖或封禁"
```

### 9. 治理建议

- 对高度疑似团组进入灰度治理：奖励延迟发放、提现复核、任务冷却、设备/账号团组加采。
- 对已命中的团组做分层，不直接影响全量活动参与者。
- 补合法矩阵和活动运营授权排查，避免误伤商家、达人、机构或内部运营。
- 若下一轮补证闭合，再考虑局部奖励冻结、账号团组限权、规则补洞和收益回收。

### 10. 是否需要人工确认

需要。虽然 mock 返回为 success，但关键反证排除项缺失；涉及奖励、提现或处罚，应人工确认。

### 11. 自评：是否符合 dataagent_conclusion_thresholds_v1.md

符合。成功返回不等于明确判断；在缺少合法矩阵排除和收益链闭合时，只给“高度疑似”，符合群控和活动黑产阈值。

## Case 3：渠道点击注入 / 归因抢量

### 1. 用户问题

怀疑渠道存在点击注入或归因抢量，能否判断为渠道作弊？

### 2. 触发 Skill

- 主控 Skill：`traffic_anti_cheating_expert_skill`
- 辅助 Skill：`evidence_decomposition_skill`、`risk_chain_reconstruction_skill`

### 3. query_intent 摘要

- intent_id：`case_003_channel_attribution_hijack_001`
- target_evidence：CTIT / 渠道归因 + 自然量跷跷板 + 后验质量
- 期望返回：CTIT 分布、渠道份额变化、自然量跷跷板、新客真实性、后验质量、设备/IP/UA 或点击模板异常、预算/活动/版本/归因规则对照。
- 安全边界：不得仅凭 CTIT 异常、渠道上涨或自然量下降直接定渠道作弊。

### 4. mock dataagent response

```yaml
mock_dataagent_response:
  status: "no_permission"
  returned_type:
    - "失败响应"
  evidence_summary:
    - "未取得渠道归因、点击链路和后验质量数据。"
  key_findings:
    - "无可解释的数据结果。"
    - "未返回 CTIT 分布。"
    - "未返回自然量跷跷板。"
    - "未返回后验质量或设备/IP/UA 异常。"
  missing_evidence:
    - "CTIT 分布。"
    - "渠道份额和自然量变化。"
    - "后验质量。"
    - "设备/IP/UA 或点击行为模板。"
    - "预算、活动、版本、归因规则变更对照。"
  confidence_hint: "low"
  permission_notes:
    - "mock 状态为 no_permission，表示未来平台阶段需要补充渠道归因和后验质量相关权限。"
```

### 5. Dennis Agent 证据解释

强证据：

- 无。

中证据：

- 无。mock response 没有返回可用于支持渠道作弊的有效数据。

弱证据：

- 用户提出的“怀疑”只能作为待查线索，不能作为风险证据。

反证：

- 无数据反证。但无权限导致证据缺失，不等于风险不存在，也不等于风险成立。

### 6. 结论等级

证据不足。

### 7. 为什么能或不能下强结论

不能下强结论。mock response 为 no_permission，按照要求必须降级。渠道抢量 / 归因劫持明确判断需要 CTIT 异常、自然量跷跷板、渠道后验质量异常、设备/IP/UA/点击行为异常和归因链路可复现；当前全部关键证据缺失，因此只能进入权限补齐和人工查数。

### 8. 下一步补证 query_intent

```yaml
query_intent:
  intent_id: "case_003_channel_attribution_hijack_002"
  risk_question: "补齐渠道归因权限后，验证渠道异常是否由点击注入、归因抢量或业务变更导致"
  target_evidence: "CTIT / 自然量跷跷板 / 后验质量 / 业务变更排除"
  applicable_skill:
    primary: "traffic_anti_cheating_expert_skill"
    auxiliary:
      - "evidence_decomposition_skill"
      - "risk_chain_reconstruction_skill"
  minimum_inputs:
    required:
      - "目标渠道集合"
      - "异常时间窗口"
      - "归因口径"
      - "渠道归因数据访问权限"
      - "后验质量数据访问权限"
    optional:
      - "预算调整记录语义"
      - "活动排期语义"
      - "版本发布语义"
      - "归因规则变更语义"
    missing:
      - "渠道归因权限"
      - "点击链路权限"
      - "后验质量权限"
      - "业务变更对照信息"
  query_dimensions:
    entities:
      - "渠道"
      - "点击"
      - "安装"
      - "激活"
      - "新客"
      - "设备"
      - "IP"
      - "UA"
    group_by:
      - "渠道"
      - "媒体或广告位"
      - "CTIT 时间桶"
      - "自然/付费来源"
      - "设备分群"
      - "新客质量分层"
      - "版本或活动周期"
    joins:
      - "点击日志"
      - "安装/激活日志"
      - "归因结果"
      - "自然量与渠道量指标"
      - "后验质量指标"
      - "设备/IP/UA 环境信息"
      - "预算、活动、版本、归因规则变更信息"
  time_window:
    baseline: "待补充历史对照窗口"
    observation: "待补充异常观测窗口"
    granularity: "小时或天"
  expected_outputs:
    - "CTIT 分布及异常短/长尾"
    - "渠道份额变化"
    - "自然量跷跷板关系"
    - "新客真实性和设备历史摘要"
    - "留存/付费/活跃后验质量"
    - "设备/IP/UA 或点击模板异常"
    - "预算、活动、版本、归因规则变更对照"
  interpretation_notes:
    strong_evidence_if:
      - "CTIT 异常、自然量跷跷板、后验质量异常、设备/IP/UA 或点击模板异常同时成立，并排除业务变更"
    weak_signal_if:
      - "只有 CTIT 偏移或只有渠道转化上涨"
    counter_evidence_if:
      - "预算变化、活动排期、归因规则调整或版本发布可解释"
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with:
      - "CTIT 分布"
      - "自然量跷跷板"
      - "后验质量"
      - "设备/IP/UA 或点击行为"
      - "业务变更排除"
  safety_boundary:
    false_positive_risks:
      - "预算调整"
      - "活动排期"
      - "版本发布"
      - "归因规则变化"
      - "媒体策略变化"
      - "数据 SLA 或口径变化"
    prohibited_actions:
      - "不得在无权限、无数据时拒付、扣减结算或定义作弊"
```

### 9. 治理建议

- 当前不做渠道扣减、拒付或处罚。
- 先补权限和业务变更信息，进入人工查数或平台权限申请。
- 在权限补齐前，只能做监控和风险看板占位，不输出渠道作弊定性。
- 若后续证据闭合，再按渠道维度做灰度结算复核、分渠道限量、渠道沟通和归因规则审计。

### 10. 是否需要人工确认

需要。当前 no_permission，必须由人工或平台补齐权限后再进入下一轮解释。

### 11. 自评：是否符合 dataagent_conclusion_thresholds_v1.md

符合。no_permission 被降级为“证据不足”，没有把用户怀疑、CTIT 假设或渠道异常描述伪装成真实结果；也没有在缺少 CTIT、自然量、后验质量和设备/IP/UA 证据时判断渠道作弊。

## 总结

| Case | mock status | 结论等级 | 是否强结论 | 核心原因 |
|---|---|---|---|---|
| 协议攻击但前端无日志 | partial | 证据不足 | 否 | 缺 SDK、包、token/device/ip/ua、授权工具排除 |
| 活动场景群控抢奖励 | success | 高度疑似 | 否 | 有多项中强证据，但缺合法矩阵排除和收益链闭合 |
| 渠道点击注入 / 归因抢量 | no_permission | 证据不足 | 否 | 无权限导致关键数据未返回 |

整体自评：符合 `dataagent_result_interpretation_rules_v1.md` 和 `dataagent_conclusion_thresholds_v1.md`。本轮闭环验证了三个约束：mock 结果不能伪装成真实数据；partial / no_permission 必须降级；缺少关键反证排除项时不得给明确判断。
