# Batch Risk Clustering Runtime Routing Dry Run v1

## 本轮目标

验证 Batch Risk Clustering Analysis Pack 是否能被 Dennis Risk Agent 的路由、回答模板和多入口 runtime 正确触发，而不是只停留在文档层。

本轮只做本地文档、样例、文本回归和 run log。

## 新增文件

- `computer_use_poc/batch_risk_clustering/batch_risk_runtime_prompt_examples_v1.md`
- `computer_use_poc/run_logs/batch_risk_clustering_runtime_routing_dry_run_v1.md`

## 修改文件

- `computer_use_poc/batch_risk_clustering/batch_risk_response_template_v1.md`
- `computer_use_poc/answer_experience_templates.md`

修改原因：

- 当前 routing 阈值已经覆盖。
- 但回答模板里的异常相关性矩阵字段偏简化，缺少 relation_family、evidence_basis、denominator_status、relationship_strength、reverse_check_result、confounder_risk、cannot_conclude_boundary。
- 本轮已补齐，避免 runtime response 只输出浅层 A -> B。

## 12 条 Routing Dry-run 结果

| case_id | prompt summary | expected_mode | result |
|---|---|---|---|
| BRR-001 | 10 个用户像不像一批 ATO | batch_clustering_mode | pass |
| BRR-002 | 4 个用户查盗号 | small_multi_case_execution_mode | pass |
| BRR-003 | 5 个用户看起来一批 | small_batch_mode | pass |
| BRR-004 | 100 个 uid 是否一批风险 | large_batch_aggregation_mode | pass |
| BRR-005 | 接口请求量突然升高 | interface/request batch clustering | pass |
| BRR-006 | 这批告警帮我归因 | alert_batch_clustering | pass |
| BRR-007 | 活动渠道用户是否假量 | business-arbitrage clustering | pass |
| BRR-008 | 这些设备是不是群控 | infrastructure correlation clustering | pass |
| BRR-009 | 旧版本请求是否协议上号 | toolchain correlation clustering | pass |
| BRR-010 | 扫码/OAuth ATO 灰度和误伤控制，附 3 个 user_id | strategy_recommendation_plan_mode | pass |
| BRR-011 | 上一批 ATO 后，新接口告警怎么看 | fresh_context + interface/request clustering | pass |
| BRR-012 | 继续查一下吧 | context-dependent continuation | pass_with_context_dependency |

## Key Checks

- 5 个以下是否允许全量深查：pass，BRR-002。
- 10+ 是否默认 batch_clustering：pass，BRR-001。
- 50+ 是否默认 aggregation / DataAgent-Hive query plan：pass，BRR-004。
- 策略建议带 user_id 是否仍 plan_mode：pass，BRR-010。
- 新批次是否 fresh_context：pass，BRR-011。
- abnormal correlation matrix 是否出现在标准回答结构中：pass，已补充 response template 字段。
- no_data / timeout / blocked 是否不会被当成无风险反证：pass，继承 evidence card 和 batch response boundary，必须 source_gap。

## 发现的问题

1. Routing 文档本身已经满足 threshold / intent / context 规则。
2. Response template 原本的异常相关性矩阵字段不够深，已补齐 relation_family、denominator、relationship_strength、reverse/confounder 和 cannot_conclude_boundary。
3. BRR-012 依赖上一轮 task fingerprint，无法仅凭短句独立定路由；必须读取上一轮 batch_id/entities/time_window/risk_domain 后决定 same_task_continuation 或 fresh_context。

## 是否需要补 routing / answer template

- routing：暂不需要补，现有 `scene_to_capability_routing.md` 已覆盖本轮 12 类触发。
- answer template：已补齐 batch risk clustering 中 abnormal correlation matrix 的深度字段。

## 是否建议进入 release patch 候选

建议进入 release patch 候选，但仍需 release 打包前 preflight。

## 未做事项

- 未访问真实平台。
- 未调用 DataAgent。
- 未修改 auth / gateway。
- 未重新打包 release。
- 未提交 git。
