# Batch Risk Clustering Methodology v1

## 1. Method Goal

Batch clustering converts a flat case list into risk clusters, representative samples, abnormal correlations, evidence gaps and strategy actions.

It must not turn similarity into a gang conclusion without join keys or shared infrastructure evidence.

## 2. Workflow

1. Validate batch schema and threshold mode.
2. Normalize entities and time windows.
3. Generate L1 wide table / profile shallow query plan.
4. Use `batch_feature_table` to run TOP dimension drilldown.
5. Run frequent pattern / contribution analysis.
6. Build cluster candidates by dimension.
7. Build abnormal A -> B correlation matrix.
8. Compare with baseline if available; mark `baseline_missing` if not.
9. Apply domain lens overlay when relevant. For batch ATO / compromised-account suspicion, apply `ato_cluster_lens` on top of existing clusters.
10. Select representative samples.
11. Build cluster evidence cards.
12. Produce pattern summary and hypotheses.
13. Separate current evidence, historical similar pattern and missing evidence.
14. Produce follow-up plan and strategy / monitoring suggestions.

## 2A. L1 Batch Feature Layer

Use `batch_l1_feature_query_contract_v1.md` before abnormal matrix construction.

L1 layer output:

- `batch_feature_table`.
- `top_dimension_summary`.
- `frequent_pattern`.
- `contribution_score`.

DataAgent/Hive can later extract and aggregate this layer. Dennis Agent only plans, interprets, clusters and recommends.

L1 results feed:

- abnormal A -> B directed correlation matrix.
- cluster hints.
- representative case sampling.
- cluster evidence cards.
- expansion / strategy / monitoring candidates.

## 3. Entity Cluster

Cluster by:

- `user_id`
- `device_id`
- `ip`
- `phone_hash`
- `app_version`
- `channel`
- `campaign_id`
- `interface`
- `strategy_id`
- `login_method`
- `entry_source`

Boundary:

- UID / DID / IP are internal risk analysis entity fields.
- Phone plaintext must not be output; use `phone_hash` or safe_ref.
- Shared entity can support a cluster, but risk conclusion still needs behavior or source evidence.

## 4. Time Cluster

Cluster by:

- 集中爆发.
- 周期性.
- 活动窗口.
- 夜间 / 异常时间段.
- 策略上线前后.
- 版本发布前后.

Boundary:

- 时间集中是 risk clue, not final evidence.
- Campaign windows and product launches can create normal bursts.

## 5. Behavior Cluster

Cluster by:

- 登录.
- 发布.
- 评论.
- 私信.
- 关注.
- 提现.
- 下单.
- 助力.
- 接口请求.
- 前端行为缺失.
- 高风险动作链路.

Boundary:

- Behavior event proves occurrence, not necessarily malicious control.
- User claim and model inference cannot replace behavior evidence.

## 6. Environment Cluster

Cluster by:

- 设备型号.
- 系统版本.
- 客户端版本.
- 异常 mod 字段.
- 模拟器.
- root / hook / frida.
- 代理 / VPN.
- 异常网络环境.
- 多账号共设备.
- 多设备共账号.

Boundary:

- Device abnormality is supporting evidence, not standalone cheating / ATO conclusion.
- `mod=POST` or similar field names must be interpreted by field semantics; do not misread as HTTP method without source definition.

## 7. Strategy Cluster

Cluster by:

- 策略命中.
- 命中原因.
- 命中强度.
- 处置动作.
- 误伤反馈.
- 策略命中后行为.
- 策略未命中但异常集中的缺口.

Boundary:

- Strategy hit is evidence of model/rule response, not final human risk judgement.
- Strategy recall batches need secondary attribution and false-positive review.

## 8. Entry / Path Cluster

Cluster by:

- 扫码.
- OAuth.
- 一键登录.
- H5.
- Web.
- App.
- 协议直调.
- 外链入口.
- 投放渠道.
- 活动入口.

Boundary:

- Login or entry path must be linked to downstream abnormal action before being used as attack-path evidence.
- ATO Harmony / OAuth / one-key login must not be collapsed into credential stuffing.

## 9. Interface / Request Cluster

Cluster by:

- 请求量突增.
- 前端行为缺失.
- UA 异常.
- 版本异常.
- endpoint 集中.
- 参数模式异常.
- 请求时间间隔异常.
- response code 分布异常.

Boundary:

- Interface spike may be crawler, protocol direct call, retry storm, product launch or campaign traffic.
- Need frontend activity, UA, request interval, endpoint and response-code evidence before strong conclusion.

## 10. Abnormal Correlation Cluster

Use `abnormal_correlation_matrix_v1.md`.

Abnormal correlation is one of the core methods:

- A 条件下 B 是否异常集中.
- 是否高于正常基线.
- 是否覆盖足够比例.
- 是否解释工具链、基础设施、入口或策略漏洞.
- 是否单向或双向.

Without baseline, output `baseline_missing`.

Inputs from the L1 layer:

- TOP dimension concentration can create A -> B candidate relations.
- Frequent patterns with high contribution become candidate matrix rows.
- Contribution score can prioritize validation, but cannot upgrade to final risk judgement by itself.

## 10A. ATO / Compromised-Account Cluster Lens

Use `batch_ato_cluster_lens_v1.md` when the batch may contain stolen-account posting, non-trusted WEB / H5 / PC login, token / OAuth / scan / one-click control-chain abnormality, or common `device_id` with identity-variable drift.

This lens is additive:

- Keep existing content, device, strategy, time, account-profile and behavior clusters.
- Add `ato_cluster_lens_overlay` to each relevant cluster.
- Output whether the cluster is `existing_cluster_plus_ato_lens`, `web_untrusted_login_cluster`, `login_to_action_cluster`, `device_identity_inconsistency_cluster`, `compromised_account_cluster`, `content_abuse_only_cluster`, `mixed_cluster` or `insufficient_evidence_cluster`.

Required ATO lens checks:

- WEB / H5 / PC login commonality and whether login source shifted from historical APP.
- abnormal login method: token / OAuth / scan / one-click / refreshToken / passToken / byToken / resetPwd / kick out.
- `login_to_action_delta` between suspicious login/control event and publish, live, comment, private message, profile change or four-items change.
- `content_action_deep_dive` for representative samples: `photo_id` / `live_id` / `comment_id`, action time, publish source, publish device, IP / UA, audit / strategy / diversion reason and four-items if available.
- `device_identity_consistency`: device model, OS, app version, UA, browser fingerprint, IP / province / city / ASN, login source and login type. Common `device_id` cannot reduce ATO confidence unless these identity variables are also consistent.
- shared infrastructure: IP, ASN, UA, browser fingerprint, landing page, contact info, diversion wording and cadence.
- historical behavior shift: normal historical accounts suddenly publish diversion content or use a new WEB / control endpoint.

Representative deep dive:

- For every suspected ATO cluster, select 2-3 high-suspicion, 1-2 medium-suspicion, 1 boundary and 1 counter-example sample when available.
- Representative samples run the current ATO single-case realtime P0 chain: `login_logs_search + archives_user_profile + archives_user_analysis + archives_photo_search + track_analysis_check_data_ready -> multi-source suspicious anchor derivation -> candidate_control_endpoint_extraction -> device_identity_consistency -> historical_baseline_comparison -> business evidence card`.
- Backfill single-case findings to cluster level as `cluster_level_backfill`: `login_to_action_delta` distribution, identity inconsistency coverage, possible spoofing coverage, shared infrastructure coverage, content similarity, historical behavior shift, strategy-hit combination, source quality and missing evidence.

Boundary:

- Representative single-case proof does not prove every account in the full batch is stolen.
- Content diversion cluster + ATO lens hit should be written as "content diversion cluster with ATO stolen-account posting suspicion", not as mutually exclusive labels.
- Track activity cannot prove owner operation.
- Online login no_data, `response_too_large`, wrapper mismatch, blocked or timeout is `source_gap` / Hive-required evidence gap, not low-risk evidence.
- Admin APP-only login evidence cannot cover WEB/H5/PC/token/OAuth/scan control-chain evidence.
- Batch ATO long-window or incomplete realtime login/control evidence must use the account-security Hive registry first; no free table guessing and no DataAgent/Hive execution without authorization.
- Incomplete realtime control-chain evidence should surface `login_log_window_incomplete`, `admin_app_log_only_gap`, `web_control_chain_missing` and `offline_hive_required` in evidence gaps / next actions.

## 11. Evidence Boundaries

- current batch facts must come from `current_input` or `current_task_observation`.
- historical case can be similar pattern / hypothesis only.
- no_data 不能作为无风险反证.
- blocked/timeout/partial source 必须 source_gap.
- 不能仅凭相似性判断同团伙.
- 高频组合 / 高贡献度 only creates cluster hint or candidate feature hint.
- 批量共性不能证明每个账号被盗；ATO lens 必须通过覆盖率、相似度、反例和 source quality 回填置信度.
- 常用 `device_id` 不能排除 ATO；必须比较 `device_identity_consistency`.
- 身份证、手机号、实名信息 and credential-like fields are controlled auxiliary evidence and must not be output in plaintext.
