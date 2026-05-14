# Protocol Attack Evidence Minimum Pilot v1

试点名称：`protocol_attack_evidence_minimum_pilot_v1`

## 0. 边界说明

本文件只设计未来内部平台最小试点方案。

当前阶段：

- 不调用真实 Data Agent。
- 不定义真实 API、认证、接口路径或请求参数。
- 不编造真实表名、字段名、SQL、看板、数据集或画像标签。
- 不修改现有 Skill。
- 试点只做协议攻击补证和研判闭环，不做自动处置。

## 1. 试点目标

验证 Dennis Agent 生成的 `query_intent_schema_v2`，未来如何通过 adapter 调用真实 Data Agent，完成协议攻击补证闭环。

核心目标：

- 验证“前端无日志 / 后端有请求”时，是否支持协议攻击判断。
- 验证能否稳定生成 `query_intent_schema_v2`。
- 验证 adapter 能否转换为 `dataagent_request`。
- 验证 Data Agent 返回后能否归一化为 `normalized_evidence`。
- 验证 Dennis Agent 能否基于证据强弱、反证和缺口输出结论等级。

必须排除：

- 破解包绕 SDK。
- 官方包埋点缺失。
- 前后端 join 口径问题。
- 合法自动化工具。
- 授权工具或合法矩阵调用。

## 2. 适用问题

本试点适用于以下问题：

- 是否协议攻击。
- 是否前后端链路不一致。
- 是否 SDK 缺失 / 绕采集。
- 是否 token / device / ip / ua 冲突。
- 是否接口序列固化。
- 是否存在 NG 网关或风控引擎识别到的异常请求链路。

不适用：

- 只有高频访问但没有链路、SDK、token、设备、接口序列证据。
- 明确由官方工具或授权工具产生的接口化调用。
- 只需要业务指标看板归因、活动效果复盘或渠道归因分析的场景。

## 3. 输入信息

### 3.1 必填输入

- `user_id` 或 `device_id`。
- `api_name` 或业务动作。
- `time_window`。

### 3.2 可选输入

- `app_version`。
- `channel`。
- `token_id`。
- `risk_event_id`。
- SDK 状态语义。
- 客户端版本或渠道语义。
- 网关或风控事件语义。

### 3.3 输入缺失处理

若缺少必填输入：

- 不生成真实查询。
- 输出缺失输入清单。
- 结论等级固定为 `证据不足`。
- 生成下一步补输入动作。

若缺少可选输入：

- 可生成第一轮 `query_intent`。
- 在 `minimum_inputs.missing` 中显式记录。
- 不得因缺少可选输入自行假设。

## 4. 取证流程

### Step 1：生成 query_intent_schema_v2

Dennis Agent 根据用户问题生成：

```yaml
query_intent:
  intent_type: "protocol_frontend_backend_join"
  target_evidence: "前后端链路一致性、SDK覆盖、token/device/ip/ua一致性、接口序列、网关/风控记录"
  applicable_skill:
    primary: "protocol_attack_expert_skill"
    auxiliary:
      - "cracked_app_expert_skill"
      - "account_security_expert_skill"
      - "group_control_expert_skill"
```

要求：

- 必须包含 `required_data_domains`。
- 必须包含 `field_types_needed`。
- 必须包含 `join_paths_needed`。
- 必须包含 `quality_checks`。
- 必须包含 `next_query_intent_when_insufficient`。
- 不得写真实表名、字段名、SQL 或 API。

### Step 2：adapter 转 dataagent_request

adapter 将 `query_intent_schema_v2` 转换为抽象 `dataagent_request`：

```yaml
dataagent_request:
  task_type: "data_query"
  source_query_intent_id: "<query_intent.intent_id>"
  natural_language_question: "<面向 Data Agent 的证据问题>"
  target_evidence: "<协议攻击补证目标>"
  data_domains:
    required: []
    optional: []
  field_types_needed: {}
  join_paths_needed: []
  quality_checks: {}
  safety_boundary: {}
```

要求：

- `natural_language_question` 必须说明“返回证据，不做最终风控定性”。
- `safety_boundary` 必须携带“不得自动处罚、冻结、扣除、策略上线”。
- `quality_checks` 必须原样传递。

### Step 3：dataagent 返回 response

未来 Data Agent 返回抽象响应。

可能状态：

- `success`
- `partial`
- `failed`
- `no_permission`
- `timeout`
- `empty_result`
- `ambiguous_result`
- `data_quality_risk`
- `permission_limited`

可能返回类型：

- `dataset_analysis`
- `dashboard_analysis`
- `table_summary`
- `sql`
- `partial`
- `error`
- `no_permission`

说明：

- 返回 SQL 不等于已经查到结果。
- 返回看板或数据集趋势不等于协议攻击事实。
- `empty_result` 不等于无风险。
- `no_permission` 不等于无风险。

### Step 4：adapter 转 normalized_evidence

adapter 将 `dataagent_response` 标准化为：

```yaml
normalized_evidence:
  evidence_type: "协议攻击补证"
  strong_evidence: []
  medium_evidence: []
  weak_evidence: []
  counter_evidence: []
  missing_evidence: []
  quality_risks: []
  conclusion_support:
    level: "<明确判断 | 高度疑似 | 证据不足 | 反向排除/暂不支持>"
```

要求：

- 只表达证据支持程度。
- 不替代 Dennis Agent 最终判断。
- 若 `partial / no_permission / empty_result / ambiguous_result`，必须降级。
- 若缺少关键反证排除项，不得输出 `明确判断`。

### Step 5：Dennis Agent 做证据解释

Dennis Agent 基于 `normalized_evidence` 输出：

- 强证据。
- 中证据。
- 弱证据。
- 反证。
- 缺口。
- 当前最多支持的结论等级。
- 下一步补证。
- 治理建议。
- 是否需要人工确认。

### Step 6：输出结论等级和下一步补证

输出四档结论：

- 明确协议。
- 高度疑似协议。
- 证据不足。
- 反向排除 / 转其他 Skill。

若证据不足，必须输出下一步 `query_intent`：

- 破解包 / SDK 绕采集补证。
- 官方包埋点缺失补证。
- token 泄露 / 登录态复用补证。
- 群控真机补证。
- 合法自动化 / 授权工具补证。

## 5. 第一轮主证据包

第一轮围绕协议攻击主证据闭环。

### 5.1 前后端链路一致性

目标：

- 判断后端请求是否有合理前端事件链路支撑。
- 判断是否存在前端无日志但后端有请求。
- 判断前端缺失是否可能由日志延迟、丢点或埋点缺失造成。

抽象 join path：

- `frontend_backend_chain_join`

### 5.2 SDK 日志覆盖

目标：

- 判断端侧 SDK 信号是否存在。
- 判断 SDK 信号是否延迟、缺失或异常。
- 判断是否可能为破解包绕 SDK 或采集异常。

抽象 join path：

- `request_device_environment_join`

### 5.3 token / device / ip / ua 一致性

目标：

- 判断请求环境与登录态、设备、网络、UA 是否一致。
- 判断是否存在 token 复用、登录态迁移异常或设备环境冲突。

抽象 join path：

- `token_session_environment_join`
- `request_device_environment_join`

### 5.4 接口序列

目标：

- 判断接口调用顺序是否固化。
- 判断是否绕过正常页面路径或业务前置动作。
- 判断是否存在模板化接口调用。

抽象 join path：

- `frontend_backend_chain_join`

### 5.5 NG 网关 / 风控引擎记录

目标：

- 判断网关或风控引擎是否有拦截、挑战、放行、限权等记录。
- 判断策略命中是否只是风险线索，还是能与请求链路、设备环境形成闭环。

抽象 join path：

- `strategy_decision_outcome_join`

## 6. 第二轮反证 / 缺口补证

第一轮证据不足或存在反证时，进入第二轮补证。

### 6.1 破解包 / SDK 绕采集

触发条件：

- 前端无日志。
- SDK 缺失或异常。
- 但仍存在端侧行为或版本/渠道异常线索。

下一步 intent：

- `sdk_bypass_or_cracked_app_check`

### 6.2 官方包埋点缺失

触发条件：

- 官方版本或正常版本也出现同类前端日志缺失。
- 前端日志缺失集中在某版本、渠道或埋点口径。

下一步 intent：

- `protocol_frontend_backend_join`

目标：

- 补官方版本对照和埋点覆盖口径。

### 6.3 join 口径问题

触发条件：

- 前后端时间窗口、session、用户、设备或事件口径不一致。
- 后端请求无法与前端事件稳定关联。

下一步 intent：

- `permission_or_lineage_check`

目标：

- 检查数据口径、血缘、延迟和 join 可行性。

### 6.4 合法自动化 / 授权工具

触发条件：

- 存在商家、达人、MCN、机构、客服、官方工具或授权工具可能。
- 接口化调用具有业务合理性。

下一步 intent：

- `legal_operation_matrix_check`

抽象 join path：

- `legal_operation_matrix_authorization_join`

### 6.5 群控真机可能性

触发条件：

- 有端侧行为。
- 设备是真机。
- 行为路径相似、同批启动停止或设备团组明显。

下一步 intent：

- `group_control_dispatch_check`

## 7. 结论等级

### 7.1 明确协议

满足：

- 无正常端链路。
- 后端请求直达或接口序列固化。
- SDK / token / device / ip / ua 异常形成闭环。
- 网关或风控引擎记录可解释风险链路。
- 已排除破解包、官方包埋点缺失、join 口径问题、合法自动化工具。

### 7.2 高度疑似协议

满足：

- 前后端链路冲突明显。
- 接口序列或请求环境异常明显。
- 但包证据、token 证据、合法工具反证或 join 口径仍有一项未闭合。

适合：

- 灰度监控。
- 加采。
- 人工复核。
- 小流量挑战或验证。

### 7.3 证据不足

满足任一：

- 只有前端无日志。
- 只有高频请求。
- 只有后端请求量上涨。
- `partial / no_permission / empty_result / failed / timeout`。
- 官方包、埋点、合法工具、破解包、join 口径反证未排除。

### 7.4 反向排除 / 转其他 Skill

转交条件：

- 官方包埋点缺失成立：转数据质量 / 埋点修复。
- 破解包绕采集更合理：转 `cracked_app_expert_skill`。
- 合法自动化成立：转 `legal_operation_matrix_playbook_v2_3`。
- 设备真机统一调度更明显：转 `group_control_expert_skill`。
- token 泄露更明显：转 `account_security_expert_skill`。

## 8. 成功标准

试点成功必须同时满足：

- 能生成完整 `query_intent_schema_v2`。
- 能生成完整 `dataagent_request`。
- 能产出 `normalized_evidence`。
- `partial / no_permission / empty_result` 能正确降级。
- 不因前端无日志直接判协议。
- 能显式列出破解包、官方包埋点、join 口径、合法自动化反证。
- 不编造真实表名、字段名、SQL、API。
- 不触发自动处罚、冻结、扣除或策略上线。

## 9. 人工确认边界

必须人工确认：

- 策略上线。
- 策略扩量。
- 处罚。
- 冻结。
- 扣除。
- 封禁。
- 大规模限权。
- 影响商家、达人、MCN、机构或授权工具的治理动作。

试点只做：

- 补证。
- 证据解释。
- 结论等级判断。
- 下一步补证建议。
- 治理建议草案。

试点不做：

- 自动处置。
- 自动处罚。
- 自动扣除。
- 自动策略上线。

## 10. 审计与回放

未来内部平台必须记录：

- 用户问题。
- Skill 路由。
- `query_intent`。
- `dataagent_request`。
- `dataagent_response` 摘要。
- `normalized_evidence`。
- Dennis 结论。
- 人工最终判断。
- 是否回写 schema / join path / Skill。
- 权限和质量风险。
- 是否触发人工确认。

### 10.1 回放触发

以下情况应支持回放：

- 权限补齐。
- 数据质量问题修复。
- 前后端 join 口径修复。
- SDK 采集延迟修复。
- 新增破解包补证能力。
- 新增合法自动化授权数据。
- schema / join path / threshold 升级。

### 10.2 回写判断

需要回写：

- 协议判断过度自信：回写 `dataagent_conclusion_thresholds_v1.md` 或协议 Skill。
- query_intent 字段不足：回写 `query_intent_schema_v2.md`。
- join path 无法表达证据链：回写 `data_join_paths_v1.md`。
- 多个 case 重复出现同类边界：回写相关 Skill 或 playbook。

## 11. 试点风险

### 11.1 数据权限不足

风险：

- token、设备、网关、风控引擎等证据可能权限敏感。

降级：

- `no_permission` 或 `permission_limited` 不得解释为无风险。
- 保留 replay，权限补齐后重跑。

### 11.2 前后端 join 口径不一致

风险：

- session、时间窗口、用户、设备、事件口径不一致会制造假冲突。

降级：

- 进入 join 口径补证。
- 不得直接判协议。

### 11.3 SDK 采集延迟

风险：

- 异步 SDK 信号可能晚于后端请求。

降级：

- 标记 freshness risk。
- 等待或补异步窗口后重放。

### 11.4 官方版本埋点缺失

风险：

- 官方包缺日志会制造“像协议”的证据。

降级：

- 补官方版本对照。
- 转数据质量或埋点修复。

### 11.5 破解包绕采集

风险：

- 破解包不是协议，但会造成前端日志缺失和 SDK 缺失。

降级：

- 转 `cracked_app_expert_skill` 和 `sdk_bypass_or_cracked_app_check`。

### 11.6 合法自动化误判

风险：

- 商家、达人、MCN、机构、客服、授权工具可能产生接口化调用。

降级：

- 先走 `legal_operation_matrix_check`。
- 不得一刀切当协议攻击。

## 12. 后续扩展

### 12.1 群控补证试点

目标：

- 设备团组、同批启停、行为路径相似、收益聚集、合法矩阵反证。

候选试点名：

- `group_control_dispatch_evidence_minimum_pilot_v1`

### 12.2 token 泄露试点

目标：

- token / session / device / ip / ua 一致性、登录迁移、验证链路、敏感动作。

候选试点名：

- `token_reuse_account_takeover_evidence_minimum_pilot_v1`

### 12.3 渠道抢量试点

目标：

- 曝光、点击、激活、CTIT、自然量跷跷板、新客真实性、后验质量。

候选试点名：

- `channel_attribution_hijacking_evidence_minimum_pilot_v1`

### 12.4 导流截流试点

目标：

- 信息暴露入口、目标获取、搜索/关注/私信触达、站外承接、账号矩阵。

候选试点名：

- `traffic_diversion_chain_evidence_minimum_pilot_v1`
