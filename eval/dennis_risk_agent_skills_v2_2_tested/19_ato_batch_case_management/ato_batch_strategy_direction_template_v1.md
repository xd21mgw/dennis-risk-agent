# ATO Batch Strategy Direction Template v1

## 1. 定位

本模板用于从 ATO 批量模式摘要中沉淀候选策略方向。它不是自动策略上线文档，不产生处置动作，不替代人工评审和实验评估。

必须明确：

- 只能输出候选策略方向。
- 不能直接给自动上线结论。
- 不能直接给封禁、冻结、限流、放过等处置建议。
- 必须包含误伤风险、补证建议、AB / 查杀分离评估建议。

## 2. Strategy Direction Summary

| 字段 | 内容 |
|---|---|
| direction_id |  |
| direction_name |  |
| related_pattern_summary |  |
| affected_case_count |  |
| target_attack_path | token 复用 / OAuth 滥用 / 新设备接管 / 本机被控 / 待确认 |
| current_confidence | high / medium / low |
| recommended_stage | evidence_collection / offline_eval / shadow_monitoring / manual_review |

## 3. Candidate Rule Hypothesis

| component | draft |
|---|---|
| candidate_condition |  |
| strong_required_evidence |  |
| medium_supporting_evidence |  |
| negative_or_counter_evidence |  |
| exclusion_conditions |  |
| missing_evidence_before_eval |  |

边界：candidate_condition 只是策略假设，不得直接上线。

## 4. False Positive Risk

| risk | why_it_matters | mitigation |
|---|---|---|
| 家庭共用设备 / 本人误操作 | 可能误判正常用户 | 查常用设备、常用 IP、历史行为连续性 |
| 登录日志在线窗口不完整 | no_data 可能是假阴性 | 标记 offline_hive_required |
| OAuth 正常授权场景 | 授权并不必然恶意 | 结合 scope、时间、后续动作 |
| 设备异常单点命中 | 设备异常不等于账号被盗 | 必须结合账号行为和登录链路 |

## 5. Evidence To Collect Before Action

| evidence | priority | expected_value_if_true | expected_value_if_false |
|---|---|---|---|
| 发布审计日志 | P0 | 异常 IP / UA / token 链路 | 常用设备和常用来源 |
| token / passToken 使用链路 | P0 | 异常复用或刷新 | 正常本人链路 |
| OAuth 授权记录 | P1 | 新授权 / 异常 scope | 无新授权或正常 scope |
| 离线 Hive 登录日志 | P1 | 补足超窗登录 | 仍无证据但不能强反证 |
| 封禁/审核工单 | P2 | 内容处置上下文 | 与 ATO 不相关 |

## 6. AB / 查杀分离评估建议

建议先分层评估：

- offline_eval: 只评估命中率、覆盖、误伤样本，不影响用户。
- shadow_monitoring: 只记录候选命中和人工复核结果，不处置。
- check_kill_separation: 查证规则和处置规则分离，不用同一条件直接处罚。
- manual_review_sampling: 对高风险命中和疑似误伤样本做人工抽检。

评估指标：

- case_hit_rate
- confirmed_support_rate
- counter_evidence_rate
- missing_evidence_rate
- false_positive_review_rate
- user_appeal_risk
- action_precision_after_manual_review

## 7. Candidate Output Wording

推荐话术：

- “当前可形成一个候选策略方向：围绕 XXX 模式做离线评估和 shadow 监控。”
- “该方向需要先补足 XXX 证据，不能直接上线。”
- “建议采用查杀分离：先查证聚合和人工复核，再决定是否进入处置策略设计。”

禁止话术：

- “可以直接上线拦截。”
- “这批用户确认是盗号。”
- “命中该模式即可封禁。”
- “无登录记录所以排除 ATO。”

## 8. Manual Review Boundary

进入人工评审前必须检查：

- 是否存在强反证。
- 是否存在在线日志窗口缺口。
- 是否将用户申诉或人工备注当作事实。
- 是否把关联关系直接当风险结论。
- 是否明确误伤保护和退出条件。
