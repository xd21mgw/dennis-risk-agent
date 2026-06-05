# Batch Risk Text Dry Run v1

Status: historical_validation_refreshed

This dry run applies the three-mode batch attack judgement contract to the
golden sample groups. It is text-level validation only: no real platform access,
no DataAgent/Hive execution, no auth / gateway change.

## Summary Table

| group | selected_mode check | clustering check | evidence boundary | overall |
|---|---|---|---|---|
| ATO mixed batch | `sample_expand_validate_mode` unless <=10 explicit small set | pass | pass | pass with ATO lens caution |
| Protocol downgrade | `sample_expand_validate_mode` or `wide_table_aggregate_mode` by scale | pass | pass | pass with field-semantics caution |
| Interface spike | `wide_table_aggregate_mode` when population/statistics intent | pass | pass | pass with baseline caution |
| Activity arbitrage | `wide_table_aggregate_mode` for channel cohort statistics | pass | pass | pass |
| Alert secondary attribution | `wide_table_aggregate_mode` for recall batch attribution | pass | pass | pass |

## Group Expectations

### ATO Mixed Batch

Expected answer:

- If 10 or fewer entities: `full_observation_mode`.
- If >10 urgent same-origin check: `sample_expand_validate_mode`.
- Split credential-stuffing candidate, Harmony/OAuth candidate,
  user-claim/source-gap, normal migration and content-abuse-only clusters.
- Apply `ato_cluster_lens` after existing content/device/strategy/time clusters.
- Never claim the full batch is stolen from representative samples alone.

### Protocol Downgrade / Forged Client

Expected answer:

- Select `sample_expand_validate_mode` for urgent unknown batches or
  `wide_table_aggregate_mode` for feature/statistical analysis.
- Split old-version high-frequency, DID mismatch, abnormal field semantics
  pending, and frontend activity gap.
- `mod=POST` is field content until schema confirms semantics.

### Interface Request Spike

Expected answer:

- Select `wide_table_aggregate_mode` for population spike / coverage analysis.
- Separate crawler/protocol candidate from campaign traffic and monitoring
  sampling artifacts.
- Without baseline/control group, emit `not_evaluable` for lift/precision.

### Activity Arbitrage / Channel Fake Volume

Expected answer:

- Select `wide_table_aggregate_mode` for channel cohort statistics.
- Separate channel-specific candidate clusters and normal high-reward channel
  counterexamples.
- Low retention remains derived business-quality evidence, not black-production
  proof.

### Internal Alert Batch Secondary Attribution

Expected answer:

- Select `wide_table_aggregate_mode` for strategy recall / alert population
  attribution.
- Strategy hit is input evidence, not final judgement.
- Recommend representative samples for `full_observation_mode` before converting
  statistical chains into stronger attack-chain claims.

## Cross-Group Findings

Strengths:

- Three current modes replace the old small/batch/large ladder.
- Entity graph, source commonality, fusion, cluster summary and attack-chain
  rendering are now required.
- Strategy candidates include both `priority` and `action_group`; P0 maps to
  controlled gray validation only, not auto-disposition.
- DataAgent/Hive remains query-plan or authorization-only.

Historical-only:

- Older golden answer files may still contain legacy mode names. They remain
  regression sources for content quality, not runtime routing truth.

## User-visible Render Regression

The following rendered samples use mock observations only. They verify user
answer feel: cluster-first, chain-first, no old mode names, no real platform
access, and no DataAgent/Hive execution.

### Case A: full_observation_mode Render

```text
一、批量结论
这 8 个 mixed user/device 里，5 个样本共享“集中登录窗口 + 高连接设备 +
目标行为承接”三类信号，更像同一批设备农场 / 群控候选；2 个样本有稳定
历史设备和连续登录基线，先列为正常混入；1 个样本证据不足。当前不能写
整批同团伙，只能写 cluster_A 有中高置信风险共性。

二、实体扩展结果
entity_graph：8 个输入扩展出 8 个 user、6 个 device、11 条 user-device
edge；d_cluster_01 关联 5 个风险样本，d_stable_02 / d_stable_03 只关联
各自历史稳定账号。entity_resolution_quality=partial，1 个 user 缺设备边。

三、分 source 共性发现
login_log_commonality_card：5/8 在 20 分钟内出现同 ASN / 相近 IP 段登录，
3/5 带 quickLogin/token refresh；2 个反证样本仍使用历史常用设备。login
no_data 的 1 个样本只记 source gap，不作无风险。
weapon_commonality_card：5/8 共享 1 个高连接 device cluster；同设备只是
扩散线索，不能单独定性团伙。
strategy_hit_commonality_card：6/8 命中相近策略 source_id；策略命中只作
辅助证据，不作为最终风险结论。

四、多源融合判断 / multi_source_fusion
strong_shared_signals：设备共性 + 登录窗口 + 行为承接三源在 5 个样本上对齐。
conflicting_signals：2 个样本历史设备稳定、行为时间不聚集。
counter_evidence：稳定设备、历史 IP 延续、无后置异常动作。

五、风险分簇
cluster_A：5/8，risk_type=group_control / device_farm，confidence=medium_high。
cluster_B：2/8，risk_type=normal_or_counter_evidence。
cluster_C：1/8，risk_type=normal_or_insufficient_evidence。

六、攻击链路还原
cluster_A attack_chain=partial_chain：entry_point=集中登录窗口；
infrastructure=高连接 device；behavior_execution=登录后目标行为承接；
missing_links=历史设备基线和完整后置行为明细。

七、推荐特征与策略优先级
strategy_recommendation_card:
- priority: P0
  action_group: ready_for_controlled_gray_validation
  feature_or_strategy: 高连接 device + 20 分钟集中登录 + 目标行为承接组合
  coverage_estimate: 5/8 sample estimate
  precision_estimate: pending_validation
  not_recommended_usage: 不单独用策略命中或同设备直接处置。
- priority: P1
  action_group: combine_before_use
  feature_or_strategy: 同 ASN / 相近 IP 段集中登录
- priority: P2
  action_group: monitor_or_expand_only
  feature_or_strategy: 单一 app_version 聚集

八、缺失证据与下一步补查
补历史设备基线、完整后置行为窗口、正常混入样本反证。若要扩大到更多账号，
需要用户授权离线回放或批量验证；本轮未调用 DataAgent/Hive。

九、结论边界
no_data 不是无风险反证；策略命中不是最终判断；代表样本不能证明全量覆盖；
Dennis 只给候选策略和灰度验证建议，不自动上线或处置。
```

### Case B: sample_expand_validate_mode Render

```text
一、当前模式与抽样轮次
selected_mode=sample_expand_validate_mode。sampling_plan：initial_sample_size=10，
sampling_method=random，max_rounds=5，max_deep_checked=50。本轮 mock 已完成
2 轮，深查 20/80。

二、已查样本与 source 完成情况
round_result R1：10 个样本，8 个命中“设备簇 + 集中登录 + 登录后目标行为”。
round_result R2：10 个样本，7 个命中同一主共性。source_completion：login /
device / behavior mock 均 completed；strategy_hit 仅辅助；无 DataAgent/Hive。

三、每轮共性和累计覆盖
coverage_in_round：R1=8/10，R2=7/10。cumulative_coverage=15/20=75%。
主共性跨两轮稳定，但仍只代表抽样样本，不等于 80 个全量已覆盖。

四、风险簇和正常混入
主簇 cluster_A：15/20，疑似同源设备簇 / 批控行为。
正常混入：3/20 有稳定历史设备或行为不承接。
证据不足：2/20 source gap 或关键字段缺失。

五、是否继续扩样 / 离线验证 / 停止
decision.action=offline_validate。原因：两轮均超过约 70% 默认验证阈值。
70% 是进入批量/离线验证的判断阈值，不是自动处置阈值。
next_action_required_authorization：全量 80 个覆盖验证、长窗口设备基线或
Hive/DataAgent 统计都需要用户明确授权。

六、攻击链假设
attack_chain=hypothesis_chain：集中登录 -> 高连接设备 -> 目标行为承接。
missing_links：全量覆盖、历史设备基线、正常混入边界。

七、候选特征和策略建议
- priority: P0
  action_group: ready_for_controlled_gray_validation
  feature_or_strategy: 高连接设备 + 集中登录 + 登录后目标行为组合
  coverage_estimate: 75% sample estimate
  precision_estimate: pending_full_batch_validation
- priority: P1
  action_group: combine_before_use
  feature_or_strategy: 同 IP/C 段集中登录
- priority: P2
  action_group: monitor_or_expand_only
  feature_or_strategy: 单一策略命中共性

八、缺失证据与结论边界
未授权 DataAgent/Hive 不写成已完成；代表样本结论不能直接等同全量覆盖；
策略命中本身不得作为 P0 策略；不自动上线、不自动处置。
```

### Case C: wide_table_aggregate_mode Render

```text
一、DataAgent/Hive 统计范围
selected_mode=wide_table_aggregate_mode。mock input_summary：500 case、500
features、7 天窗口、join_keys=[user_id, device_id]。本轮只使用 mock
wide_table_aggregate_report，不调用 DataAgent/Hive。

二、字段质量 / field_quality
usable_fields=126；low_coverage_fields=74；constant_fields=18；
high_cardinality_fields 包含 IP、device_id、UA，要求 Top values / 分桶 /
代表样本，不把全量原始值倒给 Dennis。

三、Top 共性特征
top_univariate_signals：device_degree_bucket>=5 覆盖 61%；login_hour_bucket
集中在 21-23 点覆盖 58%；frontend_duration_zero 覆盖 44%。这些是统计信号，
不是完整攻击链事实。

四、对照组差异 / 不可评估说明
control_group=partial / missing。normal_support_rate、lift、precision_estimate
均标 not_evaluable；只能输出 case 内共性和候选解释，不能声称准召已闭环。

五、组合特征覆盖
candidate_feature_combinations：device_degree_bucket>=5 + login_hour_bucket
21-23 + frontend_duration_zero，case_coverage=42%，normal_coverage=not_evaluable，
false_positive_risk=medium，需要代表样本细查。

六、分簇候选
cluster_A：设备农场 / 群控候选，sample_ratio=42%。
cluster_B：策略召回但无设备共性，sample_ratio=18%，可能是策略选择偏差。
cluster_C：证据不足或正常混入，sample_ratio=20%。

七、代表样本细查建议
representative_samples：从 cluster_A 抽高置信、边界、反证样本进入
full_observation_mode，验证登录、设备、行为链是否真实闭合。

八、攻击链解释
attack_chain=statistical_chain_hypothesis：统计上支持“高连接设备 -> 集中
登录 -> 前端活跃缺失”的协议/群控候选，但缺代表样本实时证据，不能写
complete_chain。

九、P0/P1/P2 策略建议
- priority: P0
  action_group: ready_for_controlled_gray_validation
  feature_or_strategy: 高连接设备 + 集中登录 + 前端活跃缺失组合
  coverage_estimate: 42% case estimate
  precision_estimate: not_evaluable
  rollout_suggestion: 只进入受控灰度验证，先补对照组和代表样本。
- priority: P1
  action_group: combine_before_use
  feature_or_strategy: device_degree_bucket>=5 单项
- priority: P2
  action_group: monitor_or_expand_only
  feature_or_strategy: 单一策略命中或单一 UA 聚集

十、结论边界
DataAgent/Hive pending 不等于已验证；DataAgent 做统计，Dennis 做风险解释；
无对照组不能评估 precision/lift；宽表相关性不能直接等同完整攻击链事实。
```

### Render Checklist Result

| case | conclusion | clusters | attack chain | strategy priority/action_group | boundary | feel |
|---|---|---|---|---|---|---|
| A full_observation | pass | pass | partial_chain | pass | pass | usable small-batch risk review |
| B sample_expand_validate | pass | pass | hypothesis_chain | pass | pass | usable sampling decision note |
| C wide_table_aggregate | pass | pass | statistical_chain_hypothesis | pass | pass | usable wide-table analysis report |
