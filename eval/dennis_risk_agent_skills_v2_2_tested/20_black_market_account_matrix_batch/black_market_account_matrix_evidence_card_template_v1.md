# Black Market Account Matrix Evidence Card Template v1

## 1. 定位

本模板用于单个账号矩阵样本的证据卡生成。它服务于导流互动、互粉互动、账号池、养号账号矩阵归因，不服务于 ATO 控制权异常判断。

## 2. Case Summary

| 字段 | 内容 |
|---|---|
| case_id |  |
| account_ref |  |
| uid_segment |  |
| nickname_pattern |  |
| intro_pattern |  |
| adminaction_code |  |
| registration_age_days |  |
| sample_date |  |
| observed_behavior |  |

## 3. Strong Evidence

| evidence | observed | supports | why_strong | boundary |
|---|---|---|---|---|
| 简介签名聚类 | pending | 账号矩阵 / 导流池 | 高度一致文案和联系方式归一化后同源 | 联系方式必须脱敏 |
| adminaction 一致 | pending | 同治理/命中背景 | 同一 code 在样本内高度一致 | code 需要上下文 |
| 多维聚集共现 | pending | 黑产账号池 | 昵称模板、注册天数、UID 号段、日期窗口同时聚集 | 不直接等于处置依据 |
| 行为链路补证 | pending | 导流互动 / 互粉互评 | 账号间有关注、评论、私信、互动边 | 需真实行为链路补证 |

## 4. Medium Evidence

| evidence | observed | supports | limitation |
|---|---|---|---|
| 昵称模板化 | pending | 账号批量生成 | 单独昵称相似可能误伤 |
| 注册天数 cohort | pending | 批量养号 | 可能是正常活动拉新 |
| UID 号段聚集 | pending | 批量注册或批次投放 | 需要注册来源/设备/IP补证 |
| 日期窗口集中 | pending | 同波次操作 | 需行为时间链路确认 |

## 5. Weak Evidence

| evidence | observed | why_weak |
|---|---|---|
| 单账号简介可疑 | pending | 单点资料不足以定性 |
| 人工备注“同波黑产” | pending | 备注需证据验证 |
| 单一 adminaction | pending | 缺上下文时不能强判 |

## 6. Counter Evidence

| counter_evidence | observed | refutes_or_limits |
|---|---|---|
| 正常活动统一模板 | pending | 可能解释简介一致 |
| 无互动/导流行为链路 | pending | 降低导流互动作弊支持 |
| 设备/IP/注册来源分散 | pending | 降低账号池聚集支持 |
| 账号自然历史行为 | pending | 支持正常用户或低置信 |

## 7. Missing Evidence

| missing_item | why_needed | priority |
|---|---|---|
| 联系方式归一化 hash | 判断同源联系方式 | P0 |
| 账号间互动边 | 判断互粉互评/导流互动 | P0 |
| 设备/IP/注册来源聚合 | 判断账号池基建 | P1 |
| 行为时间序列 | 判断同波次操作 | P1 |
| adminaction 上下文 | 判断 code 与黑产治理关系 | P1 |
| 正常活动/运营模板反证 | 控制误伤 | P2 |

## 8. Conclusion Support Level

可选值：

- strong_matrix_support
- partial_matrix_support
- insufficient_support
- counter_evidence_present
- not_evaluated

边界：support level 只表示账号矩阵 / 导流互动假设的证据支持程度，不是自动处置结论。
