# Batch Risk Response Template v1

Status: runtime_template

Use this template for the three Dennis batch attack-judgement modes. The output
must be chain-first and cluster-first, not a per-entity transcript.

Common boundary for all modes:

- `no_data` / timeout / blocked / auth_failed is source quality, not no-risk.
- Strategy hit is not final judgement.
- DataAgent/Hive pending is not verified evidence.
- DataAgent/Hive execution requires explicit per-call authorization.
- Wide-table correlation is not a complete attack-chain fact.
- Representative sample evidence does not prove full population coverage.
- Dennis recommends strategy candidates; it does not auto-launch or auto-dispose.

## 1. full_observation_mode

Applicable: 2-10 entities, small-batch full observation.

```text
一、批量结论
- 当前更像：
- 置信度：
- 不能强判的点：

二、实体扩展结果
- input_users / input_devices:
- entity_graph:
- high_degree_entities:
- unresolved_entities:
- entity_resolution_quality:

三、分 source 共性发现
- login_log_commonality_card:
- archive/admin profile commonality:
- Weapon graph/riskData commonality:
- RCP/Tianshi strategy commonality:
- Track/frontend behavior commonality:

四、多源融合判断
- strong_shared_signals:
- medium_shared_signals:
- conflicting_signals:
- counter_evidence:
- possible_normal_mixed_entities:

五、风险分簇
- cluster_summary_card:
- representative_entities:
- boundary_entities:
- counter_evidence_entities:

六、攻击链路还原
- attack_chain_renderer by cluster:
- strong / inferred / missing links:

七、候选特征与策略建议
- strategy_recommendation_card:
- priority: P0 | P1 | P2
- action_group: ready_for_controlled_gray_validation | combine_before_use | monitor_or_expand_only
- coverage / precision / false-positive boundary:
- required_validation_data:

八、缺失证据与下一步补查
- realtime source gap:
- offline query plan if authorized:
- representative follow-up:

九、结论边界
- not full-population proof:
- not auto-action:
```

Minimal output fragment:

```text
一、批量结论：10 个样本里 7 个共享 WEB 登录后异常发布链路，更像 ATO 后内容承接簇；2 个样本有稳定历史设备，单列为边界样本。
三、分 source 共性：登录日志 7/10 命中 WEB quickLogin；Weapon 6/10 共用 2 个 DID；策略命中 9/10 只能作为辅助。
五、风险分簇：cluster_A=疑似 WEB 接管发布，cluster_B=证据不足/正常混入。
```

## 2. sample_expand_validate_mode

Applicable: >10 entities, urgent / unknown / no wide-table yet.

```text
一、当前模式与抽样轮次
- selected_mode: sample_expand_validate_mode
- sampling_plan:
  - initial_sample_size:
  - sampling_method:
  - max_rounds:
  - max_deep_checked:
- initial_sample_size:
- max_rounds:
- max_deep_checked:

二、已查样本与 source 完成情况
- round_result:
  - round_id:
  - sampled_count:
  - sampled_entities:
  - source_completion:

三、每轮共性和累计覆盖
- main_shared_signals:
- coverage_in_round:
- cumulative_coverage:

四、风险簇和正常混入
- discovered_clusters:
- normal_or_counter:
- boundary_entities:

五、是否继续扩样 / 离线验证 / 停止
- decision.action: continue | offline_validate | stop
- decision.reason:

六、攻击链假设
- cluster_attack_chain:
- missing_links:

七、候选特征和策略建议
- strategy_recommendation_card:
- priority:
- action_group:

八、缺失证据与结论边界
- next_action_required_authorization:
- DataAgent/Hive authorization boundary:
- no auto full-batch realtime deep check:
```

Minimal output fragment:

```text
一、当前模式：sample_expand_validate_mode，第 2 轮，已深查 20/100。
三、累计覆盖：主簇两轮分别 8/10、7/10，累计约 75%，达到进入离线验证的默认条件。
五、决策：offline_validate。70% 只是验证阈值，不是自动处置阈值；DataAgent/Hive 需你确认后才执行。
```

## 3. wide_table_aggregate_mode

Applicable: wide table / features / coverage / precision / strategy /
historical review / DataAgent/Hive intent.

```text
一、DataAgent/Hive 统计范围
- input_summary:
- selected_registered_table:
- authorization_status:

二、字段质量
- usable_fields:
- low_coverage_fields:
- constant_fields:
- high_cardinality_fields:

三、Top 共性特征
- top_univariate_signals:

四、对照组差异 / 不可评估说明
- normal_support_rate:
- lift:
- if no control group: not_evaluable

五、组合特征覆盖
- candidate_feature_combinations:

六、分簇候选
- cluster_candidates:
- representative_samples:

七、代表样本细查建议
- suggested_followup_mode: full_observation_mode

八、攻击链解释
- statistical_chain_hypothesis:
- missing runtime evidence:

九、候选特征与策略建议
- strategy_recommendation_card:
- priority:
- action_group:

十、结论边界
- DataAgent returns statistics, Dennis interprets risk.
- No auto strategy launch.
```

Minimal output fragment:

```text
一、统计范围：计划使用注册候选宽表 ks_rc_bs.dws_risk_register_gang_user_week_feature_wide_di，当前仅生成 query plan，未调用 DataAgent/Hive。
四、对照组：本轮无 control group，precision/lift 不可评估，只能解释 case 内共性。
七、代表样本：建议从 cluster_A 抽高置信、边界、反证样本进入 full_observation_mode 细查攻击链。
```

## 4. source_completion_matrix Position

`source_completion_matrix` and raw debug metadata are audit material. User-facing
answers show concise source-quality summaries. Full routing/debug YAML appears
only in debug, run log, validation or explicit user request.
