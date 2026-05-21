# ATO Batch Pattern Summary Template v1

## 1. 定位

本模板用于 5-20 个 ATO case 的批量模式聚合。它帮助发现共性路径、证据缺口和候选治理方向，但不输出自动策略上线结论。

## 2. Batch Metadata

| 字段 | 内容 |
|---|---|
| batch_id |  |
| case_count |  |
| source_channel |  |
| analysis_date |  |
| analyst |  |
| scope_boundary | 半自动归因，不调用真实平台，不自动处置 |

## 3. Common Entity Pattern

| pattern | case_ids | evidence_strength | interpretation | boundary |
|---|---|---|---|---|
| 同一设备 / 相似设备簇 |  |  | 可能存在设备侧聚集 | 关联关系不是风险定性 |
| 同一 IP 网段 / 地域突变 |  |  | 可能存在代理或异常接管 | IP 需脱敏，单点 IP 不强判 |
| 同一授权来源 / 活动页线索 |  |  | 可能存在 OAuth / 钓鱼链路 | 需要授权记录补证 |

## 4. Common Device / IP / Login Pattern

| dimension | common_pattern | affected_cases | missing_check | confidence |
|---|---|---:|---|---|
| device |  |  | device risk / graphData |  |
| ip |  |  | IP 脱敏聚合 / 登录来源 |  |
| login |  |  | online window / offline Hive |  |
| token |  |  | token 使用 / 刷新链路 |  |

## 5. Common Behavior Path

| behavior_path | case_ids | common_sequence | likely_path | counter_hypothesis |
|---|---|---|---|---|
| 点击外部链接后发布 |  | claim → authorization/token → publish | token/OAuth 滥用 | 本人误操作 / 家庭共用 |
| 登录验证后异常动作 |  | failed login → success → abnormal action | 新设备接管 | 在线日志窗口缺失 |
| 无明显登录但发生发布 |  | no visible login → publish | token/cookie 复用 | 登录日志超窗 / 数据缺口 |

## 6. Shared Missing Evidence

| missing_evidence | affected_cases | priority | why_it_matters |
|---|---:|---|---|
| 发布审计日志 |  | P0 | 判断发布来源和链路 |
| token / passToken 使用链路 |  | P0 | 判断凭证复用 |
| OAuth / 第三方授权记录 |  | P1 | 判断授权滥用 |
| 离线 Hive 登录日志 |  | P1 | 补足在线窗口缺失 |
| 审核 / 封禁工单 |  | P2 | 区分内容处置原因 |

## 7. Suspected Attack Path

候选路径排序：

| suspected_path | likelihood | supporting_cases | supporting_evidence | refuting_or_missing_evidence |
|---|---|---|---|---|
| token / cookie 复用发布链路 | high / medium / low |  |  |  |
| OAuth / 第三方授权滥用 | high / medium / low |  |  |  |
| 新设备盗号登录 | high / medium / low |  |  |  |
| 本机被控 / 恶意插件 | high / medium / low |  |  |  |
| 本人误操作 / 家庭共用 | high / medium / low |  |  |  |

## 8. Case Clustering Result

| cluster_id | cluster_name | case_ids | cluster_reason | confidence | recommended_next_check |
|---|---|---|---|---|---|
| cluster_1 | suspected_token_reuse |  | 无新设备可见但异常发布 |  | 发布审计 + token 使用 |
| cluster_2 | suspected_oauth_abuse |  | 活动页 / 授权线索聚集 |  | OAuth 记录 + scope |
| cluster_3 | insufficient_evidence |  | 关键证据缺失 |  | 补足 P0 evidence |

## 9. Confidence Level

- batch_confidence: high / medium / low
- confidence_reason:
- key_supporting_patterns:
- key_counter_patterns:
- key_missing_evidence:
- quality_risk:

## 10. Boundary Notes

- 批量聚合是模式总结，不是最终定性。
- 关联聚集不等于团伙作弊。
- 缺失证据不能被当作无风险。
- 样本量 5-20 只能支持候选策略方向和补证优先级，不支持直接全量上线。
