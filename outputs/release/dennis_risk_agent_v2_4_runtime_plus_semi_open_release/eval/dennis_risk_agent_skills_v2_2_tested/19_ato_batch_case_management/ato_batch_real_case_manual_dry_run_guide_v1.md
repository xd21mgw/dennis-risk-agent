# ATO Batch Real Case Manual Dry-run Guide v1

## 1. 定位

本指南用于把 5-10 条真实但已脱敏的 ATO / 盗号申诉 case 手工填入 batch registry，并人工完成 evidence card、pattern summary 和 strategy direction draft。

本轮只做人工 dry-run：

- 不调用真实 DataAgent。
- 不访问真实内部平台。
- 不接内部 Agent。
- 不执行 SQL / API / browser 查询。
- 不修改 release / dist。
- 不自动上线策略。
- 不执行处置动作。

目标不是确认某个用户是否被盗号，而是验证当前 ATO batch case analysis MVP 是否能稳定支持 case 标准化、证据缺口识别、模式聚合和候选策略方向。

## 2. 适合填入 Registry 的真实脱敏 Case 标准

适合纳入的 case：

| 标准 | 要求 |
|---|---|
| case 数量 | 5-10 条，最多不超过 20 条 |
| case 类型 | 账号安全 / ATO / 盗号申诉相关 |
| 核心实体 | 至少有脱敏 user_id；device_id 可缺失但需标记 |
| 事件时间 | 有明确或近似 event_time |
| 异常动作 | 有清楚 abnormal_action，如发布、换绑、改密、私信、关注、支付、活动参与 |
| 用户说法 | 有 user_claim 或客服 / 人工备注 |
| 现有材料 | 至少有一类 available_evidence，如申诉文本、人工备注、历史摘要、工单摘要 |
| 当前状态 | 能标记 current_status，如 standardized / missing_entity / pending_review |

优先选择：

- 用户称非本人操作，且存在发布、换绑、改密、私信、关注、支付等后置动作。
- 用户提到外部链接、活动页、授权页面、二维码、验证码、账号异常提示等线索。
- 人工备注中存在疑似 token / OAuth / 登录态 / 异设备 / 换绑链路线索。
- 同一批 case 可能存在相似后置动作或相似申诉描述，适合观察模式。

## 3. 不适合纳入 ATO Batch 的 Case 类型

以下 case 不应进入本 ATO batch，或应先转到其他场景：

| case 类型 | 原因 | 建议去向 |
|---|---|---|
| 纯内容违规，无非本人或账号异常描述 | 更像内容安全或账号治理问题 | 内容安全 / 用户画像 |
| 纯活动套利，无账号控制权异常 | 更像活动反作弊 | 活动反作弊 |
| 纯关注 / 点赞 / 导流异常，但无凭证或控制权线索 | 更像互动作弊或导流作弊 | 导流 / 互动作弊 |
| 纯设备 root / hook / frida 风险 | 更像设备风险补证 | device_risk_read |
| 只有策略命中，无用户申诉或账号异常链路 | 更像策略命中解释 | strategy_hit_read |
| 批量上百上千 case | 超出人工 dry-run 范围 | 先抽样 / 分层 |
| 包含未脱敏手机号、IP、token、cookie、身份证、完整设备指纹 | 不符合安全边界 | 先脱敏后再纳入 |

关键规则：

- 发布、私信、关注、支付、活动参与等只是 ATO 后置异常动作。
- 如果没有凭证 / token / OAuth / 登录态异常，或改密、换绑、异设备登录等控制权变化线索，不应强行归入 ATO。
- 若 case 只能说明导流、互动或活动套利，应转入对应领域，不要用 ATO 框架过拟合。

## 4. 真实 Case 脱敏方法

### 4.1 实体脱敏

| 原始类型 | 推荐写法 | 禁止写法 |
|---|---|---|
| user_id | user_real_001 / user_hash_abc | 原始 userId 明文 |
| device_id | device_real_a / device_hash_xxx | 完整 did / device fingerprint |
| phone | phone_last4_1234 或 hidden | 完整手机号 |
| IP | ip_subnet_x 或 ip_region_only | 完整 IP |
| work_id / photo_id | work_hash_001 | 原始 ID |
| token / cookie / session | token_present_redacted | 任意明文 |
| OAuth app / 外部链接 | oauth_app_type_x / external_link_redacted | 完整 URL、完整参数 |

### 4.2 文本脱敏

保留：

- 用户主张的事实结构。
- 异常动作类型。
- 相对时间。
- 是否提到链接、授权、二维码、验证码、第三方登录等线索。
- 是否有人工备注或工单摘要。

删除或改写：

- 真实姓名、手机号、身份证、住址。
- 完整链接、完整参数、token、cookie。
- 内部账号、内部权限、真实工单明细 URL。
- 可直接定位用户的原始日志字段。

### 4.3 时间脱敏

可保留：

- 年月日时分级别的异常时间，如果业务允许。
- 相对时间，如“异常发布前 30 分钟出现登录验证”。

如需更强脱敏：

- 使用 T0、T0+10m、T0+1d。
- 保留顺序关系，不保留绝对时间。

## 5. Registry 人工填写方法

使用 `ato_batch_case_registry_template_v1.csv` 的字段。

填写建议：

| 字段 | 填写方式 |
|---|---|
| case_id | 使用 ATO_REAL_DRYRUN_001 这类内部 dry-run ID |
| user_id | 写脱敏 ID |
| device_id | 有则写脱敏 ID，无则留空并在 current_status 标 missing_entity |
| event_time | 写脱敏或允许保留的时间 |
| abnormal_action | 写后置异常动作，如非本人发布 / 换绑 / 改密 / 私信 |
| user_claim | 摘要化描述，不贴原文 |
| source_channel | appeal / customer_service / manual_review / sampled_case |
| available_evidence | 只写材料类型和摘要，不写明文日志 |
| missing_evidence | 写需要补证的关键证据 |
| initial_risk_hint | 写候选路径，如 token_reuse_hint / oauth_abuse_hint |
| current_status | standardized / missing_entity / pending_review |
| manual_label | pending_review / insufficient / suspected 等 |
| confidence | low / medium / unknown |
| notes | 只写脱敏备注 |

## 6. Evidence Card 人工填写方法

每个 case 填一张简版 evidence card。

### 6.1 Strong Evidence

只有已经有明确材料支持时才填 strong，例如：

- 异常发布来源与常用设备 / 常用 IP 明显不一致。
- token / passToken 在异常来源被使用。
- OAuth 新授权后立即出现异常动作。
- 换绑 / 改密由异常设备或异常 IP 触发，随后发生非本人动作。

如果只是用户申诉、人工备注或怀疑，不得填 strong。

### 6.2 Medium Evidence

可填：

- 登录失败后成功，但还缺设备/IP确认。
- 策略命中与异常时间接近。
- 设备存在风险标签，但未和后置动作闭环。
- 改密 / 换绑 / 发布等高相关异常动作存在，但缺审计。

### 6.3 Weak Evidence

可填：

- 用户称非本人。
- 客服记录。
- 人工备注。
- 单条异常行为。
- 外部链接 / 助力 / 二维码描述。

### 6.4 Counter Evidence

必须主动填写反证或反证缺失：

- 常用设备 / 常用 IP 操作。
- 用户历史行为连续。
- 家庭共用设备可能。
- 本人误操作可能。
- 平台日志窗口不完整，不能反向排除 ATO。

### 6.5 Missing Evidence

常见必填缺口：

- 发布 / 私信 / 关注 / 支付 / 活动参与等后置动作审计。
- token / refreshToken / passToken 使用链路。
- OAuth / 第三方授权记录。
- 登录日志窗口完整性。
- 离线 Hive 登录日志。
- 换绑 / 改密 / 找回 / 短信验证审计。
- 设备风险补证。
- 审核 / 封禁工单。

### 6.6 Conclusion Support Level

建议规则：

| support level | 使用条件 |
|---|---|
| strong_support | 多条强证据闭环支持 ATO，且反证弱 |
| partial_support | 有中等证据或强线索，但缺关键链路 |
| insufficient_support | 只有申诉/备注/后置动作，缺控制权或凭证证据 |
| counter_evidence_present | 存在明显本人操作、常用设备、正常授权等反证 |
| not_evaluated | 信息不足或未完成证据卡 |

人工 dry-run 默认不建议填 strong_support，除非已有脱敏材料明确支持完整链路。

## 7. Pattern Summary 聚合方法

聚合时先按 ATO 主线分组，而不是按后置动作简单分组。

优先聚合维度：

1. 凭证 / 登录态异常：
   - token 复用。
   - session / cookie 异常。
   - refreshToken / passToken 使用异常。

2. OAuth / 第三方授权异常：
   - 新授权。
   - 异常 scope。
   - 授权后出现后置动作。

3. 账号控制权变化：
   - 异设备登录。
   - 登录验证后成功。
   - 改密。
   - 换绑。
   - 找回流程异常。

4. ATO 后置异常动作：
   - 发布。
   - 私信。
   - 关注 / 点赞。
   - 支付。
   - 活动参与。
   - 直播。

5. 反证 / 非 ATO 分流：
   - 本人误操作。
   - 家庭共用。
   - 纯互动作弊。
   - 纯活动套利。
   - 纯内容安全。

输出 pattern summary 时必须写：

- 哪些 case 支持该模式。
- 支持证据强度。
- 缺哪些关键证据。
- 哪些 case 应从 ATO 分流到其他领域。
- 当前 confidence。

## 8. 如何区分 ATO 主线和后置异常动作

ATO 主线：

- 凭证 / token / OAuth / 登录态异常。
- 账号控制权变化，如改密、换绑、异设备登录。
- 非本人动作与上述异常在时间上、实体上、链路上可连接。

后置异常动作：

- 发布。
- 私信。
- 关注。
- 点赞。
- 支付。
- 活动参与。
- 直播。

判断规则：

- 后置动作本身不是 ATO。
- 后置动作必须能和凭证异常、授权异常、登录态异常或控制权变化连接，才支持 ATO。
- 如果只有后置动作，没有控制权证据，应转为对应领域：
  - 活动参与异常：活动反作弊。
  - 关注/点赞/私信导流：导流 / 互动作弊。
  - 发布违规内容：内容安全 / 账号治理。
  - 支付异常：交易风控。

## 9. 策略方向输出规则

策略方向只能是候选方向。

必须包含：

- candidate_direction。
- related_cases。
- target_attack_path。
- strong_required_evidence。
- false_positive_risk。
- missing_before_eval。
- recommended_stage。

推荐方向类型：

- 凭证 / 登录态异常补证方向。
- 账号控制权变化补证方向。
- ATO 后置异常动作补证方向。
- 非 ATO 分流规则方向。

禁止输出：

- 直接上线。
- 直接封禁。
- 命中即处置。
- “这批都是盗号”。
- “后置动作异常就是 ATO”。

评估建议：

- 先 evidence_collection。
- 再 offline_eval。
- 再 shadow_monitoring。
- 查杀分离，不把查证条件直接变成处置条件。
- 人工抽检误伤样本。

## 10. 5-10 Case 人工 Dry-run 验收标准

通过标准：

| 验收项 | 标准 |
|---|---|
| registry 完整性 | 5-10 条 case 均满足最小字段，敏感信息已脱敏 |
| ATO 主线清晰 | 每条 case 都区分控制权证据和后置动作 |
| evidence card 完整 | 每条 case 都有强/中/弱/反证/缺口 |
| 缺口识别清晰 | 每条 case 至少列出 P0/P1 缺失证据 |
| pattern summary 可读 | 能聚合出 2-4 个候选模式或分流方向 |
| 非 ATO 分流 | 对纯活动/导流/互动/内容 case 有明确分流说明 |
| 策略方向克制 | 只输出候选方向，不自动上线，不处置 |
| 误伤风险 | 每个策略方向都包含 false_positive_risk |
| 数据窗口边界 | 登录日志超窗或未知时不把 no_data 当反证 |
| 人工复核 | 最终输出 manual_review_required |

失败标准：

- 出现真实敏感明文。
- 把用户申诉当强证据。
- 把后置动作直接定义为 ATO。
- 把活动页 / 导流 / 点赞直接写成 ATO 风险类型。
- 输出自动上线或自动处置建议。
- 忽略反证和误伤风险。

## 11. 本指南的使用方式

建议顺序：

1. 复制 registry template，填入 5-10 条真实脱敏 case。
2. 按本指南检查是否适合纳入 ATO batch。
3. 每条 case 人工填 evidence card。
4. 汇总 pattern summary。
5. 输出 candidate strategy direction。
6. 由人工 reviewer 检查 ATO 主线、反证、缺口和分流。

本指南只用于人工 dry-run，不是运行时系统，不接 DataAgent，不接内部 Agent。
