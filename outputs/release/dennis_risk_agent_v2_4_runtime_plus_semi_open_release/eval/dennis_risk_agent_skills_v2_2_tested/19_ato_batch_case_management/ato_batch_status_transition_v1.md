# ATO Batch Status Transition v1

## 1. 定位

本文件定义 ATO / 盗号 batch case analysis 的 case 与 batch 状态流转，确保从用户输入、字段校验、证据卡生成、模式聚合到人工复核边界都有明确状态。

状态流转不代表真实平台查询已经发生，也不代表可以自动处置用户。

## 2. case_status

| status | 含义 | 进入条件 | 下一步 |
|---|---|---|---|
| received | 已收到 case 原始输入 | 用户提交 case | 做 input contract 校验 |
| normalized | 已完成字段标准化 | 必填字段满足或可解析 | 生成 evidence card |
| needs_fields | 缺少关键字段 | 缺 user_id / event_time / abnormal_action 等 | 向用户补要字段 |
| evidence_ready | 证据卡可生成 | 至少有可用 evidence source | 进入支持等级判断 |
| needs_offline_hive | 在线来源不足，需要离线补查 | 登录日志超窗、长周期链路、批量聚合缺口 | 生成 DataAgent/Hive query plan，不直接调用 |
| partial_support | 部分证据支持 ATO，但未闭环 | 有中等证据或部分来源阻塞 | 补证或人工复核 |
| high_priority_review | 证据较强，建议人工优先复核 | 多来源强证据闭环 | 人工审核 / 策略评估 |
| not_recommended_for_action | 不建议处置 | 反证较强、来源不足或非 ATO 类型 | 暂缓动作或转其他场景 |

## 3. batch_status

| status | 含义 | 进入条件 | 下一步 |
|---|---|---|---|
| intake_received | 批量输入已收到 | 用户提交 5-20 cases | 执行 schema check |
| schema_checked | 输入契约检查完成 | 字段覆盖和规模已评估 | 生成单 case evidence card |
| evidence_card_generated | 单 case 证据卡已生成 | 每个 case 至少有状态 | 聚合 batch pattern |
| pattern_aggregated | 跨 case 模式已聚合 | 有 pattern summary | 检查 source coverage |
| source_checked | source coverage 已检查 | source / freshness / permission 风险已可见 | 草拟候选策略方向 |
| strategy_direction_drafted | 候选策略方向已输出 | strategy 仅为 candidate direction | 进入人工复核边界 |
| manual_review_required | 需要人工复核 | 存在 high priority 或处置前置需求 | 人工审核，不自动处置 |
| completed_with_gaps | 批量分析完成但有缺口 | 结论、缺口、下一步均已输出 | 等待补证或离线扩量 |

## 4. Case 状态推荐流转

| from | to | 触发条件 |
|---|---|---|
| received | normalized | 必填字段齐全且 case type 为 ATO |
| received | needs_fields | 缺少 user_id / event_time / abnormal_action |
| received | not_recommended_for_action | 明确不是 ATO 且不适合纳入本 batch |
| normalized | evidence_ready | 有平台、人工或离线来源可形成证据卡 |
| normalized | needs_offline_hive | event_time 超过在线登录日志可靠窗口，或长周期数据必需 |
| evidence_ready | partial_support | 有支持证据但缺少关键闭环 |
| evidence_ready | high_priority_review | 多来源证据较强，且误伤风险需人工评估 |
| evidence_ready | not_recommended_for_action | 反证明显或证据质量不足 |
| partial_support | needs_offline_hive | 关键缺口需要 Hive / 离线日志 |
| partial_support | high_priority_review | 补证后支持等级提升 |

## 5. Batch 状态推荐流转

```text
intake_received
→ schema_checked
→ evidence_card_generated
→ pattern_aggregated
→ source_checked
→ strategy_direction_drafted
→ manual_review_required
→ completed_with_gaps
```

说明：
- `completed_with_gaps` 是 v1 的正常结束状态，不代表所有证据已闭环。
- 如果 batch 内存在 `needs_offline_hive` case，输出必须包含离线补查问题清单。
- 如果 batch 内存在 high priority case，仍不能自动处置，只能进入人工复核。

## 6. 禁止状态跳转

| 禁止跳转 | 原因 |
|---|---|
| received → high_priority_review | 未做字段校验和证据卡，不能直接高优先级 |
| manual_input only → strong support | 人工输入不能单独形成强结论 |
| model_inference only → high_priority_review | 模型推断不是原始证据 |
| needs_fields → strategy_direction_drafted | 缺关键字段不能输出策略方向 |
| strategy_direction_drafted → auto_disposition | 本能力不支持自动处置 |
| strategy_direction_drafted → auto_strategy_launch | 策略只能是候选方向 |

## 7. 状态输出要求

每个 case 输出必须包含：
- `case_status`
- `status_reason`
- `required_next_input_or_evidence`
- `support_level`
- `manual_review_needed`

每个 batch 输出必须包含：
- `batch_status`
- `status_reason`
- `blocking_gaps`
- `safe_next_actions`
- `not_auto_disposition=true`

