# Data Agent Query Intent 4 Case Rerun After Schema Fix

本轮只验证 Dennis 风控 Agent 是否能在不查数、不调用真实 Data Agent、不生成 mock response 的情况下，把 4 个薄弱历史 case 稳定转换为 `query_intent_schema_v2`。

约束：

- 不调用真实 Data Agent。
- 不编造真实表名、字段名、SQL 或 API。
- 不修改 Skill 文件。
- 字段均使用 `field_dictionary_template_v1.md` 中的抽象字段类型。
- join path 均使用 `data_join_paths_v1.md` 中的抽象 join path。

---

## Case 1：合法矩阵 商家/达人/MCN 批量登录或接口化运营

### 1. 用户问题

商家、达人或 MCN 账号出现批量登录、接口化运营、多账号代管行为，是否应该定性为协议攻击、群控，还是合法矩阵或局部超范围违规？

### 2. 应触发 Skill

- 主控：`legal_operation_matrix_playbook_v2_3`
- 辅助：`account_security_expert_skill`、`protocol_attack_expert_skill`、`group_control_expert_skill`、`traffic_diversion_interception_skill`

### 3. 目标证据

- 授权主体、账号范围、工具来源、操作人、操作目的、调用接口、敏感动作、收益主体、业务登记信息、历史违规记录。
- 批量行为是否在授权范围内。
- 是否存在导流、骚扰、欺诈、支付、结算等局部风险。
- 是否存在无授权工具、规避平台规则、收益主体异常、账号关系异常等黑产线索。

### 4. query_intent_schema_v2 完整结构

```yaml
query_intent:
  intent_id: "LEGAL-001_operation_matrix_rerun_v2_001"
  intent_type: "legal_operation_matrix_check"
  risk_question: "商家/达人/MCN 批量登录或接口化运营是否属于合法矩阵、超范围局部违规或非授权黑产自动化"
  target_evidence: "合法矩阵授权边界与局部风险证据"
  applicable_skill:
    primary: "legal_operation_matrix_playbook_v2_3"
    auxiliary:
      - "account_security_expert_skill"
      - "protocol_attack_expert_skill"
      - "group_control_expert_skill"
      - "traffic_diversion_interception_skill"
  minimum_inputs:
    required:
      - "账号集合或操作主体集合"
      - "异常动作类型，如登录、接口化调用、批量发布、私信、投放、结算"
      - "time_window"
    optional:
      - "疑似商家/达人/MCN/机构主体"
      - "工具来源或操作入口"
      - "敏感动作样本"
      - "收益主体线索"
    missing:
      - "授权主体"
      - "授权账号范围"
      - "工具来源"
      - "操作人"
      - "收益主体"
  required_data_domains:
    - "用户信息域"
    - "后端数据域"
    - "策略引擎域"
    - "关联网络域"
    - "风险画像域"
  optional_data_domains:
    - "前端行为域"
    - "活动信息域"
  field_types_needed:
    identity_and_account:
      - "user_id"
      - "account_id"
      - "login_time"
      - "account_status"
    device_and_network:
      - "device_id"
      - "ip"
      - "ua"
      - "app_version"
    session_and_chain:
      - "session_id"
      - "backend_api"
      - "request_time"
      - "api_sequence"
      - "gateway_decision"
    activity_and_channel:
      - "campaign_id"
      - "reward_status"
      - "withdraw_status"
    risk_and_strategy:
      - "risk_label"
      - "risk_score"
      - "strategy_hit"
      - "engine_decision"
      - "disposal_action"
      - "appeal_status"
    relation_network:
      - "relation_group_id"
      - "user_group_id"
      - "relation_edge_type"
      - "relation_strength"
  join_paths_needed:
    - "legal_operation_matrix_authorization_join"
    - "account_lifecycle_device_join"
    - "request_device_environment_join"
    - "strategy_decision_outcome_join"
    - "risk_profile_behavior_outcome_join"
  query_dimensions:
    entities:
      - "账号"
      - "授权主体"
      - "操作人"
      - "工具来源"
      - "收益主体"
      - "设备"
      - "接口"
    group_by:
      - "授权主体"
      - "账号范围"
      - "工具来源"
      - "操作人"
      - "敏感动作"
      - "收益主体"
      - "历史违规类型"
    compare_with:
      - "授权范围"
      - "合法矩阵"
      - "超范围动作"
      - "无授权工具"
      - "正常商家/达人/MCN运营基线"
    joins:
      - "账号与授权主体关联"
      - "账号与操作人关联"
      - "请求与工具来源关联"
      - "敏感动作与策略决策关联"
      - "收益主体与账号关系关联"
  time_window:
    baseline: "历史正常运营窗口，未知时待补充"
    observation: "异常批量运营窗口，未知时待补充"
    granularity: "小时"
  expected_outputs:
    metric_outputs:
      - "授权内账号占比"
      - "超范围账号占比"
      - "未知工具来源占比"
      - "敏感动作分布"
      - "收益主体聚集分布"
      - "历史违规分布"
    evidence_outputs:
      - "合法矩阵依据"
      - "超范围局部违规证据"
      - "非授权黑产嫌疑证据"
      - "导流/欺诈/支付/结算等局部风险证据"
      - "协议/群控转交证据"
    quality_outputs:
      - "授权信息覆盖率"
      - "操作人可追溯性"
      - "工具来源识别覆盖率"
      - "策略日志覆盖率"
      - "关联网络更新时间"
  interpretation_notes:
    strong_evidence_if:
      - "存在授权主体、登记账号范围、可追溯操作人、明确工具来源和审计链路，且动作未超范围"
      - "超范围行为集中在局部账号、局部工具、局部接口或局部操作人，可定位局部违规"
      - "无授权且存在规避平台规则、工具来源异常、收益主体异常、历史违规聚集"
    medium_evidence_if:
      - "存在部分授权或部分审计链路，但账号范围、工具来源或收益主体不完整"
      - "批量行为异常但可被商家/达人/MCN运营场景部分解释"
    weak_signal_if:
      - "只有批量登录、批量调用或多账号代管"
      - "只有设备或 IP 聚集"
    counter_evidence_if:
      - "行为完全在授权账号范围内"
      - "工具来源为官方或授权工具"
      - "敏感动作有审计且无导流、欺诈、支付、结算风险"
      - "收益主体与授权主体一致"
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with:
      - "授权主体与账号范围"
      - "工具来源与操作人"
      - "敏感动作与收益主体"
      - "策略命中与历史违规"
    cannot_conclude_if:
      - "只有批量行为"
      - "授权范围未返回"
      - "工具来源不可识别"
      - "收益主体缺失"
      - "无法区分官方工具、授权工具和非授权工具"
  quality_checks:
    required:
      - "授权信息是否缺失或过期"
      - "账号范围和操作人是否可追溯"
      - "后端接口与策略日志口径是否一致"
      - "风险画像是否为事实标签还是模型/策略推断"
      - "关联网络是否存在离线延迟"
    downgrade_if:
      - "partial / failed / no_permission"
      - "授权主体或账号范围未返回"
      - "操作人、工具来源或收益主体缺失"
      - "只有批量行为，无敏感动作和收益证据"
  freshness_expectation: "准实时"
  permission_boundary: "高敏"
  manual_review_required: "true"
  safety_boundary:
    false_positive_risks:
      - "合法商家/达人/MCN运营被误判为协议或群控"
      - "客服或运营代管被误伤"
      - "官方工具或授权工具被错误拦截"
    prohibited_actions:
      - "不得仅因批量登录或接口化运营直接封禁"
      - "不得仅因授权存在就放过导流、欺诈、支付、结算风险"
      - "不得自动处罚、冻结、扣除或上线策略"
  next_query_intent_when_insufficient:
    intent_type: "strategy_effect_and_false_positive_review"
    target_evidence: "局部处置效果与误伤复盘证据"
    reason: "若只能确认授权存在但不能定位超范围动作，需要进一步评估局部限权、验证、审计或申诉影响"
```

### 5. 为什么选择这些数据域

合法矩阵不是单纯安全攻击问题，必须同时看主体、账号、工具、接口、策略、关系和画像。用户信息域解释账号身份和登录；后端数据域解释接口化动作；策略引擎域解释处置链路；关联网络域解释账号和收益主体关系；风险画像域用于历史风险分层，但不能单独定性。

### 6. 为什么选择这些 join path

`legal_operation_matrix_authorization_join` 是本 case 的核心补强点，用于先判断授权、范围、工具、操作人和收益主体。`account_lifecycle_device_join` 与 `request_device_environment_join` 用于排查账号安全和协议边界；`strategy_decision_outcome_join` 用于避免策略命中即事实；`risk_profile_behavior_outcome_join` 用于把画像降级为辅助证据。

### 7. 是否使用 legal_operation_matrix_authorization_join

使用，且作为主 join path。

### 8. 哪些质量风险会导致降级

- 授权主体、账号范围、工具来源、操作人、收益主体缺失。
- 策略命中和风险事实混用。
- 风险画像只代表模型或策略推断。
- 关联网络离线延迟导致关系不完整。
- 只能看到批量动作，看不到敏感动作和局部违规结果。

### 9. 当前是否足够发给未来 adapter

足够。新 join path 已经覆盖合法矩阵最关键的授权边界，不再只能勉强映射到账号、协议或群控查询。

### 10. 如果仍不够，缺什么输入

仍需要业务侧提供授权主体、授权范围、工具来源、操作人、收益主体、异常动作样本和时间窗口；缺这些输入时只能进入补证，不能直接下协议或群控结论。

---

## Case 2：MIX-001 直播间截流 / 站外添加

### 1. 用户问题

直播间用户被站外添加，疑似有人在直播间截流，是否应该归为反爬、协议，还是导流截流链路？

### 2. 应触发 Skill

- 主控：`traffic_diversion_interception_skill`
- 辅助：`anti_crawler_expert_skill`、`protocol_attack_expert_skill`、`legal_operation_matrix_playbook_v2_3`、`risk_chain_decomposition_skill`

### 3. 目标证据

- 信息暴露入口：直播间、评论、昵称、粉丝列表、动态、私信、搜索等。
- 目标获取路径：如何识别被添加用户。
- 触达方式：搜索、关注、私信、主页承接、站外添加。
- 站外承接证据：外部联系方式、站外群、站外账号、投诉举报线索等。
- 黑产账号矩阵与正常社交、普通关注、用户主动外联、授权运营触达反证。

### 4. query_intent_schema_v2 完整结构

```yaml
query_intent:
  intent_id: "MIX-001_live_diversion_rerun_v2_001"
  intent_type: "traffic_diversion_chain_check"
  risk_question: "直播间用户被站外添加是否属于目标信息暴露后的导流截流链路，而非默认反爬或协议"
  target_evidence: "目标获取 -> 触达 -> 站外承接 -> 矩阵化变现链路"
  applicable_skill:
    primary: "traffic_diversion_interception_skill"
    auxiliary:
      - "anti_crawler_expert_skill"
      - "protocol_attack_expert_skill"
      - "legal_operation_matrix_playbook_v2_3"
      - "risk_chain_decomposition_skill"
  minimum_inputs:
    required:
      - "直播间或目标场景"
      - "被站外添加的用户样本"
      - "异常发生 time_window"
    optional:
      - "触达账号样本"
      - "投诉或举报线索"
      - "站外承接样本"
      - "疑似主播/达人/MCN/客服运营主体"
    missing:
      - "触达账号集合"
      - "站外承接证据"
      - "信息暴露入口"
      - "是否存在授权触达"
  required_data_domains:
    - "前端行为域"
    - "用户信息域"
    - "关联网络域"
    - "风险画像域"
  optional_data_domains:
    - "后端数据域"
    - "策略引擎域"
  field_types_needed:
    identity_and_account:
      - "user_id"
      - "account_id"
      - "account_status"
    device_and_network:
      - "device_id"
      - "ip"
      - "ua"
    session_and_chain:
      - "frontend_event"
      - "page_path"
      - "click_sequence"
      - "backend_api"
      - "request_time"
    activity_and_channel:
      - "activity_participation"
    risk_and_strategy:
      - "risk_label"
      - "risk_score"
      - "strategy_hit"
      - "engine_decision"
      - "disposal_action"
    relation_network:
      - "relation_group_id"
      - "user_group_id"
      - "relation_edge_type"
      - "relation_strength"
      - "common_device_count"
  join_paths_needed:
    - "diversion_exposure_touch_offsite_join"
    - "legal_operation_matrix_authorization_join"
    - "risk_profile_behavior_outcome_join"
    - "frontend_backend_chain_join"
  query_dimensions:
    entities:
      - "直播间"
      - "目标用户"
      - "触达账号"
      - "主播/达人/MCN/客服运营主体"
      - "站外承接线索"
    group_by:
      - "信息暴露入口"
      - "搜索/关注/私信触达方式"
      - "触达账号团组"
      - "站外承接类型"
      - "投诉/举报类型"
      - "授权触达状态"
    compare_with:
      - "正常直播间社交互动"
      - "普通关注"
      - "用户主动外联"
      - "授权运营触达"
      - "无站外承接样本"
    joins:
      - "目标用户与触达账号关系"
      - "信息暴露入口与后续触达关系"
      - "触达账号与站外承接线索关系"
      - "触达账号与授权运营主体关系"
  time_window:
    baseline: "同直播间或同类直播场景正常互动窗口，未知时待补充"
    observation: "被站外添加异常窗口，未知时待补充"
    granularity: "小时"
  expected_outputs:
    metric_outputs:
      - "目标用户被搜索/关注/私信比例"
      - "触达账号集中度"
      - "站外承接线索覆盖率"
      - "投诉/举报集中度"
      - "授权触达覆盖率"
    evidence_outputs:
      - "信息暴露入口证据"
      - "目标获取路径证据"
      - "触达方式证据"
      - "站外承接证据"
      - "账号矩阵证据"
      - "正常社交或授权运营反证"
    quality_outputs:
      - "前端行为日志覆盖率"
      - "关系网络更新时间"
      - "投诉/举报样本可用性"
      - "站外证据回流完整性"
  interpretation_notes:
    strong_evidence_if:
      - "目标用户从直播间暴露后被同一批账号搜索、关注、私信，并出现站外承接证据"
      - "触达账号存在团组化、重复话术、重复承接入口或历史导流风险"
    medium_evidence_if:
      - "有批量触达和目标获取路径，但站外承接证据不完整"
      - "有用户投诉或举报，但触达账号矩阵尚未完整"
    weak_signal_if:
      - "只有关注或私信增多"
      - "只有直播间用户被站外添加的主观反馈"
    counter_evidence_if:
      - "正常社交互动可解释"
      - "普通关注或用户主动外联可解释"
      - "存在授权客服/运营触达且未站外导流"
      - "单个账号偶发行为"
      - "无站外承接证据"
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with:
      - "信息暴露入口"
      - "目标获取路径"
      - "触达方式"
      - "站外承接证据"
      - "账号矩阵或重复行为"
      - "正常社交/授权运营反证"
    cannot_conclude_if:
      - "没有站外承接证据"
      - "只有私信/关注异常"
      - "只有直播间公开信息暴露"
      - "授权运营触达未排除"
      - "无爬虫证据时直接判反爬或协议"
  quality_checks:
    required:
      - "前端行为日志是否延迟或丢点"
      - "关系网络是否存在离线延迟"
      - "站外证据是否可验证"
      - "投诉/举报是否存在样本偏差"
      - "授权运营触达是否已排除"
    downgrade_if:
      - "partial / failed / no_permission"
      - "站外承接证据缺失"
      - "触达账号样本不足"
      - "信息暴露入口不清"
      - "无法排除正常社交或授权运营触达"
  freshness_expectation: "准实时"
  permission_boundary: "高敏"
  manual_review_required: "true"
  safety_boundary:
    false_positive_risks:
      - "正常社交互动被误判为导流"
      - "授权客服/运营触达被误伤"
      - "直播间公开信息暴露被误归为爬虫或协议"
    prohibited_actions:
      - "不得无站外承接证据直接定义导流黑产"
      - "不得无爬虫证据直接触发反爬强结论"
      - "不得自动处罚、冻结、扣除或上线策略"
  next_query_intent_when_insufficient:
    intent_type: "legal_operation_matrix_check"
    target_evidence: "授权运营触达反证与超范围私信/导流证据"
    reason: "若存在主播、达人、MCN、客服或运营主体，需要先判断是否授权触达，再判断是否超范围导流"
```

### 5. 为什么选择这些数据域

导流截流的本质不是“有没有接口异常”，而是目标信息被暴露后被获取、触达、站外承接。前端行为域支撑曝光和触达路径；用户信息域支撑目标用户和触达账号；关联网络域支撑矩阵化；风险画像域只作为辅助分层；后端和策略域用于补充接口行为和处置链路。

### 6. 为什么选择这些 join path

`diversion_exposure_touch_offsite_join` 是主链路，直接表达“目标获取 -> 触达 -> 站外承接”。`legal_operation_matrix_authorization_join` 用于排除授权客服、运营、达人或 MCN 触达。`risk_profile_behavior_outcome_join` 避免只因风险画像下结论。`frontend_backend_chain_join` 只在涉及搜索、私信等接口动作时补充，不用于直接定协议。

### 7. 是否使用 legal_operation_matrix_authorization_join

使用，作为反证 join path，不是主定性路径。

### 8. 哪些质量风险会导致降级

- 站外承接证据不可验证或缺失。
- 触达账号样本不足。
- 无法排除普通关注、正常社交、用户主动外联。
- 授权客服、运营、达人、MCN 触达未排除。
- 关系网络和投诉举报存在延迟或偏差。

### 9. 当前是否足够发给未来 adapter

足够。结构上已经能把直播截流从反爬/协议误归类中拉回导流截流链路，并保留授权触达反证。

### 10. 如果仍不够，缺什么输入

需要目标直播间、被添加用户样本、触达账号、站外承接样本、投诉举报线索和是否存在授权运营主体。缺站外承接时最多只能判“导流截流嫌疑/需补证”。

---

## Case 3：AC-001 外网跟价但内部无明显攻击

### 1. 用户问题

外网价格变化与平台价格高度同步，但内部暂时没有明显接口异常，是否可以直接判定被爬或协议攻击？

### 2. 应触发 Skill

- 主控：`anti_crawler_expert_skill`
- 辅助：`protocol_attack_expert_skill`、`evidence_decomposition_skill`、`dataagent_result_interpretation_rules_v1`

### 3. 目标证据

- 外网价格变化与内部价格变更时间线是否对齐。
- 内部资产访问路径是否异常。
- 是否存在前端公开信息、缓存、合作方同步、内部导出、真人访问等反证路径。
- 是否存在设备、账号、IP、接口、页面访问聚集。
- 是否能排除“外网跟价不等于内部接口被爬”的误判。

### 4. query_intent_schema_v2 完整结构

```yaml
query_intent:
  intent_id: "AC-001_external_price_tracking_rerun_v2_001"
  intent_type: "anti_crawler_asset_leakage_check"
  risk_question: "外网跟价但内部无明显接口异常时，是否存在内部资产访问异常或其他可解释路径"
  target_evidence: "价格/库存等资产访问路径、外部同步时间线与反证路径"
  applicable_skill:
    primary: "anti_crawler_expert_skill"
    auxiliary:
      - "protocol_attack_expert_skill"
      - "evidence_decomposition_skill"
      - "dataagent_result_interpretation_rules_v1"
  minimum_inputs:
    required:
      - "资产类型，如价格、库存或商品信息"
      - "外网跟价样本或外部变化时间"
      - "内部观测 time_window"
    optional:
      - "商品或内容对象集合"
      - "内部价格变更窗口"
      - "可疑访问主体样本"
      - "合作方或公开展示路径线索"
    missing:
      - "外网样本时间线"
      - "内部资产变更时间线"
      - "缓存/合作方/内部导出反证"
  required_data_domains:
    - "前端行为域"
    - "后端数据域"
    - "设备信息域"
    - "关联网络域"
  optional_data_domains:
    - "风险画像域"
    - "策略引擎域"
  field_types_needed:
    identity_and_account:
      - "user_id"
      - "account_id"
    device_and_network:
      - "device_id"
      - "device_profile"
      - "realtime_fingerprint"
      - "ip"
      - "ua"
      - "app_version"
      - "sdk_status"
    session_and_chain:
      - "frontend_event"
      - "backend_api"
      - "event_time"
      - "request_time"
      - "page_path"
      - "api_sequence"
      - "gateway_decision"
    activity_and_channel:
      - "campaign_id"
    risk_and_strategy:
      - "risk_label"
      - "strategy_hit"
      - "engine_decision"
      - "disposal_action"
    relation_network:
      - "relation_group_id"
      - "strong_device_relation"
      - "user_group_id"
      - "common_device_count"
      - "relation_strength"
  join_paths_needed:
    - "asset_access_device_network_join"
    - "frontend_backend_chain_join"
    - "request_device_environment_join"
    - "batch_case_business_context_join"
    - "risk_profile_behavior_outcome_join"
  query_dimensions:
    entities:
      - "资产对象"
      - "页面"
      - "接口"
      - "账号"
      - "设备"
      - "IP"
      - "外部跟价样本"
    group_by:
      - "资产对象"
      - "访问路径"
      - "页面/接口"
      - "设备/账号/IP团组"
      - "访问时间与外部变化时间差"
      - "业务活动/版本/缓存/合作方上下文"
    compare_with:
      - "历史正常资产访问"
      - "同类商品或内容访问"
      - "外部价格变化时间线"
      - "内部价格变更窗口"
      - "公开前端展示路径"
      - "合作方同步或缓存路径"
    joins:
      - "资产对象与前端访问路径关联"
      - "资产对象与后端请求关联"
      - "请求与设备/IP/账号关联"
      - "外部变化时间与内部访问时间对齐"
      - "业务上下文与访问峰值关联"
  time_window:
    baseline: "外网跟价前的历史正常访问窗口，未知时待补充"
    observation: "外网跟价发生前后窗口，未知时待补充"
    granularity: "分钟"
  expected_outputs:
    metric_outputs:
      - "资产访问量趋势"
      - "页面/接口访问分布"
      - "设备/账号/IP聚集度"
      - "外部变化与内部访问时间差分布"
      - "公开展示/缓存/合作方路径覆盖情况"
    evidence_outputs:
      - "内部资产访问异常证据"
      - "前后端链路一致性证据"
      - "设备/账号/IP聚集证据"
      - "协议或自动化访问线索"
      - "公开路径、缓存、合作方、内部导出、真人访问反证"
    quality_outputs:
      - "前端与后端日志覆盖率"
      - "资产对象匹配完整性"
      - "外部样本时间线完整性"
      - "业务上下文覆盖率"
  interpretation_notes:
    strong_evidence_if:
      - "外部变化前存在高度聚集的内部资产访问，并能对齐目标资产、访问路径和异常主体"
      - "内部访问具备前后端链路缺失、设备/IP/账号团组、接口序列异常等多类证据"
    medium_evidence_if:
      - "外部变化与内部访问时间相关，但存在公开展示、缓存或合作方同步未排除"
      - "资产访问有聚集，但主体和链路证据不完整"
    weak_signal_if:
      - "只有外网跟价相似"
      - "只有价格变化时间接近"
      - "只有访问量上涨"
    counter_evidence_if:
      - "公开前端页面可获得同样信息"
      - "缓存、合作方同步、内部导出或业务发布节奏可解释"
      - "访问来源离散且行为符合真人路径"
      - "内部无对应目标资产访问峰值"
  conclusion_threshold:
    sufficient_for: "证据不足"
    must_combine_with:
      - "外部时间线"
      - "内部资产访问路径"
      - "异常访问主体聚集"
      - "公开/缓存/合作方/内部/真人访问反证排除"
    cannot_conclude_if:
      - "只有外网跟价"
      - "内部无明显接口异常且未排查公开路径"
      - "缓存、合作方、内部导出未排除"
      - "无法对齐具体资产对象和时间窗口"
  quality_checks:
    required:
      - "前端日志是否延迟、丢点或埋点缺失"
      - "后端与前端 join 口径是否一致"
      - "资产对象映射是否准确"
      - "外部样本时间是否可信"
      - "业务活动、版本、缓存、合作方上下文是否完整"
    downgrade_if:
      - "partial / failed / no_permission"
      - "外部时间线缺失"
      - "资产对象无法匹配"
      - "公开路径或合作方路径未排除"
      - "只有访问量或价格相似性"
  freshness_expectation: "准实时"
  permission_boundary: "中高敏"
  manual_review_required: "true"
  safety_boundary:
    false_positive_risks:
      - "把公开信息同步误判为爬虫"
      - "把缓存、合作方或内部导出误判为协议攻击"
      - "把真人比价访问误判为黑产"
    prohibited_actions:
      - "不得仅因外网跟价直接封禁访问主体"
      - "不得在无内部访问异常证据时下反爬强结论"
      - "不得自动处罚、冻结、扣除或上线策略"
  next_query_intent_when_insufficient:
    intent_type: "protocol_frontend_backend_join"
    target_evidence: "若内部出现可疑请求，再补前后端链路一致性、SDK覆盖和接口序列证据"
    reason: "外网跟价本身不是协议或爬虫证据，只有发现内部访问异常后才进入协议链路补证"
```

### 5. 为什么选择这些数据域

反爬资产泄漏必须先证明内部资产访问异常，而不是从外部结果倒推攻击成立。前端行为域和后端数据域支撑资产访问路径；设备信息域和关联网络域支撑主体聚集；风险画像和策略域只做辅助，不做事实定性。

### 6. 为什么选择这些 join path

`asset_access_device_network_join` 是主链路；`frontend_backend_chain_join` 与 `request_device_environment_join` 用于判断是否有协议或端侧异常；`batch_case_business_context_join` 用于排除业务活动、版本、缓存、合作方等上下文；`risk_profile_behavior_outcome_join` 用于避免画像过拟合。

### 7. 是否使用 legal_operation_matrix_authorization_join

不使用。该 case 当前核心是资产访问和外部跟价路径，不是商家/达人/MCN/机构授权运营。若后续发现合作方、授权工具或商家矩阵参与同步，可追加合法矩阵查询。

### 8. 哪些质量风险会导致降级

- 外部样本时间线不可信。
- 内部资产对象无法对齐。
- 公开路径、缓存、合作方同步、内部导出未排除。
- 前后端日志 join 口径不一致。
- 只有价格相似或访问量上涨，没有目标资产访问链路。

### 9. 当前是否足够发给未来 adapter

基本足够。它能约束 adapter 先查资产访问和反证路径，而不是直接查协议或下反爬结论。

### 10. 如果仍不够，缺什么输入

最缺外部跟价样本时间线、内部资产变更窗口、具体资产对象集合、公开展示路径、缓存和合作方同步线索。缺这些输入时只能做监控和补证。

---

## Case 4：ADV-003 真实用户同任务且设备离散

### 1. 用户问题

大量真实用户完成相同任务，设备离散、行为看起来像真人，是否可以排除黑产或直接判群控？

### 2. 应触发 Skill

- 主控：`real_user_crowdsourcing_skill`
- 辅助：`activity_anti_cheating_expert_skill`、`group_control_expert_skill`、`risk_profile_behavior_outcome_join`

### 3. 目标证据

- 真人众包本质证据：行为真实但目标任务化。
- 任务平台、收益链、教程话术、任务完成窗口、奖励/提现聚集。
- 活动后留存、付费、复访等后验质量。
- 设备离散、真实行为、自然传播、活动规则导致相似的反证。
- 与群控、活动低质、正常自然用户的边界。

### 4. query_intent_schema_v2 完整结构

```yaml
query_intent:
  intent_id: "ADV-003_real_user_task_rerun_v2_001"
  intent_type: "activity_black_industry_or_low_quality_check"
  risk_question: "真实用户设备离散但同任务完成，是否属于真人众包、活动低质或正常自然用户"
  target_evidence: "任务化完成、收益链、后验质量、自然传播与群控反证"
  applicable_skill:
    primary: "real_user_crowdsourcing_skill"
    auxiliary:
      - "activity_anti_cheating_expert_skill"
      - "group_control_expert_skill"
      - "risk_profile_behavior_outcome_join"
  minimum_inputs:
    required:
      - "活动或任务场景"
      - "用户样本集合"
      - "任务完成 time_window"
    optional:
      - "任务入口或传播渠道"
      - "奖励/提现线索"
      - "教程话术或外部任务平台线索"
      - "留存/付费/复访观察窗口"
    missing:
      - "任务平台线索"
      - "教程话术线索"
      - "收益链路"
      - "自然用户对照组"
      - "活动后验质量窗口"
  required_data_domains:
    - "活动信息域"
    - "用户信息域"
    - "设备信息域"
    - "前端行为域"
    - "风险画像域"
    - "关联网络域"
  optional_data_domains:
    - "策略引擎域"
  field_types_needed:
    identity_and_account:
      - "user_id"
      - "account_id"
      - "account_age"
      - "register_time"
      - "login_time"
      - "account_status"
    device_and_network:
      - "device_id"
      - "device_profile"
      - "realtime_fingerprint"
      - "async_sdk_signal"
      - "ip"
      - "ua"
      - "app_version"
    session_and_chain:
      - "frontend_event"
      - "event_time"
      - "page_path"
      - "click_sequence"
    activity_and_channel:
      - "campaign_id"
      - "invite_relation"
      - "return_user_flag"
      - "activity_participation"
      - "reward_status"
      - "withdraw_status"
    risk_and_strategy:
      - "risk_label"
      - "risk_score"
      - "strategy_hit"
      - "engine_decision"
      - "disposal_action"
    relation_network:
      - "relation_group_id"
      - "strong_device_relation"
      - "user_group_id"
      - "relation_edge_type"
      - "relation_strength"
  join_paths_needed:
    - "activity_participation_device_reward_join"
    - "invite_relation_network_join"
    - "risk_profile_behavior_outcome_join"
    - "batch_case_business_context_join"
  query_dimensions:
    entities:
      - "活动"
      - "任务"
      - "用户"
      - "设备"
      - "邀请关系"
      - "奖励/提现结果"
      - "自然用户对照组"
    group_by:
      - "任务完成窗口"
      - "活动入口"
      - "任务路径"
      - "奖励/提现状态"
      - "邀请关系"
      - "后验质量"
      - "设备离散度"
      - "用户生命周期"
    compare_with:
      - "正常自然用户"
      - "活动规则预期路径"
      - "真实用户低质群体"
      - "群控统一调度样本"
      - "历史同类活动"
    joins:
      - "活动参与与设备关系"
      - "活动参与与奖励/提现结果"
      - "邀请关系与用户团组"
      - "风险画像与后验行为结果"
      - "业务活动规则与任务路径相似度"
  time_window:
    baseline: "活动前或历史同类活动自然用户窗口，未知时待补充"
    observation: "任务集中完成窗口，未知时待补充"
    granularity: "小时"
  expected_outputs:
    metric_outputs:
      - "任务完成时间集中度"
      - "任务路径相似度"
      - "设备离散度"
      - "邀请关系聚集度"
      - "奖励/提现聚集度"
      - "活动后留存/付费/复访等后验质量"
    evidence_outputs:
      - "真人众包任务化证据"
      - "活动低质证据"
      - "群控统一调度反证或转交证据"
      - "正常自然用户反证"
      - "任务平台/教程话术/收益链补证方向"
    quality_outputs:
      - "活动数据覆盖率"
      - "设备画像更新时间"
      - "后验质量观察窗口完整性"
      - "风险画像来源说明"
      - "自然对照组可用性"
  interpretation_notes:
    strong_evidence_if:
      - "用户行为真实且设备离散，但任务目标、完成窗口、奖励/提现结果和后验低质高度聚集"
      - "存在任务平台、教程话术或收益链线索，并能解释同任务完成"
    medium_evidence_if:
      - "任务窗口和奖励结果聚集明显，但外部任务平台或教程话术证据缺失"
      - "后验质量显著低，但活动目标和自然对照仍需确认"
    weak_signal_if:
      - "只有大量用户完成相同任务"
      - "只有低留存或低付费"
      - "只有设备离散"
    counter_evidence_if:
      - "活动规则本身要求相同任务路径"
      - "自然传播、达人传播或官方运营可解释"
      - "用户后验质量与正常自然用户接近"
      - "无奖励/提现聚集"
      - "无任务平台、教程话术或收益链线索"
  conclusion_threshold:
    sufficient_for: "高度疑似"
    must_combine_with:
      - "任务完成窗口"
      - "任务路径相似"
      - "奖励/提现结果"
      - "后验质量"
      - "自然对照组"
      - "任务平台/教程话术/收益链线索"
    cannot_conclude_if:
      - "只有设备离散"
      - "只有任务相同"
      - "活动规则本身导致路径一致"
      - "缺少收益链和后验质量"
      - "无法排除正常自然用户或活动低质"
  quality_checks:
    required:
      - "活动规则是否导致天然路径一致"
      - "设备画像是否存在更新延迟"
      - "后验质量观察窗口是否足够"
      - "风险画像是否为事实标签还是策略/模型推断"
      - "自然对照组是否可用"
    downgrade_if:
      - "partial / failed / no_permission"
      - "奖励/提现口径缺失"
      - "后验质量窗口不足"
      - "缺少自然对照组"
      - "缺少任务平台、教程话术或收益链线索"
  freshness_expectation: "T+1"
  permission_boundary: "高敏"
  manual_review_required: "true"
  safety_boundary:
    false_positive_risks:
      - "把真实自然用户误判为黑产"
      - "把活动规则导致的路径一致误判为众包"
      - "把真人低质直接定性为黑产"
      - "把设备离散误认为一定正常"
    prohibited_actions:
      - "不得因任务相同直接判群控"
      - "不得因低钱效直接定义黑产"
      - "不得自动处罚、冻结、扣除或上线策略"
  next_query_intent_when_insufficient:
    intent_type: "group_control_dispatch_check"
    target_evidence: "若出现同批启停、统一调度、设备团组或路径高度机械化，再补群控统一调度证据"
    reason: "当前主问题是真人众包/低质/自然用户边界，只有出现调度和设备团组证据时才转交群控"
```

### 5. 为什么选择这些数据域

ADV-003 的关键是“行为真实但目标任务化”，不是设备聚集。活动信息域解释任务和奖励；用户信息域解释生命周期；设备信息域用于排除群控但不能单独定性；前端行为域解释任务路径；风险画像域和关联网络域用于辅助分层和关系聚集。

### 6. 为什么选择这些 join path

`activity_participation_device_reward_join` 是核心，用于把任务、设备、奖励、提现放在一起看。`invite_relation_network_join` 观察邀请和传播结构。`risk_profile_behavior_outcome_join` 把风险画像和后验质量联动，避免只看标签。`batch_case_business_context_join` 排除活动规则、版本、运营节奏导致的相似。

### 7. 是否使用 legal_operation_matrix_authorization_join

默认不使用。该 case 核心是活动任务化与真人众包边界；若后续发现商家、达人、MCN 或机构运营在组织任务，再追加 `legal_operation_matrix_authorization_join`。

### 8. 哪些质量风险会导致降级

- 活动规则本身导致所有用户路径一致。
- 缺少自然用户对照组。
- 奖励/提现口径缺失。
- 后验质量窗口太短。
- 风险画像是模型推断或策略结果，不是事实标签。
- 没有任务平台、教程话术或收益链线索。

### 9. 当前是否足够发给未来 adapter

足够作为首轮 query_intent。它能稳定避免“设备离散即自然用户”和“任务相同即群控”两类误判。

### 10. 如果仍不够，缺什么输入

缺活动规则、任务入口、奖励/提现口径、任务平台或教程线索、自然用户对照组、活动后验质量窗口。缺这些输入时最多下“低质/众包嫌疑”，不能定义黑产。

---

## 汇总

### 1. 修复前后完整率变化

修复前 10 case 回归结论为：`8/10` 基本可发给未来 adapter，`2/10` 勉强可用。勉强项主要来自合法矩阵缺专门 join path，以及导流/授权触达、外网跟价、真人众包的反证表达不够稳定。

本轮 4 个薄弱 case 复跑后：

- 完整率：`4/4` 结构完整。
- adapter 可发程度：`4/4` 可发首轮 query_intent。
- 强结论可下程度：`0/4` 可直接强结论。四个 case 都必须等待 Data Agent 返回后再按阈值解释。

### 2. 4 个 case 是否还有“勉强可用”

没有结构层面的“勉强可用”。

- 合法矩阵：由勉强可用提升为可发，核心原因是新增 `legal_operation_matrix_authorization_join`。
- MIX-001：可发，且能明确把直播间站外添加归到导流截流链路，并保留授权触达反证。
- AC-001：可发，但结论层仍保守，外网跟价必须补外部时间线和内部资产访问路径。
- ADV-003：可发，能把设备离散、真人行为、任务化完成拆开解释。

### 3. query_intent_schema_v2 是否足够稳定

足够稳定进入 adapter 设计。新增标准字段解决了三个关键缺口：

- `freshness_expectation`：让 adapter 知道实时、准实时、T+1、离线画像或长周期后验的预期差异。
- `permission_boundary`：让 adapter 在内部平台阶段承接权限判断，但 Codex 阶段不访问真实数据。
- `next_query_intent_when_insufficient`：让证据不足时有下一步补证路径，而不是停在弱结论。

### 4. data_join_paths_v1 是否还缺 join path

本轮 4 个 case 没有阻塞性缺失。

可选后续增强：

- 若外网跟价、合作方同步、缓存、内部导出场景高频出现，可新增更细的“外部资产同步反证 join path”。当前可由 `asset_access_device_network_join` + `batch_case_business_context_join` 覆盖。
- 若授权运营和导流违规高频交叉，可在 adapter 层支持 `traffic_diversion_chain_check` 自动串联 `legal_operation_matrix_authorization_join`，不一定需要新增 join path。

### 5. 是否可以进入 adapter 设计

可以进入 adapter 设计，但 adapter 第一阶段应只做规划翻译，不做真实处罚或最终定性：

- 输入：`query_intent_schema_v2`
- 输出：Data Agent 可理解的抽象查询计划、数据域路由、字段类型需求、质量检查需求
- 禁止：生成真实 SQL、真实表名、真实字段名、真实 API，或直接触发治理动作

### 6. 是否修改了 Skill 文件

否。本轮未修改任何 Skill 文件，只新增回归输出文件：

- `outputs/reviews/dataagent_query_intent_4_case_rerun_after_schema_fix.md`
