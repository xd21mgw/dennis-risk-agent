# Batch Risk Runtime Prompt Examples v1

These examples validate routing and response-shape behavior at text level only.

No real platform access. No DataAgent execution. DataAgent/Hive appears only as query plan where expected.

| case_id | user_prompt | expected_mode | actual_routing_by_current_docs | expected_response_shape | should_call_platform | should_call_DataAgent | context_inheritance_policy | failure_risk | pass_fail |
|---|---|---|---|---|---|---|---|---|---|
| BRR-001 | 这 10 个用户像不像一批 ATO？ | batch_clustering_mode | threshold policy says 10-49 -> batch_clustering_mode; ATO batch routing also supports batch pattern summary | threshold mode, cluster summary, representative samples, abnormal correlation matrix, missing evidence, follow-up plan | false | false | fresh_context unless same batch fingerprint exists | Might incorrectly deep-check all 10 or collapse into one ATO cluster | pass |
| BRR-002 | 这 4 个用户帮我查下是不是盗号 | small_multi_case_execution_mode | threshold policy says 3-4 -> small_multi_case_execution_mode; explicit query with <5 can full investigate | per-case concise evidence cards plus cross-case comparison | true_readonly_allowed | false | fresh_context for new entities; same_task only if continuing same four users | Might route to batch_plan_mode and refuse full investigation | pass |
| BRR-003 | 这 5 个用户看起来一批，帮我判断 | small_batch_mode | threshold policy says 5-9 -> small_batch_mode | light grouping, risk hypotheses, priority order, recommend full check or 3-5 samples | false_by_default | false | fresh_context unless same batch_id/entities/time_window | Might either over-execute all long chains or under-answer with generic plan | pass |
| BRR-004 | 这 100 个 uid 帮我判断是不是一批风险 | large_batch_aggregation_mode | threshold policy says 50-499 -> large_batch_aggregation_mode | aggregation plan, abnormal correlation dimensions, representative sampling, DataAgent/Hive query plan | false | false | fresh_context for new 100 uid batch | Might try one-by-one lookup or imply DataAgent execution | pass |
| BRR-005 | 这个接口请求量突然升高，是不是被爬？ | interface/request batch clustering | scene routing says interface/request spike -> batch clustering / population analysis depending scale | distinguish crawler, protocol direct call, business campaign, monitoring metric change; matrix + follow-up | false | false | fresh_context for new interface alert | Might directly strong-judge crawler | pass |
| BRR-006 | 这批告警帮我归因 | alert_batch_clustering | scene routing says alert batch -> batch risk clustering / secondary attribution | secondary attribution, clusters, representative samples, false-positive boundary, expansion | false | false | fresh_context for new alert batch | Might repeat strategy hit reason only | pass |
| BRR-007 | 这批活动渠道用户是不是假量？ | business-arbitrage clustering | scene routing says channel/campaign abnormal -> batch risk clustering | channel -> reward/retention/device_reuse matrix, normal channel counterexamples, grey plan | false | false | fresh_context for new channel batch | Might write generic "channel abnormal" without direction | pass |
| BRR-008 | 这些设备是不是群控？ | infrastructure correlation clustering | device group-control prompt maps to infrastructure correlation and representative sampling | device clusters, account clusters, IP/proxy/environment evidence boundary, same-gang caveat | false_by_default | false | fresh_context for device batch | Might treat device relation alone as cheating conclusion | pass |
| BRR-009 | 这些旧版本请求是不是协议上号？ | toolchain correlation clustering | old version + request pattern maps to toolchain correlation | old_version -> high_risk_behavior; mod/device_model -> request_pattern; field semantics boundary | false_by_default | false | fresh_context for request/version batch | Might misread mod=POST as HTTP method | pass |
| BRR-010 | 针对扫码/OAuth 类 ATO，应该怎么做灰度验证和误伤控制？848577102,495187398,5298282292 | strategy_recommendation_plan_mode | strategy plan priority says grey/false-positive/control design overrides user_id execution | strategy framework, grey validation, false-positive controls, monitoring, DataAgent/Hive query plan | false | false | methodology_mode; user ids are optional validation samples, not execution trigger | Might query the three users because IDs are present | pass |
| BRR-011 | 上一批 ATO 之后，这个新接口告警怎么看？ | fresh_context + interface/request batch clustering | context boundary says new risk domain / interface alert -> fresh_context; only methodology can be inherited | current alert first, no inherited ATO evidence, interface/request matrix and follow-up | false | false | fresh_context; inherit methodology only | Might contaminate interface alert with previous ATO evidence | pass |
| BRR-012 | 继续查一下吧 | context-dependent continuation | routing docs require task fingerprint before inheriting; same 4-user query -> small_multi_case_execution_mode; same 100-user batch -> continue aggregation/batch mode | if previous four users: per-case evidence/cross comparison; if previous 100 users: clustering/aggregation continuation | depends_on_prior_scope | false unless separately authorized; DataAgent plan only for 50+ | same_task_continuation only if same batch/entities/time_window; otherwise clarify/fresh_context | Might lose prior mode and suddenly deep-check 100 users | pass_with_context_dependency |

## Aggregate Findings

- 5 个以下允许全量深查: covered by BRR-002.
- 10+ 默认 batch_clustering: covered by BRR-001.
- 50+ 默认 aggregation / DataAgent-Hive query plan: covered by BRR-004.
- 策略建议带 user_id 仍 plan_mode: covered by BRR-010.
- 新批次 fresh_context: covered by BRR-011.
- abnormal correlation matrix appears in standard response: covered by response templates and BRR-001/005/007/008/009.
- no_data / timeout / blocked should remain source_gap: inherited from batch response boundary and evidence card rules.
