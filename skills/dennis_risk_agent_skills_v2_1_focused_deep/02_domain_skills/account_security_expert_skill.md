# Account Security Expert Skill：账号安全专项专家 Skill v2.3 executable-deep

## 0. Skill 定位

本 Skill 解决账号生命周期风险，包括盗号、撞库/ATO、token 泄露、小号、交易号、租借实名、二次放号、验证体系、可信体系和弱端负债治理。账号安全不是登录拦截，而是在安全、体验和治理之间做分层决策。

不解决：纯反爬资产保护、纯活动套利、单纯流量刷量的主控问题；这些场景需组合对应领域 Skill。

## 1. 触发条件

- 关键词触发：账号安全、盗号、ATO、撞库、token 泄露、登录态、踢 token、小号、交易号、二次放号、租借实名、验证体系、可信体系、验无可验、弱端未接。
- 业务场景触发：登录异常、敏感动作、换绑、私信导流、支付/提现、注册小号、账号交易、找回、验证打扰、token 跨环境、商家/达人/机构批量登录、客服工具或 ISV 接口化运营。
- 用户意图触发：用户问“是不是被盗”“怎么判断 token 泄露”“登录风控怎么平衡体验”“小号怎么全链路治理”“验证体系怎么建”。
- 反向不触发：只讨论资产爬取、活动钱效、刷量口径且不涉及账号生命周期时，不作为主控。
- 需要转交给其他 Skill 的情况：
  - 凭证批量测试：credential_stuffing_ato_skill 辅助。
  - token 复用接口化：protocol_attack_expert_skill 辅助。
  - 统一调度登录/养号：group_control_expert_skill 辅助。
  - 商家/达人/MCN/机构批量登录、多账号代管或接口化运营：先引用 `06_templates/legal_operation_matrix_playbook_v2_3.md` 判断授权主体、账号范围、操作人、工具来源、敏感动作、收益主体，再组合 risk_governance_design_skill 或 protocol_attack_expert_skill。
  - 年度述职：material_delivery_skill 辅助。

## 2. 输入格式

- 必需输入：账号场景、异常动作、登录/token/设备/验证/下游行为中的至少两类证据、处置目标。
- 可选输入：账号价值、历史可信设备、登录失败/成功序列、token 签发/刷新日志、找回/客诉、验证通过率、黑市报价、弱端入口。
- 缺失时可默认假设：用户只问概念时，默认按账号生命周期给本质、证据和补证动作。
- 缺失但不可假设时如何处理：缺少账号、登录/token、设备或下游行为证据时，不强定性盗号或 token 泄露。
- 用户只给模糊问题时的最小可用输入：账号风险类型、发生环节、是否有环境变化、是否有敏感动作、是否有客诉或找回。

## 3. 专家认知

- 这类风险的本质：账号安全不是登录拦截，而是围绕账号生命周期，在安全、体验和治理之间分层决策；高价值重安全，低价值重体验，不确定时兜底验证和柔性处置。
- 黑产 / 风险动机：接管账号资产、复用账号身份、交易账号、用小号参与活动/刷量/导流/爬取、规避实名和验证成本。
- 主要风险形态：盗号、小号、租借实名、二次放号、交易号、仿冒号、token 泄露、验证体系缺口。
- 常见混合形态：撞库+ATO、钓鱼/欺诈验证、token 泄露+协议复用、群控登录、扫码/验证链路滥用、小号交易后下游作恶。
- 和相近风险的区别：
  - 登录异常不等于盗号，要看本人意愿、环境、下游行为和找回/客诉。
  - 低质账号不等于黑产，要看资源组织、交易、收益和下游作恶。
  - token 跨环境不等于正常换机，要看是否重新建立信任关系。

### 四纵一横

四纵：漏洞机制加固、登录降发生、链路防扩散、踢出降影响。  
一横：损益可量化。

材料化表达：降负债、降发生、降影响、损益量化。历史负债包括漏洞、不支持验证、token 永久有效、无法踢出登录态、未接风控、弱端入口、核心指纹缺失。

## 4. 判断规则

按顺序判断，命中即进入对应分支；证据不足时不得强结论。

1. 如果登录失败/成功序列、同 IP/代理多账号尝试、成功后行为突变同时成立，则判断为撞库/ATO 方向，组合 credential_stuffing_ato_skill。
2. 如果无重新登录但 token 在新设备/IP/UA/SDK/环境调用账号态接口，且伴随敏感动作或批量模板，则判断为 token 泄露/复用方向。
3. 如果号主本人扫码/人脸/验证码通过，但站外诱导、意图被操控、下游接管成立，则判断为欺诈盗号。
4. 如果账号从注册、登录、活跃、回扫、任务、交易到下游作恶形成链路，则判断为黑产小号/交易号治理问题。
5. 如果二次放号涉及新旧号主权益冲突，则进入合规解绑、风险隔离、体验保护分支。
6. 如果风险识别明确但验证手段不足，则进入验证体系建设分支，不强拦。
7. 如果只有 IP 变化、设备变化、城市变化、单次登录异常，则不得定性盗号或 token 泄露，只能补证或 step-up。
8. 如果存在商家、达人、MCN、机构、ISV、客服工具等批量登录、多账号代管或接口化运营，先引用 `06_templates/legal_operation_matrix_playbook_v2_3.md` 进入合法自动化/授权矩阵审计分支，校验授权主体、账号范围、操作人、工具来源、调用范围、敏感动作、收益主体、审计和配额；不得因为多账号登录或接口化登录直接定性盗号、群控或协议。
9. 如果存在正常换机、多端登录、漫游、企业 MDM、可信旧设备确认、SDK 口径变化等反证，则降级判断。

### 4.2 批量 ATO 攻击类型细分：撞库 vs 一键登录 / 鸿蒙授权接管

批量 ATO 分析禁止只看 totalCount、kick_out 次数、password fail / CAPTCHA 次数后直接跳到“撞库 ATO”。

#### 鸿蒙一键登录 ATO pattern

触发信号：

- 出现 `HARMONY_` 设备 ID 或鸿蒙设备前缀。
- token issued / token 下发成功。
- 多账号登录成功。
- 同一 IP 集中登录多个用户。
- token revoke / kick out。
- 后续小米 / Android 设备改密或密码验证失败。
- 用户原设备与新 HARMONY 设备明显不一致。

判断：

- 优先识别为“一键登录 / 三方授权接管 / 鸿蒙一键登录 ATO”候选。
- 不应直接归为撞库。
- 大量 password fail / CAPTCHA 可能来自改密环节，而不一定是撞库尝试。

#### 批量 ATO 逐条时序抽样规则

当批量 ATO case 中出现以下任一情况，必须抽取 3-5 个代表用户做 timeline：

- kick_out 密集。
- password fail / CAPTCHA 密集。
- 多设备切换。
- 同 IP 集中。
- 三方登录 / 一键登录 / OAuth / HARMONY 相关字段。

timeline 必须包含：

- 正常登录设备。
- 异常登录设备。
- 登录方式。
- token issued。
- token revoke / kick out。
- password verify / change password。
- IP。
- device model / did prefix。
- event order。

#### 区分表

| 类型 | 主线 | 关键证据 | 易误判点 |
|---|---|---|---|
| 撞库 ATO | 密码尝试、失败爆发、CAPTCHA、少量成功登录 | 同 IP/代理多账号密码试探，失败后成功登录，成功后敏感动作 | 不能只凭 kick_out 或改密失败定性 |
| 一键登录 / 鸿蒙 ATO | 三方授权 / oneKey / OAuth / HARMONY token issued、设备切换、改密、token revoke | HARMONY_ 设备、token 下发成功、同源 IP 多账号登录、后续小米/Android 改密或密码验证失败 | 改密环节的 password fail / CAPTCHA 容易被误读成撞库 |

标准结论口径：

- “当前批量统计能说明存在账号安全异常，但不能直接定性撞库。”
- “由于出现 HARMONY_ 设备、同源 IP token 下发、token revoke / kick out、后续小米 / Android 改密尝试，应优先验证一键登录 / 三方授权接管 / 鸿蒙一键登录 ATO 链路。”

### 4.3 协议上号字段语义纠偏：mod / mods 不等于 HTTP method

账号安全场景中遇到客户端版本降级、疑似协议上号、设备字段异常时，必须先区分字段语义。

- `mod` / `mods` / `model` / `device_model` 应按设备型号或设备上报字段理解。
- `POST` 出现在 `mod` / `mods` 字段里，只能说明设备型号字段异常、占位符异常或伪造值异常。
- 不得将 `mod='POST'` 或 `mods=['POST', ...]` 解释为 `HTTP method=POST`。
- 只有字段明确为 `method` / `request_method` / `http_method` / `requestMethod` 时，才能作为请求方法证据。
- `POST` 不能单独作为协议上号或接口直调证据。

协议上号判断必须依赖组合证据：

- 异常 `mod` / 非真实机型 / 加密样式字符串。
- 多版本混用。
- 旧版本高频。
- `did` 不一致。
- 正常设备与降级设备差异。
- 前端行为缺失或请求链路异常。

标准表达：

- “当前 `POST` 出现在设备型号字段中，不能推出攻击者使用 HTTP POST 直调后端。”
- “它更像设备上报字段异常或伪造值异常，需要结合版本降级、did 不一致、前端行为缺失和请求链路异常再判断。”

### 4.1 统一登录日志在线窗口限制

ATO / 盗号研判必须先判断 `suspicious_event_time` 与 `query_time` 的时间差。

- 统一登录日志在线 API 按约 7 天可靠窗口处理。
- 超过在线窗口的历史登录记录可能缺失。
- 在线 API 返回 `no_data`、少量 token 刷新、无 LOGIN 事件，不代表该时间点没有登录行为。
- 当异常发布、换绑、改密、色情视频发布等关键动作发生在在线日志窗口外时，必须标记：
  - `login_log_window_incomplete`
  - `offline_hive_required`
  - `online_login_log_may_be_false_negative`
- 不允许把“异常当天零登录记录”作为强反证。
- 不允许把“无异设备登录”作为强反证，除非登录日志窗口完整覆盖异常时间。
- 不允许把“用户设备页只显示本人设备”直接当成强反证，除非数据窗口完整且覆盖异常动作时间。

结论等级约束：

- 缺少离线 Hive 登录日志、发布审计日志、token 使用链路时，ATO 结论最多为 `partial_support` 或 `insufficient_support`。
- 不能用在线 API `no_data` 反向证明 `data_does_not_support_ato`。
- 不能把在线窗口外的无登录记录写成“排除 ATO”。

历史动作补证优先级：

1. 离线 Hive 登录日志。
2. 发布审计日志。
3. token 使用 / token 刷新 / passToken 相关链路。
4. 封禁 / 审核工单。

标准表达：

- “当前在线统一登录日志未观察到异常时间点的登录记录，但该异常时间已超过在线日志可靠窗口，因此该结果不能作为无异设备登录的强反证。”
- “该窗口需要离线 Hive 登录日志或发布审计日志补证。”
- “现有证据不足以闭合 ATO 链路，也不足以反向排除 ATO。”

### 4.4 账号安全 Hive 数据源选表规则

当在线登录日志窗口不足、历史 ATO 需要补证、批量 case 需要离线聚合，必须从“补充登录日志”升级为明确 Hive query plan。不要把在线日志窗口不足误写成“无登录异常”。

核心表：

| 目标 | 推荐 Hive 表 | 关键分区 / 过滤 | 边界 |
|---|---|---|---|
| 成功登录链路 / 异设备成功登录 | `ks_rc_bs.ks_account_login_basic_info` | `p_date` + `user_id` | 只包含登录成功，不适合分析登录失败 / 撞库失败。 |
| 登录失败 / 撞库 / 暴力破解 | `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info` | `p_date` + `p_action_type='login'` + `user_id` | 表名是 `orign`，不能改成 `origin`；`finalloginresult=1` 才是成功，其他为失败，null 为未走完流程 / 不确定。 |
| 改密相关事件 | `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info` | `p_date` + `p_action_type='resetPwd'` + `user_id` | resetPwd no_data 只能作为改密链路缺口，不排除其他 ATO 链路。 |
| Web/H5 风控拦截 | `ks_rc_arch.antispam_feature_map_default_partitioned` | `p_date + p_hourmin + p_action_type` | 生命周期 30 天；超窗 no_data 是 source_gap。 |
| App 风控拦截 | `ks_raw_log_v2.antispam_feature_map_partitioned` | `p_date + p_hourmin + p_action_type` | 生命周期 50 天；表极大，必须强制分区，禁止全表扫。 |

runtime 回答要求：

- 在线 no_data / 超窗 no_data 不得作为“无登录异常”或“无 ATO 风险”反证。
- 如果缺在线数据，应输出明确 Hive query plan，包括 `selected_table`、`reason_for_table_selection`、`partition_filters`、`entity_filters`、`key_fields`、`expected_signal`、`risk_if_missing`、`fallback_table`、`no_data_interpretation`。
- DataAgent 只作为 Hive / 数仓取数分析能力，不得泛化成万能风控执行器。

## 5. 证据体系

- 强证据：
  - 登录环境突变 + 下游敏感行为突变；
  - token 与设备/IP/UA/SDK/环境冲突；
  - 无登录但账号态敏感接口调用；
  - 账号换绑、支付/提现、私信导流、资产转移；
  - 找回/客诉确认；
  - 账号交易、实名租借、黑市报价和下游作恶闭环。
- 中证据：
  - 登录失败/成功同步上升；
  - 同 IP/代理多账号尝试；
  - 账号价值高；
  - 设备关系异常；
  - 验证链路命中；
  - 小号活跃/回扫异常。
- 弱证据：
  - IP 变化；
  - 城市变化；
  - 设备型号变化；
  - 单次登录失败；
  - 账号低质。
- 反证：
  - 用户正常换机、多端登录、漫游；
  - 可信旧设备确认；
  - 企业/机构账号；
  - 商家/达人/ISV/客服工具等授权批量运营；
  - SDK 升级或埋点口径变化；
  - 用户本人正常操作；
  - 合规二次放号。
- 反证使用限制：
  - “无异设备登录”只有在登录日志窗口完整覆盖异常时间时，才能作为反证。
  - 在线统一登录日志超过约 7 天可靠窗口后的 `no_data` / 无 LOGIN 事件，只能作为数据缺口，不能作为反证。
  - “只有本人设备在线可见”必须确认覆盖异常时间和相关登录链路，否则不能用于排除 ATO。
- 误判来源：网络出口变化、家庭/公司 NAT、端采集缺失、登录日志延迟、客服/运营代操作。
- 最小补证清单：
  - 登录失败/成功序列；
  - token 签发/刷新/踢出链路；
  - 设备/IP/UA/SDK/地理一致性；
  - 账号价值和历史可信环境；
  - 登录后敏感动作；
  - 验证链路和通过率；
  - 客诉、找回、黑市报价、下游扩散。
  - 在线日志超窗场景：离线 Hive 登录日志、发布审计日志、token 使用 / passToken 链路、封禁 / 审核工单。
  - 合法自动化 / 合法矩阵：按 `06_templates/legal_operation_matrix_playbook_v2_3.md` 补授权主体、账号范围、工具来源、操作人、操作目的、调用接口、敏感动作、收益主体、业务登记信息、历史违规记录。

### 5.1 单例 Case Evidence Source Metadata

单例 ATO / 账号安全研判输出一张 evidence card 时，每条 strong / medium / weak / counter evidence 都必须带来源追踪字段，口径与 ATO batch evidence source schema 保持一致。

每条证据必须包含：

```yaml
evidence_source:
  source_name:
  source_type:
  source_tool_or_hand:
  source_platform:
  collected_at:
  evidence_time_range:
  raw_reference:
source_quality:
  freshness_status:
  freshness_risk:
  permission_status:
  reliability_level:
```

`source_type` 枚举：

- `internal_platform_api`
- `browser_dom_read`
- `screenshot_manual_read`
- `dataagent_hive`
- `manual_input`
- `model_inference`
- `historical_doc`

边界：

- `model_inference` 不能当作 raw evidence，只能作为 hypothesis / interpretation。
- `manual_input` 不能单独支撑 strong conclusion，只能作为 clue 或弱证据。
- `user_claim` 只能作为用户主张 / weak signal。用户声称“被盗”“非本人发布”不能直接证明 ATO。
- `behavior_event` 只能证明行为发生。违规内容发布只能证明违规内容或异常动作发生，不能证明账号被盗。
- 未实际查到的钓鱼页访问、OAuth 授权、前端行为、token 链路、发布审计等，必须写入 `missing_evidence`，不得写成“已确认”。
- 单案 evidence card 中每条证据必须标注 `evidence_type` 和 `strength`。
- 登录日志超窗 `no_data` 不能当作 counter evidence，必须标记 freshness / window risk。
- blocked / partial source 必须显式标记 `permission_status`，并降低结论置信度。
- 设备关联只能作为候选关联风险，不能直接定性作弊或盗号。
- `raw_reference` 只能是内部安全引用，不得包含 cookie / token / session / header / 手机号 / IP 明文等敏感内容。

`evidence_type` 推荐枚举：

- `raw_evidence`: 平台日志、审计、策略命中、设备画像、前端观察等可追溯事实。
- `behavior_event`: 发布、改密、换绑、私信、关注、支付等业务动作事实。
- `user_claim`: 用户反馈、客服记录、人工备注。
- `inference`: 基于多条证据的解释。
- `hypothesis`: 待验证假设。
- `missing_evidence`: 应查但未查到 / blocked / timeout / 超窗。

单案明确查询或 `single_entity_execution_mode` 必须输出 evidence card。字段至少包含：

- `conclusion`
- `confidence`
- `strong_evidence`
- `medium_evidence`
- `weak_evidence`
- `counter_evidence`
- `missing_evidence`
- `completed_sources`
- `blocked_or_timeout_sources`
- `source_quality`
- `next_action`

平台 blocked / timeout / loop 时也必须输出 partial evidence card，不能裸 timeout。

## 6. 输出格式

### 6.1 短答版

```text
一句话判断：
本质标识：
- 正常用户：
- 黑灰产：
- 最小区分点：
关键识别标识：
最小补证动作：
治理抓手：
```

### 6.2 深度分析版

```text
一句话判断：
领域归类：账号安全
风险类型：盗号 / ATO / token 泄露 / 小号 / 交易号 / 验证体系 / 二次放号
关键证据：
反证 / 误判：
补证动作：
治理方案：
灰度策略：
评估指标：
可沉淀资产：
```

### 6.3 材料交付版

```text
核心本质：
业务情况：
核心思考：
策略打法：
核心进展 + 一句话总结：
做得好的：
可提升的：
下一步方向：
指标附录：
```

字段级输出必须包含：一句话判断、领域归类、风险类型、关键证据、反证 / 误判、补证动作、治理方案、灰度策略、评估指标、可沉淀资产。

## 7. 治理闭环

- 查数补证：登录、token、设备、验证、下游敏感动作、客诉/找回、黑市报价 join。
- 识别策略：异常登录、token 环境一致性、小号生命周期、交易号、欺诈验证、被攻击账号库。
- 合法自动化治理：按 `06_templates/legal_operation_matrix_playbook_v2_3.md` 做授权登记、调用范围绑定、操作审计、配额控制、敏感动作 step-up、局部违规限权、非授权接口收紧。
- 分层处置：
  - 高准：风险 token 踢出、账号保护、敏感动作冻结、快速找回。
  - 中准：Step-up、可信设备确认、限权、延迟敏感动作。
  - 低准：加采、提醒、观察、低风险验证。
- 灰度策略：先高价值账号、高风险 token、敏感动作；低风险普通浏览不强打扰。
- 业务协同：弱端接风控、支持验证、token 机制改造、用户教育、客服找回流程。
- 体验 / 误伤控制：高价值重安全，非高价值重体验；兜底验证替代一刀切封禁。
- 指标评估：盗号客诉、高准盗号量、登录打扰率、验证量、验证覆盖率、风险 token 踢出、小号发生/漏过、黑市账号报价、注册合规率、找回成功率。
- 样本回流和复盘：盗号风险标签库、被攻击账号库、风险 token 标签、交易号标签、小号全链路样本。

## 8. 禁止行为

- 禁止把账号安全等同登录拦截。
- 禁止只看 IP/设备变化就定性盗号或 token 泄露。
- 禁止忽略安全和体验平衡。
- 禁止验无可验时只强拦。
- 禁止把低质账号直接等同黑产。
- 禁止把商家/达人/机构批量运营直接等同黑产接口滥用。
- 禁止证据不足强结论。
- 禁止忽略快速找回、柔性踢出、Step-up 和用户教育。

## 9. 质量校验

输出前自查：

- 是否识别账号安全子领域？
- 是否保留四纵一横？
- 是否区分安全和体验？
- 是否列出强 / 中 / 弱证据和反证？
- 是否给出 token、验证、小号、弱端或下游扩散补证动作？
- 是否对商家/达人/机构批量运营先进入授权矩阵审计，而不是直接拦截？
- 是否给出柔性踢出、快速找回、Step-up、验证覆盖率、登录打扰率等治理和指标？
- 是否能沉淀标签库、策略、材料或测试集？

不合格时必须补齐后再输出。

## 10. 失败处理

- 信息不足：降级为账号风险假设，列登录/token/设备/下游补证清单。
- 证据冲突：输出盗号、正常换机、合法多端、SDK 口径变化等多分支。
- 超出 Skill 边界：切换或组合 credential_stuffing、protocol、group_control、activity、anti_crawler Skill。
- 工具 / API 不可用：说明缺少哪类日志，给端侧、服务端、客诉、找回、黑市报价替代路径。
- 无法判断：明确说“当前不足以判断账号被盗或 token 泄露”，说明缺少登录链路、token 链路还是下游行为证据。
