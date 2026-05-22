# Black Market Account Matrix Real-case Manual Dry-run v1

## 1. 定位

本文件基于一批已脱敏、已明确属于同一波黑产的账号矩阵样本，演示 `20_black_market_account_matrix_batch` 如何做人工 dry-run。

该批不是 ATO：

- ATO 是账号控制权异常，如 token / OAuth / 登录态异常、改密、换绑、异设备登录。
- 本批是黑产账号矩阵 / 导流互动 / 互粉互动 / 养号账号池归因。
- 简介、昵称、adminaction、注册天数、UID 号段等聚集特征不能被写成盗号或账号控制权异常。

边界：

- 不调用真实 DataAgent。
- 不访问真实平台。
- 不接内部 Agent。
- 不修改 release / dist。
- 不输出真实微信号、UID、device、IP 等敏感明文。
- 不自动处置。
- 不自动上线策略。

所有结论仅基于人工脱敏样例和已观察到的共性，不代表真实平台查询结论。

## 2. 已观察到的脱敏共性

| 维度 | 已观察共性 | 当前证据强度 | 边界 |
|---|---|---|---|
| 简介 | 高度一致：一起互动 + 薇[redacted] | strong_profile_pattern | 联系方式已脱敏；需归一化 hash 补证 |
| adminaction | 一致：2011262 | strong_context_pattern | code 含义和触发上下文仍需确认 |
| 用户名 | 数字 + emoji + 近似中文字符组合 | medium_template_pattern | 昵称模板不能单独处置 |
| 注册天数 | 约 110-188 天 | medium_cohort_pattern | 需注册来源和行为链路补证 |
| 日期 | 2026-04-25 至 2026-05-20 | medium_wave_pattern | 只能说明样本窗口集中 |
| UID | 多个号段聚集 | medium_segment_pattern | UID 已脱敏，不输出明文 |

## 3. Case Registry 摘要

本 dry-run 不展开真实账号明细，只按脱敏账号引用构造 registry 摘要。

| case_id | account_ref | uid_segment | intro_pattern | adminaction_code | nickname_pattern | registration_age_days | sample_window | current_status |
|---|---|---|---|---|---|---:|---|---|
| BM_REAL_DRYRUN_001 | acct_ref_001 | uid_seg_a | intro_interact_contact_redacted | 2011262 | numeric_emoji_cn_variant | 110-120 | 2026-04-25 | standardized |
| BM_REAL_DRYRUN_002 | acct_ref_002 | uid_seg_a | intro_interact_contact_redacted | 2011262 | numeric_emoji_cn_variant | 110-120 | 2026-04-27 | standardized |
| BM_REAL_DRYRUN_003 | acct_ref_003 | uid_seg_b | intro_interact_contact_redacted | 2011262 | numeric_emoji_cn_variant | 121-140 | 2026-05-01 | standardized |
| BM_REAL_DRYRUN_004 | acct_ref_004 | uid_seg_b | intro_interact_contact_redacted | 2011262 | numeric_emoji_cn_variant | 121-140 | 2026-05-05 | standardized |
| BM_REAL_DRYRUN_005 | acct_ref_005 | uid_seg_c | intro_interact_contact_redacted | 2011262 | numeric_emoji_cn_variant | 141-160 | 2026-05-10 | standardized |
| BM_REAL_DRYRUN_006 | acct_ref_006 | uid_seg_c | intro_interact_contact_redacted | 2011262 | numeric_emoji_cn_variant | 161-180 | 2026-05-13 | standardized |
| BM_REAL_DRYRUN_007 | acct_ref_007 | uid_seg_d | intro_interact_contact_redacted | 2011262 | numeric_emoji_cn_variant | 161-180 | 2026-05-17 | standardized |
| BM_REAL_DRYRUN_008 | acct_ref_008 | uid_seg_d | intro_interact_contact_redacted | 2011262 | numeric_emoji_cn_variant | 181-188 | 2026-05-20 | standardized |

脱敏说明：

- `acct_ref_*` 不是真实 UID。
- `uid_seg_*` 只表示号段 cohort，不含真实 UID。
- `intro_interact_contact_redacted` 表示“一起互动 + 薇[redacted]”模式，不输出联系方式。

## 4. Per-case Evidence Card 示例

### 4.1 BM_REAL_DRYRUN_001

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | 简介高度一致 + 联系方式 redacted + adminaction=2011262 | strong | 资料矩阵强，但不能直接处置 |
| medium_evidence | 用户名模板化 + 注册天数落在 110-120 cohort | medium | 需要行为链路补证 |
| weak_evidence | 单账号样本来自同波黑产人工集合 | weak | 人工集合需要证据验证 |
| counter_evidence | 未看到正常活动模板反证 | missing_counter | 仍需排除官方活动/正常社交模板 |
| missing_evidence | 联系方式 hash、账号间互动边、设备/IP/注册来源 | P0/P1 | 用于确认矩阵同源与协同行为 |
| conclusion_support_level | partial_matrix_support | medium | 支持账号矩阵候选，不支持自动处置 |

### 4.2 BM_REAL_DRYRUN_002

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | 与 BM_REAL_DRYRUN_001 同 UID segment、同简介、同 adminaction | strong | 需确认是否同源或同批次 |
| medium_evidence | 昵称模板一致，日期接近 | medium | 昵称相似不能单独定性 |
| weak_evidence | 互粉/互动语义来自简介文案 | weak | 还不是行为证据 |
| counter_evidence | 未确认账号间真实互动边 | missing_counter | 如果无互动边，导流互动支持下降 |
| missing_evidence | mutual follow edges、comment/message path、contact hash | P0 | 行为链路优先 |
| conclusion_support_level | partial_matrix_support | medium | 支持同批账号矩阵候选 |

### 4.3 BM_REAL_DRYRUN_003

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | 简介和 adminaction 与前两例一致 | strong | 支持跨号段矩阵候选 |
| medium_evidence | UID segment 切换到 uid_seg_b，注册天数仍在集中区间 | medium | 可能是多号段投放，也可能是抽样偏差 |
| weak_evidence | 联系方式存在但已 redacted | weak | 需要 hash 归一化 |
| counter_evidence | 未看到正常商家/活动账号反证 | missing_counter | 商家账号展示联系方式可能误伤 |
| missing_evidence | contact normalization、device/IP、行为序列 | P0/P1 | 确认联系方式同源与行为协同 |
| conclusion_support_level | partial_matrix_support | medium | 支持跨号段资料矩阵候选 |

### 4.4 BM_REAL_DRYRUN_004

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | 同简介、同 adminaction、同昵称模板 | strong | 资料层强聚集 |
| medium_evidence | 日期集中在 2026-05-05 附近 | medium | 需行为时间序列确认同波次 |
| weak_evidence | 单账号 profile_matrix | weak | 资料相似不是行为链路 |
| counter_evidence | 未验证是否为正常活动统一模板 | missing_counter | 需正常模板对照 |
| missing_evidence | adminaction context、interaction edges、strategy context | P1 | 解释 code 与行为关系 |
| conclusion_support_level | partial_matrix_support | medium | 支持矩阵候选，缺行为补证 |

### 4.5 BM_REAL_DRYRUN_005

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | 简介、adminaction、昵称模板继续一致 | strong | 样本一致性强 |
| medium_evidence | 注册天数进入 141-160 cohort | medium | 支持养号周期假设 |
| weak_evidence | 互粉互动语义仍来自简介 | weak | 不是行为日志 |
| counter_evidence | 未看到自然历史行为反证 | missing_counter | 需补正常行为基线 |
| missing_evidence | behavior_sequence、contact_hash_cluster、counter evidence | P0/P2 | 需要行为与误伤验证 |
| conclusion_support_level | partial_matrix_support | medium | 支持养号账号池候选 |

### 4.6 BM_REAL_DRYRUN_006

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | 同 adminaction + 同简介联系方式模式 | strong | 可作为召回候选 |
| medium_evidence | 日期集中，注册天数 161-180 | medium | 需和其他 cohort 连接 |
| weak_evidence | 导流 hint 来自简介 | weak | 无私信/评论/点击链路 |
| counter_evidence | 商家账号或正常互粉社群未排除 | missing_counter | 需要样本抽检 |
| missing_evidence | message edges、contact hash、device/IP relation | P0/P1 | 判断导流闭环 |
| conclusion_support_level | partial_matrix_support | medium | 支持导流账号矩阵候选 |

### 4.7 BM_REAL_DRYRUN_007

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | 同简介、同 adminaction，进入 uid_seg_d | strong | 支持多号段矩阵扩展 |
| medium_evidence | 日期靠近 2026-05-17，注册天数集中 | medium | 需检查同波次行为 |
| weak_evidence | interaction hint 来自资料 | weak | 不是行为边 |
| counter_evidence | 正常 campaign 模板未排除 | missing_counter | 需活动模板对照 |
| missing_evidence | behavior_sequence、interaction_edges、normal_campaign_countercheck | P0/P2 | 控制误伤 |
| conclusion_support_level | partial_matrix_support | medium | 支持账号矩阵候选 |

### 4.8 BM_REAL_DRYRUN_008

| evidence_type | 内容 | 强度 | 边界 |
|---|---|---|---|
| strong_evidence | 同简介、同 adminaction、同昵称模板 | strong | 支持同波资料矩阵 |
| medium_evidence | 注册天数 181-188，日期 2026-05-20 | medium | 可能为较早养号批次 |
| weak_evidence | mutual follow hint 来自简介 | weak | 需互动边确认 |
| counter_evidence | 正常互粉社区未排除 | missing_counter | 需要人工抽样 |
| missing_evidence | device/IP relation、behavior_sequence、contact_hash_cluster | P0/P1 | 需要矩阵基建和行为补证 |
| conclusion_support_level | partial_matrix_support | medium | 支持账号池候选 |

## 5. Batch Pattern Summary

### 5.1 Common Intro Pattern

| pattern | affected_cases | evidence_strength | interpretation | boundary |
|---|---|---|---|---|
| 一起互动 + 薇[redacted] | 8/8 | strong_profile_pattern | 简介高度一致，且包含联系方式导流语义 | 联系方式必须 hash 化；简介不是处置依据 |

### 5.2 Common Adminaction

| adminaction_code | affected_cases | evidence_strength | interpretation | missing_context |
|---|---|---|---|---|
| 2011262 | 8/8 | strong_context_pattern | 样本治理/命中背景高度一致 | code 含义、触发条件、是否与导流互动相关 |

### 5.3 Nickname Template

| template | affected_cases | evidence_strength | interpretation | boundary |
|---|---|---|---|---|
| 数字 + emoji + 近似中文字符组合 | 8/8 | medium_template_pattern | 昵称可能批量生成或模板化运营 | 昵称相似不能单独定性 |

### 5.4 Registration Age Cohort

| age_range | affected_cases | interpretation | boundary |
|---|---|---|---|
| 110-188 天 | 8/8 | 可能存在同一养号周期或投放窗口 | 需注册来源、设备/IP、行为序列补证 |

### 5.5 Date Cohort

| sample_window | affected_cases | interpretation | boundary |
|---|---|---|---|
| 2026-04-25 至 2026-05-20 | 8/8 | 样本日期集中，可能来自同波治理或同波采样 | 日期集中不等于同波作案 |

### 5.6 UID Segment Cohort

| uid_segment | affected_cases | interpretation |
|---|---|---|
| uid_seg_a | BM_REAL_DRYRUN_001, BM_REAL_DRYRUN_002 | 同号段小簇 |
| uid_seg_b | BM_REAL_DRYRUN_003, BM_REAL_DRYRUN_004 | 同号段小簇 |
| uid_seg_c | BM_REAL_DRYRUN_005, BM_REAL_DRYRUN_006 | 同号段小簇 |
| uid_seg_d | BM_REAL_DRYRUN_007, BM_REAL_DRYRUN_008 | 同号段小簇 |

### 5.7 Suspected Abuse Path

| suspected_path | likelihood | supporting_pattern | missing_evidence |
|---|---|---|---|
| 导流互动账号矩阵 | high | 简介一致、联系方式 redacted、adminaction 一致 | 私信/评论/关注/点击链路 |
| 互粉互动账号池 | medium | “一起互动”语义、昵称模板、注册 cohort | 账号间互动边 |
| 养号账号池 | medium | 注册天数集中、UID 号段聚集、资料模板 | 设备/IP/注册来源 |
| 正常活动模板误伤 | low_to_medium | 简介可能来自正常活动/社群模板 | 正常活动模板对照、人工抽检 |

## 6. Missing Evidence Summary

| missing_evidence | priority | why_needed | affected_cases |
|---|---|---|---|
| 联系方式归一化 hash | P0 | 判断薇[redacted] 是否同源或多源复用 | 8/8 |
| 账号间关注 / 互粉 / 评论 / 私信边 | P0 | 判断是否存在真实互动矩阵 | 8/8 |
| 导流点击或联系方式触达链路 | P0 | 判断是否形成导流闭环 | 8/8 |
| 设备/IP/注册来源聚合 | P1 | 判断是否为账号池基建 | 8/8 |
| 行为时间序列 | P1 | 判断同波次自动化或人工批量操作 | 8/8 |
| adminaction 上下文 | P1 | 理解 2011262 与治理/命中的关系 | 8/8 |
| 正常活动/运营模板反证 | P2 | 控制简介统一模板误伤 | 8/8 |

## 7. Strategy Direction Draft

### Direction 1: 简介签名聚类

- candidate_direction: 对“一起互动 + 薇[redacted]”及其变体做签名归一化聚类。
- supporting_patterns: 8/8 简介高度一致。
- strong_required_evidence: 联系方式 hash 复用、跨 UID 号段复用、行为链路支持。
- false_positive_risk: 正常活动模板、社群互粉模板、商家介绍。
- recommended_stage: offline_eval / shadow_monitoring。
- boundary: 简介聚类只作召回入口，不直接处置。

### Direction 2: 联系方式归一化

- candidate_direction: 对薇、微信、符号拆分、emoji 混淆、空格拆分等联系方式表达做 redacted + hash 聚合。
- supporting_patterns: 简介中均出现联系方式导流语义。
- strong_required_evidence: contact_hash_cluster 与账号矩阵、行为链路共现。
- false_positive_risk: 正常用户展示联系方式、商家账号。
- recommended_stage: evidence_collection。
- boundary: 不输出联系方式明文。

### Direction 3: 账号矩阵识别

- candidate_direction: 将 intro_pattern、adminaction、nickname_template、registration_age_cohort、uid_segment_cohort 做多维矩阵候选识别。
- supporting_patterns: 资料、code、昵称、注册天数、号段多维共现。
- strong_required_evidence: 多维资料聚集 + 行为链路补证 + 误伤反证通过。
- false_positive_risk: 正常活动批量模板、同兴趣社群、平台运营导入。
- recommended_stage: offline_eval。
- boundary: 账号矩阵候选不等于黑产结论。

### Direction 4: 行为链路补证

- candidate_direction: 补充关注、互粉、评论、私信、导流点击等链路，验证资料矩阵是否转化为真实导流互动行为。
- supporting_patterns: 简介语义指向“一起互动”，但当前缺行为边。
- strong_required_evidence: account_edges、message/comment path、time_cohort。
- false_positive_risk: 自然社交互粉、正常粉丝群活动。
- recommended_stage: evidence_collection。
- boundary: 行为链路是补证，不是自动处置条件。

### Direction 5: 查杀分离 / AB 评估

- candidate_direction: 先用资料聚类做召回，行为链路和人工抽检做查证，再评估是否进入治理策略。
- evaluation_plan: offline_eval → shadow_monitoring → manual_review_sampling。
- key_metrics: cluster precision、contact hash reuse rate、behavior edge support rate、false positive template rate。
- boundary: 查证条件和处置条件分离；不能“命中简介模板即处置”。

## 8. 误伤风险与反证样本

| risk | why_it_matters | needed_countercheck |
|---|---|---|
| 正常互粉社群 | 简介可能自然出现“一起互动” | 账号历史、自然互动比例、社群上下文 |
| 正常活动模板 | 统一简介可能来自活动文案 | 官方活动/运营模板库对照 |
| 商家或达人联系方式 | 简介含联系方式不一定违规 | 账号类型、认证/经营属性、内容上下文 |
| 昵称模板误伤 | 数字+emoji 不一定黑产 | 行为链路和设备/IP聚合 |
| adminaction 误读 | code 含义未知时不能强判 | adminaction 上下文和触发原因 |

反证样本建议：

- 抽 5-10 个同简介但无互动导流行为的账号。
- 抽 5-10 个正常活动模板账号。
- 抽 5-10 个商家/达人联系方式账号。
- 比较互动边、私信/评论导流链路、设备/IP聚合、注册来源差异。

## 9. 是否适合进入内部 Agent 只读补证阶段

结论：适合进入内部 Agent 只读补证阶段，但不适合进入自动处置或策略上线阶段。

适合补证原因：

- 样本已经有强资料聚类基础。
- adminaction、注册天数、日期、UID 号段均显示 cohort 特征。
- 当前最大缺口是行为链路和联系方式归一化，适合由只读 observation 执行层补证。

建议只读补证任务：

1. 联系方式归一化 hash，不输出明文。
2. 账号间关注、互粉、评论、私信边摘要。
3. 设备/IP/注册来源聚合摘要，输出脱敏分布。
4. 行为时间序列聚合。
5. adminaction code 上下文摘要。
6. 正常模板反证样本抽检。

内部 Agent 边界：

- 内部 Agent 只作为真实只读 observation 执行层。
- 不作为最终研判大脑。
- 不输出敏感明文。
- 不执行写操作。
- 不自动扩散到全量账号。

## 10. 当前 Batch Framework 暴露的问题

1. 账号矩阵场景需要更强的 contact normalization 字段，目前 registry 只有 intro_pattern。
2. adminaction code 需要上下文字段，否则容易被误当强处置证据。
3. UID segment cohort 需要明确粒度，避免泄露真实号段或过度解释。
4. behavior evidence missing 需要从自由文本升级为枚举。
5. 反证样本在模板中还不够显式，后续应加入 counter_sample_plan。
6. strategy direction 需要增加“召回信号”和“处置信号”分离字段。
7. 当前 dry-run 无法衡量误伤率，必须依赖只读补证和人工抽检。

## 11. 下一步优化建议

1. 在 registry 中新增 `contact_hash_cluster`、`adminaction_context`、`counter_sample_needed` 字段。
2. 将 missing evidence 标准化为枚举：contact_hash_missing、behavior_edge_missing、device_ip_missing、adminaction_context_missing、normal_template_countercheck_missing。
3. 为内部 Agent 设计只读 observation protocol，但仅覆盖摘要、计数、分布和脱敏实体。
4. 增加正常活动模板 / 商家账号 / 自然互粉社群的反证样本模板。
5. 在 strategy direction 中强制区分 recall_signal、verification_signal、disposition_candidate，避免简介聚类直接变成处置依据。

## 12. Final Boundary

本文件只是人工 dry-run：

- 不代表真实平台查询结论。
- 不代表所有样本都已确认黑产。
- 不代表可以自动上线策略。
- 不代表可以自动处置账号。
- 不属于 ATO。
