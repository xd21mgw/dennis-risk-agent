# Black Market Account Matrix Pattern Summary Template v1

## 1. 定位

本模板用于黑产账号矩阵 / 导流互动 / 互粉互动 / 养号账号池的批量模式聚合。

它不是 ATO pattern summary。ATO 关注账号控制权异常；本模板关注账号资料、治理 code、注册 cohort、UID 号段、互动行为和导流链路聚集。

## 2. Batch Metadata

| 字段 | 内容 |
|---|---|
| batch_id |  |
| case_count |  |
| sample_window |  |
| source_channel |  |
| scope_boundary | 非 ATO；只做账号矩阵/导流互动 batch 样板 |

## 3. Common Intro Pattern

| intro_pattern | case_ids | normalized_contact | evidence_strength | boundary |
|---|---|---|---|---|
| 一起互动 + 联系方式 redacted |  | contact_hash_pending | high / medium / low | 联系方式不输出明文 |

## 4. Common Adminaction

| adminaction_code | case_ids | interpretation | missing_context | boundary |
|---|---|---|---|---|
| 2011262 |  | 样本内一致，可能对应同类治理/命中背景 | code 含义、触发上下文 | code 一致不等于自动处置 |

## 5. Nickname Template

| nickname_template | case_ids | template_features | evidence_strength | boundary |
|---|---|---|---|---|
| 数字 + emoji + 近似中文字符组合 |  | numeric_prefix / emoji / similar_cn_chars | medium | 昵称相似需结合行为链路 |

## 6. Registration Age Cohort

| age_range_days | case_ids | interpretation | boundary |
|---|---|---|---|
| 110-188 |  | 可能为同一养号批次或投放波次 | 需注册来源、设备/IP、行为序列补证 |

## 7. UID Segment Cohort

| uid_segment | case_ids | interpretation | boundary |
|---|---|---|---|
| uid_seg_a |  | 多号段聚集之一 | UID 号段只作 cohort，不输出明文 |
| uid_seg_b |  | 多号段聚集之一 | 需结合注册时间和行为 |
| uid_seg_c |  | 多号段聚集之一 |  |
| uid_seg_d |  | 多号段聚集之一 |  |

## 8. Behavior Evidence Missing

| missing_evidence | priority | why_needed |
|---|---|---|
| 账号间关注/互粉/互动边 | P0 | 判断是否为互粉互动矩阵 |
| 私信/评论/导流链路 | P0 | 判断是否有导流闭环 |
| 联系方式归一化 hash | P0 | 判断简介联系方式是否同源 |
| 设备/IP/注册来源聚合 | P1 | 判断账号池基建 |
| 行为时间序列 | P1 | 判断同波次自动化 |
| 正常活动模板反证 | P2 | 控制误伤 |

## 9. Suspected Attack / Abuse Path

| suspected_path | likelihood | supporting_pattern | missing_evidence |
|---|---|---|---|
| 导流互动账号矩阵 | high / medium / low | 简介一致、联系方式一致、互动行为 | 私信/评论/关注链路 |
| 互粉互评账号池 | high / medium / low | 昵称模板、注册 cohort、互动边 | 账号间边和行为节奏 |
| 养号账号池 | high / medium / low | 注册天数集中、UID 号段聚集、资料模板 | 设备/IP/注册来源 |
| 正常活动模板误伤 | high / medium / low | 统一模板可能来自正常活动 | 官方活动/运营模板反证 |

## 10. Confidence

- batch_confidence:
- key_supporting_patterns:
- key_missing_evidence:
- key_counter_evidence:
- quality_risk:

## 11. Boundary Notes

- 该聚合不代表 ATO。
- 简介和昵称聚类不是处置依据。
- 联系方式必须脱敏或 hash 化。
- 策略方向必须查杀分离、先评估后处置。
