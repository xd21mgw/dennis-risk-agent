# Batch Risk Runtime Prompt Examples v1

Status: validation_examples

These examples validate three-mode routing and response shape at text level
only. They do not access real platforms and do not call DataAgent/Hive.

| case_id | user_prompt | expected_mode | expected_response_shape | should_call_platform | should_call_DataAgent | failure_risk |
|---|---|---|---|---|---|---|
| BRR-001 | 这 8 个用户像不像一批 ATO？ | `full_observation_mode` | entity graph, source commonality, fusion, cluster summary, attack-chain boundary | readonly_allowed_when_execution_scope_safe | false | Might output per-user transcript only |
| BRR-002 | 这 10 个用户疑似同批异常，判断是否存在团伙化、套利化、策略绕过 | `full_observation_mode` | full observation across all 10, horizontal commonality first | readonly_allowed_when_execution_scope_safe | false | Might route to old `batch_clustering_mode` |
| BRR-003 | 这 100 个 uid 帮我先看看是不是一批风险 | `sample_expand_validate_mode` | round_result, cumulative_result, sample 10, max 5 rounds / 50 deep checks | sampled_readonly_only_if_execution_scope_safe | false | Might one-by-one check all 100 |
| BRR-004 | 这 300 个账号用宽表看覆盖率、准召和候选策略 | `wide_table_aggregate_mode` | wide_table_aggregate_report plan, control/lift boundary, representative follow-up | false | false_without_authorization | Might call Hive or request select * |
| BRR-005 | 这个接口请求量突然升高，是不是被爬？ | `sample_expand_validate_mode` or `wide_table_aggregate_mode` by scale/intent | clusters, source commonality or statistical report, crawler vs campaign vs monitoring boundary | false_by_default | false_without_authorization | Might directly strong-judge crawler |
| BRR-006 | 这批告警帮我归因 | `sample_expand_validate_mode` or `wide_table_aggregate_mode` by scale/intent | secondary attribution, false-positive boundary, strategy-hit-not-final | false_by_default | false_without_authorization | Might repeat strategy hit reason only |
| BRR-007 | 这批活动渠道用户是不是假量？ | `sample_expand_validate_mode` or `wide_table_aggregate_mode` | channel clusters, retention/reward/device commonality, strategy candidates | false_by_default | false_without_authorization | Might write generic "channel abnormal" |
| BRR-008 | 这些设备是不是群控？ | `full_observation_mode` if <=10 else `sample_expand_validate_mode` | entity graph, high-degree devices, device/user clusters, counter evidence | readonly_allowed_when_execution_scope_safe | false | Might treat same device as final cheating |
| BRR-009 | 这些旧版本请求是不是协议上号？ | `sample_expand_validate_mode` or `wide_table_aggregate_mode` | request/toolchain commonality, field semantics boundary | false_by_default | false_without_authorization | Might misread field semantics |
| BRR-010 | 针对扫码/OAuth 类 ATO，应该怎么做灰度验证和误伤控制？848577102,495187398,5298282292 | plan/report mode | strategy framework and validation samples; ids are optional examples | false | false | Might query ids because they are present |
| BRR-011 | 上一批 ATO 之后，这个新接口告警怎么看？ | fresh_context + selected three-mode path | current alert first, no inherited ATO evidence | false_by_default | false_without_authorization | Might contaminate new alert with prior batch evidence |
| BRR-012 | 继续查一下吧 | context-dependent continuation | same task only if task fingerprint matches; otherwise ask/fresh context | depends_on_prior_scope | false_without_authorization | Might lose prior mode or inherit wrong batch |

Aggregate findings:

- 2-10 entities -> `full_observation_mode`.
- 10+ urgent / unknown / no-wide-table -> `sample_expand_validate_mode`.
- 10+ wide-table / strategy / coverage / retrospective -> `wide_table_aggregate_mode`.
- DataAgent/Hive remains authorization-only.
- Golden answers and old dry runs with legacy mode names are historical
  regression sources, not current runtime routing truth.
