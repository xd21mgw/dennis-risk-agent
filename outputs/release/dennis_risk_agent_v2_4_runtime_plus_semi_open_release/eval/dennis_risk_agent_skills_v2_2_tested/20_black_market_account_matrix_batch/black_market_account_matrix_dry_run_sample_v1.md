# Black Market Account Matrix Dry-run Sample v1

## 1. 定位

本 dry-run 基于 `black_market_account_matrix_registry_template_v1.csv` 的 8 条脱敏合成样例，演示黑产账号矩阵 / 导流互动 batch analysis。

它不是 ATO：

- 不分析账号控制权异常。
- 不判断 token / OAuth / 登录态被盗。
- 只分析账号矩阵、资料模板、导流互动、互粉互动和养号池模式。

边界：

- 不调用真实 DataAgent。
- 不访问真实平台。
- 不自动上线策略。
- 不输出微信号、UID、device、IP 明文。

## 2. 输入特征摘要

样例共同特征：

- intro_pattern: `一起互动 + 联系方式 redacted`
- adminaction_code: `2011262`
- nickname_pattern: `数字 + emoji + 近似中文字符组合`
- registration_age_days: 约 112-188 天
- sample_date: 2026-04-25 到 2026-05-20
- uid_segment: 多个脱敏号段聚集

## 3. 简版 Evidence Cards

| case_id | strong_evidence | medium_evidence | weak_evidence | missing_evidence | counter_evidence | support_level |
|---|---|---|---|---|---|---|
| BM_MATRIX_DEMO_001 | intro_pattern + adminaction + nickname 共现 | 注册 112 天、uid_seg_a | 单账号资料可疑 | 互动边、设备/IP、联系方式 hash | 正常活动模板未排除 | partial_matrix_support |
| BM_MATRIX_DEMO_002 | intro_pattern + adminaction + uid_seg_a 共现 | 互粉 hint、注册 118 天 | 单账号行为摘要 | 互粉边、私信/评论路径 | 正常社交互粉未排除 | partial_matrix_support |
| BM_MATRIX_DEMO_003 | intro_pattern + nickname + 注册 cohort | 联系方式导流 hint | 单账号样本来源 | contact_hash、行为序列 | 商家/正常联系方式未排除 | partial_matrix_support |
| BM_MATRIX_DEMO_004 | intro_pattern + adminaction + 日期窗口 | 注册 141 天 | interaction hint | 设备/IP、互动边、策略上下文 | 正常活动模板未排除 | partial_matrix_support |
| BM_MATRIX_DEMO_005 | intro_pattern + uid_seg_c + registration cohort | mutual engagement hint | 单点账号资料 | 行为序列、contact hash、反证 | 正常用户群未排除 | partial_matrix_support |
| BM_MATRIX_DEMO_006 | intro_pattern + adminaction + nickname | diversion hint | 单账号可疑 | 设备/IP、私信边、contact hash | 商家账号可能性未排除 | partial_matrix_support |
| BM_MATRIX_DEMO_007 | intro_pattern + uid_seg_d + 日期窗口 | interaction hint | 单点资料 | 行为序列、互动边、活动反证 | 正常活动批量模板未排除 | partial_matrix_support |
| BM_MATRIX_DEMO_008 | intro_pattern + adminaction + registration cohort | mutual follow hint | 单点资料 | 设备/IP、行为序列、contact hash | 正常互粉社区未排除 | partial_matrix_support |

## 4. Pattern Summary

### 4.1 Common Intro Pattern

| pattern | cases | interpretation | boundary |
|---|---|---|---|
| 一起互动 + 联系方式 redacted | 8/8 | 强资料模板聚集，适合作为账号矩阵召回入口 | 联系方式需 hash 化，简介不能直接处置 |

### 4.2 Common Adminaction

| adminaction_code | cases | interpretation | boundary |
|---|---|---|---|
| 2011262 | 8/8 | 样本内 code 完全一致，可能说明同类治理/命中背景 | 需确认 code 含义和触发上下文 |

### 4.3 Nickname Template

| template | cases | interpretation | boundary |
|---|---|---|---|
| 数字 + emoji + 近似中文字符组合 | 8/8 | 昵称生成模板化，支持账号池假设 | 昵称相似不能单独定性 |

### 4.4 Registration Age Cohort

| cohort | cases | interpretation | boundary |
|---|---|---|---|
| 约 110-188 天 | 8/8 | 可能为同一养号周期或投放批次 | 需注册来源、设备/IP和行为序列补证 |

### 4.5 UID Segment Cohort

| uid_segment | cases | interpretation |
|---|---|---|
| uid_seg_a | DEMO_001, DEMO_002 | 小号段聚集 |
| uid_seg_b | DEMO_003, DEMO_004 | 小号段聚集 |
| uid_seg_c | DEMO_005, DEMO_006 | 小号段聚集 |
| uid_seg_d | DEMO_007, DEMO_008 | 小号段聚集 |

### 4.6 Behavior Evidence Missing

| missing_evidence | priority | reason |
|---|---|---|
| 账号间关注/互粉/互动边 | P0 | 证明互动矩阵是否真实协同 |
| 私信/评论/导流链路 | P0 | 证明是否有导流闭环 |
| 联系方式归一化 hash | P0 | 验证联系方式是否同源 |
| 设备/IP/注册来源聚合 | P1 | 验证账号池基建 |
| 行为时间序列 | P1 | 验证同波次操作 |
| 正常活动模板反证 | P2 | 控制误伤 |

### 4.7 Suspected Attack / Abuse Path

| suspected_path | likelihood_in_sample | supporting_pattern | missing_evidence |
|---|---|---|---|
| 导流互动账号矩阵 | medium_to_high | 简介一致、联系方式线索、昵称模板 | 私信/评论/关注链路 |
| 互粉互评账号池 | medium | 一起互动文案、互粉 hint | 账号间互动边 |
| 养号账号池 | medium | 注册天数集中、UID 号段、模板资料 | 设备/IP/注册来源 |
| 正常活动模板误伤 | low_to_medium | 统一文案可能来自正常活动 | 活动/运营模板反证 |

## 5. Strategy Direction Draft

### Direction 1: 简介签名聚类

- candidate_direction: 对“一起互动 + 联系方式 redacted”做归一化聚类。
- required_evidence: intro_pattern、contact_hash、重复比例。
- boundary: 简介聚类只作召回入口，不直接处置。

### Direction 2: 联系方式归一化

- candidate_direction: 对薇 / 微信 / 符号拆分 / emoji 混淆做 redacted + hash 聚合。
- required_evidence: contact_hash_cluster、复用账号数、跨号段分布。
- boundary: 不输出联系方式明文。

### Direction 3: 账号矩阵识别

- candidate_direction: 将简介、昵称、adminaction、注册天数、UID 号段组合成账号矩阵候选。
- required_evidence: 多维共现 + 行为链路补证。
- boundary: 账号矩阵候选不是黑产结论。

### Direction 4: 行为链路补证

- candidate_direction: 补充关注、互粉、评论、私信、导流点击链路。
- required_evidence: account_edges、behavior_sequence、time_cohort。
- boundary: 行为链路用于补证，不能替代误伤评估。

## 6. 查杀分离 / AB 评估建议

- offline_eval: 评估样本覆盖、聚类纯度、正常模板重合。
- shadow_monitoring: 只记录候选命中，不处置。
- manual_review_sampling: 抽检商家账号、正常活动模板、真实社交用户。
- check_kill_separation: 召回/查证条件与处置条件分离。

## 7. Final Boundary

本 dry-run 只是模板样例：

- 不代表真实账号风险。
- 不代表真实平台结果。
- 不代表可上线策略。
- 不属于 ATO。
- 不输出自动处置建议。
