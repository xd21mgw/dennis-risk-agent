# Data Agent query_intent 3 Case 离线测试

说明：本文件基于 `07_tools/dataagent/` 下的工具抽象层生成，仅用于设计未来 Data Agent 接入方式。本轮不调用真实 Data Agent，不编造 API，不编造真实表名、字段名、接口路径或真实查询结果。

## Case 1：怀疑一批请求是协议攻击，但前端无日志

### 应触发的 Skill

- 主控 Skill：`protocol_attack_expert_skill`
- 辅助 Skill：`cracked_app_expert_skill`、`evidence_decomposition_skill`
- 必要边界：前端无日志不等于协议；必须排查埋点缺失、SDK 采样、官方包版本问题、破解包绕采集、合法工具调用。

### 需要的证据

- 前后端链路一致性：服务端请求是否有前置页面、事件、端上下文。
- SDK 日志覆盖：缺日志是否集中在特定版本、渠道、包签名或 SDK 模块状态。
- token / device / ip / ua 一致性：请求环境是否和登录态、设备、UA、IP 合理匹配。
- 接口序列固化：是否存在高度模板化接口顺序、间隔和参数模式。

### 应生成的 query_intent

```yaml
query_intent:
  intent_id: "case_001_protocol_frontend_missing_001"
  risk_question: "怀疑一批服务端请求是协议攻击，但前端无日志，是否存在脱端请求"
  target_evidence: "前后端链路一致性"
  applicable_skill:
    primary: "protocol_attack_expert_skill"
    auxiliary:
      - "cracked_app_expert_skill"
      - "evidence_decomposition_skill"
  minimum_inputs:
    required:
      - "观测时间窗口"
      - "目标业务动作或接口语义"
      - "风险请求对象集合或筛选口径"
      - "前端事件链路口径"
    optional:
      - "客户端版本"
      - "渠道"
      - "包签名状态语义"
      - "SDK 日志口径"
    missing:
      - "待补充具体观测窗口"
      - "待补充风险请求集合来源"
  query_dimensions:
    entities:
      - "用户"
      - "账号"
      - "设备"
      - "请求"
      - "前端事件"
      - "客户端包"
    group_by:
      - "业务动作"
      - "客户端版本"
      - "渠道"
      - "设备分群"
      - "请求链路完整性"
    joins:
      - "服务端请求日志"
      - "前端事件日志"
      - "端侧上下文日志"
      - "SDK 日志覆盖信息"
      - "客户端包信息"
  time_window:
    baseline: "待补充历史对照窗口"
    observation: "待补充异常观测窗口"
    granularity: "小时或天"
  expected_outputs:
    - "端链路覆盖率"
    - "无前端事件请求占比"
    - "缺失日志的版本/渠道/包分布"
    - "接口序列重复度"
    - "token/device/ip/ua 冲突分布"
    - "官方版本对照与异常样本摘要"
  interpretation_notes:
    strong_evidence_if:
      - "关键请求长期缺少前置页面/事件链"
      - "接口序列高度固化"
      - "token/device/ip/ua 存在批量冲突"
      - "已排除官方埋点缺失、SDK 采样、破解包绕采集和合法工具调用"
    weak_signal_if:
      - "只有前端无日志或请求频次高"
      - "只在单个版本存在日志缺失但无包或链路证据"
    counter_evidence_if:
      - "官方包同版本同样缺日志"
      - "缺失集中于埋点口径变更或日志延迟"
      - "请求来自授权工具或合法矩阵范围内"
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with:
      - "接口序列固化"
      - "token/device/ip/ua 一致性异常"
      - "SDK 或包完整性排查结果"
  safety_boundary:
    false_positive_risks:
      - "埋点缺失"
      - "SDK 采样"
      - "日志延迟"
      - "官方版本问题"
      - "破解包绕采集"
      - "授权接口化运营"
    prohibited_actions:
      - "不得仅凭前端无日志直接定协议"
      - "不得直接封禁或上线强拦截"
```

### Data Agent 预期返回类型

- 链路覆盖率、缺失率、趋势分布。
- 无前端事件请求的版本、渠道、设备、账号分布。
- SDK 日志覆盖摘要和官方版本对照。
- 接口序列模板、重复率、间隔分布。
- token/device/ip/ua 冲突摘要。
- 异常样本说明，不包含真实敏感标识。

### 返回后如何解释

- 如果只有服务端请求且前端无日志：最多解释为“链路冲突待补证”。
- 如果官方包同版本也缺日志：优先解释为埋点、SDK 或口径问题。
- 如果风险请求集中在异常包签名、SDK 缺失或安全模块异常：优先转破解包判断。
- 如果无端链路、接口直达、接口序列固化、token/device/ip/ua 异常同时成立，且排除合法工具和采集问题：可升级为协议高度疑似或明确判断。

### 够不够下结论的判断标准

- 明确判断：无正常端链路 + 接口直达 + 接口序列固化 + token/device/ip/ua 异常 + 排除埋点缺失、官方工具、破解包绕采集。
- 高度疑似：服务端请求与端链路冲突，接口序列异常，但包证据或 token 证据未闭合。
- 证据不足：只有前端无日志、只有高频请求或只有接口调用量上涨。
- 反向排除 / 暂不支持：官方工具授权调用、官方包同样缺日志、埋点口径变化可解释。

### 如果证据不足，下一步 query_intent

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
      - "待补充官方版本对照口径"
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
  time_window:
    baseline: "待补充历史对照窗口"
    observation: "待补充异常观测窗口"
    granularity: "天"
  expected_outputs:
    - "SDK 覆盖率"
    - "日志缺失分布"
    - "风险请求与异常包关联"
    - "官方版本对照"
  interpretation_notes:
    strong_evidence_if:
      - "风险请求集中于签名、版本、SDK 或安全模块异常包"
    weak_signal_if:
      - "只看到 SDK 日志缺失，没有包或版本证据"
    counter_evidence_if:
      - "官方包同版本同样缺失"
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with:
      - "包签名/版本/安全模块异常"
      - "端行为或请求链路证据"
  safety_boundary:
    false_positive_risks:
      - "官方埋点缺失"
      - "日志延迟"
      - "采样口径变化"
    prohibited_actions:
      - "不得把 SDK 缺失直接等同协议攻击"
```

## Case 2：怀疑活动场景存在群控抢奖励

### 应触发的 Skill

- 主控 Skill：`activity_anti_cheating_expert_skill`
- 辅助 Skill：`group_control_expert_skill`、`real_user_crowdsourcing_skill`、`evidence_decomposition_skill`
- 必要边界：高频参与、设备聚集、奖励领取多都不能单独定群控；必须排除活动自然高峰、真人众包、合法运营和低质用户。

### 需要的证据

- 设备团组：设备、账号、IP、环境是否形成稳定团组。
- 行为路径相似：任务路径、点击序列、完成窗口是否模板化。
- 同批启动 / 停止：是否存在批次化同步调度。
- 活动奖励 / 提现：奖励、提现、核销是否向少量主体聚集。
- 后验质量：留存、付费、复访、退款或投诉是否显著异常。
- 授权主体 / 合法矩阵：是否是商家、达人、机构、客服等授权活动运营。

### 应生成的 query_intent

```yaml
query_intent:
  intent_id: "case_002_activity_group_control_001"
  risk_question: "怀疑活动场景存在群控抢奖励，是否存在设备/账号统一调度和奖励聚集"
  target_evidence: "设备团组 + 同批启动/停止 + 活动奖励/提现"
  applicable_skill:
    primary: "activity_anti_cheating_expert_skill"
    auxiliary:
      - "group_control_expert_skill"
      - "real_user_crowdsourcing_skill"
      - "evidence_decomposition_skill"
  minimum_inputs:
    required:
      - "活动场景或活动 ID 语义"
      - "活动规则和奖励动作语义"
      - "观测时间窗口"
      - "参与对象集合或筛选口径"
    optional:
      - "提现或核销口径"
      - "自然用户对照口径"
      - "业务活动日历"
    missing:
      - "待补充活动规则和奖励口径"
      - "待补充异常参与对象集合"
  query_dimensions:
    entities:
      - "账号"
      - "设备"
      - "IP"
      - "活动任务"
      - "奖励"
      - "提现主体"
    group_by:
      - "设备团组"
      - "账号团组"
      - "分钟级启动窗口"
      - "任务路径模板"
      - "奖励结果"
      - "提现或收益主体"
    joins:
      - "活动参与日志"
      - "设备环境日志"
      - "行为路径事件"
      - "奖励发放记录"
      - "提现或核销记录"
      - "后验质量指标"
  time_window:
    baseline: "待补充历史活动或活动前对照窗口"
    observation: "待补充活动异常窗口"
    granularity: "分钟、小时、天"
  expected_outputs:
    - "设备/账号团组连接图摘要"
    - "同批启动/停止同步率"
    - "行为路径相似度分布"
    - "奖励和提现聚集分布"
    - "后验留存/付费/复访质量"
    - "自然高峰或业务活动对照"
  interpretation_notes:
    strong_evidence_if:
      - "设备/账号团组稳定"
      - "同批启停明显"
      - "行为路径高度相似"
      - "奖励或提现向少量主体聚集"
      - "无合法矩阵授权或业务合理解释"
    weak_signal_if:
      - "只有奖励领取多"
      - "只有设备聚集"
      - "只有低留存或低付费"
    counter_evidence_if:
      - "活动自然高峰可解释同步"
      - "合法商家/达人/MCN 矩阵授权"
      - "设备离散但任务窗口集中，更像真人众包"
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with:
      - "设备团组"
      - "同批启动/停止"
      - "行为路径相似"
      - "收益聚集"
      - "合法矩阵排除"
  safety_boundary:
    false_positive_risks:
      - "活动开抢自然高峰"
      - "真实用户被活动规则引导到相同路径"
      - "真人众包"
      - "商家/达人/机构合法运营"
      - "活动低质而非黑产"
    prohibited_actions:
      - "不得仅凭奖励领取多直接定群控"
      - "不得直接扣除或封禁全量活动参与者"
```

### Data Agent 预期返回类型

- 设备/账号/IP 团组摘要和连接关系。
- 同批启动/停止峰值、同步率、批次稳定性。
- 行为路径相似度、任务完成窗口、自然用户对照。
- 奖励、提现、核销、收益主体聚集分布。
- 后验质量分布，例如留存、付费、复访、退款或投诉。
- 授权主体或合法矩阵审计状态摘要。

### 返回后如何解释

- 设备聚集只是中证据，不能直接定群控。
- 行为路径相似也可能来自活动规则、教程传播或真人众包。
- 奖励/提现聚集能提高组织化置信，但商家、机构、MCN 也可能存在合法收益聚集。
- 只有设备团组、同批调度、路径模板、收益聚集、无授权审计同时成立，才接近群控抢奖励强证据。
- 如果设备离散、行为真实、目标一致、任务窗口集中，优先转真人众包或低质用户分支。

### 够不够下结论的判断标准

- 明确判断：设备/账号团组 + 同批启动停止 + 行为路径高度相似 + 奖励/提现聚集 + 无合法矩阵授权，链路稳定复现。
- 高度疑似：设备团组和行为路径异常明显，但收益链或调度证据不足。
- 证据不足：只有多设备、多账号、高频参与、低留存、低付费或奖励领取多。
- 反向排除 / 暂不支持：合法矩阵、活动自然高峰、企业网络、测试流量、活动机制导致低质。

### 如果证据不足，下一步 query_intent

```yaml
query_intent:
  intent_id: "case_002_activity_group_control_002"
  risk_question: "活动异常参与是否更像真人众包或活动低质，而不是群控"
  target_evidence: "任务化完成 + 活动奖励/提现 + 后验质量"
  applicable_skill:
    primary: "real_user_crowdsourcing_skill"
    auxiliary:
      - "activity_anti_cheating_expert_skill"
      - "group_control_expert_skill"
  minimum_inputs:
    required:
      - "活动任务语义"
      - "参与用户集合"
      - "观测时间窗口"
      - "奖励和提现口径"
    optional:
      - "教程话术或外部任务平台线索"
      - "自然用户对照口径"
    missing:
      - "待补充任务平台或教程线索"
  query_dimensions:
    entities:
      - "用户"
      - "账号"
      - "设备"
      - "活动任务"
      - "奖励"
      - "提现主体"
    group_by:
      - "任务完成窗口"
      - "设备离散度"
      - "行为路径模板"
      - "奖励聚集"
      - "后验质量分层"
    joins:
      - "活动参与日志"
      - "行为路径事件"
      - "奖励发放记录"
      - "提现或核销记录"
      - "后验质量指标"
  time_window:
    baseline: "待补充自然用户对照窗口"
    observation: "待补充活动异常窗口"
    granularity: "小时或天"
  expected_outputs:
    - "任务完成窗口集中度"
    - "设备离散度"
    - "奖励/提现聚集"
    - "留存/付费/复访后验质量"
    - "自然用户对照"
  interpretation_notes:
    strong_evidence_if:
      - "行为真实但目标任务化"
      - "任务窗口集中"
      - "奖励/提现聚集"
      - "存在教程话术或任务平台线索"
    weak_signal_if:
      - "只有低留存或低钱效"
      - "只有设备离散和目标一致"
    counter_evidence_if:
      - "自然传播或活动规则足以解释任务集中"
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with:
      - "任务平台或教程话术证据"
      - "收益链证据"
  safety_boundary:
    false_positive_risks:
      - "真实用户参与"
      - "活动机制导致低质"
      - "达人或商家运营"
    prohibited_actions:
      - "证据不足时不得定义黑产"
```

## Case 3：怀疑渠道存在点击注入或归因抢量

### 应触发的 Skill

- 主控 Skill：`traffic_anti_cheating_expert_skill`
- 辅助 Skill：`evidence_decomposition_skill`、`risk_chain_reconstruction_skill`
- 可能辅助：若出现协议化点击或 SDK 异常，再引入 `protocol_attack_expert_skill` 或 `cracked_app_expert_skill`。
- 必要边界：CTIT 异常、渠道转化上涨或自然量下降都不能单独定渠道作弊。

### 需要的证据

- CTIT / 渠道归因：点击到安装、激活、转化时间间隔是否异常。
- 自然量跷跷板：渠道增长是否伴随自然量或其他渠道异常下跌。
- 新客真实性：新客设备历史、注册路径、留存、付费是否自然。
- 后验质量：渠道用户留存、付费、活跃、退款、投诉是否异常。
- token/device/ip/ua 一致性或点击行为异常：是否存在批量设备、IP、UA、点击模板。
- AB 或归因规则变更：排除预算、活动、版本、归因口径变化。

### 应生成的 query_intent

```yaml
query_intent:
  intent_id: "case_003_channel_attribution_hijack_001"
  risk_question: "怀疑渠道存在点击注入或归因抢量，是否存在 CTIT 异常、自然量跷跷板和后验质量异常"
  target_evidence: "CTIT / 渠道归因 + 自然量跷跷板 + 后验质量"
  applicable_skill:
    primary: "traffic_anti_cheating_expert_skill"
    auxiliary:
      - "evidence_decomposition_skill"
      - "risk_chain_reconstruction_skill"
  minimum_inputs:
    required:
      - "目标渠道或渠道集合"
      - "归因口径"
      - "观测时间窗口"
      - "转化动作语义"
    optional:
      - "投放预算或活动排期"
      - "版本发布信息"
      - "归因规则变更信息"
      - "自然量对照口径"
    missing:
      - "待补充目标渠道集合"
      - "待补充归因规则变更信息"
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
    joins:
      - "点击日志"
      - "安装/激活日志"
      - "归因结果"
      - "自然量与渠道量指标"
      - "后验质量指标"
      - "设备/IP/UA 环境信息"
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
      - "CTIT 异常集中于目标渠道"
      - "目标渠道增长伴随自然量或其他渠道异常下降"
      - "后验质量显著差"
      - "设备/IP/UA 或点击行为存在模板化异常"
      - "排除预算、活动、版本和归因口径变化"
    weak_signal_if:
      - "只有 CTIT 偏移"
      - "只有某渠道转化上涨"
      - "只有自然量下跌"
    counter_evidence_if:
      - "预算变化、活动排期、归因规则调整或版本发布可解释"
      - "后验质量与自然用户接近"
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with:
      - "CTIT 异常"
      - "自然量跷跷板"
      - "后验质量异常"
      - "设备/IP/UA 或点击行为异常"
  safety_boundary:
    false_positive_risks:
      - "预算调整"
      - "活动排期"
      - "版本发布"
      - "归因规则变化"
      - "媒体策略变化"
      - "数据 SLA 或口径变化"
    prohibited_actions:
      - "不得仅凭 CTIT 异常直接判渠道作弊"
      - "不得直接全量拒付或扣减结算"
```

### Data Agent 预期返回类型

- CTIT 分布、异常时间桶、渠道对照。
- 渠道转化份额、自然量与其他渠道变化趋势。
- 新客真实性、设备历史和来源质量摘要。
- 后验留存、付费、活跃、退款或投诉质量分布。
- 设备/IP/UA 聚集或点击行为模板摘要。
- 预算、活动、版本、归因规则变更对照信息。

### 返回后如何解释

- CTIT 异常只是归因异常信号，不等于点击注入。
- 渠道上涨加自然量下降支持抢量假设，但也可能由预算、活动、版本或归因规则变化导致。
- 后验质量差说明渠道价值低，但仍需设备/IP/UA、点击行为或归因链路证据才能靠近作弊结论。
- 如果 CTIT 异常、自然量跷跷板、后验质量异常、设备/IP/UA 或点击模板异常同时成立，并排除业务变更，才可进入渠道抢量高度疑似或明确判断。

### 够不够下结论的判断标准

- 明确判断：CTIT 异常 + 自然量跷跷板 + 渠道后验质量异常 + 设备/IP/UA/点击行为异常 + 归因链路可复现。
- 高度疑似：CTIT 和自然量结构异常，但渠道行为或后验质量证据不完整。
- 证据不足：只有渠道转化上涨、只有 CTIT 偏移或只有自然量下降。
- 反向排除 / 暂不支持：预算变化、活动排期、归因规则调整、版本发布、媒体策略变化可解释。

### 如果证据不足，下一步 query_intent

```yaml
query_intent:
  intent_id: "case_003_channel_attribution_hijack_002"
  risk_question: "渠道归因异常是否由预算、活动、版本或归因规则变化导致，而不是点击注入或抢量"
  target_evidence: "AB 实验结果 / 归因规则变更 / 后验质量对照"
  applicable_skill:
    primary: "traffic_anti_cheating_expert_skill"
    auxiliary:
      - "evidence_decomposition_skill"
  minimum_inputs:
    required:
      - "目标渠道集合"
      - "异常时间窗口"
      - "归因口径"
    optional:
      - "AB 实验名称或链接语义"
      - "预算调整记录语义"
      - "活动排期语义"
      - "版本发布语义"
    missing:
      - "待补充实验/活动/版本变更信息"
  query_dimensions:
    entities:
      - "渠道"
      - "实验组"
      - "对照组"
      - "自然量"
      - "新客"
      - "设备"
    group_by:
      - "渠道"
      - "实验组/对照组"
      - "时间桶"
      - "版本"
      - "活动周期"
      - "后验质量分层"
    joins:
      - "归因结果"
      - "渠道量与自然量指标"
      - "AB 实验分析"
      - "版本发布信息"
      - "活动排期信息"
      - "后验质量指标"
  time_window:
    baseline: "待补充变更前窗口"
    observation: "待补充变更后窗口"
    granularity: "小时或天"
  expected_outputs:
    - "实验组/对照组差异"
    - "变更前后渠道和自然量趋势"
    - "后验质量对照"
    - "归因规则或版本变更解释"
  interpretation_notes:
    strong_evidence_if:
      - "异常只出现在目标渠道，且不能被预算、活动、版本、实验或归因规则解释"
    weak_signal_if:
      - "异常与业务变更同周期，但缺对照组"
    counter_evidence_if:
      - "实验或规则变更可以解释 CTIT 和自然量结构变化"
  conclusion_threshold:
    sufficient_for: "证据不足"
    must_combine_with:
      - "CTIT 分布"
      - "自然量跷跷板"
      - "后验质量"
      - "设备/IP/UA 或点击行为"
  safety_boundary:
    false_positive_risks:
      - "投放策略变化"
      - "归因规则调整"
      - "实验流量"
      - "版本发布"
    prohibited_actions:
      - "不得在业务变更未排除前拒付或扣减结算"
```

