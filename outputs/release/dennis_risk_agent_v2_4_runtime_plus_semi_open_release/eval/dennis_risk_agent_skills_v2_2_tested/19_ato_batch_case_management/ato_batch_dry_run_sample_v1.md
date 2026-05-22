# ATO Batch Dry-run Sample v1

## 1. 定位

本文件基于 `ato_batch_case_registry_template_v1.csv` 中的 8 条脱敏合成 case，演示 ATO 批量 case analysis 最小闭环如何工作。

本 dry-run 只做样例推演：

- 不调用真实 DataAgent。
- 不访问真实内部平台。
- 不执行真实 SQL / API / browser 查询。
- 不生成真实 observation。
- 不自动上线策略。
- 不执行任何处置动作。

所有结论均基于合成样例字段和模板推理，只能说明模板如何组织信息，不代表真实风险结论。

ATO 主线口径：

- ATO 的核心不是“活动页”“助力”“导流”“点赞”等业务行为本身。
- ATO 的核心应围绕账号控制权异常：凭证 / token / OAuth / 登录态异常，改密、换绑、异设备登录等控制权变化，以及这些变化之后发生的非本人动作。
- 发布、私信、关注、支付、活动参与、点赞等只能作为 ATO 后置异常动作样例。
- 如果没有异常登录态、凭证滥用、OAuth 滥用或账号控制权变化证据，这些后置动作应归入活动反作弊、导流作弊、互动作弊或内容安全等其他场景，不应归入 ATO。

## 2. 输入样例范围

| case_id | user_id | device_id | event_time | abnormal_action | initial_risk_hint |
|---|---|---|---|---|---|
| ATO_BATCH_DEMO_001 | user_demo_001 | device_demo_a | 2026-05-10 12:53:16 | 非本人发布违规作品 | 疑似token_cookie复用 |
| ATO_BATCH_DEMO_002 | user_demo_002 | device_demo_b | 2026-05-11 09:20:00 | 异常关注导流账号 | 疑似授权滥用或本机被控 |
| ATO_BATCH_DEMO_003 | user_demo_003 | missing | 2026-05-12 18:45:00 | 账号被登录验证后发布 | 疑似新设备接管 |
| ATO_BATCH_DEMO_004 | user_demo_004 | device_demo_d | 2026-05-13 21:10:00 | 异常换绑手机号 | 疑似ATO换绑 |
| ATO_BATCH_DEMO_005 | user_demo_005 | device_demo_e | 2026-05-14 07:30:00 | 异常改密后发布 | 疑似凭证接管 |
| ATO_BATCH_DEMO_006 | user_demo_006 | device_demo_f | 2026-05-15 15:05:00 | 异常直播开播 | 疑似账号被控或家庭共用设备 |
| ATO_BATCH_DEMO_007 | user_demo_007 | device_demo_g | 2026-05-16 23:40:00 | 批量点赞和关注 | 疑似OAuth授权滥用 |
| ATO_BATCH_DEMO_008 | user_demo_008 | device_demo_h | 2026-05-17 10:18:00 | 发布后账号封禁 | 疑似活动页钓鱼 |

## 3. 简版 Evidence Cards

### 3.1 ATO_BATCH_DEMO_001

一句话判断：当前 ATO 主线应先验证 token / cookie / OAuth 或登录态是否异常；“助力页面”和“发布违规作品”只能作为可能的前置线索与后置动作，不能直接定义为 ATO。

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | none | none | 未查询真实日志，无强证据 |
| medium_evidence | 用户称登录设备只有本人，且曾访问助力页面 | medium_hint | 只是申诉线索，不是事实 |
| weak_evidence | 非本人发布违规作品描述 | weak | 需要发布审计确认 |
| counter_evidence | none | none | 未看到常用设备 / 常用 IP / 本人操作反证 |
| missing_evidence | 发布审计日志、token 使用链路、OAuth 授权记录 | P0/P1 | 缺这些证据时只能 partial / insufficient |
| freshness_risk | unknown | risk | 如事件超出在线登录窗口，no_data 不能作为反证 |
| conclusion_support_level | insufficient_support | low | 当前仅为样例推演 |

### 3.2 ATO_BATCH_DEMO_002

一句话判断：当前 ATO 视角只能把异常关注导流账号作为后置异常动作；是否属于 ATO 取决于能否补到 OAuth / token / 登录态异常或账号控制权变化证据。

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | none | none | 无真实接口证据 |
| medium_evidence | 异常关注导流账号 + 用户否认操作 | medium_hint | 这是后置动作线索；没有账号控制权异常证据时应转为导流/互动作弊场景 |
| weak_evidence | 客服记录和异常关注描述 | weak | 不能单独支持 ATO |
| counter_evidence | none | none | 缺历史关注习惯反证 |
| missing_evidence | 关注接口 IP/UA、登录日志、设备风险补证 | P0/P1 | 用于区分授权滥用、本机被控、本人操作 |
| freshness_risk | unknown | risk | 需确认行为时间是否在在线日志窗口内 |
| conclusion_support_level | insufficient_support | low | 当前只适合进入补证 |

### 3.3 ATO_BATCH_DEMO_003

一句话判断：当前更像新设备接管或登录验证链路异常的候选样例，但 device_id 缺失，不能进入设备风险补证。

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | none | none | 无登录成功链路或发布审计 |
| medium_evidence | 登录验证后发布 + 策略命中摘要 | medium_hint | 策略命中摘要不是最终事实 |
| weak_evidence | 人工备注 | weak | 不替代数据证据 |
| counter_evidence | none | none | 未见本人设备连续性反证 |
| missing_evidence | device_id、登录成功链路、发布审计日志 | P0 | 缺 device_id 时不得直接查 Device SDK |
| freshness_risk | unknown | risk | 需检查在线窗口完整性 |
| conclusion_support_level | insufficient_support | low | 缺关键实体 |

### 3.4 ATO_BATCH_DEMO_004

一句话判断：当前更像换绑型 ATO 候选样例，但换绑审计、短信验证链路和登录日志缺失，不能确认。

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | none | none | 无换绑审计 |
| medium_evidence | 异常换绑手机号 + 用户无法登录 | medium_hint | 仍需确认是否本人或客服流程 |
| weak_evidence | 申诉摘要、账号状态变化 | weak | 只是线索 |
| counter_evidence | none | none | 缺常用设备 / 常用手机号流程反证 |
| missing_evidence | 换绑审计日志、短信验证链路、登录日志 | P0 | 用于区分 ATO、误操作和账号找回流程 |
| freshness_risk | unknown | risk | 登录日志超窗需 offline 补证 |
| conclusion_support_level | partial_support | medium_hint_only | 仅因异常动作更具 ATO 相关性，仍缺强证据 |

### 3.5 ATO_BATCH_DEMO_005

一句话判断：当前更像凭证接管或新设备登录后的改密发布链路候选样例，但需要改密审计和发布来源确认。

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | none | none | 无改密 / 发布真实日志 |
| medium_evidence | 改密后发布，用户否认 | medium_hint | 可作为高优先级补证 case |
| weak_evidence | 改密现象和发布现象描述 | weak | 仍可能是本人、家庭共用或申诉不完整 |
| counter_evidence | none | none | 未见常用设备 / 常用 IP 反证 |
| missing_evidence | 改密审计、发布接口来源、token 刷新链路 | P0 | 用于区分凭证复用和新设备接管 |
| freshness_risk | unknown | risk | 需标注在线窗口风险 |
| conclusion_support_level | partial_support | medium_hint_only | 候选优先级较高但不定性 |

### 3.6 ATO_BATCH_DEMO_006

一句话判断：当前既可能是账号被控，也可能是家庭共用设备或本人操作，反证风险较高。

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | none | none | 无直播开播审计 |
| medium_evidence | 异常直播开播 + 用户否认 | medium_hint | 直播场景需强审计补证 |
| weak_evidence | 申诉文本、账号操作摘要 | weak | 不能直接支持 ATO |
| counter_evidence | 反证可能：常用设备本人操作 | counter_hint | 需要常用设备/IP/前端活跃确认 |
| missing_evidence | 直播开播审计、设备/IP、前端活跃信号 | P0/P1 | 用于区分被控和本人/共用设备 |
| freshness_risk | unknown | risk | 在线日志 no_data 不可强反证 |
| conclusion_support_level | insufficient_support | low | 反证空间较大 |

### 3.7 ATO_BATCH_DEMO_007

一句话判断：当前只能把批量点赞和关注视为 ATO 后置动作样例；若无法证明 OAuth / token / 登录态异常，应从互动作弊或导流作弊方向研判，而不是 ATO。

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | none | none | 无 OAuth / 行为接口证据 |
| medium_evidence | 批量点赞关注 + 用户否认 | medium_hint | 需要行为节奏和来源确认 |
| weak_evidence | 客服记录、行为数量摘要 | weak | 只说明现象 |
| counter_evidence | none | none | 缺用户历史关注/点赞习惯 |
| missing_evidence | 关注/点赞接口来源、设备共用关系、OAuth 授权 | P0/P1 | 可区分授权滥用、群控、本机被控 |
| freshness_risk | unknown | risk | 需明确行为窗口 |
| conclusion_support_level | insufficient_support | low | 只能支持“后置动作值得补证”，不能支持 ATO 归因 |

### 3.8 ATO_BATCH_DEMO_008

一句话判断：当前 ATO 视角应先验证活动页是否导致 token / OAuth / 登录态被滥用；“发布后封禁”只是后置结果，不能单独证明 ATO。

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | none | none | 无发布审计或审核工单 |
| medium_evidence | 点击外部活动链接 + 发布后封禁 | medium_hint | 只能作为凭证/授权滥用线索；没有登录态异常证据时不能归入 ATO |
| weak_evidence | 申诉文本、封禁现象 | weak | 封禁不等于盗号 |
| counter_evidence | none | none | 未见本人发布或违规历史反证 |
| missing_evidence | 发布审计、封禁/审核工单、登录日志窗口完整性 | P0/P2 | 需要区分 ATO 与内容安全历史问题 |
| freshness_risk | high_potential | risk | 登录日志窗口不完整会影响 ATO 判断 |
| conclusion_support_level | partial_support | medium_hint_only | 只能作为候选模式样例 |

## 4. Pattern Summary

### 4.1 Common Entity Pattern

| pattern | case_ids | evidence_strength | interpretation | boundary |
|---|---|---|---|---|
| 凭证 / 授权异常线索 | DEMO_001, DEMO_008 | weak_to_medium_hint | 外部活动页 / 助力只作为可能的凭证或授权滥用入口线索 | 需 token / OAuth / 登录态证据；活动页本身不是 ATO 类型 |
| ATO 后置互动行为异常 | DEMO_002, DEMO_007 | weak_to_medium_hint | 关注 / 点赞 / 导流只作为账号疑似被控后的后置动作样例 | 若无异常登录态或控制权变化证据，应归入导流/互动作弊，不归入 ATO |
| 账号关键安全动作异常 | DEMO_004, DEMO_005 | medium_hint | 换绑、改密和发布更接近账号接管链路 | 需换绑/改密审计和登录链路确认 |
| device_id 缺失影响设备补证 | DEMO_003 | data_gap | 无法进入设备风险补证 | 缺实体不能伪造 |

### 4.2 Common Device / IP / Login Pattern

| dimension | common_pattern | affected_cases | missing_check | confidence |
|---|---|---:|---|---|
| device | 大多数 case 有脱敏 device_id，但未验证设备可信度 | 7 | Device SDK / graphData future check | low |
| ip | 当前样例不含 IP | 8 | 发布/登录接口 IP 脱敏聚合 | unknown |
| login | 多 case 需要登录链路补证 | 8 | 登录日志窗口完整性、offline Hive when needed | low |
| token | 发布、改密、外部活动页线索都需要 token 链路验证 | 4 | token / refreshToken / passToken 使用链路 | medium_hint |
| oauth | 关注/点赞/活动参与等后置动作需要授权记录验证 | 4 | OAuth 授权记录、scope、授权时间 | medium_hint |

### 4.3 Common Behavior Path

| behavior_path | case_ids | likely_path | counter_hypothesis |
|---|---|---|---|
| 疑似凭证/授权入口后发生发布 | DEMO_001, DEMO_008 | token/cookie 复用或 OAuth 滥用 | 本人误操作、申诉信息不完整；若无凭证异常证据则不归入 ATO |
| 关注/点赞等后置互动异常 | DEMO_002, DEMO_007 | OAuth 授权滥用或账号被控后的后置动作 | 用户历史行为变化、误触授权；若无控制权异常证据应转互动/导流作弊 |
| 安全动作后异常发布 | DEMO_004, DEMO_005 | 账号接管、凭证接管 | 找回流程、本人操作、家庭共用 |
| 登录验证后发布 | DEMO_003 | 新设备接管 | 缺 device_id，无法确认 |
| 直播开播异常 | DEMO_006 | 账号被控或本机被控 | 本人/共用设备操作 |

### 4.4 Shared Missing Evidence

| missing_evidence | affected_cases | priority | why_it_matters |
|---|---:|---|---|
| 发布 / 直播 / 行为接口审计 | 6 | P0 | 判断异常动作来源 |
| token / passToken 使用链路 | 4 | P0 | 判断凭证复用 |
| OAuth / 第三方授权记录 | 4 | P1 | 判断授权滥用 |
| 登录日志窗口完整性 / offline Hive | 8 | P1 | 避免在线 no_data 假阴性 |
| 换绑 / 改密审计 | 2 | P0 | 判断安全动作链路 |
| 封禁 / 审核工单 | 1 | P2 | 区分内容处置原因和 ATO 原因 |

### 4.5 Suspected Attack Path Ranking

| suspected_path | likelihood_in_sample | supporting_cases | supporting_evidence | refuting_or_missing_evidence |
|---|---|---|---|---|
| 凭证 / token / 登录态异常 | medium | DEMO_001, DEMO_005, DEMO_008 | 发布、改密、外部链接线索需要凭证链路验证 | 缺 token 使用、登录态和发布审计 |
| OAuth / 第三方授权滥用 | medium | DEMO_001, DEMO_002, DEMO_007, DEMO_008 | 后置发布/关注/点赞/活动参与需要授权记录验证 | 缺授权记录和 scope；后置行为本身不是 ATO |
| 新设备盗号登录 | low_to_medium | DEMO_003, DEMO_004, DEMO_005 | 登录验证、换绑、改密链路更相关 | 缺登录成功链路和设备详情 |
| 本机被控 / 恶意插件 | low_to_medium | DEMO_002, DEMO_006, DEMO_007 | 用户否认但行为在账号内发生 | 缺本机设备风险和前端活跃 |
| 本人误操作 / 家庭共用 | low_to_medium | DEMO_006, partial all | 部分场景反证空间较大 | 缺常用设备/IP/历史行为反证 |

### 4.6 Case Clustering Result

| cluster_id | cluster_name | case_ids | cluster_reason | confidence | recommended_next_check |
|---|---|---|---|---|---|
| C1 | suspected_credential_or_session_abuse | DEMO_001, DEMO_008 | 外部链接线索与发布/封禁相邻，需验证是否存在凭证/登录态异常 | low_to_medium | 发布审计 + token 使用链路 + OAuth |
| C2 | ato_post_action_requires_control_proof | DEMO_002, DEMO_007 | 关注/点赞/导流只是后置动作，需先证明 OAuth / token / 登录态异常 | low | 行为接口来源 + OAuth scope + 登录态证据 |
| C3 | suspected_account_takeover_security_action | DEMO_004, DEMO_005 | 换绑/改密后异常动作 | medium_hint | 换绑/改密审计 + 登录链路 |
| C4 | insufficient_entity_or_high_counter_risk | DEMO_003, DEMO_006 | 缺 device_id 或共用设备反证空间大 | low | 补实体 + 常用设备/IP反证 |

### 4.7 Batch Confidence

- batch_confidence: low_to_medium
- confidence_reason: 样例中只包含脱敏 case 字段和用户描述，没有真实 observation；只能验证模板能否组织证据和缺口。
- key_supporting_patterns: 凭证/授权异常线索、账号控制权变化、非本人后置动作。
- key_counter_patterns: 家庭共用设备、本机误操作、申诉信息不完整仍可能解释部分 case。
- key_missing_evidence: 发布审计、token/OAuth、登录日志窗口完整性、设备风险补证。
- quality_risk: 所有 case 均为合成样例，不能外推真实风险规模。

## 5. Strategy Direction Draft

### Direction 1: 凭证 / 登录态异常补证方向

| 字段 | 内容 |
|---|---|
| related_cases | DEMO_001, DEMO_005, DEMO_008 |
| candidate_direction | 围绕 token / cookie / refreshToken / passToken / session 使用异常做证据补全 |
| target_attack_path | 凭证复用、登录态被滥用、合法 token 被异常使用 |
| strong_required_evidence | 异常 token 使用、异常登录态续期、发布/改密来源与常用链路不一致 |
| false_positive_risk | 本人多端使用、家庭共用设备、正常登录态续期、申诉信息不完整 |
| missing_before_eval | token/passToken 使用链路、发布审计、登录态刷新记录、常用设备/IP反证 |
| recommended_stage | evidence_collection |

边界：外部活动页、助力页面、发布或封禁只能作为线索和后置动作；没有凭证/登录态异常证据时，不能归因为 ATO。

### Direction 2: 账号控制权变化补证方向

| 字段 | 内容 |
|---|---|
| related_cases | DEMO_003, DEMO_004, DEMO_005 |
| candidate_direction | 对改密、换绑、异设备登录、登录验证后成功等控制权变化做链路补证 |
| target_attack_path | 新设备接管、换绑型 ATO、改密后接管 |
| strong_required_evidence | 异设备登录成功、换绑/改密由异常设备或异常 IP 触发、控制权变化后发生非本人动作 |
| false_positive_risk | 用户找回流程、客服协助流程、本人操作、家庭共用设备 |
| missing_before_eval | 登录成功链路、换绑/改密审计、短信验证链路、设备/IP 变化 |
| recommended_stage | evidence_collection |

边界：账号控制权变化比后置动作更接近 ATO 主线，但仍需验证是否非本人触发。

### Direction 3: ATO 后置异常动作补证方向

| 字段 | 内容 |
|---|---|
| related_cases | DEMO_001, DEMO_002, DEMO_006, DEMO_007, DEMO_008 |
| candidate_direction | 对发布、私信、关注、点赞、直播、支付、活动参与等非本人后置动作做来源和前置控制权证据补齐 |
| target_attack_path | ATO 后置动作，需由凭证/登录态异常或控制权变化支撑 |
| strong_required_evidence | 后置动作来源异常且时间上跟随异常登录态、OAuth 授权或控制权变化 |
| false_positive_risk | 本人误操作、家庭共用设备、正常互动/活动行为、导流/互动作弊但非 ATO |
| missing_before_eval | 行为接口来源、OAuth 授权、token 使用、登录/控制权变化证据、历史行为反证 |
| recommended_stage | evidence_collection |

边界：后置动作不能单独定义 ATO。若没有异常登录态 / 控制权变化证据，应转入活动反作弊、导流作弊、互动作弊或内容安全场景。

### AB / 查杀分离建议

- 第一阶段只做 evidence_collection，不影响用户。
- 第二阶段可做 offline_eval，统计候选方向对历史 case 的覆盖和反证比例。
- 第三阶段才考虑 shadow_monitoring，且只记录命中，不做处置。
- 查证规则和处置规则必须分离；候选方向不能直接变成封禁条件。
- 每个方向都要设置人工复核样本，重点看家庭共用、本人误操作、正常授权和在线日志窗口缺口。

## 6. 本轮模板暴露的问题

1. `available_evidence` 当前是自由文本，后续需要更结构化，例如区分 claim、manual_note、existing_observation、policy_hit_summary。
2. `missing_evidence` 可以进一步标准化为枚举，方便跨 case 聚合。
3. `confidence` 当前来自样例初始字段，建议拆成 input_confidence 和 analysis_confidence。
4. `event_time` 未自动判断是否超出在线登录日志窗口，后续可加入 freshness check 字段。
5. device_id 缺失时目前只靠 notes 说明，后续 registry 可增加 `entity_completeness_status`。
6. strategy direction 仍需加入“反证优先级”，避免只从风险路径聚合。
7. 样例无法验证真实误伤率；需要真实只读 observation 或人工标注才能进入评估。

## 7. 下一轮优化建议

1. 增加 `evidence_source_type` 字段，区分 user_claim、manual_note、observation、audit_log、policy_hit、offline_hive。
2. 增加 `freshness_window_status` 字段，强制标记 online_login_log_window_complete / incomplete。
3. 增加 `entity_completeness_status`，明确 missing_user_id、missing_device_id、missing_event_time。
4. 增加 evidence card 的机器可读 YAML 版本，方便后续批量聚合。
5. 增加 pattern summary 的 cluster scoring 规则，但只作为排序，不作为定性。
6. 在真实半开放前，用人工脱敏 case 做一轮 reviewer calibration，验证模板对策略同学是否可读。

## 8. Final Boundary

本 dry-run 的所有 case、证据、模式和策略方向均为脱敏合成样例推演：

- 不代表真实用户风险。
- 不代表真实平台观察结果。
- 不代表 DataAgent / Hive 结果。
- 不代表可上线策略。
- 不代表处置建议。
